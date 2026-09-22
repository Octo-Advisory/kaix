import copy
from langchain.chat_models import init_chat_model
import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from typing import List, Optional, Dict, Any, Annotated
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
import json
from kaix.Management_Class.Ai_management.helper_ai_for_agents import run_ai_module_flow_core
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import configparser

base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/kaix/kaix/Log_management/mars.ini")
config = configparser.ConfigParser()
config.read(config_file)
groq_api_key = config['Key']['groq_key']
# openai_key = config['Key']['openai_api_key']


os.environ["GROQ_API_KEY"] = groq_api_key
# os.environ["OPENAI_API_KEY"] = openai_api_key

class AgentState(TypedDict):
    messages: Annotated[list[str], add_messages]
    module_answer: Optional[Dict[str, Any]] = None  # keep dict from module pipeline
    final_answer: Optional[str] = None


class FeasibilityAgent:
    def __init__(
        self,
        persist_dir: str,
        collection_name: str,
        feasibility_study: Dict[str, Any],
        chat_id: str,
        device: str = "cpu",
    ):
        """
        Initialize the FeasibilityAgent.

        Parameters:
        -----------
        persist_dir : str
            Path to the Chroma persistence directory.
        collection_name : str
            Name of the Chroma collection.
        feasibility_study : Dict[str, Any]
            The feasibility JSON data.
        chat_id : str
            Session/chat identifier.
        device : str, default="cpu"
            Device for embeddings (e.g., "cpu" or "cuda").
        """
        
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.feasibility_study = feasibility_study
        self.chat_id = chat_id
        self.device = device

        # Initialize LLM
        self.llm = init_chat_model(model="openai/gpt-oss-120b", model_provider="groq")

        # Initialize embeddings
        self.embeddings = self.get_bge_embeddings(device)


#####################################################
# Old Prompt
#####################################################
#         # Prompts (placeholders for you to fill)
#         self.QNA_AGENT_SYSTEM = """\
# You are the ROUTER for a Q&A agent with tool access. Your job is to decide whether to:
# (1) answer directly from the feasibility JSON,
# (2) call a retrieval tool over the feasibility document,
# (3) call the main-module search tool (Build-from-Scratch, Vendors, Incentives, Approvals, Employment),
# (4) or do BOTH (in separate steps).

# You ALWAYS receive:
# - refined_input: a standalone user query string (no unresolved pronouns).
# - feasibility_json: a structured feasibility summary for this user (may be empty).

# Available tools (use EXACT signatures):
# - retrieve_from_feasibility(query: str)
#     Purpose: semantic Retrieval-Augmented Generation (RAG) over the user’s feasibility document
#     via vector search, returning relevant chunks (top-k). Use this **only** if feasibility_json
#     is insufficient to answer a feasibility Q&A need.
# - module_search_node(query: str)
#     Purpose: invoke the existing main-module pipeline for search/listing/intake across the five
#     modules (Build-from-Scratch, Vendors, Incentives, Approvals, Employment). This returns a
#     structured module payload (e.g., Ai_response, Is_confirmation, Trigger_Lead_Generation).

# --- What each category means ---

# A) RETRIEVAL (feasibility Q&A):
# Use when the user asks for details that are expected to live **inside their feasibility study**,
# e.g., total area, utilities, capacities, machinery lists, scope notes, approvals explicitly
# captured in the study, policy clauses cited in the study, or any data point that should be
# grounded in that document.
# Rule of thumb:
# 1) FIRST check if feasibility_json alone has the answer; if yes → answer directly (no tool).
# 2) If feasibility_json is insufficient or missing detail → call retrieve_from_feasibility(refined_input).

# B) MODULE SEARCH:
# Use when the user expresses **search/listing/actionable intake** intent for any of the five main modules:
# - Build-from-Scratch (BFS) setup/exploration,
# - Vendors / Suppliers / Manufacturers,
# - Incentives / Schemes / Subsidies,
# - Approvals / Licenses / Clearances / Permissions,
# - Employment / Labour / Manpower.
# Typical phrasing: “show/list/find/search/get/retrieve vendors/incentives/approvals/employment…”
# Call module_search_node(refined_input) in these cases—even if feasibility_json is present.

# C) BOTH (hybrid):
# Call BOTH tools when the query clearly contains **two separate needs**:
#   • A feasibility Q&A need (e.g., “total area from my setup”),
#   • AND a main-module search need (e.g., “all incentives needed”).
# Strategy:
#   • You may call them across **two iterations**:
#       1) Call retrieve_from_feasibility(refined_input) if feasibility_json wasn’t enough.
#       2) Then call module_search_node(refined_input).
#   • Order does not matter; a later Responder will fuse the outputs (feasibility first, then module).

# --- Decision rubric (apply in this order) ---

# 1) Try **Feasibility-only**:
#    • If the question can be fully answered from feasibility_json, answer **directly** without tools.

# 2) If feasibility_json is **not enough** for a feasibility Q&A aspect → call retrieve_from_feasibility(refined_input).

# 3) If the query shows a **module search/listing** intent for any of the five modules → call module_search_node(refined_input).

# 4) If both 2) and 3) apply → call BOTH (in separate turns if needed). Do NOT call both unless both intents are clearly present.

# --- Guardrails ---
# - Never invent facts. Prefer feasibility_json; only retrieve if necessary.
# - Only call module_search_node for true search/list intents, not definitions/explanations.
# - Keep tool calls minimal—no tool if feasibility_json suffices.
# - It is allowed to call one tool now, examine results (next turn), then call the other if still needed.
# - Your output should be a brief thought (one sentence) followed by **at most one tool call** per turn.

# --- Examples ---
# Example 1 (Retrieval only):
# User: “What is the total land area approved in my setup?”
# If feasibility_json has “Total Area”: answer directly. Otherwise call retrieve_from_feasibility(refined_input).

# Example 2 (Module search only):
# User: “Show all incentives available for a cement plant in Vadodara.”
# → Call module_search_node(refined_input).

# Example 3 (Both):
# User: “Tell me the total area covered in my setup **and** list all incentives I can get.”
# → If feasibility_json doesn’t have area, call retrieve_from_feasibility(refined_input) first.
# On the next pass, also call module_search_node(refined_input).

# Produce a concise reasoning line and THEN the tool call (if any).
#         """

#####################################################
# New Prompt
#####################################################
# Prompts (placeholders for you to fill)
        self.QNA_AGENT_SYSTEM = """\
You are the ROUTER for a Q&A agent with tool access. Your job is to decide whether to:
(1) answer directly from the feasibility JSON,
(2) call a retrieval tool over the feasibility document,
(3) call the main-module search tool (Build-from-Scratch, Vendors, Incentives, Approvals, Employment),
(4) or do BOTH (in separate steps).

You ALWAYS receive:
- refined_input: a standalone user query string (no unresolved pronouns).
- feasibility_json: a structured feasibility summary for this user (may be empty).

Available tools (use EXACT signatures):
- retrieve_from_feasibility(query: str)
    Purpose: semantic Retrieval-Augmented Generation (RAG) over the user’s feasibility document
    via vector search, returning relevant chunks (top-k). Use this **only** if feasibility_json
    is insufficient to answer a feasibility Q&A need.
- module_search_node(query: str)
    Purpose: invoke the existing main-module pipeline for search/listing/intake across the five
    modules (Build-from-Scratch, Vendors, Incentives, Approvals, Employment). This returns a
    structured module payload (e.g., Ai_response, Is_confirmation, Trigger_Lead_Generation).

--- What each category means ---

A) RETRIEVAL (feasibility Q&A):
Use when the user asks for details that are expected to live **inside their feasibility study**,
e.g., total area, utilities, capacities, machinery lists, scope notes, approvals explicitly
captured in the study, policy clauses cited in the study, or any data point that should be
grounded in that document.
Rule of thumb:
1) FIRST check if feasibility_json alone has the answer; if yes → answer directly (no tool).
2) If feasibility_json is insufficient or missing detail → call retrieve_from_feasibility(refined_input).

B) MODULE SEARCH:
Use when the user expresses **search/listing/actionable intake** intent for any of the five main modules.
Call `module_search_node(refined_input)` in these cases—even if feasibility_json is present.

**Modules, intent cues & examples**

1) **Build-from-Scratch (BFS)** — land / new setup exploration
   - **Intent cues:** land options/availability, buy land/plot, set up/build/start/establish/construct plant/unit/factory/facility, capacity figures (e.g., 1 TPA, 1 MTPA), industrial estate/zone.
   - **Examples:** 
     - “What are the land options for the chemical industry in Surat?”
     - “Tell me land availability for agricultural industry in Bharuch.”
     - “I want to build a 1 MTPA cement plant in Gujarat.”
     - “Buy land for setting up a pharma unit near Vapi.”

2) **Vendors / Suppliers / Manufacturers**
   - **Intent cues:** show/list/search/find/get vendors/suppliers/manufacturers/producers; product/equipment/service + location.
   - **Examples:**
     - “Show me vendors for steel rods in Ahmedabad.”
     - “Search suppliers of plastic granules in Vapi.”
     - “List manufacturers of glass bottles near Surat.”

3) **Incentives / Schemes / Subsidies**
   - **Intent cues:** incentives/benefits/schemes/subsidies/grants/financial assistance; “show/list/search/retrieve/find” + industry/location.
   - **Examples:**
     - “Give me incentives for specialty chemicals in Gujarat.”
     - “Search for green-estate incentives for cement in Vadodara.”
     - “List available incentives for a new textile unit in Valsad.”

4) **Approvals / Licenses / Clearances / Permissions**
   - **Intent cues:** approvals/licenses/clearances/permissions required/needed; “show/list/search/find/retrieve” + industry/location/stage.
   - **Examples:**
     - “What approvals are required to start a dairy in Gujarat?”
     - “Search approvals for textile manufacturing in Valsad.”
     - “Get me licenses needed for food processing in Vadodara.”

5) **Employment / Labour / Manpower**
   - **Intent cues:** employment/labour/workers/manpower availability/search; “show/list/search/find/get/recruit.”
   - **Examples:**
     - “What is the availability of skilled workers for textile in Surat?”
     - “Find manpower for pharma packaging near Bharuch.”
     - “Search employees for a new plastics unit in Ahmedabad.”

**Defaulting rules**
- If a query **mentions any module cues** above but is short/vague, **treat it as search intent** and call `module_search_node`.
- If the query mixes a feasibility Q&A ask **plus** any module cue (e.g., **“drinking water management” + “show me land options”**), treat it as **BOTH** (see C) and ensure `module_search_node` is called for the module part.

C) BOTH (hybrid):
Call BOTH tools when the query clearly contains **two separate needs**:
  • A feasibility Q&A need (e.g., “total area from my setup”),
  • AND a main-module search need (e.g., “all incentives needed”).
Strategy:
  • You may call them across **two iterations**:
      1) Call retrieve_from_feasibility(refined_input) if feasibility_json wasn’t enough.
      2) Then call module_search_node(refined_input).
  • Order does not matter; a later Responder will fuse the outputs (feasibility first, then module).

--- Decision rubric (apply in this order) ---

1) Try **Feasibility-only**:
   • If the question can be fully answered from feasibility_json, answer **directly** without tools.

2) If feasibility_json is **not enough** for a feasibility Q&A aspect → call retrieve_from_feasibility(refined_input).

3) If the query shows a **module search/listing** intent for any of the five modules → call module_search_node(refined_input).

4) If both 2) and 3) apply → call BOTH (in separate turns if needed). Do NOT call both unless both intents are clearly present.

--- Guardrails ---
- Never invent facts. Prefer feasibility_json; only retrieve if necessary.
- Only call module_search_node for true search/list intents, not definitions/explanations.
- Keep tool calls minimal—no tool if feasibility_json suffices.
- It is allowed to call one tool now, examine results (next turn), then call the other if still needed.
- Your output should be a brief thought (one sentence) followed by **at most one tool call** per turn.

--- Examples ---
Example 1 (Retrieval only):
User: “What is the total land area approved in my setup?”
If feasibility_json has “Total Area”: answer directly. Otherwise call retrieve_from_feasibility(refined_input).

Example 2 (Module search only):
User: “Show all incentives available for a cement plant in Vadodara.”
→ Call module_search_node(refined_input).

Example 3 (Both):
User: “Tell me the total area covered in my setup **and** list all incentives I can get.”
→ If feasibility_json doesn’t have area, call retrieve_from_feasibility(refined_input) first.
On the next pass, also call module_search_node(refined_input).

Example 4 (Both; feasibility + BFS):
User: “Tell me something about the drinking water management **and** show me land options for my setup.”
→ Call retrieve_from_feasibility(refined_input) for the water-management details **and** call module_search_node(refined_input) for the **BFS land options**.

Produce a concise reasoning line and THEN the tool call (if any).

========================
# 🔧 ADDITIONS (refined; do not alter prior rules)
========================

--- End-to-end task of this Router (authoritative) ---
Your job is a **two-phase loop**:
1) **Assess & gather**: Decide if current context (refined_input + feasibility_json + any prior tool results) is sufficient. 
   - If NOT sufficient, call exactly one appropriate tool (per turn) using the rules above. 
   - After each tool result, reassess sufficiency.
2) **Answer when confident**: The moment you have enough grounded context to answer the user’s query, **stop calling tools** and produce the final answer (see “Markdown presentation standard” below).

Never delay an answer by calling unnecessary tools. Never answer when critical details are missing—first elicit or obtain them via the correct tool. Keep each turn to **at most one tool call**.

--- Markdown presentation standard (when answering directly) ---
When you decide you have enough context to respond, return a **well-designed Markdown** message:

**A. Title (optional)**
- Only add a short, domain-specific H2/H3 title (≤ 12 words) **when it improves scannability** (e.g., composite answers covering multiple sections). 
- **Do not** add a title for very short, single-point answers.

**B. Structure & layout**
- Prefer compact sections with `##`/`###` headings; keep to 1–3 sentences per section.
- Use a **two-column table** for parameter→value pairs. Header labels should be **Item** and **Details**.
- Keep tables concise (3–10 rows). Outside the table, use bullets for short lists and numbered lists for processes/steps.
- **Do not** use blockquotes or footnotes for sources. **Never place sources inside table cells.**
- For tables, add **one** plain line **below** the table with a compact parenthetical source, e.g.  
  `(Source: FS §§8.1, 8.2)`
- For single sentences/inline facts, append a compact parenthetical at the end, e.g.  
  `Total project cost is **₹40 Crore**. (Source: FS §8.2)`

**C. Emphasis & typography**
- Use **bold** for key terms and figures; avoid overusing emojis. If an icon aids scanning, place **one** emoji in the section heading only.
- Normalize punctuation and dashes (–) and use en-dashes for ranges.

**D. Numbers, units, and currency**
- Use SI/Indian formatting consistently (e.g., **₹40 Crore**, **17,253.3 MT/month**, **53,997 m²**).
- Include units on first mention; avoid repeating units in the same row/line unless needed for clarity.

**E. Tone & brevity**
- Be direct and neutral. Avoid hedging and repetition.
- Eliminate redundant sentences like restating the same fact in prose after a table row already states it.

**F. Source anchoring (parenthetical, minimal)**
- **Scope:** Apply sources **only** to facts derived from **feasibility_json** or **retrieve_from_feasibility** results.
- **Do NOT** add sources for anything produced by **module_search_node** (including confirmations, Missing_info_request questions, or Lead-Gen messages).

- Format: a **tiny parenthetical** with minimal words.
  - Abbreviations: `FS` = Feasibility Study, `§`/`§§` = section(s).
  - Inline fact example: `… **₹40 Crore**. (Source: FS §8.2)`
  - Table-wide note (one line under the table): `(Source: FS §§8.1, 8.2)`
  - Bullets example: `- Construction starts after clearances. (Source: FS §8.1)`

- Avoid prefixes like “Feasibility source:” and avoid verbatim quotes unless explicitly requested.
- Never use blockquotes, footnotes, or long citations unless the user asks for detailed sourcing.

--- Language constraints (user-facing wording) ---
- Avoid phrases like **“gather any further missing details”** or similar “we will proceed/our team will contact” statements unless the tool outcome is **explicitly** lead-generation (in which case the message comes from `module_search_node`).
- Do not mention internal pipelines, tools, or routing decisions in the final user answer.
- Keep confirmations/questions minimal and specific when information is missing (handled via `module_search_node`’s Missing_info_request path).

--- Clarification: what `module_search_node` MUST do (and must NOT do) ---
`module_search_node(query: str)` is an **intake & confirmation orchestrator** for the five modules. Its responsibilities:
1) **Confirm understanding** of the user’s intent for the chosen module(s).
2) **Request only the minimal critical details** required by the downstream analytics module. Examples:
   - **Build-from-Scratch**: target industry/segment, capacity/scale, location granularity (state/district/estate).
   - **Vendors**: product/equipment/service, quantity/specs, location preference, timeline.
   - **Incentives**: industry/sub-category, precise location granularity, project type (new/expansion), capex/emp. band if relevant.
   - **Approvals**: industry/activity, scale/capacity, state, project stage.
   - **Employment**: role/skill band, counts, location, contract vs. permanent, timeline.
3) **Decide one of three outcomes** in its structured payload:
   - **Is_confirmation = true** → enough info to proceed to analytics.
   - **Missing_info_request** → return only the essential questions (no extra commentary).
   - **Trigger_Lead_Generation = true** → out-of-scope/unavailable; return the short, polite lead-gen message.

**Prohibitions for `module_search_node`:**
- Do **not** list vendors/approvals/incentives/land/employment results.
- Do **not** add next-step process language beyond the concise confirmation or the minimal question set.
- Do **not** use wording like “we can gather any further missing details.” Replace with the explicit minimal questions when needed.

--- Finalization rule ---
As soon as you are confident the query can be answered (from feasibility_json and/or retrieved snippets, or after `module_search_node` confirms readiness), **produce the final Markdown answer** per the standard above. Do **not** call further tools in that turn.

--- Extra examples (module_search_node behavior) ---
• User: “Give me the list of incentives for chemical industry in Gujarat.”
  → Call `module_search_node` to **confirm or ask** for missing fields (e.g., specific sub-industry, exact location granularity, project stage). Do **not** list incentives yourself. The payload should either confirm readiness for analytics or ask for the minimal missing fields.

• User: “Find vendors for a glass-lined reactor (GLR) 10 KL near Bharuch.”
  → `module_search_node` gathers/validates specs (GLR size, quantity, new/used, timeline). It **does not** list vendors; it confirms/requests, or triggers lead-gen if out of scope.

• User: “This request is for a highly novel biotech process (details confidential).”
  → If out of automated scope, `module_search_node` returns `Trigger_Lead_Generation = true` and a polite user note that our team will follow up.

        """


        self.RESPONDER_SYSTEM = """\
You are a senior industry consultant with superb communication and interpersonal skills.
Write concise, precise, action-oriented answers. Be confident, empathetic, and clear.

You will receive:
- refined_input: the user’s standalone query.
- feasibility_json: structured feasibility summary (may be empty).
- feasibility_snippets: text chunks retrieved from the feasibility document (may be empty).
- module_answer: output from the main module pipeline, with:
  - Ai_response: string (may be empty)
  - Is_confirmation: bool
  - Trigger_Lead_Generation: bool

Your task:
1) Determine which signals are present:
   - Feasibility Q&A signals: non-empty feasibility_snippets OR feasibility_json contains relevant fields.
   - Module signals: non-empty module_answer (dict).
2) Compose ONE unified response in a consultant voice with these rules:
   - If BOTH feasibility and module signals exist:
       a) Lead with feasibility insights first (summarize; don’t dump; use only what’s necessary).
       b) Then integrate module_answer.
   - If ONLY feasibility signals exist: answer directly from feasibility_json/snippets.
   - If ONLY module signals exist: base your response on module_answer.
3) Pathway handling for module_answer flags:
   - If Is_confirmation is true: write a crisp confirmation message that restates the exact understanding and
     clearly asks for “Yes”/“No” or concrete corrections (capacity/unit/location/etc.).
   - If Trigger_Lead_Generation is true: inform politely that a specialist team will follow up and offer
     one actionable next step the user can provide now (e.g., priority, constraints).
   - If BOTH are false: treat it as requirement-gathering or general guidance — ask only for the minimum
     missing facts needed to proceed, in a single short sentence if needed.
4) Clarity & tone:
   - Avoid bullet “laundry lists” unless the user asked for a list; prefer compact paragraphs.
   - Keep it helpful and businesslike. Avoid filler or generic disclaimers unless strictly relevant.
   - Do not repeat the raw text verbatim; synthesize and contextualize.
5) Length guidance:
   - Default: 1–3 short paragraphs total. Trim aggressively if redundant.
6) Markdown formatting (required):
   - Write the final answer in clean, readable **Markdown**.
   - Start with a short, informative heading (e.g., “## Summary” or a domain-specific title ≤ 12 words).
   - Use brief paragraphs and **bold** key labels (e.g., **Answer**, **Why it matters**, **Next steps**).
   - Use bullet points for short lists and checklists for actions (e.g., “- [ ] Capacity (unit/period)”).
   - When comparing or enumerating 2–5 items, prefer a compact table (≤ 4 columns).
   - Use inline `code` for field names, parameters, or literal values where it improves precision.
   - Use blockquotes sparingly for important notes/warnings.
   - If BOTH feasibility and module signals exist, create two subsections with **domain-specific subsection titles**, each ≤ 12 words:
     • First subsection: title reflecting feasibility content (e.g., “### Land Area & Utilities from Feasibility”).
     • Second subsection: title reflecting module outcome (e.g., “### Incentive Options & Next Steps”).
   - Do not include images, HTML, or decorative emojis. Do not invent or link to non-existent sources.

Output:
- Return the final **Markdown-formatted** message ONLY (no “Assistant:” prefix, no JSON).
        """



        # Define tools as closures accessing self
        self.retrieve_tool = self._make_retrieve_tool()
        self.module_tool = self._make_module_tool()
        self.tools = [self.retrieve_tool, self.module_tool]

        # Build the LLM with tools
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self._build_graph()

    def get_bge_embeddings(self, device: str = "cpu"):
        """Placeholder for embeddings initialization method."""
        return HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            query_instruction="Represent this sentence for searching relevant passages:"
        )

    def _make_retrieve_tool(self):
        @tool
        def retrieve_from_feasibility(query: str, top_k: int = 5):
            """
            Retrieve feasibility-document context for a refined user query via a Chroma vector store.

            Purpose
            -------
            This tool grounds answers in the user's uploaded **feasibility study** by performing semantic
            search over an embedded Chroma collection. Call it **only** when the feasibility JSON you
            already have is **insufficient** to answer the question and deeper source context is needed.

            When to Call (Routing Guidance for the Agent)
            ---------------------------------------------
            - The latest query is feasibility Q&A (or a hybrid path) and requires citations/details that
            are unlikely to exist in the structured feasibility JSON alone.
            - The agent has a **standalone refined query string** (include product/industry, capacity+unit+period,
            and location when known).
            - Prefer reading the feasibility JSON first; if gaps remain, use this retrieval tool.

            Inputs
            ------
            query : str
                The **refined** standalone user query to search with. Avoid unresolved pronouns (“it/this/there”).
                Example: "Could you please provide details about the project schedule and cost estimates?"
            
            top_k : int, default=5
                The number of top relevant documents to retrieve (k in similarity search). 
                Use higher values (e.g., 10-20) for broader context or when expecting diverse matches; 
                lower values (e.g., 1-3) for focused, precise retrieval to minimize noise. 
                Recommended: Start with 5; adjust based on query specificity and document density.

            Global Dependencies (configured elsewhere)
            ------------------------------------------
            COLLECTION_NAME : str
                Name of the Chroma collection containing feasibility embeddings.
            PERSIST_DIR : str
                Filesystem path where the Chroma collection is persisted.
            embeddings : Callable
                An embedding function/class compatible with LangChain/Chroma (must be callable).

            Behavior
            --------
            1) Validates the `query` and `top_k` (must be positive integer >=1).
            2) Opens the Chroma store for `COLLECTION_NAME` at `PERSIST_DIR` using `embeddings`.
            3) Executes a semantic search with the specified `top_k` and returns the relevant `Document` chunks.

            Returns
            -------
            List[langchain.schema.Document]
                A (possibly empty) list of Documents with `page_content` and `metadata`. The function is
                **read-only** and has no side effects (does not mutate chat history or persistent state).

            Failure Handling
            ----------------
            - On any validation/store/embedding error, returns an empty list `[]`.
            - Keep calling code resilient: if empty, answer from feasibility JSON and/or other tools.

            Best-Practice Notes
            -------------------
            - Ensure the `query` already reflects carried-forward context (industry/product, capacity with unit
            and time period for BFS, and location) when available.
            - Tune `top_k` intelligently: For simple fact-checks, use 3; for exploratory Q&A, use 10+ to capture nuances.
            - Consider re-ranking/fusion when combining results from multiple sources.
            - Cite or summarize minimally—avoid dumping large chunks verbatim.

            Example
            -------
            # Given globals are configured elsewhere:
            #   COLLECTION_NAME = "feasibility_project_42"
            #   PERSIST_DIR = "/var/chroma/feasibility"
            #   embeddings = OpenAIEmbeddings(...)

            # Default k=5
            docs = retrieve_from_feasibility(
                "List critical environmental approvals for Specialty Chemicals in Gujarat."
            )
            
            # Explicit higher k for broader context
            docs = retrieve_from_feasibility(
                "List critical environmental approvals for Specialty Chemicals in Gujarat.",
                top_k=10
            )
            """
            # ---- Guarded retrieval with structured failure handling ----
            try:
                if top_k < 1:
                    raise ValueError("top_k must be a positive integer >=1")
                
                user_query = query
                collection_name = self.collection_name
                persist_dir = self.persist_dir
                embeddings_layer = self.embeddings
                # Initialize vector DB and retriever
                vectordb = Chroma(
                    # IMPORTANT: point to the folder that contains chroma.sqlite
                    persist_directory=os.path.join(self.persist_dir) if os.path.isdir(self.persist_dir) else self.persist_dir,
                    # You may omit collection_name when each DB has only one collection,
                    # but keeping it is fine as long as it matches the stored one.
                    collection_name=self.collection_name,
                    embedding_function=embeddings_layer,
                )

                retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
                # Perform retrieval
                docs = retriever.get_relevant_documents(user_query)
                with open("testlog.txt", "a") as file:
                    file.write(f"\n================= Retrieved Docs: \n \t\t\t{docs}")
                return docs or []
            except Exception as e:
                return []
        return retrieve_from_feasibility

    def _make_module_tool(self):
        @tool
        def module_search_node(query: str) -> Dict[str, Any]:
            """
            Dispatch the **main module search pipeline** for a refined query and return the
            pipeline’s raw payload — without mutating chat history.

            What this tool does
            -------------------
            Runs your existing `run_ai_module_flow_core(...)` to handle one of the five supported
            search/intake workflows:
            1) Build from Scratch (BFS)
            2) Vendors
            3) Incentives
            4) Approvals
            5) Employment

            When the agent should call it
            -----------------------------
            - Only when the classifier/routing has **positively identified** that the user’s request
            is a *search/retrieval/listing* intent for one (or more) of the five modules.
            - Do **not** call for:
                • purely informational/definitional questions (use your “Other industry-related” path),
                • off-topic/valueless small talk,
                • feasibility Q&A that should be answered via feasibility JSON / document retrieval.

            Inputs
            ------
            query : str
                The **standalone, refined** query string (carry-forward already applied).
                Examples:
                - "Show incentives for cement in Vadodara."
                - "Find vendors for solar panels in Low-veld."
                - "Show approvals required for food processing in Gujarat."

            Global dependencies (provided by the host app)
            ----------------------------------------------
            USER_INPUT : str
                The raw latest user message (pre-refinement).
            CHAT_ID : str
                Session identifier for downstream pipeline usage.
            USER_INTENSION : str
                The resolved intent label (one of the 5 main modules).
                The tool relies on this being correctly set before invocation.

            Behavior & Side-effects
            -----------------------
            - Calls `run_ai_module_flow_core(input=USER_INPUT, chatId=CHAT_ID,
            refine_user_input=query, user_intension=USER_INTENSION, ...)`.
            - **Does not** append to or mutate chat history (the caller is responsible for persistence).
            - Returns whatever the module pipeline returns **verbatim** under `"module_answer"`.

            Returns
            -------
            Dict[str, Any]
                Success:
                {"module_answer": <dict from run_ai_module_flow_core>}
                Failure:
                {"module_error": "<short error string>"}

            Agent routing guidance (important)
            ----------------------------------
            - Ensure `query` is truly standalone (no unresolved pronouns like “it/this/there”).
            - Ensure `USER_INTENSION` corresponds to one of:
                "Query to build industry from Scratch",
                "Query to search Vendors",
                "Query to search Incentives",
                "Query to Get Approvals",
                "Query to Get Employee Search".
            - If the intent is *not* one of the above, **do not** call this tool.

            Example (how the agent should call)
            -----------------------------------
            # Given globals are already set by the runtime:
            #   USER_INPUT = "Show incentives for cement in Vadodara"
            #   CHAT_ID = "sess_123"
            #   USER_INTENSION = "Query to search Incentives"

            result = module_search_node("Show incentives for cement in Vadodara.")
            if "module_answer" in result:
                # pass to responder/composer
                answer = result["module_answer"]
            else:
                # fallback or error path
                err = result.get("module_error")

            """
            try:
                # These will be set in invoke() before graph execution
                user_input = self.user_input
                chat_id = self.chat_id
                refined_input = query
                user_intension = self.user_intension
                # Call your existing pipeline. IMPORTANT: ensure it won't append to history in this path.
                resp = run_ai_module_flow_core(
                    input=user_input,
                    chatId=chat_id,
                    refine_user_input=refined_input,
                    user_intension=user_intension,
                    # e.g., append_to_history=False (if your core supports it)
                )
                return {"module_answer": resp}
            except Exception as e:
                # Keep it structured so the collector can merge errors too
                return {"module_error": f"{e.__class__.__name__}: {e}"}
        return module_search_node

    def _safe_json_loads(self, maybe_json: Any) -> Optional[dict]:
        """Parse dict-like content that may arrive as a JSON string. Returns dict or None."""
        if isinstance(maybe_json, dict):
            return maybe_json
        if isinstance(maybe_json, str):
            try:
                return json.loads(maybe_json)
            except Exception:
                return None
        return None

    def _collect_feasibility_snippets(self, messages: List[Any]) -> List[str]:
        """Extract plain-text snippets from any ToolMessage produced by `retrieve_from_feasibility`."""
        snippets: List[str] = []
        for m in messages or []:
            if isinstance(m, ToolMessage) and getattr(m, "name", None) == "retrieve_from_feasibility":
                content = m.content
                # Tool content can be list[Document], list[str], list[dict], or JSON-encoded string
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, str) and item.strip():
                            snippets.append(item.strip())
                        elif isinstance(item, dict):
                            text = item.get("page_content") or item.get("text") or ""
                            if isinstance(text, str) and text.strip():
                                snippets.append(text.strip())
                        else:
                            text = getattr(item, "page_content", None)
                            if isinstance(text, str) and text.strip():
                                snippets.append(text.strip())
                elif isinstance(content, str):
                    # Try JSON array first
                    parsed = self._safe_json_loads(content)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict):
                                text = item.get("page_content") or item.get("text") or ""
                                if isinstance(text, str) and text.strip():
                                    snippets.append(text.strip())
                            elif isinstance(item, str) and item.strip():
                                snippets.append(item.strip())
                    elif content.strip():
                        # Fall back to raw string chunk
                        snippets.append(content.strip())

        # Deduplicate (preserve order)
        seen, unique = set(), []
        for s in snippets:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique

    def _collect_module_answer(self, messages: List[Any]) -> Optional[Dict[str, Any]]:
        """
        Find the latest ToolMessage from `module_search_node` and return its payload as a dict:
        either {"module_answer": {...}} or {"module_error": "..."} depending on tool output.
        Handles dict content or JSON-encoded strings.
        """
        # Scan from the end so we prefer the most recent tool run
        for m in reversed(messages or []):
            if isinstance(m, ToolMessage) and getattr(m, "name", None) == "module_search_node":
                content = m.content
                payload = content if isinstance(content, dict) else self._safe_json_loads(content)
                if isinstance(payload, dict):
                    # Pass through only the keys we care about
                    out: Dict[str, Any] = {}
                    if "module_answer" in payload:
                        out["module_answer"] = payload["module_answer"]
                    if "module_error" in payload:
                        out["module_error"] = payload["module_error"]
                    if out:
                        return out
        return None

    def _render_llm_responder_prompt(
        self,
        refined_input: str,
        feasibility_json: Optional[Dict[str, Any]],
        feasibility_snippets: List[str],
        module_answer: Optional[Dict[str, Any]],
    ) -> List[Any]:
        """
        Helper: Render the prompt messages for the responder LLM.
        """
        human_payload = {
            "refined_input": refined_input,
            "feasibility_json": feasibility_json or {},
            "feasibility_snippets": feasibility_snippets[:8],
            "module_answer": module_answer or {},
        }
        return [
            SystemMessage(content=self.RESPONDER_SYSTEM),
            HumanMessage(content=json.dumps(human_payload, ensure_ascii=False)),
        ]

    def qna_agent(self, state: AgentState):
        """
        Placeholder for qna_agent node docstring.
        Replace with your description of the router logic.
        """
        # Extract the last message as refined input (assuming messages is list[str] or list[BaseMessage])
        refined = state["messages"]
        msgs = [
            SystemMessage(content=self.QNA_AGENT_SYSTEM),
            HumanMessage(content=(
                "refined_input:\n"
                f"{refined}\n\n"
                "feasibility_json:\n"
                f"{json.dumps(self.feasibility_study or {}, ensure_ascii=False)}\n"
            ))
        ]
        llm_out = self.llm_with_tools.invoke(msgs)
        state["messages"] =  [llm_out]
        return state

    def responder_node_llm(self, state: AgentState):
        """
        LLM-powered Responder node that composes the final consultant-grade message.

        Reads from state:
        - state["refined_input"]: str
        - state["feasibility_json"]: Optional[dict]
        - state["messages"]: list (to collect tool outputs from ToolNode)
        - state["module_answer"]: Optional[dict] (if already set elsewhere)

        Writes to state:
        - state["final_answer"]: str
        - (optionally) state["module_answer"]: dict (auto-filled if found in messages)
        - (optionally) state["module_error"]: str  (auto-filled if found in messages)

        Behavior:
        - Collect feasibility text snippets from any `retrieve_from_feasibility` ToolMessage(s).
        - If `module_answer` not present, try to harvest the latest `module_search_node` tool payload.
        - Build a structured prompt with persona + pathway rules and generate a single unified response.
        - No chat-history persistence or other side effects.
        """
        try:
            refined_input: str = state.get("refined_input", "") or ""
            feasibility_json: Optional[Dict[str, Any]] = state.get("feasibility_json")
            messages: List[Any] = state.get("messages", [])
            # Harvest feasibility snippets from tool messages
            fea_snippets = self._collect_feasibility_snippets(messages)
            # Prefer an existing module_answer in state; else try to harvest from ToolMessages
            module_answer: Optional[Dict[str, Any]] = state.get("module_answer")
            if not module_answer:
                mod_payload = self._collect_module_answer(messages)
                if mod_payload:
                    # persist back into state so downstream consumers can see it too
                    if "module_answer" in mod_payload:
                        state["module_answer"] = mod_payload["module_answer"]
                    if "module_error" in mod_payload:
                        state["module_error"] = mod_payload["module_error"]
                    module_answer = mod_payload.get("module_answer")
            # Keep only the keys the prompt expects
            module_subset = {}
            if isinstance(module_answer, dict):
                for k in ("Ai_response", "Is_confirmation", "Trigger_Lead_Generation"):
                    if k in module_answer:
                        module_subset[k] = module_answer[k]
            msgs = self._render_llm_responder_prompt(
                refined_input=refined_input,
                feasibility_json=feasibility_json,
                feasibility_snippets=fea_snippets,
                module_answer=module_subset,
            )
            out = self.llm.invoke(msgs)
            state["final_answer"] = (getattr(out, "content", None) or "").strip() or \
                "I can proceed once you share a bit more detail on product/industry and location."
            return state
        except Exception:
            state["final_answer"] = (
                "I wasn’t able to assemble the full answer just now. "
                "Share the product/industry and location (plus capacity if relevant), and I’ll continue."
            )
            return state

    def _build_graph(self):
        """Internal: Build and compile the LangGraph workflow."""
        

        workflow = StateGraph(AgentState)

        workflow.add_node("QnA Agent", self.qna_agent)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("Responder", self.responder_node_llm)

        workflow.set_entry_point("QnA Agent")
        workflow.add_conditional_edges("QnA Agent", tools_condition)
        workflow.add_edge("tools", "QnA Agent")
        # workflow.add_edge("tools", "Responder")
        # workflow.add_edge("Responder", "QnA Agent")
        # workflow.add_edge("QnA Agent", "Responder")
        # workflow.add_edge("QnA Agent", "Responder")  # for the no-tool path
        # workflow.add_edge("Responder", END)

        self.graph = workflow.compile()

    def invoke(
        self,
        user_input: str,
        refined_user_input: Optional[str] = None,
        user_intension: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Invoke the agent for a query.

        Parameters:
        -----------
        user_input : str
            The raw user input (used in module tool).
        refined_user_input : Optional[str], default=None
            The refined standalone query. If None, uses user_input.
        user_intension : Optional[str], default=None
            The resolved intent (e.g., one of the 5 modules). Set before calling module tool if needed.

        Returns:
        --------
        Dict[str, Any]
            The full state response, including "final_answer".
        """
        if refined_user_input is None:
            refined_user_input = user_input

        # Set per-call values for tool access
        self.user_input = user_input
        self.refined_user_input = refined_user_input  # Optional, for consistency
        self.user_intension = user_intension
        input_state = {
            "messages": [refined_user_input],
            "refined_input": refined_user_input,
            "feasibility_json": self.feasibility_study,
        }

        response = self.graph.invoke(input_state, config={"recursion_limit": 50})
        messages: List[Any] = response.get("messages", [])
        module_answer: Optional[Dict[str, Any]] = response.get("module_answer")
        if not module_answer:
            mod_payload = self._collect_module_answer(messages)
            if mod_payload:
                # persist back into state so downstream consumers can see it too
                if "module_answer" in mod_payload:
                    response["module_answer"] = mod_payload["module_answer"]
                if "module_error" in mod_payload:
                    response["module_error"] = mod_payload["module_error"]
                module_answer = mod_payload.get("module_answer")
        return response


# After agent.invoke(...)
# Process the result based on the three types

def process_agent_result(result):
    """
    Intelligently processes the agent result into a standardized module_answer format
    based on the presence of keys and message types.
    """

    has_module_answer = "module_answer" in result
    has_final_answer = "final_answer" in result
    
    has_last_ai_content = False
    last_ai_content = None
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content.strip():
                last_ai_content = msg.content.strip()
                has_last_ai_content = True
                break
    
    if has_module_answer and not has_final_answer:
        # Type 1: Has module_answer, no final_answer -> Replace Ai_response with last_ai_content
        if not has_last_ai_content:
            raise ValueError("No last AI message content found in messages for Type 1 response processing.")
        processed = copy.deepcopy(result["module_answer"])
        processed["Ai_response"] = last_ai_content
        return processed
    
    if not has_module_answer and has_final_answer:
        return {
            "Ai_response": result["final_answer"],
            "Is_confirmation": None,
            "Trigger_Lead_Generation": False
        }

    elif not has_module_answer and not has_final_answer:
        # Type 2: No module_answer, no final_answer -> Wrap last_ai_content in module format
        if not has_last_ai_content:
            raise ValueError("No last AI message content found in messages for Type 2 response processing.")
        return {
            "Ai_response": last_ai_content,
            "Is_confirmation": None,
            "Trigger_Lead_Generation": False
        }
    
    elif has_module_answer and has_final_answer:
        # Type 3: Has both -> Replace Ai_response in module_answer with final_answer
        processed = copy.deepcopy(result["module_answer"])
        processed["Ai_response"] = result["final_answer"]
        return processed
    
    else:
        # Unexpected case: Neither or other combinations -> Raise error
        raise ValueError("Unexpected agent response format: No valid module_answer or final_answer found, and unable to fallback.")

# Example usage (replace with your values):
# agent = FeasibilityAgent(
#     persist_dir="store",
#     collection_name="feasibility_docs",
#     feasibility_study={"Location": "Gujarat", "final_product_capacity": "17253.3 MT/Month", "product": "Specialty Chemicals"},
#     chat_id="xyzabe",
#     device="cpu",
# )
# result = agent.invoke(
#     user_input="I want to know all incentives needed for my setup and can you also tell me about the project schedule and cost estimates?",
#     refined_user_input="I want to know all incentives needed for my setup and can you also tell me about the project schedule and cost estimates?",
#     user_intension=None,  # Set to e.g., "Query to search Incentives" if calling module tool
# )
# print(result["final_answer"])