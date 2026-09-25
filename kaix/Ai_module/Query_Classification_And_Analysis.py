import os
import re
import json 
from typing import List, Dict, Tuple, Union, Any
import copy
# import ast
# from dotenv import load_dotenv
import spacy
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from rapidfuzz import fuzz, process
from langchain.schema import HumanMessage, AIMessage
import frappe
from kaix.Management_Class.helpers.utility import update_llm_token  
from kaix.Management_Class.Redis_management.Redis_chat import get_chat,save_chat,get_state,save_state
import configparser
import frappe
import random
from kaix.Ai_module.parsers import (parse_llm_response, extract_json_object, safe_parse_output, extract_json_from_llm_response, convert_string_json,)
from kaix.Ai_module.intent_detection.schemas import IntentClassification,IntentClassificationFailure
from kaix.Ai_module.query_refinement.logic import refine_query_with_history
from kaix.Ai_module.intent_detection.logic import update_user_intension, detect_module_switch_intent, check_industry_scope_with_feasibility
# from langchain_openai import ChatOpenAI

base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/kaix/kaix/Log_management/mars.ini")
config = configparser.ConfigParser()
config.read(config_file)
groq_api_key = config['Key']['groq_key']
openai_key = config['Key']['openai_api_key']




# Initialize LLM
llm_70b_vers = ChatGroq(groq_api_key=groq_api_key, model_name="openai/gpt-oss-120b", temperature=0.0)
llm_70b_vers_creative = ChatGroq(groq_api_key=groq_api_key, model_name="openai/gpt-oss-120b", temperature=0.7)
llm_8b_inst=ChatGroq(groq_api_key=groq_api_key,model_name="llama-3.3-8b-instant", temperature=0.0)
llm_gpt_oos_120b = ChatGroq(groq_api_key=groq_api_key, model_name="openai/gpt-oss-120b", temperature=0.0)
llm_maverik = ChatGroq(groq_api_key=groq_api_key, model_name="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5)
# llm_openai = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=openai_key)
# llm_openai_inf_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_key)
# llm_openai_inf_4o = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=openai_key)
# llm_openai_inf_4 = ChatOpenAI(model="gpt-4", temperature=0.0, api_key=openai_key)
# llm_openai_inf_3_5 = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.0, api_key=openai_key)

# RESPONDER_LLM = ChatGroq(
#     groq_api_key=groq_api_key,
#     model_name="llama-3.3-70b-versatile",
#     temperature=0.7,                        # was 0.5 → tighter, still natural
#     model_kwargs={
#         "top_p": 0.9,                      # was 0.9 → fewer side-asks
#     },
# )

RESPONDER_LLM = ChatGroq(
    groq_api_key=groq_api_key,
    model_name="openai/gpt-oss-120b",
    temperature=0.7,                        # was 0.5 → tighter, still natural
    # model_kwargs={
    #     "top_p": 0.9,                      # was 0.9 → fewer side-asks
    # },
)

# RESPONDER_LLM = ChatOpenAI(
#     model="gpt-4o-mini", 
#     temperature=0.7, 
#     api_key=openai_key,
#     top_p = 0.9
# )
# with open("testlog.txt", "a") as file:
#     file.write(f"\n%%%%%%%% Model: gpt-4o-mini")

# RESPONDER_LLM = ChatOpenAI(
#     model="gpt-4o", 
#     temperature=0.7, 
#     api_key=openai_key,
#     top_p = 0.9
# )
# with open("testlog.txt", "a") as file:
#     file.write(f"\n%%%%%%%% Model: gpt-4o")

INDUSTRY_NOT_AVAILABLE_MSG = (
    "Thank you for sharing your requirements. The industry/product you’re exploring isn’t in our current coverage just yet. "
    "We’re actively expanding to include a wider range of industries and product lines—your request helps us prioritize. "
    "We’ve recorded your details, and our team will review them and get in touch with you soon. "
    "We truly value your interest as we grow."
)


LOCATION_NOT_AVAILABLE_MSG = (
    "Thank you for sharing your requirements. The location you’ve requested is currently outside our coverage. "
    "Good news: we’re steadily adding more cities, districts, and states to broaden our reach. "
    "We’ve logged your query, and our team will review it and get in touch with you soon. "
    "We appreciate your interest as we expand our map."
)

SUPPLIES_NOT_AVAILABLE_MSG = (
    "Thank you for sharing your requirements. The supplies you’re looking for (raw materials, services, or equipment) "
    "aren’t available in our catalog yet. We’re rapidly onboarding more supply categories and vendors to serve requests like yours. "
    "We’ve recorded your details, and our team will review them and reach out to you soon. "
    "Thanks for helping us grow."
)

# Load the SpaCy model for better entity recognition
nlp = spacy.load("en_core_web_lg")

@frappe.whitelist()
# Define the function
def classify_query(
        user_query: str,
        llm: Any,
        chatId: str,
) -> str:
    """
    Classifies a business-related query into one of eight predefined categories based on its intent and context.

    Parameters:
    -----------
    user_query : str
        A user-submitted query related to industry or business.

    Returns:
    --------
    str
        A single category name from the following list that best matches the user's query:
        
        - "Query to build industry from Scratch"
        - "Query to search Vendors"
        - "Query to search Incentives"
        - "Query to Get Approvals"
        - "Query to Get Employee Search"
        - "Negatively Intended Query"
        - "Other industry-related queries"
        - "Valueless queries"

    Notes:
    ------
    - The classification is powered by a language model and follows strict rules for interpreting the query’s intent.
    - Only one category is returned per query.
    - The function does not provide explanations or return multiple categories.
    """
    chat_history = get_chat(f"chat_{chatId}") or []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]

    # query = f"""
    # SELECT 1
    # FROM `tabSession` AS s
    # JOIN `tabChat history` AS ch
    # ON s.name = ch.parent
    # WHERE s.name = '{chatId}'
    # AND ch.result IS NOT NULL
    # AND TRIM(ch.result) != ''
    # LIMIT 1
    # """

    # result = frappe.db.sql(query)

    is_result_shown = False

    if is_result_shown:
        # Post Result
        prompt_template = """
You are an expert in understanding business-related queries and classifying them into a single most relevant category.

You will be given:
1. The user’s current query.
2. The last few messages exchanged between the user and the AI (chat_history_normal), which may contain clues to what the user has seen or asked earlier.

If the current query seems to build upon or refer to a previous topic from the chat history, classify it as a “Follow-up Query”.

Your task is to strictly assign the query to only one category, even if multiple classes seem applicable.  

Analyze the context carefully and ensure that you return only one category that best fits the query.  

Pay special attention to whether the current query could be referring back to a previously answered module.

Ask yourself:
- Did the user recently ask for approvals, incentives, vendors, or build-from-scratch info?
- Does the current query mention or rely on a detail that could only be known from a previous result?

If so, the current query is not standalone — it is a **Follow-up Query**.

Categories & Their Definitions:

1. Query to build industry from Scratch:  
    - Examples: 
        - I want to build a 1 TPA Cement Factory. 
        - What are the land options for the chemical industry in Battambang? 
        - Tell me the land availability for the agricultural industry in Kampong Cham.
    - This refers to queries about establishing an industry from the ground up, including land purchase, infrastructure setup, or capacity planning.  
    - Assign this category if the user's query indicates any intent to establish, set up, construct, initiate, develop, or start a new industry or factory, regardless of the exact words used.  
    - The classification must be based on understanding the overall intent and context rather than focusing on specific words like "build" or "establish."  
    - Queries about buying property for building an industry may fall under this category only if the intent to use that property for setting up an industry is clearly indicated.  
    - Queries about selling property, renting land, or general property transactions that do not involve setting up an industry should not be classified under this category.  
    - If the intent to build is unclear, vague, or mixed with other topics, classify it under "Other industry-related queries."

2. Query to search Vendors:  
    - Example: I am searching for a vendor who supplies pharmaceutical-grade raw chemicals for drug manufacturing.  
    - This category is used for queries about finding suppliers, manufacturers, or vendors for raw materials, equipment, or services.

3. Query to search Incentives:  
    - Example: 
        - What benefits are available for setting up a cement manufacturing plant in XYZ area?  
        - Tell me the government incentives for cement industry in Siem Reap,Cambodia
        - Incentive for Anand Cement
    - This category is used for queries asking about government incentives, grants, or subsidies related to setting up or expanding an industry.

4. Query to Get Approvals:  
    - Example: I want to get approval for my Cement Factory.  
    - This category is used for queries about obtaining permits, licenses, or regulatory approvals for a business or industry.

5. Query to Get Employee Search:  
    - Example: 
        - What is the availability of employment in XYZ area for the Pharmaceutical industry?  
        - What are the labor options for agricultural industry in Siem Reap?
    - This category is used for queries about recruiting or finding employees for an industry or in a specific location.

6. Negatively Intended Query:
    - Example: I don't want to search for incentives for the cement industry in Phnom Penh.  
    - This category is used for queries where the user clearly expresses that they do not want to proceed with a specific industry-related topic (such as incentives, approvals, vendors, land, or employment).  
    - This includes statements where the user rejects, declines, or expresses disinterest, such as "I don't want to...", "No need to...", or "I'm not looking for...".  
    - Classify here only if the overall intent is negative toward one or more categories and there is no indication that the user still wants to proceed within the same topic under different parameters (e.g., different city or industry).  
    - Do not classify vague queries or neutral statements under this category unless the negative intent is explicit or clearly implied in context.

If None of the Above Apply, Use These Two Categories:

7. Other industry-related queries:  
    - Example: 
        - What is the role of AI in manufacturing?  
        - What investment amount is needed for setting up a bottle manufacturing industry?
    - This refers to general industry discussions, trends, or innovations that do not fit into the above categories.
    - Queries about selling property, renting facilities, or unrelated infrastructure transactions should be classified here.

8. Valueless queries:  
    - Example: Who is Donald Trump?  
    - This refers to queries that are irrelevant to business, industry setup, or supply chains.  
    - If the query contains industry-related words but the intent is not meaningful, classify it here.  
    - Example: I'm going to buy a new bike, for that which approvals do I need? (Not relevant to industry-building)

9. Follow-up Query:
    - This refers to queries that build upon or refer to a solution the user was shown earlier in the flow.
    - You do NOT have access to the actual solution content, but you will be given the `chat_history_normal`, which helps infer what module the user previously queried.
    - If the current query appears to rely on or continue a past result, classify it as a Follow-up Query.
    When in doubt, lean toward "Follow-up Query" if the chat history contains a module-triggering query and the current query references or depends on details that are only available through that module's results.

    Common signs of a Follow-up Query:
        - The query refers to specific content that would have been shown in a result (e.g., vendors, approvals, incentives, employment, properties, etc.)
        - The query is vague or incomplete on its own, but makes sense when seen as a continuation of a previous query
        - The chat history shows a module was recently used, and the user is now referring to something shown in that module

    Very likely Follow-up Queries (if they follow a module-based response):
        - Query asking for **number of vendors for a specific supply item**
        - Query asking for **more details about a vendor previously shown**
        - Query asking for **number of total approvals, or stage-wise counts (e.g., how many pre-operational approvals?)**
        - Query asking about a **specific approval or incentive name** (e.g., CGTMSE, Fire NOC)
        - Query asking for **number of incentives shown**
        - Query referring to **employment availability** or **skill level counts**
        - Query asking about **infrastructure, seaport/power/rail connectivity** for a known property
        - Query referring to a **specific property** already discussed

    Follow-up Query Examples by Module:

    Build from Scratch:
        - Earlier: "Show me land options for chemical industry in Kampong Seila"
        - Now: "What is the power connectivity there?"
        - Now: "Which is the nearest port to the Chbar Mon plot you showed?"
        - Now: "Tell me the number of vendors who supply clay"
        - Now: "How many approvals are needed in total?"
        - Now: "How many are pre-establishment approvals?"
        → These are follow-ups because Build-from-Scratch results include full property-wise information: land infrastructure, supply chain, employment stats, approvals, and incentives.

    Incentives:
        - Earlier: "What are the incentives for textile units in Kampong Cham?"
        - Now: "Tell me more about the CGTMSE scheme"
        - Now: "Can I get capital subsidy under this?"
        - Now: "How many incentives are shown in total?"
        - Now: "What all schemes exist under Cambodia Industrial Policy 2020?"
        - Now: "What is the eligibility for Assistance for Dormitories?"
        - Now: "What is the incentive period or status for Cambodia Industrial Policy?"
        - Now: "What is the procedure to take incentives for toy manufacturing?"
        → These refer to specific incentives from the previous result.

    Approvals:
        - Earlier: "Which approvals are needed in Siem Reap for pharma units?"
        - Now: "Do I need GPCB clearance too?"
        - Now: "What’s the timeline for Fire Department NOC?"
        - Now: "How many pre-operational approvals were shown?"
        - Now: "From which department is the Factory Plan Application taken?"
        - Now: "What is the mode of application for Factory License?"
        - Now: "can you brief me about the scheme development for green estate"
        → These are continuations based on previous approval breakdown.

    Vendors:
        - Earlier: "Show vendors of Polypropylene in Kampong Seila"
        - Now: "Can you show one that is within 50 km?"
        - Now: "Are there more vendors for Styrene?"
        - Now: "How many vendors were shown in total?"
        - Now: "Can Maniratna Metal Industries supply Silver?"
        - Now: "What is the company Statistics for Maniratna Metal Industries?"
        - Now: "Where does Maniratna Metal Industries operate?"

        → These refer back to the vendor list shown earlier.

    Employment:
        - Earlier: "What is the employment availability in Chbar Mon?"
        - Now: "How many unskilled workers are there?"
        - Now: "What about skilled labor for textile?"
        → These build upon the employment result shared earlier.

    Important: If the user has recently seen a module-based result (especially Build-from-Scratch), and now asks about a specific part of that result (e.g., vendor count, approval name, incentive details, employment count, power status, etc.), classify the query as “Follow-up Query”.

    Do NOT classify a query as Follow-up if it is independently meaningful and can be understood without any prior context.

    Important Exception:
    If the current query uses similar or same keywords (e.g., industry, factor, or module) as a previous query, but introduces a different location, scale, or sub-sector, and the query is independently meaningful on its own (e.g., “incentive for cement in Siem Reap” after “incentive for cement in Anand”), then it should be classified as a new search intent, not a Follow-up Query.

    For example:

    Earlier: “Incentives for cement in Anand”

    Now: “Incentives for cement in Siem Reap”
    → This is not a Follow-up Query, but a new search, and should be classified as: ["Query to search Incentives"].

    This applies across all modules — including vendors, approvals, employment, etc. — whenever the new query introduces a distinct search condition, especially a new location or a redefined scope.

    If the current query asks about a **different module** than the previous query — such as switching from incentives to approvals, or from vendors to employment — and the query is clear and complete on its own, then treat it as a **new search intent**, not a Follow-up Query.  
    This holds true even if the industry and location remain the same.

    For example:  
    Earlier: "I want incentives for cement in Kampong Cham."  
    Now: "I want approvals for cement in Kampong Cham."  
    → This is a new module with full context, so it should be classified as: ["Query to Get Approvals"], not a Follow-up.

    If the query introduces a new location or different business condition (e.g., industry type, scale, or region), even if it uses similar keywords as a previous one, treat it as a new main category query, not a Follow-up.

Strict Classification Rules:

1. Return Only One Class:  
    - If the query seems to match multiple categories, analyze the overall intent and assign it to the single most appropriate category.  

2. Assign "Query to build industry from Scratch" ONLY if Confident:  
    - Assign this category only if the query's overall context and intent clearly suggest setting up or establishing an industry, using any terminology (like initiate, develop, set up, start, construct, etc.).  
    - Do not classify queries about selling, renting, or unrelated property dealings under this category.  
    - Queries that simply mention "property for an industry" but do not clearly indicate an intent to build should be classified under "Other industry-related queries."  
    - The classification should be based on a thorough understanding of the full query, not on the presence of single words.

3. Do Not Assign "Query to build industry from Scratch" If the Query Contains Only Approvals, Incentives, Vendors, or Employee Searches:  
    - If the user is asking about any combination of these categories (Approvals, Incentives, Vendors, or Employee Searches) but does not explicitly or contextually mention setting up a new industry, assign the most relevant category among them.  
    - Example: "I need vendors for raw materials and want to know about required approvals and incentives." → Correct classification: Either "Query to search Vendors" or "Query to Get Approvals" based on context.  
    - Example: "I want to search vendors, approvals, and also check employment availability in my city." → Correct classification: Choose the most dominant category based on intent.  

4. Prioritize Meaningful Context, Not Just Keywords:  
    - Do not assign a category just because it contains words like "approval," "vendor," or "incentive."  
    - Analyze the full context of the query before assigning a category.  

5. Identify and classify Follow-up Queries precisely:
    - Look for references to previously shown properties, areas, vendors, incentives, approvals, or employment results.
    - Use the chat history to determine if the user is continuing a query based on a module already discussed.
    - Strong follow-up signals include queries about: vendor counts for a supply, employment figures, specific incentive or approval names, stage-wise approvals, infrastructure distances, or land-specific questions.
    - Especially for Build-from-Scratch results, where all modules (land, supply, approval, employment, incentives) are shown together, queries targeting any of these components are likely follow-up.
    - Do not assign this category if the query is standalone and makes no reference to prior context.
    - Queries that reference a specific company, vendor, approval department, or policy clause — when the same topic was discussed recently — are very strong indicators of a Follow-up Query.


---

Your job is to:
1. Review the `Chat_history_normal` carefully.
2. Review the current query.
3. Choose only ONE best-fitting category from the list.

Return just one category name from:
- "Query to build industry from Scratch"
- "Query to search Vendors"
- "Query to search Incentives"
- "Query to Get Approvals"
- "Query to Get Employee Search"
- "Negatively Intended Query"
- "Other industry-related queries"
- "Valueless queries"
- "Follow-up Query"

---

Final Output Instructions:
- Strictly return only the category name from the list above.  
- Do not include multiple categories.  
- Do not provide explanations, justifications, or extra details.  

Chat History:
{chat_history_normal}

Query:  
{query}

Output:  
(Return only one category name from the list)
        """
    
    else:
        # Pre-Result
        prompt_template = """
You are an expert in understanding business-related queries and classifying them into a single most relevant category.

You will be given:
1. The user's current query.
2. The last few messages exchanged between the user and the AI (chat_history_normal), which may contain clues about what the user has previously asked.

The user has **not been shown any result yet**. Therefore, if the query refers to a specific vendor, approval, or incentive — such as asking about a vendor's capability, incentive eligibility, incentive program period, application procedure, approval source department, etc. — but **does not explicitly request a search**, it should be classified as **“Other industry-related queries”**.

These types of queries often become **Follow-up Queries** once a result is shown (e.g., after a vendor list or incentive list is displayed). However, at this stage — before any result — they lack proper context and must be treated as vague or general.

Your task is to strictly assign the query to only one category, even if multiple classes seem applicable.  
Analyze the query **and** the chat history carefully and ensure that you return only one category that best fits the query.

Note:
If the query appears vague, generic, or refers to a specific vendor, policy, or scheme — but does NOT ask to act on it (e.g., search, get, list, or retrieve) — and the user has not seen any related results yet — then treat it as “Other industry-related queries”.

Categories & Their Definitions:

1. "Query to build industry from Scratch"  

    Examples:  
    - I want to build a 1 TPA Cement Factory.  
    - What are the land options for the chemical industry in Battambang?  
    - Tell me the land availability for the agricultural industry in Kampong Cham.  
    - I want to buy a 1 TPA cement industry  
    - 1 MTPA Cement Industry  
    - 1 million barrels per month petrochemical industry  

    Core Definition:  
    Classify here for queries where the user wants to start, establish, or set up a new manufacturing industry — whether:  
    - Explicitly stated (clear build/setup request), or  
    - Implied/vague but reasonably indicating intent to search for or explore manufacturing industry setup options.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention an **industry type, capacity, or location** in the context of building/starting from scratch.  
    - Vague references like “1 MTPA Cement Industry”, “1 metric tonne per month tablets industry”, etc. — treat these as build/setup intent unless they are clearly about industrial setup **guidance** details (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to build industry from Scratch”:  
    - “Build a factory for…”  
    - “Set up a manufacturing unit for…”  
    - “Start an industry for…”  
    - “Establish a plant for…”  
    - “Construct a facility for…”  
    - “Buy land for setting up…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details or guidance about industrial setup **without** an implied intent to search for or initiate the build itself.  
    2. The query is purely informational or advisory about setup processes, requirements, or characteristics — not about finding or acquiring land/facilities to start manufacturing.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General industrial setup guidance:  
    - What investment is needed for setting up a cement plant?  
    - What are the best characteristics of land for a cement factory? 
    - How to start a cement factory   
    - Evaluation questions:  
    - How to evaluate land for a cement setup?  
    - How to vet vendors for my cement plant?  
    - Supply-related queries:  
    - What supplies are needed for cement production?  
    - What is the proportion of raw material to cement production?  
    - Non‑manufacturing property queries:  
    - I want to rent a shop in Mangal Bazaar, Siem Reap.  
    - Looking for office space for my IT startup.  
    - Want to sell 10 acres of farmland in Nashik.  
    - Need warehouse space for my trading business.  
    - Looking for a place to open a hospital.  
    - Want to buy an existing textile shop.   
    - I want to buy land to grow unicorns.  

    Final Rule:  
    Default to “Query to build industry from Scratch” for any query mentioning industry type, capacity, or location in the context of manufacturing setup, unless it is damn sure the user is asking for setup guidance or purely informational content. This ensures vague but build‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.


2. "Query to search Vendors"  

    Examples:  
    - I am searching for a vendor who supplies pharmaceutical-grade raw chemicals.  
    - Show me vendors for steel rods in Phnom Penh.  
    - Search for suppliers of plastic granules in Bavet.  
    - List manufacturers who produce glass bottles near Battambang.  
    - Vendors for Anand Cement  
    - Steel supplier who has ISO 9001 certificate  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list vendor, supplier, or manufacturer options for materials, components, products, or services — whether:  
    - Explicitly stated (clear search request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “vendor(s)”, “supplier(s)”, “manufacturer(s)”, or “producer(s)” in relation to an industry, supply/suppies, location, or business type.  
    - Vague vendor references like “Vendors for cement in Siem Reap”, “Vendor Anand Cement”, etc. — treat these as search intent unless they are clearly detail‑focused (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to search Vendors”:  
    - “Show me vendors for…”  
    - “List suppliers of…”  
    - “Search for manufacturers of…”  
    - “Find suppliers for…”  
    - “Get me vendors for…”  
    - “Retrieve producers of…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details about a specific known vendor without any implied search or exploration intent.  
    2. The query is purely informational or definitional about a vendor or supply type.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General information:  
    - What does Maniratna Metal Industries supply?  
    - What supplies are needed for cement production?  
    - Company capability details:  
    - What are the past clients of Anand Cement?  
    - What standard certifications does Maheta Pvt Ltd have?  
    - Definitions:  
    - What is an ISO 9001 certificate?  
    - Specific detail request:  
    - What products does Agriland Biotech supply?  
    - What are all raw materials needed for school bag production?  
    - What is the proportion of raw material to cement production?  

    Final Rule:  
    Default to “Query to search Vendors” for any query mentioning vendors, suppliers, manufacturers, or producers in an industry/location/business/supply context, unless it is damn sure the user is asking for details of one known vendor or purely informational content. This ensures vague but search‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.


3. "Query to search Incentives"  

    Examples:  
    - What benefits are available for setting up a cement plant in XYZ area?  
    - Tell me the government incentives for cement industry in Siem Reap, Cambodia  
    - Incentive for Anand Cement  
    - Search for green estate incentives for cement industry  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list incentives, subsidies, grants, or financial schemes — whether:  
    - Explicitly stated (clear search request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “incentive(s)” in relation to an industry, location, or business type.  
    - Vague incentive references like “Incentive for cement in Siem Reap”, “Incentive Anand Cement”, etc. — treat these as search intent unless they are clearly detail-focused (see below).  

    Explicit Action-Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to search Incentives”:  
    - “Show me incentive schemes…”  
    - “List the available incentives…”  
    - “Search for schemes applicable to…”  
    - “Retrieve incentives under XYZ policy…”  
    - “Find subsidies for…”  
    - “Give me incentives for…”  

    When to Classify as “Other industry-related queries” Instead:  
    Only classify as Other industry-related queries if:  
    1. The query clearly asks for details about a specific known incentive or scheme without any implied search or exploration intent.  
    2. The query is purely informational or definitional about an incentive.  

    Exclusion Examples (These go to Other industry-related queries):  
    - General information:  
    - What assistance is available under Startup Innovation Cambodia-2020?  
    - What is the eligibility under CGTMSE?  
    - Definitions:  
    - What is CGTMSE?  
    - Program status:  
    - What is the incentive program period of the Cambodia Industrial Policy?  
    - Eligibility checks:  
    - What is the eligibility for Startup Innovation Cambodia-2020?  
    - Specific detail request:  
    - What is the quantum of assistance under Cambodia Industrial Policy?  
    - I want to know about the green estate incentive for cement industry (meaning — details about that scheme, not finding other schemes).  

    Final Rule:  
    Default to “Query to search Incentives” for any query mentioning incentives in an industry/location/business context, unless it is damn sure the user is asking for details of one known incentive or purely informational content. This ensures vague but search-intended queries are captured correctly, while truly informational-only queries remain in “Other industry-related queries”.


4. "Query to Get Approvals"  

    Examples:  
    - I want to get approval for my cement plant.  
    - What approvals are required to start a dairy in Cambodia?  
    - Search approvals for textile manufacturing in Valsad.  
    - What licenses do I need for food processing in Siem Reap?  
    - Approvals for Anand Cement  
    - Search for tree cutting approvals for cement industry  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list approvals, licenses, clearances, or permissions needed for setting up or running a business or industry — whether:  
    - Explicitly stated (clear search request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “approval(s)”, “license(s)”, “clearance(s)”, or “permission(s)” in relation to an industry, location, or business type.  
    - Vague approval references like “Approval for cement in Siem Reap”, “Approval Anand Cement”, etc. — treat these as search intent unless they are clearly detail‑focused (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to Get Approvals”:  
    - “Show me approvals for…”  
    - “List the required approvals…”  
    - “Search for licenses needed for…”  
    - “Retrieve clearance requirements for…”  
    - “Find permissions for…”  
    - “Get me approvals for…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details about a specific known approval without any implied search or exploration intent.  
    2. The query is purely informational or definitional about an approval.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General information:  
    - From which department is the Factory Plan application taken?  
    - Which department handles Factory License?  
    - Definitions:  
    - What is Environment Clearance?  
    - Process/timeframe details:  
    - How long does it take to get Environment Clearance?  
    - What is the process for Solid Waste Authorization Module (under Solid Waste Management Rules, 2016)?  
    - Specific detail request:  
    - What department issues Tree Cutting Approval?  
    - I want to know about the tree cutting approval for cement industry (meaning — details about that approval, not finding other required approvals).  

    Final Rule:  
    Default to “Query to Get Approvals” for any query mentioning approvals, licenses, clearances, or permissions in an industry/location/business context, unless it is damn sure the user is asking for details of one known approval or purely informational content. This ensures vague but search‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.


5. "Query to Get Employee Search"  

    Examples:  
    - What is the availability of employment in XYZ area for the Pharmaceutical industry?  
    - What are the labor options for agricultural industry in Siem Reap?  
    - Employment for Anand Cement  
    - Search for skilled workers for textile industry in Battambang  
    - Labour statistics for cement industry in Cambodia  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list options for employees, workers, or labour for an industry — whether:  
    - Explicitly stated (clear search/recruitment request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “employment”, “employees”, “labour”, “workers”, or “manpower” in relation to an industry, location, or business type.  
    - Vague references like “Employment for cement in Siem Reap”, “Labour for Anand Cement”, etc. — treat these as search intent unless they are clearly detail‑focused (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to Get Employee Search”:  
    - “Show me workers for…”  
    - “List available labour for…”  
    - “Search for employees in…”  
    - “Find skilled manpower for…”  
    - “Get me labour for…”  
    - “Recruit workers for…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details about employment concepts, definitions, or company‑specific employment information without any implied search/recruitment intent.  
    2. The query is purely informational about employment types, workforce structures, or general labour concepts.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General employment information:  
    - What does semi‑skilled employment mean?  
    - Who comes under skilled labour category?  
    - Employment statistics or company‑specific data:  
    - What is the employee strength of Reliance Industries?  
    - What does employee strength mean for an industry?  
    - Workforce requirement details:  
    - What kinds of employee types are needed for cement industry setup?  
    - What are all the employee and job roles needed to start a mining industry?  
    - Certification or job standard queries:  
    - What are the standard duties of a machinist?  
    - What qualifications are needed for an AI developer?  

    Final Rule:  
    Default to “Query to Get Employee Search” for any query mentioning employment, workers, labour, or manpower in an industry/location/business context, unless it is damn sure the user is asking for definitions, conceptual explanations, or specific company employment statistics. This ensures vague but search‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.

    
6. "Negatively Intended Query"  
    IMPORTANT RULE: If the user mentions one or more factors negatively, but also clearly mentions any one factor positively,  
    you MUST NOT return "Negatively Intended Query". Only return the categories that reflect the user’s positive interest.  
    This rule takes priority — a single positively intended factor invalidates the negative classification.

    - Example: I don’t want to search incentives for my project in Cambodia.  
    → Classify as: ["Negatively Intended Query"]

    - Example: I want to build industry but I don’t want incentives.  
    → Classify as: ["Query to build industry from Scratch"]

    - This category applies when the user clearly rejects or expresses disinterest in one or more key business-related factors.

    The 5 core factors to consider are:
        - Approvals
        - Incentives
        - Employment
        - Vendors
        - Building industry from scratch

    Include this category ONLY if:
        a) The query mentions exactly one of these 5 factors, and the user clearly expresses that they do not want information about it.  
        b) The query mentions multiple of these factors, and the user explicitly rejects all of them.

    DO NOT include this category if:
        - Even one of the 5 core factors is positively intended or affirmed in the query.
        - The user is asking a neutral or exploratory question without explicitly rejecting a factor.
        - The rejection is vague or ambiguous (e.g., “not sure about incentives” should not trigger this).
        - The query also includes any valid main category — in such cases, classify only the positive categories.

If None of the Above Apply, Use These Two Categories:


7. "Other industry‑related queries"  

    Examples:  
    - What is the role of AI in manufacturing?  
    - What is the eligibility under CGTMSE?  
    - Looking for office space for my IT startup.  
    - I want to rent a shop in Mangal Bazaar, Siem Reap.

    Core Definition:  
    Use this category for industry‑related questions that do not fit into any of the five main categories ("Query to build industry from Scratch", "Query to search Vendors", "Query to search Incentives", "Query to Get Approvals", "Query to Get Employee Search").  
    This includes:  
    1. Queries that are **purely informational, definitional, or knowledge‑based** about a specific topic from any of the main categories — with **no search, retrieval, or exploration intent**.  
    2. Queries that are **non‑manufacturing in scope** (e.g., retail, office, hospitality, healthcare, property sales, etc.) **but still have legitimate business/commercial intent**.  
    3. Queries that are **business-related but clearly out of scope** for manufacturing search (e.g., unrealistic business ideas with commercial intent).  

    Important:  
    - **Only** classify as "Other industry‑related queries" if it is **damn sure** the query has **legitimate business/commercial context** and is **purely informational / definitional** for that category OR is **completely outside manufacturing scope but still business-related**.  
    - If there is **any reasonable chance** that the query is a vague search intent for one of the five main categories, **do not** classify here — instead, classify under the relevant main category.  
    - **Must have business context** — if there's no business/commercial intent whatsoever, classify as "Valueless queries".

    When "Other industry‑related queries" is Correct:  

    **A. Build from Scratch context:**  
    - Query is only about setup guidance / concept, not searching to build:  
    - What investment is needed for a cement plant?  
    - What are the best characteristics of land for a cement factory? 
    - How to start a cement factory 
    - Query is non‑manufacturing property related **with business intent**:  
    - I want to rent a shop in Mangal Bazaar, Siem Reap.  
    - Looking for office space for my IT startup.  
    - Need café location in Sihanoukville.  
    - Looking for a place to open a hospital.  
    - Want to buy an existing textile shop.  
    - Unrealistic **business ideas**:  
    - I want to build chocolate factory on moon for commercial purpose.

    **B. Vendors context:**  
    - Vendor capability / product detail questions:  
    - What does Maniratna Metal Industries supply?  
    - What standard certifications does Maheta Pvt Ltd have?  
    - General supply knowledge:  
    - What supplies are needed for cement production?  
    - What is an ISO 9001 certificate?  

    **C. Incentives context:**  
    - Incentive definitions / details:  
    - What is CGTMSE?  
    - What is the eligibility for Startup Innovation Cambodia‑2020?  
    - What is the incentive program period of the Cambodia Industrial Policy?  
    - What is the quantum of assistance under Cambodia Industrial Policy?  

    **D. Approvals context:**  
    - Approval definitions / process detail:  
    - What is Environment Clearance?  
    - From which department is the Factory Plan application taken?  
    - How long does it take to get Environment Clearance?  

    **E. Employee Search context:**  
    - Employment definitions / statistics:  
    - What does semi‑skilled employment mean?  
    - Who comes under skilled labour category?  
    - What is the employee strength of Reliance Industries?  

    Final Rule:  
    If none of the five main categories are **clearly and positively intended** — and the query has **legitimate business context** and is **purely informational, definitional, non‑manufacturing business, or unrealistic business ideas** — classify as "Other industry‑related queries".  
    If **even one** main category is clearly intended (even vaguely), do **not** classify as "Other industry‑related queries".
    If there is **no business context at all**, classify as "Valueless queries".


8. "Valueless queries"  
    - Examples: 
        - Hello, how are you?
        - Who is Donald Trump?
        - What's the weather today?
        - I want to make a shirt for my friend.  
        - Want 10 acres to build a castle. (personal/fantasy, no business intent)
        - Need place for my TikTok dance studio factory. (entertainment, not serious business)
        - I want to buy a bike for personal use.
        - Tell me a joke.
        - Good morning!
        - Thank you, goodbye.
        - Blahblah build blah idk 🤷‍♀️

    - For queries that are completely irrelevant to business, industry setup, or supply chains.  
    - This includes:
        - **Conversational elements**: Greetings, pleasantries, social interactions
        - **General knowledge or political questions** unrelated to industry
        - **Personal queries**, unrelated product buying decisions, or entertainment topics
        - **Fantasy/joke queries** with no legitimate business intent
        - Queries where industry-related keywords are present but the **intent** is not relevant to industry-building or supply chains and has **no commercial purpose**

    - Use this category ONLY if:
        - None of the main 5 classes are relevant or positively intended (i.e., Build from Scratch, Vendor, Incentive, Approval, Employee Search)
        - The query contains **no actionable business or industry-specific context**
        - The user is clearly not looking for information connected to business workflows
        - **No commercial intent** — purely personal, social, entertainment, or general knowledge

    - DO NOT include this category if:
        - The query includes any valid industry intent (even alongside irrelevant elements)
        - The query could be interpreted as loosely connected to industry setup, supply chain, approvals, etc.
        - The query has **any legitimate business or commercial context**

    **Key Distinguishing Rule:**
    Ask: "Does this query have ANY business/commercial intent or context?"
    - **YES** + doesn't fit main 5 categories → "Other industry-related queries"  
    - **NO** (zero business context) → "Valueless queries"

    Additional Examples:
    - I'm going to buy a new bike, for that which approvals do I need? → Not relevant to industry-building (personal purchase)
    - What's your favorite color? → No business context
    - How are you doing today? → Social interaction, no business context

    Classify only if the query is irrelevant in both content **and** intent, with **zero commercial/business purpose**.

    
Strict Classification Rules:

1. Return Only One Class:  
    - If the query seems to match multiple categories, analyze the overall intent and assign it to the single most appropriate category.  

2. Assign "Query to build industry from Scratch" ONLY if Confident:  
    - Assign this category only if the query's overall context and intent clearly suggest setting up or establishing an industry, using any terminology (like initiate, develop, set up, start, construct, etc.).  
    - Do not classify queries about selling, renting, or unrelated property dealings under this category.  
    - Queries that simply mention "property for an industry" but do not clearly indicate an intent to build should be classified under "Other industry-related queries."  
    - The classification should be based on a thorough understanding of the full query, not on the presence of single words.

3. Do Not Assign "Query to build industry from Scratch" If the Query Contains Only Approvals, Incentives, Vendors, or Employee Searches:  
    - If the user is asking about any combination of these categories (Approvals, Incentives, Vendors, or Employee Searches) but does not explicitly or contextually mention setting up a new industry, assign the most relevant category among them.  
    - Example: "I need vendors for raw materials and want to know about required approvals and incentives." → Correct classification: Either "Query to search Vendors" or "Query to Get Approvals" based on context.  
    - Example: "I want to search vendors, approvals, and also check employment availability in my city." → Correct classification: Choose the most dominant category based on intent.  

4. Prioritize Meaningful Context, Not Just Keywords:  
    - Do not assign a category just because it contains words like "approval," "vendor," or "incentive."  
    - Analyze the full context of the query before assigning a category.  

5. Do Not Assign Module Categories for Vague or Ungrounded Queries:
    - If the query mentions a specific vendor, approval, or incentive but does NOT clearly request to search, get, retrieve, or list — classify it under “Other industry-related queries”.
    - This is especially true if the user has not yet seen any results — such queries are not grounded in action, and the system cannot know what they refer to.
    - Example: “What is the incentive program period of the Cambodia Industrial Policy?” → NOT a search query, hence “Other industry-related queries”
    - Example: “Where does Maniratna Metal Industries operate?” → NOT a vendor search, hence “Other industry-related queries”

Final Output Instructions:
- Strictly return only the category name from the list above.  
- Do not include multiple categories.  
- Do not provide explanations, justifications, or extra details.  

Chat History:
{chat_history_normal}

Query:  
{query}

Output:  
(Return only one category name from the list)
        """

    # Initialize the LLM
    # Create the prompt
    prompt = PromptTemplate(
        input_variables=["query", "chat_history_normal"],
        template=prompt_template
    )

    # Create the LLM chain
    chain = prompt | llm

    # Run the query through the chain
    category = chain.invoke({"query": user_query, "chat_history_normal": Chat_history_normal})

    return category.content.strip()

def generate_sub_queries(user_query: str, intent_classes: List[str], llm: Any) -> Dict[str, str]:
    """
    Generates one refined sub-query per classified intent from a multi-intent business query.

    Parameters:
    -----------
    user_query : str
        The original query submitted by the user.

    intent_classes : List[str]
        A list of classified intents (e.g., "Query to search Incentives", etc.).

    llm : Any
        A language model instance compatible with LangChain (e.g., LLMChain, PromptTemplate | LLM).

    Returns:
    --------
    Dict[str, str]
        A dictionary where keys are intent class names and values are individual rewritten sub-queries.
    """

    prompt_template = """
You are a conservative rewriter that decomposes a multi-intent query into one sub-query per provided class,
WITHOUT changing the user’s original meaning.

STRICT INVARIANTS — NEVER CHANGE THESE:
1) Action & intent verbs: keep words like buy/sell/build/lease/expand/apply/explore/compare exactly.
2) Negations & modality: keep “not”, “don’t”, “must”, “need”, “can”, “cannot”, “should”, “only”, etc.
3) Quantities & units: keep numbers, magnitudes, and units verbatim (e.g., 1 TPA ≠ 1 MTPA; do not convert or round).
4) Named entities & nouns: keep industry/product/company/brand/site names, SKUs, model names, and locations verbatim.
5) Time references: keep dates, months, quarters, and relative periods (“this year”, “in 2026”) verbatim.
6) Constraints: keep budget caps, capacity limits, exclusions, and any “without/except” clauses verbatim.
7) Language & formatting: preserve number/currency formatting (e.g., standard international commas), capitalization within names, and spelling present in the original text.

ATTRIBUTE SHARING RULE:
- If the original query clearly applies ONE industry/location/timeframe to multiple intents, replicate those attributes as-is across all relevant sub-queries.
- If attributes differ across parts (e.g., “incentives for cement AND approvals for chemical”), DO NOT merge or cross-share. Keep each sub-query scoped to its own subject.
- If an attribute is missing for a class, do NOT invent or infer; simply omit it for that class.

CLASS-SEMANTICS RULE:
- Do NOT coerce the wording to match a class. If the class is “Build from Scratch” but the user said “buy”, keep “buy”. Your job is to isolate the request per class while preserving the original phrasing and facts.

OUTPUT RULES:
- Produce a JSON object whose keys are EXACTLY the provided class names in the given list and whose values are single-sentence sub-queries.
- Each sub-query must be: (a) grammatical, (b) self-contained, (c) faithful to the original content for that class.
- If the original text has no details for a given class, return a minimal, neutral request for that class using ONLY unambiguously shared attributes (if any). Never invent new facts.
- No explanations, no extra keys, no comments — JSON only.

EXAMPLES (pay close attention to preserving verbs, units, and per-class subjects):

Example A
User: I want to see incentives for cement in Cambodia and take approvals for chemical in Preah Sihanouk.
Classes: ["Query to search Incentives", "Query to Get Approvals"]
Output:
{{
  "Query to search Incentives": "I want to see incentives for a cement factory in Cambodia.",
  "Query to Get Approvals": "I want to take approvals for a chemical unit in Preah Sihanouk."
}}

Example B (do NOT coerce “buy” into “build”)
User: I want to buy a 1 TPA cement factory.
Classes: ["Query to build industry from Scratch"]
Output:
{{
  "Query to build industry from Scratch": "I want to buy a 1 TPA cement factory."
}}

Example C (share unambiguous attributes; omit unknowns)
User: Can I get vendors and employment options for a dairy plant in Pune?
Classes: ["Query to search Vendors", "Query to Get Employee Search", "Query to search Incentives"]
Output:
{{
  "Query to search Vendors": "Can I get vendors for a dairy plant in Pune?",
  "Query to Get Employee Search": "Can I get employment options for a dairy plant in Pune?",
  "Query to search Incentives": "I want to know about incentives for a dairy plant in Pune."
}}

Now process the following:

User Query:
{user_query}

Classes:
{intent_classes}

Output:
    """


    prompt = PromptTemplate(
        input_variables=["user_query", "intent_classes"],
        template=prompt_template.strip()
    )

    chain = prompt | llm

    response = chain.invoke({
        "user_query": user_query,
        "intent_classes": intent_classes
    })

    try:
        raw_json = extract_json_object(response.content.strip())
        sub_queries = json.loads(raw_json)

        if not isinstance(sub_queries, dict):
            raise ValueError("Output is not a dictionary")

        # Validate that all intents have corresponding sub-queries
        missing = [cls for cls in intent_classes if cls not in sub_queries]
        if missing:
            raise ValueError(f"Missing sub-queries for: {missing}")

        return sub_queries

    except Exception as e:
        raise ValueError(f"Failed to parse sub-query output: {e}")

def decompose_multi_intent_query_into_sub_queries(user_query: str, intent_classes: List[str], llm: Any) -> Dict[str, Any]:
    """
    Decomposes a multi-intent industry-related query into:
    1. Classified intent classes (as-is)
    2. Sub-queries for each intent class

    Parameters:
    -----------
    user_query : str
        The original user query.

    intent_classes : List[str]
        The list of classified intent categories for this query.

    llm : Any
        The language model instance to use (LangChain-compatible).

    Returns:
    --------
    Dict[str, Any]
        {
            "classified_intents": [<class_1>, <class_2>, ...],
            "sub_queries": {
                <class_1>: <rewritten query>,
                ...
            }
        }
    """

    sub_queries = generate_sub_queries(user_query, intent_classes, llm)

    return {
        "classified_intents": intent_classes,
        "sub_queries": sub_queries
    }

def classify_query_multilabel(
        user_query: str, 
        llm: Any,
        chatId: str
) -> list:
    """
    Classifies a business-related query into one or more predefined categories based on its intent and context.

    Parameters:
    -----------
    user_query : str
        A user-submitted query related to industry or business.

    llm : Any
        The language model to be used for classification.

    Returns:
    --------
    list
        A list of category names from the following predefined categories:
        - "Query to build industry from Scratch"
        - "Query to search Vendors"
        - "Query to search Incentives"
        - "Query to Get Approvals"
        - "Query to Get Employee Search"
        - "Negatively Intended Query"
        - "Other industry-related queries"
        - "Valueless queries"

    Notes:
    ------
    - The model may return one or multiple categories based on the user query.
    - The returned list is validated to include only recognized categories.
    """

    chat_history = get_chat(f"chat_{chatId}") or []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]

    # query = f"""
    # SELECT 1
    # FROM `tabSession` AS s
    # JOIN `tabChat history` AS ch
    # ON s.name = ch.parent
    # WHERE s.name = '{chatId}'
    # AND ch.result IS NOT NULL
    # AND TRIM(ch.result) != ''
    # LIMIT 1
    # """

    # result = frappe.db.sql(query)

    is_result_shown = False


    MAIN_CATEGORIES = {
        "Query to build industry from Scratch",
        "Query to search Vendors",
        "Query to search Incentives",
        "Query to Get Approvals",
        "Query to Get Employee Search"
    }

    FALLBACK_CATEGORIES = {
        "Negatively Intended Query",
        "Other industry-related queries",
        "Valueless queries",
        "Follow-up Query"
    }

    def clean_categories(predicted_categories: list) -> list:
        """
        Remove fallback categories if any main category is present.
        """
        has_main = any(cat in MAIN_CATEGORIES for cat in predicted_categories)
        if has_main:
            return [cat for cat in predicted_categories if cat in MAIN_CATEGORIES]
        return predicted_categories

    if is_result_shown:
        # Post-Result prompt
        prompt_template = """
You are an expert in analyzing business-related queries and classifying them into one or more relevant categories from a predefined list.

Your task is to analyze the user's full query and return a JSON list of all categories that apply based on the user's intent and context.

You will also be given the `chat_history_normal`, which includes recent conversation history with the user.

The current query is being issued **after the user has already seen one or more results**. Therefore, if the query seems to **refer to, build upon, or depend on previously shown information** (like vendor counts, property details, approval names, incentive eligibility, employment stats, etc.), then include the category `"Follow-up Query"`.

This includes vague queries that would be ambiguous without prior context but make sense as continuations (e.g., “What is the power supply?”, “How many approvals are there?”, “Is CGTMSE applicable?”).

Categories & Their Definitions:

1. "Query to build industry from Scratch"  
    - Example: 
        - I want to build a 1 TPA Cement Factory. 
        - What are the land options for the chemical industry in Battambang? 
        - Tell me the land availability for the agricultural industry in Kampong Cham.  
        - I want to buy a 1 mtpa cement industry
    - Used for queries about establishing a new industry or factory from scratch — includes infrastructure, land, setup, and capacity planning.

2. "Query to search Vendors"  
    - Example: I am searching for a vendor who supplies pharmaceutical-grade raw chemicals.  
    - For queries about finding suppliers, manufacturers, or vendors for materials, equipment, or services.
    - IMPORTANT: If the query refers to a specific vendor or supplier (e.g., "Maniratna Metal Industries") that appears to be part of a previous result (as seen in `chat_history_normal`), do NOT classify it under "Query to search Vendors" — instead, classify only as "Follow-up Query".

3. "Query to search Incentives"  
    - Example: 
        - What benefits are available for setting up a cement plant in XYZ area?  
        - Tell me the government incentives for cement industry in Siem Reap,Cambodia
        - Incentive for Anand Cement
    - For queries asking about government incentives, grants, subsidies, or financial schemes.

4. "Query to Get Approvals"  
    - Example: I want to get approval for my cement plant.  
    - For queries about permits, licenses, clearances, or any required regulatory approvals.

5. "Query to Get Employee Search"  
    - Example: What is the workforce availability in XYZ region for my industry?  
    - For queries about recruitment, employment availability, or manpower.

6. "Negatively Intended Query"  
    IMPORTANT RULE: If the user mentions one or more factors negatively, but also clearly mentions any one factor positively,  
    you MUST NOT return "Negatively Intended Query". Only return the categories that reflect the user’s positive interest.  
    This rule takes priority — a single positively intended factor invalidates the negative classification.

    - Example: I don’t want to search incentives for my project in Cambodia.  
    → Classify as: ["Negatively Intended Query"]

    - Example: I want to build industry but I don’t want incentives.  
    → Classify as: ["Query to build industry from Scratch"]

    - This category applies when the user clearly rejects or expresses disinterest in one or more key business-related factors.

    The 5 core factors to consider are:
        - Approvals
        - Incentives
        - Employment
        - Vendors
        - Building industry from scratch

    Include this category ONLY if:
        a) The query mentions exactly one of these 5 factors, and the user clearly expresses that they do not want information about it.  
        b) The query mentions multiple of these factors, and the user explicitly rejects all of them.

    DO NOT include this category if:
        - Even one of the 5 core factors is positively intended or affirmed in the query.
        - The user is asking a neutral or exploratory question without explicitly rejecting a factor.
        - The rejection is vague or ambiguous (e.g., “not sure about incentives” should not trigger this).
        - The query also includes any valid main category — in such cases, classify only the positive categories.

7. "Other industry-related queries"  
    - Example: 
        - What is the role of AI in manufacturing?  
        - What investment amount is needed for setting up a bottle manufacturing industry?
    - For industry-related questions that don’t fit into the specific categories above (e.g., trends, innovation, non-supply chain topics).

    Use this category ONLY when none of the main factor categories are applicable.
    DO NOT include this category if the query also contains a valid main category such as approvals, incentives, vendors, employment, or industry setup.

8. "Valueless queries"  
    - Example: Who is Donald Trump?  
    - For queries that are completely irrelevant to business, industry setup, or supply chains.  
    - Use this category ONLY if none of the main classes are relevant or positively intended.  
    - If the user mentions any valid factor (e.g., industry setup, approvals, vendors, etc.), even alongside irrelevant topics, DO NOT include "Valueless queries".

9. Follow-up Query:
    - This refers to queries that build upon or refer to a solution the user was shown earlier in the flow.
    - You do NOT have access to the actual solution content, but you will be given the `chat_history_normal`, which helps infer what module the user previously queried.
    - If the current query appears to rely on or continue a past result, classify it as a Follow-up Query.
    When in doubt, lean toward "Follow-up Query" if the chat history contains a module-triggering query and the current query references or depends on details that are only available through that module's results.

    Common signs of a Follow-up Query:
        - The query refers to specific content that would have been shown in a result (e.g., vendors, approvals, incentives, employment, properties, etc.)
        - The query is vague or incomplete on its own, but makes sense when seen as a continuation of a previous query
        - The chat history shows a module was recently used, and the user is now referring to something shown in that module

    Very likely Follow-up Queries (if they follow a module-based response):
        - Query asking for **number of vendors for a specific supply item**
        - Query asking for **more details about a vendor previously shown**
        - Query asking for **number of total approvals, or stage-wise counts (e.g., how many pre-operational approvals?)**
        - Query asking about a **specific approval or incentive name** (e.g., CGTMSE, Fire NOC)
        - Query asking for **number of incentives shown**
        - Query referring to **employment availability** or **skill level counts**
        - Query asking about **infrastructure, seaport/power/rail connectivity** for a known property
        - Query referring to a **specific property** already discussed
        - Queries asking for **company stats, locations, or capabilities of a previously shown vendor** (e.g., "Maniratna Metal Industries") should only be classified as "Follow-up Query", not "Query to search Vendors".

    Follow-up Query Examples by Module:

    Build from Scratch:
        - Earlier: "Show me land options for chemical industry in Kampong Seila"
        - Now: "What is the power connectivity there?"
        - Now: "Which is the nearest port to the Chbar Mon plot you showed?"
        - Now: "Tell me the number of vendors who supply clay"
        - Now: "How many approvals are needed in total?"
        - Now: "How many are pre-establishment approvals?"
        → These are follow-ups because Build-from-Scratch results include full property-wise information: land infrastructure, supply chain, employment stats, approvals, and incentives.

    Incentives:
        - Earlier: "What are the incentives for textile units in Kampong Cham?"
        - Now: "Tell me more about the CGTMSE scheme"
        - Now: "Can I get capital subsidy under this?"
        - Now: "How many incentives are shown in total?"
        - Now: "What all schemes exist under Cambodia Industrial Policy 2020?"
        - Now: "What is the eligibility for Assistance for Dormitories?"
        - Now: "What is the incentive period or status for Cambodia Industrial Policy?"
        - Now: "What is the procedure to take incentives for toy manufacturing?"
        → These refer to specific incentives from the previous result.

    Approvals:
        - Earlier: "Which approvals are needed in Siem Reap for pharma units?"
        - Now: "Do I need GPCB clearance too?"
        - Now: "What’s the timeline for Fire Department NOC?"
        - Now: "How many pre-operational approvals were shown?"
        - Now: "From which department is the Factory Plan Application taken?"
        - Now: "What is the mode of application for Factory License?"
        - Now: "can you brief me about the scheme development for green estate"
        → These are continuations based on previous approval breakdown.

    Vendors:
        - Earlier: "Show vendors of Polypropylene in Kampong Seila"
        - Now: "Can you show one that is within 50 km?"
        - Now: "Are there more vendors for Styrene?"
        - Now: "How many vendors were shown in total?"
        - Now: "Can Maniratna Metal Industries supply Silver?"
        - Now: "What is the company Statistics for Maniratna Metal Industries?"
        - Now: "Where does Maniratna Metal Industries operate?"

        → These refer back to the vendor list shown earlier.

    Employment:
        - Earlier: "What is the employment availability in Chbar Mon?"
        - Now: "How many unskilled workers are there?"
        - Now: "What about skilled labor for textile?"
        → These build upon the employment result shared earlier.

    Important: If the user has recently seen a module-based result (especially Build-from-Scratch), and now asks about a specific part of that result (e.g., vendor count, approval name, incentive details, employment count, power status, etc.), classify the query as “Follow-up Query”.

    Do NOT classify a query as Follow-up if it is independently meaningful and can be understood without any prior context.

    Important Exception:
    If the current query uses similar or same keywords (e.g., industry, factor, or module) as a previous query, but introduces a different location, scale, or sub-sector, and the query is independently meaningful on its own (e.g., “incentive for cement in Siem Reap” after “incentive for cement in Anand”), then it should be classified as a new search intent, not a Follow-up Query.

    For example:

    Earlier: “Incentives for cement in Anand”

    Now: “Incentives for cement in Siem Reap”
    → This is not a Follow-up Query, but a new search, and should be classified as: ["Query to search Incentives"].

    This applies across all modules — including vendors, approvals, employment, etc. — whenever the new query introduces a distinct search condition, especially a new location or a redefined scope.

    If the query introduces a new location or different business condition (e.g., industry type, scale, or region), even if it uses similar keywords as a previous one, treat it as a new main category query, not a Follow-up.

Instructions:

- Return a list of all applicable categories that match the user's query.  
- If the query expresses multiple relevant intents, include all of them in the output.  
- Return "Negatively Intended Query" ONLY if:
    - All mentioned factors are rejected, OR
    - A single factor is mentioned and it is clearly rejected.
- If the user affirms even one valid factor, do NOT include "Negatively Intended Query".
- If the query includes any of the 5 main factors (Approvals, Incentives, Employment, Vendors, Building from Scratch),
then DO NOT include "Other industry-related queries" or "Valueless queries" — only return the actual main category(ies).
- If none of the categories clearly apply, use either "Other industry-related queries" or "Valueless queries" as appropriate — but never in addition to a main class.
- If the user’s query contains mixed or vague language, evaluate the overall meaning carefully and return all categories that are clearly present.  
- DO NOT include a category just because a word appears — understand the context.  
- DO NOT include explanations or anything other than the JSON list.

IMPORTANT SUPPRESSION RULE:

You must suppress "Negatively Intended Query", "Other industry-related queries", and "Valueless queries"  
if the query includes any valid and positively intended main factors from the following list:
- "Query to build industry from Scratch"
- "Query to search Vendors"
- "Query to search Incentives"
- "Query to Get Approvals"
- "Query to Get Employee Search"

If any of these valid categories apply, DO NOT return any fallback category — even if the query also contains unrelated, rejected, or vague side content.

Only return "Negatively Intended Query", "Other industry-related queries", or "Valueless queries" if none of the valid main categories apply — unless the query clearly refers to an earlier shown result (in which case, include "Follow-up Query").

However, if the query is a continuation (e.g., referencing a shown vendor, approval, incentive, employment stat, etc.), you must **suppress all main categories** and include only "Follow-up Query", even if the query contains vendor-like or approval-like wording.

This rule overrides all other instructions.

Examples of Output:
{{"categories": ["Query to search Incentives"]}}
{{"categories": ["Follow-up Query"]}}
{{"categories": ["Query to build industry from Scratch", "Query to Get Approvals", "Follow-up Query"]}}
{{"categories": ["Other industry-related queries"]}}
{{"categories": ["Negatively Intended Query"]}}
{{"categories": ["Valueless queries"]}}

Return ONLY a JSON object of the EXACT shape: {{"categories": [<one or more category strings>]}}
Do not include prose, markdown fences, or commentary.

Chat History:
{chat_history_normal}

Query:
{query}

JSON Output:
        """

    else:
        # No result shown
        prompt_template = """
You are an expert in analyzing business-related queries and classifying them into one or more relevant categories from a predefined list.

You will be given:
1. The user's current query.
2. The last few messages exchanged between the user and the AI (chat_history_normal), which may provide clues about what the user has asked previously.

Your task is to return a JSON list of all applicable categories based on the query and chat context.

Important:
if the query refers to a specific vendor, approval, or incentive (e.g., vendor capability, approval department, company statistics, incentive eligibility...) — but does **not clearly request a search, retrieval, or listing** — you must classify it as **"Other industry-related queries"**.

These queries may become **Follow-up Queries** in later stages once the user sees a result, but at this stage, they lack grounding and are considered general or exploratory in nature.

Categories & Their Definitions:

1. "Query to build industry from Scratch"  

    Examples:  
    - I want to build a 1 TPA Cement Factory.  
    - What are the land options for the chemical industry in Battambang?  
    - Tell me the land availability for the agricultural industry in Kampong Cham.  
    - I want to buy a 1 TPA cement industry  
    - 1 MTPA Cement Industry  
    - 1 million barrels per month petrochemical industry  

    Core Definition:  
    Classify here for queries where the user wants to start, establish, or set up a new manufacturing industry — whether:  
    - Explicitly stated (clear build/setup request), or  
    - Implied/vague but reasonably indicating intent to search for or explore manufacturing industry setup options.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention an **industry type, capacity, or location** in the context of building/starting from scratch.  
    - Vague references like “1 MTPA Cement Industry”, “1 metric tonne per month tablets industry”, etc. — treat these as build/setup intent unless they are clearly about industrial setup **guidance** details (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to build industry from Scratch”:  
    - “Build a factory for…”  
    - “Set up a manufacturing unit for…”  
    - “Start an industry for…”  
    - “Establish a plant for…”  
    - “Construct a facility for…”  
    - “Buy land for setting up…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details or guidance about industrial setup **without** an implied intent to search for or initiate the build itself.  
    2. The query is purely informational or advisory about setup processes, requirements, or characteristics — not about finding or acquiring land/facilities to start manufacturing.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General industrial setup guidance:  
    - What investment is needed for setting up a cement plant?  
    - What are the best characteristics of land for a cement factory?  
    - Evaluation questions:  
    - How to evaluate land for a cement setup?  
    - How to vet vendors for my cement plant?  
    - Supply-related queries:  
    - What supplies are needed for cement production?  
    - What is the proportion of raw material to cement production?  
    - Non‑manufacturing property queries:  
    - I want to rent a shop in Mangal Bazaar, Siem Reap.  
    - Looking for office space for my IT startup.  
    - Want to sell 10 acres of farmland in Nashik.  
    - Need warehouse space for my trading business.  
    - Looking for a place to open a hospital.  
    - Want to buy an existing textile shop.  
    - How to start a cement factory  
    - I want to buy land to grow unicorns.  

    Final Rule:  
    Default to “Query to build industry from Scratch” for any query mentioning industry type, capacity, or location in the context of manufacturing setup, unless it is damn sure the user is asking for setup guidance or purely informational content. This ensures vague but build‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.


2. "Query to search Vendors"  

    Examples:  
    - I am searching for a vendor who supplies pharmaceutical-grade raw chemicals.  
    - Show me vendors for steel rods in Phnom Penh.  
    - Search for suppliers of plastic granules in Bavet.  
    - List manufacturers who produce glass bottles near Battambang.  
    - Vendors for Anand Cement  
    - Steel supplier who has ISO 9001 certificate  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list vendor, supplier, or manufacturer options for materials, components, products, or services — whether:  
    - Explicitly stated (clear search request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “vendor(s)”, “supplier(s)”, “manufacturer(s)”, or “producer(s)” in relation to an industry, supply/suppies, location, or business type.  
    - Vague vendor references like “Vendors for cement in Siem Reap”, “Vendor Anand Cement”, etc. — treat these as search intent unless they are clearly detail‑focused (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to search Vendors”:  
    - “Show me vendors for…”  
    - “List suppliers of…”  
    - “Search for manufacturers of…”  
    - “Find suppliers for…”  
    - “Get me vendors for…”  
    - “Retrieve producers of…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details about a specific known vendor without any implied search or exploration intent.  
    2. The query is purely informational or definitional about a vendor or supply type.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General information:  
    - What does Maniratna Metal Industries supply?  
    - What supplies are needed for cement production?  
    - Company capability details:  
    - What are the past clients of Anand Cement?  
    - What standard certifications does Maheta Pvt Ltd have?  
    - Definitions:  
    - What is an ISO 9001 certificate?  
    - Specific detail request:  
    - What products does Agriland Biotech supply?  
    - What are all raw materials needed for school bag production?  
    - What is the proportion of raw material to cement production?  

    Final Rule:  
    Default to “Query to search Vendors” for any query mentioning vendors, suppliers, manufacturers, or producers in an industry/location/business/supply context, unless it is damn sure the user is asking for details of one known vendor or purely informational content. This ensures vague but search‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.


3. "Query to search Incentives"  

    Examples:  
    - What benefits are available for setting up a cement plant in XYZ area?  
    - Tell me the government incentives for cement industry in Siem Reap, Cambodia  
    - Incentive for Anand Cement  
    - Search for green estate incentives for cement industry  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list incentives, subsidies, grants, or financial schemes — whether:  
    - Explicitly stated (clear search request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “incentive(s)” in relation to an industry, location, or business type.  
    - Vague incentive references like “Incentive for cement in Siem Reap”, “Incentive Anand Cement”, etc. — treat these as search intent unless they are clearly detail-focused (see below).  

    Explicit Action-Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to search Incentives”:  
    - “Show me incentive schemes…”  
    - “List the available incentives…”  
    - “Search for schemes applicable to…”  
    - “Retrieve incentives under XYZ policy…”  
    - “Find subsidies for…”  
    - “Give me incentives for…”  

    When to Classify as “Other industry-related queries” Instead:  
    Only classify as Other industry-related queries if:  
    1. The query clearly asks for details about a specific known incentive or scheme without any implied search or exploration intent.  
    2. The query is purely informational or definitional about an incentive.  

    Exclusion Examples (These go to Other industry-related queries):  
    - General information:  
    - What assistance is available under Startup Innovation Cambodia-2020?  
    - What is the eligibility under CGTMSE?  
    - Definitions:  
    - What is CGTMSE?  
    - Program status:  
    - What is the incentive program period of the Cambodia Industrial Policy?  
    - Eligibility checks:  
    - What is the eligibility for Startup Innovation Cambodia-2020?  
    - Specific detail request:  
    - What is the quantum of assistance under Cambodia Industrial Policy?  
    - I want to know about the green estate incentive for cement industry (meaning — details about that scheme, not finding other schemes).  

    Final Rule:  
    Default to “Query to search Incentives” for any query mentioning incentives in an industry/location/business context, unless it is damn sure the user is asking for details of one known incentive or purely informational content. This ensures vague but search-intended queries are captured correctly, while truly informational-only queries remain in “Other industry-related queries”.


4. "Query to Get Approvals"  

    Examples:  
    - I want to get approval for my cement plant.  
    - What approvals are required to start a dairy in Cambodia?  
    - Search approvals for textile manufacturing in Valsad.  
    - What licenses do I need for food processing in Siem Reap?  
    - Approvals for Anand Cement  
    - Search for tree cutting approvals for cement industry  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list approvals, licenses, clearances, or permissions needed for setting up or running a business or industry — whether:  
    - Explicitly stated (clear search request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “approval(s)”, “license(s)”, “clearance(s)”, or “permission(s)” in relation to an industry, location, or business type.  
    - Vague approval references like “Approval for cement in Siem Reap”, “Approval Anand Cement”, etc. — treat these as search intent unless they are clearly detail‑focused (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to Get Approvals”:  
    - “Show me approvals for…”  
    - “List the required approvals…”  
    - “Search for licenses needed for…”  
    - “Retrieve clearance requirements for…”  
    - “Find permissions for…”  
    - “Get me approvals for…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details about a specific known approval without any implied search or exploration intent.  
    2. The query is purely informational or definitional about an approval.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General information:  
    - From which department is the Factory Plan application taken?  
    - Which department handles Factory License?  
    - Definitions:  
    - What is Environment Clearance?  
    - Process/timeframe details:  
    - How long does it take to get Environment Clearance?  
    - What is the process for Solid Waste Authorization Module (under Solid Waste Management Rules, 2016)?  
    - Specific detail request:  
    - What department issues Tree Cutting Approval?  
    - I want to know about the tree cutting approval for cement industry (meaning — details about that approval, not finding other required approvals).  

    Final Rule:  
    Default to “Query to Get Approvals” for any query mentioning approvals, licenses, clearances, or permissions in an industry/location/business context, unless it is damn sure the user is asking for details of one known approval or purely informational content. This ensures vague but search‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.


5. "Query to Get Employee Search"  

    Examples:  
    - What is the availability of employment in XYZ area for the Pharmaceutical industry?  
    - What are the labor options for agricultural industry in Siem Reap?  
    - Employment for Anand Cement  
    - Search for skilled workers for textile industry in Battambang  
    - Labour statistics for cement industry in Cambodia  

    Core Definition:  
    Classify here for queries where the user wants to explore, retrieve, or list options for employees, workers, or labour for an industry — whether:  
    - Explicitly stated (clear search/recruitment request), or  
    - Implied/vague but reasonably indicating search intent.  

    This includes:  
    - Queries that are short, incomplete, or ambiguous but clearly mention “employment”, “employees”, “labour”, “workers”, or “manpower” in relation to an industry, location, or business type.  
    - Vague references like “Employment for cement in Siem Reap”, “Labour for Anand Cement”, etc. — treat these as search intent unless they are clearly detail‑focused (see below).  

    Explicit Action‑Oriented Trigger Phrases:  
    If the query contains any of these phrases, it is always “Query to Get Employee Search”:  
    - “Show me workers for…”  
    - “List available labour for…”  
    - “Search for employees in…”  
    - “Find skilled manpower for…”  
    - “Get me labour for…”  
    - “Recruit workers for…”  

    When to Classify as “Other industry‑related queries” Instead:  
    Only classify as Other industry‑related queries if:  
    1. The query clearly asks for details about employment concepts, definitions, or company‑specific employment information without any implied search/recruitment intent.  
    2. The query is purely informational about employment types, workforce structures, or general labour concepts.  

    Exclusion Examples (These go to Other industry‑related queries):  
    - General employment information:  
    - What does semi‑skilled employment mean?  
    - Who comes under skilled labour category?  
    - Employment statistics or company‑specific data:  
    - What is the employee strength of Reliance Industries?  
    - What does employee strength mean for an industry?  
    - Workforce requirement details:  
    - What kinds of employee types are needed for cement industry setup?  
    - What are all the employee and job roles needed to start a mining industry?  
    - Certification or job standard queries:  
    - What are the standard duties of a machinist?  
    - What qualifications are needed for an AI developer?  

    Final Rule:  
    Default to “Query to Get Employee Search” for any query mentioning employment, workers, labour, or manpower in an industry/location/business context, unless it is damn sure the user is asking for definitions, conceptual explanations, or specific company employment statistics. This ensures vague but search‑intended queries are captured correctly, while truly informational‑only queries remain in “Other industry‑related queries”.

    
6. "Negatively Intended Query"  
    IMPORTANT RULE: If the user mentions one or more factors negatively, but also clearly mentions any one factor positively,  
    you MUST NOT return "Negatively Intended Query". Only return the categories that reflect the user’s positive interest.  
    This rule takes priority — a single positively intended factor invalidates the negative classification.

    - Example: I don’t want to search incentives for my project in Cambodia.  
    → Classify as: ["Negatively Intended Query"]

    - Example: I want to build industry but I don’t want incentives.  
    → Classify as: ["Query to build industry from Scratch"]

    - This category applies when the user clearly rejects or expresses disinterest in one or more key business-related factors.

    The 5 core factors to consider are:
        - Approvals
        - Incentives
        - Employment
        - Vendors
        - Building industry from scratch

    Include this category ONLY if:
        a) The query mentions exactly one of these 5 factors, and the user clearly expresses that they do not want information about it.  
        b) The query mentions multiple of these factors, and the user explicitly rejects all of them.

    DO NOT include this category if:
        - Even one of the 5 core factors is positively intended or affirmed in the query.
        - The user is asking a neutral or exploratory question without explicitly rejecting a factor.
        - The rejection is vague or ambiguous (e.g., “not sure about incentives” should not trigger this).
        - The query also includes any valid main category — in such cases, classify only the positive categories.

        
7. "Other industry‑related queries"  

    Examples:  
    - What is the role of AI in manufacturing?  
    - What is the eligibility under CGTMSE?  
    - Looking for office space for my IT startup.  
    - I want to rent a shop in Mangal Bazaar, Siem Reap.

    Core Definition:  
    Use this category for industry‑related questions that do not fit into any of the five main categories ("Query to build industry from Scratch", "Query to search Vendors", "Query to search Incentives", "Query to Get Approvals", "Query to Get Employee Search").  
    This includes:  
    1. Queries that are **purely informational, definitional, or knowledge‑based** about a specific topic from any of the main categories — with **no search, retrieval, or exploration intent**.  
    2. Queries that are **non‑manufacturing in scope** (e.g., retail, office, hospitality, healthcare, property sales, etc.) **but still have legitimate business/commercial intent**.  
    3. Queries that are **business-related but clearly out of scope** for manufacturing search (e.g., unrealistic business ideas with commercial intent).  

    Important:  
    - **Only** classify as "Other industry‑related queries" if it is **damn sure** the query has **legitimate business/commercial context** and is **purely informational / definitional** for that category OR is **completely outside manufacturing scope but still business-related**.  
    - If there is **any reasonable chance** that the query is a vague search intent for one of the five main categories, **do not** classify here — instead, classify under the relevant main category.  
    - **Must have business context** — if there's no business/commercial intent whatsoever, classify as "Valueless queries".

    When "Other industry‑related queries" is Correct:  

    **A. Build from Scratch context:**  
    - Query is only about setup guidance / concept, not searching to build:  
    - What investment is needed for a cement plant?  
    - What are the best characteristics of land for a cement factory? 
    - How to start a cement factory 
    - Query is non‑manufacturing property related **with business intent**:  
    - I want to rent a shop in Mangal Bazaar, Siem Reap.  
    - Looking for office space for my IT startup.  
    - Need café location in Sihanoukville.  
    - Looking for a place to open a hospital.  
    - Want to buy an existing textile shop.  
    - Unrealistic **business ideas**:  
    - I want to build chocolate factory on moon for commercial purpose.

    **B. Vendors context:**  
    - Vendor capability / product detail questions:  
    - What does Maniratna Metal Industries supply?  
    - What standard certifications does Maheta Pvt Ltd have?  
    - General supply knowledge:  
    - What supplies are needed for cement production?  
    - What is an ISO 9001 certificate?  

    **C. Incentives context:**  
    - Incentive definitions / details:  
    - What is CGTMSE?  
    - What is the eligibility for Startup Innovation Cambodia‑2020?  
    - What is the incentive program period of the Cambodia Industrial Policy?  
    - What is the quantum of assistance under Cambodia Industrial Policy?  

    **D. Approvals context:**  
    - Approval definitions / process detail:  
    - What is Environment Clearance?  
    - From which department is the Factory Plan application taken?  
    - How long does it take to get Environment Clearance?  

    **E. Employee Search context:**  
    - Employment definitions / statistics:  
    - What does semi‑skilled employment mean?  
    - Who comes under skilled labour category?  
    - What is the employee strength of Reliance Industries?  

    Final Rule:  
    If none of the five main categories are **clearly and positively intended** — and the query has **legitimate business context** and is **purely informational, definitional, non‑manufacturing business, or unrealistic business ideas** — classify as "Other industry‑related queries".  
    If **even one** main category is clearly intended (even vaguely), do **not** classify as "Other industry‑related queries".
    If there is **no business context at all**, classify as "Valueless queries".


8. "Valueless queries"  
    - Examples: 
        - Hello, how are you?
        - Who is Donald Trump?
        - What's the weather today?
        - I want to make a shirt for my friend.  
        - Want 10 acres to build a castle. (personal/fantasy, no business intent)
        - Need place for my TikTok dance studio factory. (entertainment, not serious business)
        - I want to buy a bike for personal use.
        - Tell me a joke.
        - Good morning!
        - Thank you, goodbye.
        - Blahblah build blah idk 🤷‍♀️

    - For queries that are completely irrelevant to business, industry setup, or supply chains.  
    - This includes:
        - **Conversational elements**: Greetings, pleasantries, social interactions
        - **General knowledge or political questions** unrelated to industry
        - **Personal queries**, unrelated product buying decisions, or entertainment topics
        - **Fantasy/joke queries** with no legitimate business intent
        - Queries where industry-related keywords are present but the **intent** is not relevant to industry-building or supply chains and has **no commercial purpose**

    - Use this category ONLY if:
        - None of the main 5 classes are relevant or positively intended (i.e., Build from Scratch, Vendor, Incentive, Approval, Employee Search)
        - The query contains **no actionable business or industry-specific context**
        - The user is clearly not looking for information connected to business workflows
        - **No commercial intent** — purely personal, social, entertainment, or general knowledge

    - DO NOT include this category if:
        - The query includes any valid industry intent (even alongside irrelevant elements)
        - The query could be interpreted as loosely connected to industry setup, supply chain, approvals, etc.
        - The query has **any legitimate business or commercial context**

    **Key Distinguishing Rule:**
    Ask: "Does this query have ANY business/commercial intent or context?"
    - **YES** + doesn't fit main 5 categories → "Other industry-related queries"  
    - **NO** (zero business context) → "Valueless queries"

    Additional Examples:
    - I'm going to buy a new bike, for that which approvals do I need? → Not relevant to industry-building (personal purchase)
    - What's your favorite color? → No business context
    - How are you doing today? → Social interaction, no business context

    Classify only if the query is irrelevant in both content **and** intent, with **zero commercial/business purpose**.

    
Instructions:

    - Return a list of all applicable categories that match the user's query.  
    - If the query expresses multiple relevant intents, include all of them in the output.  
    - Return "Negatively Intended Query" ONLY if:
        - All mentioned factors are rejected, OR
        - A single factor is mentioned and it is clearly rejected.
    - If the user affirms even one valid factor, do NOT include "Negatively Intended Query".
    - If the query includes any of the 5 main factors (Approvals, Incentives, Employment, Vendors, Building from Scratch),
    then DO NOT include "Other industry-related queries" or "Valueless queries" — only return the actual main category(ies).
    - If none of the categories clearly apply, use either "Other industry-related queries" or "Valueless queries" as appropriate — but never in addition to a main class.
    - If the user’s query contains mixed or vague language, evaluate the overall meaning carefully and return all categories that are clearly present.  
    - DO NOT include a category just because a word appears — understand the context.  
    - DO NOT include explanations or anything other than the JSON list.

IMPORTANT SUPPRESSION RULE:

You must suppress "Negatively Intended Query", "Other industry-related queries", and "Valueless queries"  
if the query includes any valid and positively intended main factors from the following list:
- "Query to build industry from Scratch"
- "Query to search Vendors"
- "Query to search Incentives"
- "Query to Get Approvals"
- "Query to Get Employee Search"

If any of these valid categories apply, DO NOT return any fallback category — even if the query also contains unrelated, rejected, or vague side content.

Only return "Other industry-related queries" if:
- None of the valid main categories clearly apply, AND
- The query refers to a vendor, incentive, or approval in a vague, referential way without asking to search, retrieve, or list results.

This prevents misclassification of passive or vague queries as actual search intents.

This rule overrides all other instructions.

Examples of Output:
{{"categories": ["Query to search Vendors"]}}
{{"categories": ["Query to search Incentives", "Query to Get Approvals"]}}
{{"categories": ["Negatively Intended Query"]}}
{{"categories": ["Valueless queries"]}}

Return ONLY a JSON object of the EXACT shape: {{"categories": [<one or more category strings>]}}
Do not include prose, markdown fences, or commentary.

Chat History:
{chat_history_normal}

Query:
{query}

JSON Output:
        """

    prompt = PromptTemplate(
        input_variables=["query", "chat_history_normal"],
        template=prompt_template
    )

    chain = prompt | llm
    invoke_payload = {"query": user_query, "chat_history_normal": Chat_history_normal}
    result = chain.invoke(invoke_payload)
    raw_output = getattr(result, "content", str(result)).strip()
    print(raw_output)

    # P1-5: validate the raw LLM output through IntentClassification.
    # parse_llm_response does json.loads -> IntentClassification, then
    # exactly one corrective retry (json_mode=True) on failure, then an
    # IntentClassificationFailure envelope. The legacy safe_parse_output
    # regex/literal_eval ladder is now a fallback only.
    filled_prompt = prompt.format(**invoke_payload)
    validated = parse_llm_response(
        raw=raw_output,
        model_class=IntentClassification,
        llm_client=llm,
        prompt=filled_prompt,
    )
    if isinstance(validated, IntentClassification):
        parsed_categories = list(validated.categories)
    else:
        # Failure envelope (IntentClassificationFailure or dict). Already
        # logged by parse_llm_response. Fall back to the legacy ladder so
        # the request degrades to "Other industry-related queries" via
        # the existing downstream branch rather than crashing.
        frappe.log_error(
            f"classify_query_multilabel envelope: {validated}",
            "classify_query_multilabel",
        )
        parsed_categories = safe_parse_output(raw_output)

    if parsed_categories:
        cleaned_categories = clean_categories(parsed_categories)
        
        fallback_detected = [cat for cat in FALLBACK_CATEGORIES if cat in cleaned_categories]
        if fallback_detected:
            fallback_class = fallback_detected[0]
            return {
                "classified_intents": [fallback_class],
                "sub_queries": {
                    fallback_class: user_query
                }
            }

        final_json_with_sub_queries = decompose_multi_intent_query_into_sub_queries(
            user_query=user_query,
            intent_classes=cleaned_categories,
            llm=llm
        )
        return final_json_with_sub_queries

    # Fallback — return "Other industry-related queries"
    return {
        "classified_intents": ["Other industry-related queries",],
        "sub_queries": {"Other industry-related queries": user_query}
    }

def classify_user_intent(user_query, llm, chat_id):
    """
    Classifies the main and additional user intents, and generates a refined instructional response
    using varied formal endings.

    Args:
        user_query (str): The user's input query.
        llm (object): A language model or LLM reference needed by classify_query_multilabel.

    Returns:
        dict: {
            'main_class': str,
            'additional_classes': list of str,
            'sub_queries': dict of {intent: sub_query},
            'additional_response': str
        }
    """

    # Step 1: Main and multilabel classification
    main_intent = classify_query(user_query, llm, chat_id)
    multilabel_result = classify_query_multilabel(user_query, llm, chat_id)
    classified_intents = multilabel_result.get('classified_intents', [])
    sub_queries = multilabel_result.get('sub_queries', {})

    # Step 2: Identify additional classes
    additional_classes = [intent for intent in classified_intents if intent != main_intent]

    # Step 3: Mapping for clean, human-friendly intent labels
    intent_labels = {
        "Query to build industry from Scratch": "industry creation",
        "Query to search Vendors": "vendors",
        "Query to search Incentives": "incentive information",
        "Query to Get Approvals": "approvals",
        "Query to Get Employee Search": "employee search"
    }

    # Step 4: List of formal/instructional endings
    formal_endings = [
    "in future steps.",
    "at a later time.",
    "in a separate step.",
    "as a follow-up task.",
    "through a separate query later.",
    "in a subsequent session.",
    "whenever you revisit this module.",
    "by initiating another check later.",
    "during a later exploration.",
    "via a new query at any time.",
    "in an upcoming step of the process.",
    "through a dedicated follow-up.",
    "by exploring it independently later.",
    "in a later interaction.",
    "as part of a future check."
    ]

    selected_ending = random.choice(formal_endings)

    # Step 5: Extract readable labels for additional classes
    labels = [intent_labels[c] for c in additional_classes if c in intent_labels]

    # Step 6: Construct single-sentence formal response
    if not labels:
        additional_response = ""
    elif len(labels) == 1:
        additional_response = f"You can check for {labels[0]} {selected_ending}"
    elif len(labels) == 2:
        additional_response = f"You can check for {labels[0]} and {labels[1]} {selected_ending}"
    else:
        additional_response = (
            f"You can check for {', '.join(labels[:-1])}, and {labels[-1]} {selected_ending}"
        )

    return {
        'main_class': main_intent,
        'additional_classes': additional_classes,
        'sub_queries': sub_queries,
        'additional_response': additional_response
    }


def generate_followup_response(
    user_query: str,
    llm,
    chatId
) -> str:
    """
    Generates a follow-up response message for the user based on their latest query
    and recent chat history using an LLM.

    Parameters:
    - chat_history: list of past HumanMessage and AIMessage objects
    - user_query: latest user message (string)
    - llm: a LangChain-compatible chat model (e.g., ChatOpenAI or ChatGroq)

    Returns:
    - A context-aware string message to show the user
    """

    chat_history = get_chat(f"chat_{chatId}") or []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]

    # Step 2: Create prompt 
    prompt_template = """
You are an intelligent assistant that helps determine what kind of follow-up message to show to the user based on their most recent query and the last few messages from their chat history.

The function is called only when the system has already classified the latest user message as a "Follow-up Query".

Now, your job is to decide whether this follow-up is:
1. An exact repeat or nearly same query as a previously asked question (either in wording or meaning), OR
2. A true follow-up, meaning the user is building upon a previously shown result but asking something new or related.

Use the last few messages from chat history — including both the user's and the assistant's messages — to make your judgment.

If the latest user message is similar to an earlier user query, and the AI’s response to that earlier query was already a follow-up redirect message (e.g., "go to result screen to ask"), then:
→ Assume that this is another attempt at follow-up in the same thread.
→ Respond again with a similar guidance message to direct the user to the result screen. You may paraphrase the redirection politely to avoid repetition.

Only if the latest message is similar to an earlier query and the AI had responded with a result, then say that the result already exists and can be viewed again.

Do not rely only on the user's messages — also analyze the AI messages to understand what has already been said.

Guidelines:
- If the user query is exactly the same or very similar to a past query:
    - Respond with:
      `"This query seems very similar to one you've already asked. You can revisit the result by clicking on 'View Result' to see the details again."`

- If the user query is a genuine follow-up, such as asking for additional info based on the result:
    - Respond with:
      `"It seems like your question is a follow-up to something you've already seen. For a better experience, you can go to the specific result screen and ask your question there so I can guide you more precisely."`

Inputs:

Chat history (last few turns):
{Chat_history_normal}

Latest user query:
{user_query}

Output:
Return ONLY the appropriate message (based on the 2 cases above). Do NOT include explanations or reasoning.
"""

    prompt = PromptTemplate(
        input_variables=["Chat_history_normal","user_query"],
        template=prompt_template
    )

    chain = prompt | llm
    # Step 3: Call LLM
    response = chain.invoke({"user_query": user_query, "Chat_history_normal":Chat_history_normal})
    message_from_ai = response.content.strip()
    

    return message_from_ai


def extract_location_from_query(user_input: str, available_areas: List[str], available_cities: List[str], available_states: List[str], llm) -> Dict[str, Dict[str, str]]:
    """
    Extract the location mentioned in the user query and classify it into area, city, or state.
    
    Parameters:
        user_input (str): The user-provided query.
        available_areas (List[str]): List of all available areas.
        available_cities (List[str]): List of all available cities.
        available_states (List[str]): List of all available states.
        llm: The language model instance to use for processing.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary containing the extracted location and its classification.
    """

    # Define the prompt
    prompt_template = """
You are an expert location extraction system. 
Your task is to extract ONE SINGLE, MOST RELEVANT location from the user's query based on strict hierarchy and literal user intent.

------------------------------------------------------
LOCATION EXTRACTION RULES (STRICT & HIERARCHY-AWARE)
------------------------------------------------------

1. Extract ONLY the **lowest-level (most granular)** location mentioned explicitly in the query.
   - If the query has "City + Province", return only the city.
   - If the query has "Area + City + Province", return only the area.
   - If the query has "District + Province", return only the district.
   - Always pick the location **closest to the ground level**, never the larger parent region.

   Examples:
   - "Bavet, Svay Rieng" → "Bavet"
   - "Chork, Bavet, Svay Rieng" → "Chork"
   - "Tuol Kouk, Phnom Penh" → "Tuol Kouk"
   - "Prey Nob, Preah Sihanouk" → "Prey Nob"

2. Never combine multiple levels.
   - Do NOT return "Bavet, Svay Rieng".
   - Do NOT return "City + Province".
   - Return only the **single most specific location**.

3. Never infer or hallucinate industrial estates.
   - Do NOT convert "Bavet" → "Bavet SEZ" unless the user explicitly writes "SEZ".
   - Do NOT expand locations on your own.

4. Preserve Location Abbreviations ONLY When Explicitly Present.

   - If the user includes an industrial/zone abbreviation, you MUST return it exactly as written.
   - Never expand, shorten, modify, or infer abbreviations.
   - Never add an abbreviation that the user did not explicitly mention.

   Examples:
     - "Phnom Penh SEZ" → "Phnom Penh SEZ"
     - "Sihanoukville SEZ" → "Sihanoukville SEZ"
     - "Bavet SEZ" → "Bavet SEZ"
     - "Poipet SEZ" → "Poipet SEZ"
     - "Neak Loeung SEZ" → "Neak Loeung SEZ"
     - "Manhattan SEZ" → "Manhattan SEZ"
     - "Goldfame Pak Shun SEZ" → "Goldfame Pak Shun SEZ"

   Also:
     - If user writes only "Bavet", do NOT output "Bavet SEZ".
     - If user writes only "Poipet", do NOT output "Poipet SEZ".
     - If user writes only "Neak Loeung", do NOT output "Neak Loeung SEZ".

   Only preserve abbreviations when explicitly present in the user's query.

5. Correct spelling only when it's clearly evident.
   - "Phnompenh" → "Phnom Penh"
   - "Siem Riep" → "Siem Reap"

6. Standardise only when the official modern name exists.
   - "Kompong Som" → "Sihanoukville"
   - "Kompong Cham" → "Kampong Cham"
   - "Battambong" → "Battambang"
   - Additional examples:
     - "Kratie" → "Kratié" 
     - "Takeo" → "Takéo" 
   - Only apply such standardisation if the user input uses the old name; if the user already uses modern name, leave it as is.

7. If multiple locations appear, extract ONLY the one relevant to the user's request.
   - Ignore personal or background references.
   - Example:
     "I live in Battambang but I want incentives for Kampong Seila." → "Kampong Seila"

8. If the query has NO location, return `"None"`.

9. Output ONLY the JSON. No explanations.

------------------------------------------------------
USER QUERY
{query}

------------------------------------------------------
OUTPUT FORMAT
{{
    "Location": "<Extracted Location or 'None'>"
}}
    """

    # Create a PromptTemplate and LLM chain
    prompt = PromptTemplate(
        input_variables=["query"],
        template=prompt_template
    )
    chain = prompt | llm

    # Run the LLM chain
    response = chain.invoke({"query": user_input})
    with open("testlog.txt", "a") as file:
                file.write(f"\nIn the extraction fun for emp...::: {response.content.strip()} for EMPLOYMENT :) ")
    update_llm_token(response)

    # Extract location from the model response
    location_match = re.search(r'"Location":\s*"([^"]+)"', response.content.strip())
    extracted_location = location_match.group(1) if location_match else "None"

    # **Return immediately if no location was extracted**
    if extracted_location == "None":
        Extracted_Data = {"Location": extracted_location}
        Validated_Data = {"Area": "None", "City": "None", "State": "None"}
        return Extracted_Data, Validated_Data

    # Function to find the best match using fuzzy logic
    def get_best_match(location: str, choices: List[str], threshold: int = 85) -> str:
        """
        Finds the best match for a given location from a list of choices using fuzzy matching.
        
        Parameters:
            location (str): The location extracted from the user query.
            choices (List[str]): List of available areas, cities, or states.
            threshold (int): Minimum similarity score required to consider a match.

        Returns:
            str: The best-matching location from the choices or "Not Available in List" if no match is found.
        """
        if not location.strip():
            return "Not Available in List"
        
        # Convert location and choices to lowercase for case-insensitive matching
        location_lower = location.lower()
        choices_lower = [choice.lower() for choice in choices]

        # Extract the best match (handle None case)
        result = process.extractOne(location_lower, choices_lower, scorer=fuzz.ratio)
        with open("testlog.txt", "a") as file:
                file.write(f"\nChecking result.....::::: {result} for EMPLOYMENT :) ")
        # print("="*100,"\nFuzz Result: \n",result, "\n","="*100)
        # If no match is found, return "Not Available in List"
        if result is None:
            return "Not Available in List"

        match_lower, score, _ = result  # Safely unpack the three values

        # Retrieve the original case-sensitive name from `choices`
        match_original = next((choice for choice in choices if choice.lower() == match_lower), "Not Available in List")

        return match_original if score >= threshold else "Not Available in List"

    # Validate using fuzzy matching
    best_city_match = get_best_match(extracted_location, available_cities, threshold=80)
    best_area_match = get_best_match(extracted_location, available_areas, threshold=80)
    best_state_match = get_best_match(extracted_location, available_states, threshold=80)

    # **If no match is found, return "Not Available in List" immediately**
    if best_city_match == "Not Available in List" and best_area_match == "Not Available in List" and best_state_match == "Not Available in List":
        Extracted_Data = {"Location": extracted_location}
        Validated_Data = {"Area": "Not Available in List", "City": "Not Available in List", "State": "Not Available in List"}
        return Extracted_Data, Validated_Data
    # **Prioritize classification: City > Area > State**
    validated_classification = {
        "Area": "None",
        "City": "None",
        "State": "None"
    }

    if best_city_match != "Not Available in List":
        validated_classification["City"] = best_city_match
    elif best_area_match != "Not Available in List":
        validated_classification["Area"] = best_area_match
    elif best_state_match != "Not Available in List":
        validated_classification["State"] = best_state_match

    Extracted_Data = {"Location": extracted_location}
    Validated_Data = validated_classification
    return Extracted_Data, Validated_Data

def extract_comparison_locations(user_input: str, available_areas: List[str], available_cities: List[str], available_states: List[str], llm) -> Dict[str, Dict[str, str]]:
    """
    Extract multiple locations mentioned in the user query and classify them into area, city, or state.

    Parameters:
        user_input (str): The user-provided query.
        available_areas (List[str]): List of all available areas.
        available_cities (List[str]): List of all available cities.
        available_states (List[str]): List of all available states.
        llm: The language model instance to use for processing.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary containing the extracted locations and their classification.
    """

    # Define the prompt
    prompt_template = """
    You are an expert in analyzing user queries and accurately extracting **multiple locations** for comparison purposes.
    Your task is to identify and extract **all relevant locations** mentioned in the user query.
    Do not classify the locations into area, city, or state. Simply extract the correct location names.

    Key Extraction Rules:

    1. Extract All Relevant Locations:
    - Identify and extract all locations mentioned in the query that are relevant to the comparison.
    - Ignore locations that are mentioned for personal reference or additional context (e.g., "I live in X but want to compare Y and Z" → Extract only Y and Z).

    2. Preserve Location Abbreviations:
    - If a location is followed by an abbreviation (e.g., "SEZ"), always extract the full location name including the abbreviation.
    - Do not remove or separate the abbreviation from the location name under any circumstances.

    3. Handle Spelling Errors & Variations:
    - If a location contains spelling mistakes, correct it and return the corrected value.

    4. Ensure the Official Location Name is Used:
    - If a location has multiple variants, always return the official name of the location instead of alternative or outdated names.
    - Some common examples:
        - "Kompong Som" → "Sihanoukville"
        - "Kompong Cham" → "Kampong Cham"
        - "Siem Riep" → "Siem Reap"
        - "Battambong" → "Battambang"
        - "Kratie" → "Kratié"
        - "Takeo" → "Takéo"
    - Ensure all locations are recognized and standardized to their official designation.

    5. Only Return Locations if Mentioned:
    - If no locations are found, return `"None"` as the value.

    6. Majority of Locations Will Be from Cambodia:
    - Assume most locations will be from Cambodia.
    - If a location is outside Cambodia, still extract and return it.

    7. No Additional Explanations:
    - The output must only contain the extracted locations.
    - Do not provide reasoning, context, or explanations.

    User Query:
    {query}

    Output Format:
    Provide only the extracted locations in the following **JSON format**:
    {{
        "Locations": ["<Extracted Location 1>", "<Extracted Location 2>", ...] or ["None"]
    }}
    """

    # Create a PromptTemplate and LLM chain
    prompt = PromptTemplate(
        input_variables=["query"],
        template=prompt_template
    )
    chain = prompt | llm

    # Run the LLM chain
    response = chain.invoke({"query": user_input})
    update_llm_token(response)

    # Extract locations from the model response
    locations_match = re.search(r'"Locations":\s*\[([^\]]*)\]', response.content.strip())
    extracted_locations = [loc.strip().strip('"') for loc in locations_match.group(1).split(",") if loc] if locations_match else ["None"]

    # **Return immediately if no location was extracted**
    if extracted_locations == ["None"]:
        Extracted_Data = {"Locations": extracted_locations}
        Validated_Data = {"Area": "None", "City": "None", "State": "None"}
        return Extracted_Data, Validated_Data

    # Function to find the best match using fuzzy logic
    def get_best_match(location: str, choices: List[str], threshold: int = 85) -> str:
        """
        Finds the best match for a given location from a list of choices using fuzzy matching.

        Parameters:
            location (str): The location extracted from the user query.
            choices (List[str]): List of available areas, cities, or states.
            threshold (int): Minimum similarity score required to consider a match.

        Returns:
            str: The best-matching location from the choices or "Not Available in List" if no match is found.
        """
        if not location.strip():
            return "Not Available in List"

        # Convert location and choices to lowercase for case-insensitive matching
        location_lower = location.lower()
        choices_lower = [choice.lower() for choice in choices]

        # Extract the best match (handle None case)
        result = process.extractOne(location_lower, choices_lower, scorer=fuzz.ratio)
        if result is None:
            return "Not Available in List"

        match_lower, score, _ = result  # Safely unpack the three values

        # Retrieve the original case-sensitive name from `choices`
        match_original = next((choice for choice in choices if choice.lower() == match_lower), "Not Available in List")

        return match_original if score >= threshold else "Not Available in List"

    # Validate and classify multiple locations
    validated_classification = {"Area": [], "City": [], "State": []}

    for extracted_location in extracted_locations:
        best_city_match = get_best_match(extracted_location, available_cities, threshold=70)
        best_area_match = get_best_match(extracted_location, available_areas, threshold=70)
        best_state_match = get_best_match(extracted_location, available_states, threshold=70)

        # **If no match is found, classify as "Not Available in List"**
        if best_city_match == "Not Available in List" and best_area_match == "Not Available in List" and best_state_match == "Not Available in List":
            validated_classification["Area"].append("Not Available in List")
            validated_classification["City"].append("Not Available in List")
            validated_classification["State"].append("Not Available in List")
        else:
            # **Prioritize classification: City > Area > State**
            if best_city_match != "Not Available in List":
                validated_classification["City"].append(best_city_match)
            elif best_area_match != "Not Available in List":
                validated_classification["Area"].append(best_area_match)
            elif best_state_match != "Not Available in List":
                validated_classification["State"].append(best_state_match)

    # Format as comma-separated strings or "None" if empty
    for key in validated_classification:
        validated_classification[key] = ", ".join(validated_classification[key]) if validated_classification[key] else "None"
    Extracted_Data = {"Locations": extracted_locations}
    Validated_Data = validated_classification
    return Extracted_Data, Validated_Data

module_names_list = ["Query to build industry from Scratch", "Query to search Vendors", "Query to search Incentives", "Query to Get Approvals", "Query to Get Employee Search", ]

field_with_description = {
    "Query to search Vendors": {
        "Vendor Name": "The official name of the vendor or business providing the service or goods (e.g., Bhagwati Chemicals, Agriland Biotech Limited.).",
        "Supply Description By Vendor": "A brief explanation of the products or services offered by the vendor (e.g., 'We provide high-quality steel rods for construction projects' or 'PCB Assembly|BOM Sourcing|Turnkey Manufacturing|Electronics Manufacturing').",
        "List of Certifications": "Certifications held by the vendor that validate compliance with industry standards (e.g., ISO 9001, BIS Certification, GMP Certification, ASME Certification, AS9100 (for aerospace), FDA Approval (US))."
    },
    "Query to search Incentives": {
        "Incentive Name": "The official title of the financial or non-financial support program available (e.g., Cambodia SME Seed Fund, SME Credit Guarantee Scheme, Water Infrastructure Development Program, Industrial Water Subsidy Program, Rehabilitation Support Program).",
        
        "Incentive Type": "The category of the incentive based on the type of support it provides. This includes financial and non-financial assistance that improves industrial or business growth. Examples include Equity Support, Sustenance Allowance, Tax Exemption, Interest Subsidy, Capital Investment Subsidy, Incentive in Power Tariff and Electricity Duty, Incentive in Water Duty, Subsidies for Water Infrastructure, Assistance in Water Conservation Initiatives, and Rehabilitation Assistance (for disaster recovery, employee support, or facility restoration).",
        
        "Quantum of Assistance": "The amount or percentage of financial assistance or benefit provided. This may include direct financial grants, subsidies, duty exemptions, or infrastructural support. Example statements include 'Seed support up to $30,000', 'Capital subsidy of 25% on plant and machinery cost', 'Exemption of electricity duty', 'Subsidy of 15% on water infrastructure development', 'Exemption on water duty for industrial processes', or 'Financial assistance of $10,000 for rehabilitation of industrial facilities post-natural disaster.'"
    },
    "Query to Get Approvals": {
        "Name of License / Approval": "Clearly specify the exact name of the required license, approval, clearance, or permission for business operations. This includes specific approval types such as 'Environmental Clearance', 'Fire NOC', 'Factory License', or any regulatory certificate required for setting up or operating a business. Do not include generic terms like 'approval' or 'license' without context.",
        "Government Department": "The official name of the specific government authority or department responsible for issuing licenses or approvals. This includes departments like 'Revenue Department', 'Pollution Control Board', 'Fire Department', 'Urban Development Authority', 'Municipal Corporation', or similar regulatory bodies. If the query mentions a department's name (e.g., 'Revenue', 'Fire', 'Environment'), it should always be extracted as a keyword. Do not exclude common department names even if they seem generic. For example, 'Revenue Department' must be included as 'revenue', 'department'.",
        "Land Type": "The specific classification of land where business operations or approvals apply. This could be terms like 'Agricultural Land', 'Non-Agricultural Land - Urban', or 'Industrial Land'.",
        "Business Location": "Details about the specific area or industrial zone related to the business, such as 'GIDC', 'Non GIDC', 'DSIRDA', 'MBSIRDA', 'GPCP SIRDA'. Do not include general city or state names.",
        "Stage": "The specific phase during which the approval is required, like 'Pre-establishment', 'Pre-requisite', or 'Pre-operation'.",
        "Mode of Application": "Specifies whether the approval process is 'Online' or 'Offline'. Extract only these specific terms.",
        "Vicinity Detail": "Details about the proximity to critical or sensitive areas affecting the approval process. This includes terms like 'Forest', 'Archaeological site', or 'Mineral bearing site' relevant to the business operation.",
        "Cross Following Details": "Indicates whether the business site crosses important utilities such as 'Notified rivers', 'nalas', 'canals', 'drains', or specific pipelines (e.g., 'National Gas Pipeline', 'Regional Gas Pipeline', 'Provincial Gas Line'). Also includes proximity to 'Water bodies'.",
        "Tree Cutting": "Mentions whether tree cutting is required for the business setup or operations. Keywords include 'tree cutting'.",
        "Road Cutting": "Indicates whether road cutting is necessary. Keywords include 'road cutting'.",
        "Require Pole Shifting": "Specifies if shifting of electricity or communication poles is needed. Keywords include 'pole shifting'."
    },
    "Query to build industry from Scratch": {
        "Property Type": "The type of land based on usage (Non-Agricultural Land, Agricultural Land, Industrial Land, Industrial Park Plot, GIDC Plot, Warehouse, Industrial Plant, Auction Property, Industrial Park).",
        "Business Location Type": "The classification of the business location (GIDC, Non GIDC, DSIRDA, MBSIRDA, GPCP SIRDA).",
        "Land Type": "The specific classification of land (Agricultural Land, Non-Agricultural Land (Rural), Non-Agricultural Land (Urban)).",
        "Location": "The specific area, city, or state where the property is located (e.g., Cambodia, Battambang, Prey Nob).",
        "Vicinity of": "Environmental or geographical features nearby (Forest, Archaeological site, Mineral bearing site).",
        "Tree Cutting Involved": "Indicates whether tree cutting is required for the project (Tree cutting).",
        "Road Cutting Involved": "Specifies if road cutting is required to establish infrastructure (Road Cutting).",
        "Will your industry cross the following?": "Checks whether the industry site intersects with important geographical or utility structures (Pipeline of National Gas Pipeline, Pipeline of Regional Gas Pipeline, Pipeline of Provincial Gas Line, Water bodies, Notified rivers/ nalas/ canals/ drains)."
    }
}

def extract_keywords_from_query(
    user_input: str,
    fields: Dict[str, str],
    module_names: List[str],
    llm,
    current_module: str,
    existing_keywords: Union[List[str], None] = None
) -> Dict[str, Union[List[str], None]]:
    """
    Extracts relevant single-word keywords from the user's query based on the provided field descriptions,
    excluding words that are part of predefined module names or restricted categories. Also merges with existing keywords.

    Parameters:
    ----------
    user_input : str
        The user's query from which keywords are to be extracted.

    fields : Dict[str, str]
        A dictionary mapping field names to their short explanations.

    module_names : List[str]
        A list of module names, where words from these names are to be excluded from the extracted keywords.

    llm : object
        An instance of a language learning model used to process and extract keywords from the prompt.

    current_module : str
        The name of the current module which may influence the prompt structure.

    existing_keywords : Union[List[str], None]
        A list of already identified keywords to merge with the newly extracted ones.

    Returns:
    -------
    Dict[str, Union[List[str], None]]
        A dictionary with the key "KEYWORDS" mapping to a list of merged extracted keywords.
        If no valid keywords are found, returns {"KEYWORDS": None}.
    """

    # Build a text block enumerating each field with its meaning
    field_lines = [f"{idx}) {fname}: {fdesc}" for idx, (fname, fdesc) in enumerate(fields.items(), start=1)]
    fields_explained = "\n".join(field_lines)

    # Process module names into individual lowercase words for exclusion
    module_words = set(token.strip().lower() for mod_name in module_names for token in mod_name.split())

    modules_text = ", ".join(module_names)

    ####################################################################
    # 3) Construct the Prompt (with instructions to produce single words)
    ####################################################################
    if current_module == "Query to build industry from Scratch":
        prompt_template_str = """
        You are an expert at extracting single-word keywords from a user query.

        1) FOCUS FIELDS (To Be Extracted as Keywords)
        These are the fields that you must focus on while extracting keywords. If the user's query contains any word that logically matches the meaning of these fields, it must be extracted as a keyword.

        {fields_explained}

        2) RESTRICTED CATEGORIES (Never to Be Extracted)
        Words from the following restricted categories must NEVER be extracted as keywords because they disrupt the flow.

        - Capacity Units: Measurement units related to capacity, power, or weight.
        Examples: "MW", "KW", "ton", "kg/day", "liters", "m³", "barrels", "cubic feet", "TPA"

        - Time Periods: Words referring to time durations or periods.
        Examples: "year", "month", "day", "hour", "weekly", "annually", "quarterly", "biweekly"

        - Product Names: Specific products being manufactured or sold.
        Examples: "car", "plastic", "steel", "cement", "textiles", "Aspirin", "solar panels", "fertilizers"

        - Industry or Specific Sub-Sectors: Names of industries or their sectors.
        Examples: "automobile", "chemical", "food processing", "IT sector", "agriculture", "textile industry"

        - Common Construction or Setup Terms: Words related to setting up a facility.
        Examples: "factory", "industry", "building", "setup", "establish", "construct", "infrastructure"

        - Module Names: The following module names and their variations must be excluded from keywords:
        {modules_text}

        Important Extraction Rules

        1. STRICT FOCUS ON FIELDS:
        Extract any word from the user's query that matches the FOCUS FIELDS.
        Even if the query is ambiguous, complex, or incomplete, if a word relates to a field meaning, it must be extracted.

        2. IGNORE SENTENCE STRUCTURE COMPLETELY:
        Keywords must be extracted regardless of how the sentence is structured.
        Even if the user uses vague or informal language, focus only on extracting words relevant to the fields.
        Example 1: "plastic factory in Bombay" → ["Bombay"] (Because "plastic" and "factory" are restricted)
        Example 2: "Wanna build car industry in Siem Reap" → ["Vadoadara"] (Because "car" and "industry" are restricted)

        3. Numbers Must Be Extracted If They Are Relevant:
        If a number is part of a certification or standard (like "ISO 9001", "CE 22000"), it must be included as a keyword.
        Example: "We need ISO 14001 certification" → ["ISO", "14001", "certification"]
        Example: "I want information about CE 22000" → ["CE", "22000"]

        4. Correct Misspelled Words Before Extracting Them:
        If a word is misspelled, return its corrected form.
        Example: "incentve for power" → ["incentive", "power"]
        Example: "subsidyy information" → ["subsidy", "information"]

        5. Never Extract Restricted or Module Terms:
        Words from RESTRICTED CATEGORIES or Module Names must never be included in the keywords.

        Output Format
        - The response must be a JSON object in the exact format below.
        - If no valid keywords are found, return {{ "KEYWORDS": null }} or {{ "KEYWORDS": None }}.
        - No explanations, no extra text—only the JSON object.

        User Query:
        {user_query}

        Final Output (JSON only):
        {{
        "KEYWORDS": ["word1", "word2"]  # or null if none
        }}
        """.strip()
        
    elif current_module == "Query to search Vendors":
        prompt_template_str = """
        You are an expert at extracting single-word keywords from a user query.

        1) FOCUS FIELDS (To Be Extracted as Keywords)
        These are the fields that you must focus on while extracting keywords. If the user's query contains any word that logically matches the meaning of these fields, it must be extracted as a keyword.

        {fields_explained}

        2) RESTRICTED CATEGORIES (Never to Be Extracted)
        Words from the following restricted categories must NEVER be extracted as keywords because they disrupt the flow.

        - Capacity Units: Measurement units related to capacity, power, or weight.
        Examples: "MW", "KW", "ton", "kg/day", "liters", "m³", "barrels", "cubic feet", "TPA"

        - Time Periods: Words referring to time durations or periods.
        Examples: "year", "month", "day", "hour", "weekly", "annually", "quarterly", "biweekly"

        - Product Names: Specific products being manufactured or sold.
        Examples: "car", "plastic", "steel", "cement", "textiles", "solar panels", "fertilizers"

        - Industry or Specific Sub-Sectors: Names of industries or their sectors.
        Examples: "automobile", "chemical", "food processing", "IT sector", "agriculture", "textile industry"

        - Specific Supplies: Raw materials or machinery used for industrial production.
        Examples: "raw material", "machinery", "tools", "equipment", "spare parts", "components"

        - Vendor-Related Terms: Words related to vendors or suppliers.
        Examples: "vendor", "vendors", "supplier", "suppliers"

        - Locations: Specific areas, cities, states, or countries.
        Examples: "Siem Reap", "Sihanoukville", "Battambang", "Cambodia", "Kampong Cham", "USA", "industrial zone"

        - Module Names: The following module names and their variations must be excluded from keywords:
        {modules_text}

        If any word in the query belongs to these categories, do not include them in the extracted keywords.

        Important Extraction Rules

        1. STRICT FOCUS ON FIELDS:
        Extract any word from the user's query that matches the FOCUS FIELDS.
        Even if the query is ambiguous, complex, incomplete, or vague, if a word relates to a field meaning, it must be extracted.

        2. IGNORE SENTENCE STRUCTURE COMPLETELY:
        Keywords must be extracted regardless of how the sentence is structured.
        Even if the user uses vague, incomplete, or informal language, focus only on extracting words relevant to the fields.

        Example 1: "I want to find ISO 9000 certified suppliers in Sihanoukville" → ["ISO", "9000"]
        Example 2: "Search for certified equipment providers" → ["certified"]
        Example 3: "Looking for reliable vendors in Cambodia for machinery" → null (Because "vendors", "Cambodia", and "machinery" are restricted)
        Example 4: "Find suppliers for high-quality components" → null (Because "suppliers" and "components" are restricted)
        Example 5: "List of companies with ISO certification" → ["ISO", "certification"]

        3. Numbers Must Be Extracted If They Are Relevant:
        If a number is part of a certification or standard (like "ISO 9001", "CE 22000"), it must be included as a keyword.
        Example: "We need ISO 14001 certified vendors" → ["ISO", "14001"]
        Example: "Looking for suppliers with CE 22000 certification" → ["CE", "22000"]

        4. Correct Misspelled Words Before Extracting Them:
        If a word is misspelled, return its corrected form.
        Example: "certfied suppliers for equipment" → ["certified"]
        Example: "want to find machnery providers" → null (Because "machinery" is restricted)

        5. Never Extract Restricted or Module Terms:
        Words from RESTRICTED CATEGORIES or Module Names must never be included in the keywords.

        Output Format
        - The response must be a JSON object in the exact format below.
        - If no valid keywords are found, return {{ "KEYWORDS": null }} or {{ "KEYWORDS": None }}.
        - No explanations, no extra text—only the JSON object.

        User Query:
        {user_query}

        Final Output (JSON only):
        {{
        "KEYWORDS": ["word1", "word2"]  # or null if none
        }}
        """.strip()

    elif current_module == "Query to search Incentives":
        prompt_template_str = """
        You are an expert at extracting single-word keywords from a user query.

        1) FOCUS FIELDS (To Be Extracted as Keywords)
        These are the fields that you must focus on while extracting keywords. If the user's query contains any word that logically matches the meaning of these fields, it must be extracted as a keyword.

        {fields_explained}

        2) RESTRICTED CATEGORIES (Never to Be Extracted)
        Words from the following restricted categories must NEVER be extracted as keywords because they disrupt the flow.

        - Capacity Units: Measurement units related to capacity, power, or weight.
        Examples: "MW", "KW", "ton", "kg/day", "liters", "m³", "barrels", "cubic feet", "TPA"

        - Time Periods: Words referring to time durations or periods.
        Examples: "year", "month", "day", "hour", "weekly", "annually", "quarterly", "biweekly"

        - Product Names: Specific products being manufactured or sold.
        Examples: "car", "plastic", "steel", "cement", "textiles", "solar panels", "fertilizers"

        - Industry or Specific Sub-Sectors: Names of industries or their sectors.
        Examples: "automobile", "chemical", "food processing", "IT sector", "agriculture", "textile industry"

        - Locations: Specific areas, cities, states, or countries.
        Examples: "Siem Reap", "Sihanoukville", "Battambang", "Cambodia", "Kampong Cham", "USA", "industrial zone"

        - Module Names: The following module names and their variations must be excluded from keywords:
        {modules_text}

        3) Supreme Extraction Rule (Overrides All Other Restrictions)

        - If a word is mentioned with context descriptors such as "regarding," "related to," "about," or "in context of," it must always be extracted, even if it falls under restricted categories.
        - This ensures that key incentive-related terms are never missed, even if they belong to restricted categories.

        Examples:
        - "Incentives regarding rehabilitation scheme for factories" → ["rehabilitation"]
        - "I need incentives related to water usage in industries" → ["water"]
        - "I am searching for schemes about power conservation" → ["power", "conservation"]
        - "Incentives regarding support for disaster recovery" → ["recovery"]
        - "Looking for incentives regarding product development" → ["development"]

        4) POWER, WATER, AND REHABILITATION-SPECIFIC RULES:
        1. If "power," "water," or "rehabilitation" are mentioned in any incentive-related context, they must always be extracted.
        2. If context is unclear, always extract these terms.
        3. If they clearly relate to restricted industries, they should be excluded.

        5) STRICT FOCUS ON FIELDS:
        Extract any word from the user's query that matches the FOCUS FIELDS.
        Even if the query is ambiguous, complex, incomplete, or vague, if a word relates to a field meaning, it must be extracted.

        6) IGNORE SENTENCE STRUCTURE COMPLETELY:
        Keywords must be extracted regardless of how the sentence is structured.

        Examples:
        - "I am looking for water-related incentives for milk processing." → ["water"]
        - "Incentives regarding rehabilitation scheme for industries." → ["rehabilitation"]
        - "Subsidies for water infrastructure." → ["water", "infrastructure"]
        - "Rehabilitation support in disaster-affected areas." → ["rehabilitation"]
        - "Development incentives for rural areas." → ["development"]
        - "ISO 9001 certification subsidies." → ["ISO", "9001"]

        7) NUMBERS MUST BE EXTRACTED IF THEY ARE RELEVANT:
        If a number is part of a certification or standard, it must be included as a keyword.
        - Example: "We need ISO 14001 certification for subsidy eligibility." → ["ISO", "14001"]  
        - Example: "I want information about CE 22000." → ["CE", "22000"]

        8) CORRECT MISSPELLED WORDS BEFORE EXTRACTING THEM:
        Example: "rehabilitaton subsidy related info" → ["rehabilitation"]

        9) NEVER EXTRACT RESTRICTED OR MODULE TERMS UNLESS THE SUPREME RULE APPLIES.

        Output Format:
        - The response must be a JSON object in the exact format below.
        - If no valid keywords are found, return {{ "KEYWORDS": null }} or {{ "KEYWORDS": None }}.
        - No explanations, no extra text—only the JSON object.

        User Query:
        {user_query}

        Final Output (JSON only):
        {{
        "KEYWORDS": ["word1", "word2"]  # or null if none
        }}
        """.strip()




    elif current_module == "Query to Get Approvals":
        prompt_template_str = """
        You are an expert at extracting single-word keywords from a user query.

        1) FOCUS FIELDS (To Be Extracted as Keywords)
        These are the fields that you must focus on while extracting keywords. If the user's query contains any word that logically matches the meaning of these fields, it must be extracted as a keyword.

        {fields_explained}

        - For the "Government Department" field, always extract any specific department name mentioned in the query.  
        Examples include: "Revenue Department", "Pollution Control Board", "Fire Department", "Urban Development Authority", "Environment Ministry", etc.

        2) RESTRICTED CATEGORIES (Never to Be Extracted)
        Words from the following restricted categories must NEVER be extracted as keywords because they disrupt the flow.

        - Capacity Units: Measurement units related to capacity, power, or weight.
        Examples: "MW", "KW", "ton", "kg/day", "liters", "m³", "barrels", "cubic feet", "TPA"

        - Time Periods: Words referring to time durations or periods.
        Examples: "year", "month", "day", "hour", "weekly", "annually", "quarterly", "biweekly"

        - Product Names: Specific products being manufactured or sold.
        Examples: "car", "plastic", "steel", "cement", "textiles", "solar panels", "fertilizers"

        - Industry or Specific Sub-Sectors: Names of industries or their sectors.
        Examples: "automobile", "chemical", "food processing", "IT sector", "agriculture", "textile industry"

        - Locations: Specific areas, cities, states, or countries.
        Examples: "Siem Reap", "Sihanoukville", "Battambang", "Cambodia", "Kampong Cham", "USA", "industrial zone"

        - Approval-Related Terms: Generic approval-related words that must be excluded.
        Examples: "approval", "approvals", "license", "licenses", "clearance", "permission"

        - Module Names: The following module names and their variations must be excluded from keywords:
        {modules_text}

        If any word in the query belongs to these categories, do not include them in the extracted keywords.

        3) Important Extraction Rules

        - STRICT EXTRACTION OF FOCUS FIELDS:
        Always extract any word from the user's query that logically matches the FOCUS FIELDS.  
        If there is any doubt whether a word belongs to the focus fields or restricted categories, always extract it as a keyword.

        - IGNORE SENTENCE STRUCTURE COMPLETELY:
        Keywords must be extracted regardless of how the sentence is structured.  
        Even if the user uses vague, incomplete, or informal language, focus only on extracting words relevant to the fields.

        Example 1: "Need fire NOC in Cambodia for my factory" → ["fire", "NOC"]  
        Example 2: "Apply for environmental clearance online" → ["environmental", "online"]  
        Example 3: "Setup approval for plastic factory in Battambang" → null (Because "approval", "plastic", and "Battambang" are restricted)  
        Example 4: "I want to find all the approvals required from the revenue department for cement in Siem Reap." → ["revenue", "department"]  
        Example 5: "List approvals needed from fire department" → ["fire", "department"]

        - Numbers Must Be Extracted If They Are Relevant:
        - If a number is part of a certification or standard (like "ISO 9001", "CE 22000"), it must be included as a keyword.
        - Example: "ISO 14001 clearance" → ["ISO", "14001"]  
        - Example: "CE 22000 application" → ["CE", "22000"]

        - Correct Misspelled Words Before Extracting Them:
        - If a word is misspelled, return its corrected form.
        - Example: "envrnmntal clearance for fire safty" → ["environmental", "fire", "safety"]  
        - Example: "lnsurance approval for factory" → ["insurance"]

        - Never Extract Restricted or Module Terms:
        - If a term clearly belongs to a restricted category, it must never be included.

        4) Output Format:
        - The response must be a JSON object in the exact format below.
        - If no valid keywords are found, return {{ "KEYWORDS": null }} or {{ "KEYWORDS": None }}.
        - No explanations, no extra text—only the JSON object.

        User Query:
        {user_query}

        Final Output (JSON only):
        {{
        "KEYWORDS": ["word1", "word2"]  # or null if none
        }}
        """.strip()


    else:
        prompt_template_str = """
        You are an expert at extracting single-word keywords from a user query.

        1) FOCUS FIELDS (To Be Extracted as Keywords)
        These are the fields that you must focus on while extracting keywords. If the user's query contains any word that logically matches the meaning of these fields, it must be extracted as a keyword.

        {fields_explained}

        2) RESTRICTED CATEGORIES (Never to Be Extracted)
        Words from the following restricted categories must NEVER be extracted as keywords because they disrupt the flow.

        - Capacity Units: Measurement units related to capacity, power, or weight.
        Examples: "MW", "KW", "ton", "kg/day", "liters", "m³", "barrels", "cubic feet", "TPA"

        - Time Periods: Words referring to time durations or periods.
        Examples: "year", "month", "day", "hour", "weekly", "annually", "quarterly", "biweekly"

        - Product Names: Specific products being manufactured or sold.
        Examples: "car", "plastic", "steel", "cement", "textiles", "Aspirin", "solar panels", "fertilizers"

        - Industry or Specific Sub-Sectors: Names of industries or their sectors.
        Examples: "automobile", "chemical", "food processing", "IT sector", "agriculture", "textile industry"

        - Locations: Words that indicate specific areas, cities, states, or countries.
        Examples: "Siem Reap", "Sihanoukville", "Battambang", "Cambodia", "Kampong Cham", "USA", "industrial zone"

        - Common Construction or Setup Terms: Words related to setting up, approvals, incentives, supplies, or vendor processes.
        Examples: "factory", "industry", "building", "setup", "establish", "construct", "infrastructure", 
        "approval", "approvals", "incentive", "incentives", "supply", "supplies", "raw material", "vendor", "vendors"

        - Module Names: The following module names and their variations must be excluded from keywords:
        {modules_text}

        If any word in the query belongs to these categories, do not include them in the extracted keywords.

        Important Extraction Rules

        1. STRICT FOCUS ON FIELDS:
        Extract any word from the user's query that matches the FOCUS FIELDS.
        Even if the query is ambiguous, complex, incomplete, or vague, if a word relates to a field meaning, it must be extracted.

        2. IGNORE SENTENCE STRUCTURE COMPLETELY:
        Keywords must be extracted regardless of how the sentence is structured.
        Even if the user uses vague, incomplete, or informal language, focus only on extracting words relevant to the fields.
        Example 1: "I want to find ISO 9000 certified steel suppliers in Bombay" → ["ISO", "9000"]
        Example 2: "Find subsidies power Cambodia" → ["power"]
        Example 3: "Wanna build car industry in Siem Reap" → null (Because "car", "Siem Reap" and "industry" are restricted)

        3. Numbers Must Be Extracted If They Are Relevant:
        If a number is part of a certification or standard (like "ISO 9001", "CE 22000"), it must be included as a keyword.
        Example: "We need ISO 14001 certification" → ["ISO", "14001"]
        Example: "I want information about CE 22000" → ["CE", "22000"]

        4. Correct Misspelled Words Before Extracting Them:
        If a word is misspelled, return its corrected form.
        Example: "incentve for powr" → ["power"]
        Example: "want to find invesmetn subsidy related approvals" → ["investment", "subsidy"]

        5. Never Extract Restricted or Module Terms:
        Words from RESTRICTED CATEGORIES or Module Names must never be included in the keywords.

        Output Format
        - The response must be a JSON object in the exact format below.
        - If no valid keywords are found, return {{ "KEYWORDS": null }} or {{ "KEYWORDS": None }}.
        - No explanations, no extra text—only the JSON object.

        User Query:
        {user_query}

        Final Output (JSON only):
        {{
        "KEYWORDS": ["word1", "word2"]  # or null if none
        }}
        """.strip()


    # Create the PromptTemplate and run the LLM
    prompt = PromptTemplate(
        input_variables=["fields_explained", "modules_text", "user_query"],
        template=prompt_template_str
    )
    chain = prompt | llm
    response = chain.invoke({
        "fields_explained": fields_explained,
        "modules_text": modules_text,
        "user_query": user_input
    })

    raw_output = response.content.strip()
    data = extract_json_from_llm_response(raw_output, "KEYWORDS")
    keywords = data.get("KEYWORDS", None)

    # Cleanup newly extracted keywords
    cleaned = []
    if isinstance(keywords, list):
        for kw in keywords:
            for token in kw.split():
                token_stripped = token.strip()
                if token_stripped and token_stripped.lower() not in module_words:
                    cleaned.append(token_stripped)

    # Merge with existing keywords
    final_keywords = []
    seen = set()

    # Add existing keywords first if they exist
    if existing_keywords:
        for kw in existing_keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                final_keywords.append(kw)

    # Add newly cleaned keywords, ensuring no duplicates
    for kw in cleaned:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            final_keywords.append(kw)

    # Determine final return value
    return {"KEYWORDS": final_keywords if final_keywords else None}

# General exclusion terms
EXCLUSION_TERMS = [
    "incentive", "subsidy", "approval", "supplier", "vendor",
    "suppliers", "vendors", "approvals"
]

# Quantity, Units, and Time Periods (for Scratch module only)
QUANTITY_TERMS = [
    "quantity", "amount", "number", "total", "count", "volume", "mass", "capacity"
]
QUANTITY_UNITS = [
    "kg", "kilogram", "ton", "litre", "liter", "meter", "m", "cm", "cubic",
    "grams", "lbs", "pounds", "barrels", "tpa"
]
TIME_PERIOD_TERMS = [
    "year", "month", "day", "hour", "weekly", "annually", "quarterly", "biweekly"
]

# Entity exclusions based on module
MODULE_ENTITY_EXCLUSIONS = {
    "Query to search Incentives": {"GPE", "LOC"},
    "Query to Get Approvals": {"GPE", "LOC"},
    "Query to search Vendors": {"GPE", "LOC"},
    "Query to build industry from Scratch": {"QUANTITY", "CARDINAL", "ORDINAL", "DATE", "TIME", "PERCENT", "MONEY"}
}

# Convert exclusion terms to SpaCy Doc objects for similarity comparison
def get_exclusion_docs(module: str):
    """Get exclusion terms as SpaCy Doc objects based on the module."""
    if module == "Query to build industry from Scratch":
        terms = EXCLUSION_TERMS + QUANTITY_TERMS + QUANTITY_UNITS + TIME_PERIOD_TERMS
    else:
        terms = EXCLUSION_TERMS
    return [nlp(term) for term in terms]

def is_similar_to_exclusion(word: str, exclusion_docs) -> bool:
    """Check if the word is semantically similar to any exclusion term."""
    word_doc = nlp(word)
    return any(word_doc.similarity(ex_doc) > 0.7 for ex_doc in exclusion_docs)

def get_entity_label(word: str, doc) -> str:
    """Get the entity label for a given word from the SpaCy doc."""
    for ent in doc.ents:
        if word in ent.text.lower():
            return ent.label_
    return ""

def extract_important_words(text: str, module: str = "") -> List[str]:
    """Extract important words based on module-specific rules."""
    
    doc = nlp(text)
    exclusion_docs = get_exclusion_docs(module)

    # Step 1: Extract noun chunks and named entities
    noun_chunks = {chunk.text.strip().lower() for chunk in doc.noun_chunks}
    named_entities = {
        ent.text.strip().lower() for ent in doc.ents
        if ent.label_ not in MODULE_ENTITY_EXCLUSIONS.get(module, set())
    }

    # Step 2: Extract proper nouns and common nouns
    important_pos = {token.text.strip().lower() for token in doc if token.pos_ in {"NOUN", "PROPN"}}

    # Step 3: Combine terms and prioritize longer phrases
    combined_terms = noun_chunks.union(named_entities)

    final_terms = set()
    for term in combined_terms:
        if not any(term != existing and term in existing for existing in combined_terms):
            final_terms.add(term)

    # Include single important words if not already in longer terms
    final_terms.update({
        word for word in important_pos
        if not any(word in phrase for phrase in final_terms)
    })

    # Step 4: Final Filtering
    filtered_terms = [
        word for word in final_terms
        if not is_similar_to_exclusion(word, exclusion_docs)
        and not nlp.vocab[word].is_stop
        and get_entity_label(word, doc) not in MODULE_ENTITY_EXCLUSIONS.get(module, set())
    ]

    return list(set(filtered_terms))


def extract_main_industry_and_product_universal(user_query: str, main_industries: List[str], llm) -> Dict[str, str]:
    """
    Extract the Main-Industry and Product mentioned in the user query.

    Parameters:
        user_query (str): The user-provided query.
        main_industries (List[str]): List of all available main industries.
        llm: The language model instance to use for processing.

    Returns:
        Dict[str, str]: A dictionary containing the extracted Main-Industry and Product.
    """
    # Convert the list into a formatted string for the prompt
    main_industries_str = ", ".join([f'"{m}"' for m in main_industries])

    # Define the universal prompt
    prompt_template = """
You are an expert in analyzing industry-related queries and extracting specific details.

**CRITICAL INSTRUCTION: When determining Main-Industry classification, focus ONLY on the product, service, or industry terms mentioned in the query. Completely ignore geographic locations (cities, states, countries) for industry inference. Location information should not influence industry selection in any way.**

Based on the user's query, identify the following details:

1. Main-Industry: Infer or predict the main industry based on the context of the query.  
    - Users may phrase their queries in different ways, such as:
        - "What incentives are available for the automobile sector?"
        - "Which approvals are needed for the pharmaceutical industry?"
        - "I am looking for steel vendors."
    - In all such cases, identify the relevant industry even if the query is vague or incomplete.  
    - **Focus exclusively on product/service/industry keywords - NOT on location.**
    - If the inferred main industry can logically match any category from the provided list of Main-Industries, return the matched category from the list and set `"Forced-Mapping": "No"`.  
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred main industry to the closest match from the provided list and set `"Forced-Mapping": "Yes"`.  
    - If no main industry can be inferred from the query, return `"None"` for both `"Original-Inferred-Main-Industry"` and `"Main-Industry"`.   

2. Product (if applicable): Identify the specific product mentioned in the query (e.g., "Cement," "Steel Rods").  
    - Always extract the widely recognized industry-standard name for the product.  
    - If the product is given as an abbreviation, acronym, or chemical formula, return the full name instead.  
    - Example:
        - "NaCl" → "Sodium Chloride"
        - "PVC" → "Polyvinyl Chloride"
        - "PET" → "Polyethylene Terephthalate"
        - "H₂SO₄" → "Sulfuric Acid"  
    - If a product has multiple common names, choose the most widely used commercial name.  
    - Example:
        - "Isopropanol" → "Isopropyl Alcohol"
        - "Ethene" → "Ethylene"
        - "Acetic Acid" → "Vinegar" (if referring to food-grade usage)
    - If the inferred term logically represents a product, include it in the output.  
    - If no product is mentioned or it does not logically fit as a product, return `"None"`.

**Product-to-Industry Mapping Rules (Location-Independent):**
- Chalk/Calcium Carbonate → "Mining" (manufacturing/processing)
- Steel/Iron → "Capital Goods" 
- Pharmaceuticals/Medicines → "Healthcare & Pharmaceuticals"
- Cement/Concrete → "Cement"
- Food items → "Foods and Beverages"

Logical Matching for Main Industries:
    - A logical match occurs when the inferred main industry and an available main industry from the list are conceptually or functionally similar.  
    - Examples of logical matches:  
        - Inferred: "Chemical Processing" → Available: "Chemical" (`Forced-Mapping`: "No`).  
        - Inferred: "Electronics Production" → Available: "Capital Goods" (`Forced-Mapping`: "No`).  
    - Examples of forced mappings:  
        - Inferred: "Nanotechnology Development" → Available: "Chemical" (`Forced-Mapping`: "Yes`).  
        - Inferred: "Eco-friendly Energy Solutions" → Available: "Energy" (`Forced-Mapping`: "Yes`).  

Provided List of Main-Industries:  
{main_industries}  

Important Notes:
    - Always assume that the query is related to an industry-specific inquiry, whether it is about incentives, approvals, or vendors.
    - Ensure that the output is strictly limited to the required JSON format and contains no explanations, reasoning, or comments.  
    - Do not provide additional text, explanations, or reasoning within the fields of the JSON object.  
    - Each field in the JSON must only contain the exact extracted information or the specified fallback values (e.g., "None").  
    - If the query mentions only a location but no specific industry or product context, do not infer the industry from prior knowledge of the location. Instead, return None.

Output Format:
Output the result strictly as a JSON object in the following format:  
{{
    "Main-Industry": <Mapped Main-Industry>,
    "Original-Inferred-Main-Industry": <Inferred Main-Industry or 'None'>,
    "Forced-Mapping": <'Yes' or 'No'>,
    "Product": <Extracted Product or 'None'>
}}

Query: {query}  

Provide only the JSON object in the required format.  
    """
    
    # Create the prompt using the provided variables
    prompt = PromptTemplate(
        input_variables=["query", "main_industries"],
        template=prompt_template
    )
    
    # Create the LLM chain
    chain = prompt | llm
    
    # Invoke the LLM
    result = chain.invoke({
        "query": user_query,
        "main_industries": main_industries_str,
    })
    update_llm_token(result)
    # Extract JSON response
    result_content = result.content.strip()

    # Define regex patterns for Main-Industry and Product
    main_industry_pattern = r'"Main-Industry":\s*"([^"]+)"'
    original_inferred_main_industry_pattern = r'"Original-Inferred-Main-Industry":\s*"([^"]+)"'
    forced_mapping_pattern = r'"Forced-Mapping":\s*"([^"]+)"'
    product_pattern = r'"Product":\s*"([^"]+)"'

    # Extract details using regex
    main_industry_match = re.search(main_industry_pattern, result_content)
    original_inferred_main_industry_match = re.search(original_inferred_main_industry_pattern, result_content)
    forced_mapping_match = re.search(forced_mapping_pattern, result_content)
    product_match = re.search(product_pattern, result_content)

    # Extract values or default to "None"
    main_industry = main_industry_match.group(1).strip() if main_industry_match else "None"
    original_inferred_main_industry = original_inferred_main_industry_match.group(1).strip() if original_inferred_main_industry_match else "None"
    forced_mapping = forced_mapping_match.group(1).strip() if forced_mapping_match else "No"
    product = product_match.group(1).strip() if product_match else "None"

    extracted_data = {
        "Main-Industry": main_industry,
        "Original-Inferred-Main-Industry": original_inferred_main_industry,
        "Forced-Mapping": forced_mapping,
        "Product": product
    }

    # Validate against the provided list of Segments
    validated_data = copy.deepcopy(extracted_data)
    if main_industry not in main_industries and main_industry != "None":
        validated_data["Main-Industry"] = "Not Available in List"

    return extracted_data, validated_data

def extract_sub_sector_and_product_universal(
    user_query: str,
    sub_sectors: List[str],
    llm,
    main_industry: str = None,
    product: str = None
) -> Dict[str, str]:
    """
    Extract the Sub-Sector and Product mentioned in the user query, optionally using inferred Main-Industry and Product.

    Parameters:
        user_query (str): The user-provided query.
        sub_sectors (List[str]): List of all available sub-sectors.
        llm: The language model instance to use for processing.
        main_industry (str): Inferred Main-Industry to provide additional context (default: None).
        product (str): Inferred Product to provide additional context (default: None).

    Returns:
        Dict[str, str]: A dictionary containing the extracted Sub-Sector, Original-Inferred Sub-Sector,
                        Forced-Mapping, and Product.
    """    

    # Convert the list into a formatted string for the prompt
    sub_sectors_str = ", ".join([f'"{s}"' for s in sub_sectors])

    # Define additional context for Main-Industry and Product if available
    context_lines = []
    if main_industry and main_industry not in ["None", "Not Available in List"]:
        context_lines.append(f"Inferred Main-Industry: {main_industry}")
    if product and product != "None":
        context_lines.append(f"Inferred Product: {product}")
    context = "\n".join(context_lines)

    # Define the universal prompt
    prompt_template = """
You are an expert in analyzing industry-related queries and extracting specific details.  

**CRITICAL INSTRUCTION: When determining Sub-Sector classification, focus ONLY on the product, service, or industry terms mentioned in the query. Completely ignore geographic locations (cities, states, countries) for sub-sector inference. Location information should not influence sub-sector selection in any way.**

Sub-Sector is the functional or operational category that immediately follows the Main-Industry in the hierarchy.  
It encompasses broader categories of related activities, processes, or areas of focus that form part of the Main-Industry.  

{context}

**MANDATORY CONSTRAINT: You MUST select the Sub-Sector value ONLY from the provided list below. You cannot create or invent sub-sector names that are not in this exact list.**

Provided List of Sub-Sectors (THESE ARE YOUR ONLY OPTIONS):  
{sub_sectors_str}  

Based on the user's query, identify the following details:

1. Sub-Sector Extraction:  
    - **Focus exclusively on product/service/industry keywords - NOT on location.**
    - First, infer what sub-sector the query relates to based on the product/industry mentioned
    - Then, find the CLOSEST MATCH from the provided list above
    - **STEP-BY-STEP PROCESS:**
        a) Identify what industry segment the query refers to (e.g., "chalk" → "basic chemicals/mineral processing")
        b) Check if this exactly matches any item in the provided list 
        c) If YES: Use that exact match and set `"Forced-Mapping": "No"`
        d) If NO: Find the closest related option from the provided list and set `"Forced-Mapping": "Yes"`
    
    **For Chemical Industry Products - Mapping Priority:**
    - Chalk/Calcium Carbonate → **"Paint, Coatings & Inks"** (chalk used as filler in paints)
    - Pharmaceuticals/APIs → **"Pharma and Biotechnology Chemical"**
    - Fertilizers → **"Agrochemical"**
    - Plastics/Polymers → **"Polymers and Plastics"**
    - Adhesive products → **"Adhesives"**
    - Gas products → **"Industrial Gases"**
    - Oil/petroleum products → **"Petrochemical"**

2. Product Extraction (if applicable):  
    - Always extract the widely recognized industry-standard name for the product.
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.

**VALIDATION RULES:**
- Your "Sub-Sector" field MUST contain EXACTLY one of these values: {sub_sectors_str} OR "None"
- If you cannot find any reasonable connection to the provided sub-sectors, only then return "None"
- If the "Sub-Sector" matches exactly what you inferred, set `"Forced-Mapping": "No"`
- If the "Sub-Sector" is different from what you initially inferred, set `"Forced-Mapping": "Yes"`

**Examples:**
- Query: "chalk industry approvals" 
  - Inferred: "Basic Chemicals" 
  - Closest Available: "Paint, Coatings & Inks" (chalk used in paints)
  - Output: `"Sub-Sector": "Paint, Coatings & Inks", "Original-Inferred-Sub-Sector": "Basic Chemicals", "Forced-Mapping": "Yes"`

Output Constraints:  
- The "Sub-Sector" field can ONLY contain values from the provided list or "None"
- Do not create new sub-sector names
- Strictly limit the output to the required JSON format with no explanations

Output Format:  
{{
    "Sub-Sector": <MUST be from provided list or "None">,
    "Original-Inferred-Sub-Sector": <What you initially inferred or "None">,
    "Forced-Mapping": <"Yes" if Sub-Sector differs from Original-Inferred, "No" if exact match>,
    "Product": <Extracted Product or "None">
}}

Query: {user_query}  

Provide only the JSON object in the required format.  
"""
    # Create the prompt using the provided variables
    prompt = PromptTemplate(
        input_variables=["user_query", "sub_sectors_str", "context"],
        template=prompt_template
    )
    
    # Create the LLM chain
    chain = prompt | llm
    
    # Invoke the LLM
    result = chain.invoke({
        "user_query": user_query,
        "sub_sectors_str": sub_sectors_str,
        "context": context
    })
    update_llm_token(result)
    
    # Extract JSON response
    result_content = result.content.strip()

    # Define regex patterns for Sub-Sector and Product
    sub_sector_pattern = r'"Sub-Sector":\s*"([^"]+)"'
    original_inferred_sub_sector_pattern = r'"Original-Inferred-Sub-Sector":\s*"([^"]+)"'
    forced_mapping_pattern = r'"Forced-Mapping":\s*"([^"]+)"'
    product_pattern = r'"Product":\s*"([^"]+)"'

    # Extract details using regex
    sub_sector_match = re.search(sub_sector_pattern, result_content)
    original_inferred_sub_sector_match = re.search(original_inferred_sub_sector_pattern, result_content)
    forced_mapping_match = re.search(forced_mapping_pattern, result_content)
    product_match = re.search(product_pattern, result_content)

    # Extract values or default to "None"
    sub_sector = sub_sector_match.group(1).strip() if sub_sector_match else "None"
    original_inferred_sub_sector = original_inferred_sub_sector_match.group(1).strip() if original_inferred_sub_sector_match else "None"
    forced_mapping = forced_mapping_match.group(1).strip() if forced_mapping_match else "No"
    product = product_match.group(1).strip() if product_match else "None"

    extracted_data = {
        "Sub-Sector": sub_sector,
        "Original-Inferred-Sub-Sector": original_inferred_sub_sector,
        "Forced-Mapping": forced_mapping,
        "Product": product
    }

    # Validate against the provided list of Segments
    validated_data = copy.deepcopy(extracted_data)
    if sub_sector not in sub_sectors and sub_sector != "None":
        validated_data["Sub-Sector"] = "Not Available in List"

    return extracted_data, validated_data

def extract_segment_and_product_universal(
    user_query: str,
    segments: List[str],
    llm,
    main_industry: str = None,
    sub_sector: str = None,
    product: str = None
) -> Dict[str, Dict[str, str]]:
    """
    Extract the Segment and Product mentioned in the user query, optionally using inferred Main-Industry and Sub-Sector.

    Parameters:
        user_query (str): The user-provided query.
        segments (List[str]): List of all available segments.
        llm: The language model instance to use for processing.
        main_industry (str): Inferred Main-Industry to provide additional context (default: None).
        sub_sector (str): Inferred Sub-Sector to provide additional context (default: None).
    Returns:
        Dict[str, Dict[str, str]]: A dictionary containing the extracted and validated Segment, Original-Inferred-Segment, Forced-Mapping, and Product.
    """
    # Convert the list into a formatted string for the prompt
    segments_str = ", ".join([f'"{s}"' for s in segments])

    # Define additional context for Main-Industry and Sub-Sector if available
    context_lines = []
    if main_industry and main_industry not in ["None", "Not Available in List"]:
        context_lines.append(f"Inferred Main-Industry: {main_industry}")
    if sub_sector and sub_sector not in ["None", "Not Available in List"]:
        context_lines.append(f"Inferred Sub-Sector: {sub_sector}")
    if product and product != "None":
        context_lines.append(f"Inferred Product: {product}")
    context = "\n".join(context_lines)

    # Define the prompt
    prompt_template = """
You are an expert in analyzing industry-related queries and extracting specific details.

**CRITICAL INSTRUCTION: When determining Segment classification, focus ONLY on the product, service, or industry terms mentioned in the query. Completely ignore geographic locations (cities, states, countries) for segment inference. Location information should not influence segment selection in any way.**

A Segment is a logical grouping of products or services that come immediately next in the hierarchy after the Sub-Sector.
The Sub-Sector itself is a functional or operational category following the Main-Industry in the hierarchy.

For example:
- In the "Automobile" industry, a Sub-Sector like "Automotive Components" may have Segments such as "Engines," "Batteries," or "Tires."
- In the "Pharmaceuticals" industry, a Sub-Sector like "Allopathic Medicines" may have Segments such as "Antibiotics" or "Analgesics."
- In the "Textile" industry, a Sub-Sector like "Fabric Production" may have Segments such as "Cotton Weaving" or "Synthetic Fiber Manufacturing."

{context}

**MANDATORY CONSTRAINT: You MUST select the Segment value ONLY from the provided list below. You cannot create or invent segment names that are not in this exact list.**

Provided List of Segments (THESE ARE YOUR ONLY OPTIONS):  
{segments_str}  

**Product-to-Segment Mapping Rules (Location-Independent):**
Based on your Sub-Sector context:
- If Sub-Sector is Chemical-related → Look for chemical product categories, processing types, or application segments
- If Sub-Sector is Manufacturing-related → Look for product categories, equipment types, or process segments
- If Sub-Sector is Service-related → Look for service categories, business functions, or client segments

Based on the user's query, identify the following details:

1. Segment: First, infer or predict the segment based on the context of the query.
    - **Focus exclusively on product/service/industry keywords - NOT on location.**
    - In most cases, users may not explicitly mention "business activity" or "sector-specific terms," but they are referring to industry-related segments. Assume the query relates to an industry segment unless it is clearly illogical to do so.
    - The query may sometimes be vague or incomplete. In such cases, analyze the implied intent and context to infer the appropriate segment.
    
    **STEP-BY-STEP PROCESS:**
    a) Identify what specific product/service/business activity the query refers to
    b) Check if this exactly matches any item in the provided list above
    c) If YES: Use that exact match and set `"Forced-Mapping": "No"`
    d) If NO: Find the closest related option from the provided list and set `"Forced-Mapping": "Yes"`
    
    - If the inferred segment can logically match any category from the provided list of Segments, return the matched category from the list and set `"Forced-Mapping"` to `"No"`.
    - If no exact logical match exists, identify the CLOSEST available segment based on:
        * Product category similarity
        * Business function overlap
        * Industry application area
        * Service type alignment
        * End-use market segment
    - **MANDATORY: Always attempt a forced mapping before returning "None"**
    - **Only return "None" if the query contains absolutely no industry/product/service context whatsoever**

2. Product: If the product context is provided, return the same product in the output JSON as it is in the context.  
    - **Focus exclusively on product terms - NOT on location.**
    - Identify the specific product or service the query refers to (e.g., "Cement," "Steel Rods," "Industrial Equipment").  
    - If the inferred term logically represents a product or service, include it in the output.  
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.  

**VALIDATION RULES:**
- Your "Segment" field MUST contain EXACTLY one of these values from the provided list OR "None"
- If you cannot find any reasonable connection to the provided segments, only then return "None"
- If the "Segment" matches exactly what you inferred, set `"Forced-Mapping": "No"`
- If the "Segment" is different from what you initially inferred, set `"Forced-Mapping": "Yes"`

Logical Matching for Segments:
- A logical match occurs when the inferred segment and an available segment from the list are conceptually or functionally similar.
- Examples of logical matches:
    - Inferred: "Tax Incentives for Startups" → Available: "Government Grants & Subsidies" (`Forced-Mapping`: "No").
    - Inferred: "Pollution Control Compliance" → Available: "Environmental Approvals" (`Forced-Mapping`: "No").
- Examples of forced mappings:
    - Inferred: "Basic Chemical Manufacturing" → Available: "Industrial Chemicals" (if closest match) (`Forced-Mapping`: "Yes").
    - Inferred: "Renewable Energy Investment Benefits" → Available: "Green Industry Incentives" (`Forced-Mapping`: "Yes").
    - Inferred: "Vendor Sourcing for Construction" → Available: "Building Materials Suppliers" (`Forced-Mapping`: "Yes").

**Examples:**
- Query: "chalk manufacturing approvals in Sihanoukville" 
  - Inferred: "Basic Chemical Manufacturing" 
  - Closest Available: "Industrial Chemicals" (if available in list)
  - Output: `"Segment": "Industrial Chemicals", "Original-Inferred-Segment": "Basic Chemical Manufacturing", "Forced-Mapping": "Yes"`

Output Format:
- The "Segment" field can ONLY contain values from the provided list or "None"
- Do not create new segment names
- Ensure that the output strictly adheres to the specified JSON format without any additional reasoning, explanations, or comments.
- Do not include any reasoning or justification in the fields. For example, avoid entries such as `"This matches because..."` or `"Assumed based on the context..."`.
- Each field should only contain the extracted information or the specified fallback values (e.g., "None").

Output the result strictly as a JSON object in the following format:
{{
    "Segment": <MUST be from provided list or "None">,
    "Original-Inferred-Segment": <What you initially inferred or "None">,
    "Forced-Mapping": <"Yes" if Segment differs from Original-Inferred, "No" if exact match>,
    "Product": <Extracted Product or "None">
}}

Query: {user_query}

Provide only the JSON object in the required format.
    """
    
    # Create the prompt using the provided variables
    prompt = PromptTemplate(
        input_variables=["user_query", "segments_str", "context"],
        template=prompt_template
    )

    # Create the LLM chain
    chain = prompt | llm

    # Invoke the LLM
    result = chain.invoke({
        "user_query": user_query,
        "segments_str": segments_str,
        "context": context
    })
    update_llm_token(result)

    # Extract JSON response
    result_content = result.content.strip()

    # Define regex patterns for Segment, Original-Inferred-Segment, Forced-Mapping, and Product
    segment_pattern = r'"Segment":\s*"([^"]+)"'
    original_inferred_segment_pattern = r'"Original-Inferred-Segment":\s*"([^"]+)"'
    forced_mapping_pattern = r'"Forced-Mapping":\s*"([^"]+)"'
    product_pattern = r'"Product":\s*"([^"]+)"'

    # Extract details using regex
    segment_match = re.search(segment_pattern, result_content)
    original_inferred_segment_match = re.search(original_inferred_segment_pattern, result_content)
    forced_mapping_match = re.search(forced_mapping_pattern, result_content)
    product_match = re.search(product_pattern, result_content)

    # Extract values or default to "None"
    segment = segment_match.group(1).strip() if segment_match else "None"
    original_inferred_segment = original_inferred_segment_match.group(1).strip() if original_inferred_segment_match else "None"
    forced_mapping = forced_mapping_match.group(1).strip() if forced_mapping_match else "No"
    product = product_match.group(1).strip() if product_match else "None"

    extracted_data = {
        "Segment": segment,
        "Original-Inferred-Segment": original_inferred_segment,
        "Forced-Mapping": forced_mapping,
        "Product": product
    }

    # Validate against the provided list of Segments
    validated_data = copy.deepcopy(extracted_data)
    if segment not in segments and segment != "None":
        validated_data["Segment"] = "Not Available in List"

    return extracted_data, validated_data

def generate_dynamic_confirmation_message(static_confirmation: str, llm) -> str:
    """
    Generate a dynamic confirmation message using LLM based on the provided static confirmation requirement for various modules.

    Parameters:
        static_confirmation (str): The static confirmation message to send to the user.
        llm: The language model instance.

    Returns:
        str: The dynamically generated confirmation message.
    """

    # Define the prompt
    prompt = """
    You are a professional assistant specializing in crafting formal, engaging, and accurate confirmation messages.
    Your goal is to create a polished confirmation message that clearly summarizes the provided static confirmation details in a concise, professional manner.

    Key Instructions:
    - The static confirmation message is a reference, not to be copied verbatim.
    - Use it as guidance to formulate a clear and formal confirmation question.
    - Avoid adding assumptions or additional details not present in the static confirmation message.
    - Do not introduce words like 'acquiring' or 'seeking' unless explicitly stated in the static confirmation message.
    - Retain context details such as 'based on your query' if present in the static message.
    - The message should allow the user to provide a simple 'Yes' or 'No' response.
    - Ensure all essential details from the static message are included.
    - Do NOT include any placeholders like "None" or "Not Available in List."
    - Avoid redundant confirmation phrasing—conclude with only one clear confirmation question.
    - Keep the response concise and free of unnecessary elaboration.

    Inputs
    1. Static Confirmation Message: "{static_confirmation}"

    Final Response Guidelines:
    - Summarize the static message in a professional, clear, and concise manner.
    - Craft the message as a yes/no confirmation question without adding assumptions.
    - Retain context phrases like 'based on your query' if present.
    - Do NOT copy the static message verbatim but ensure all key details are included.
    - Maintain a formal and engaging tone.
    - Prefer phrasing such as 'Please confirm if this information is correct.' for consistency.
    - Ensure that the message concludes with only one clear confirmation question.
    """

    # Prepare input to the model
    prompt_template = PromptTemplate(
        input_variables=["static_confirmation"],
        template=prompt
    )
    chain = prompt_template | llm
    message = chain.invoke({
        "static_confirmation": static_confirmation
    })

    return message.content.strip()

def generate_fallback_message(chat_history_for_context: List[dict], confirmation_message: str, llm) -> str:
    """
    Generate a dynamic fallback message using LLM when the user responds 'no' to a confirmation message.

    Parameters:
        chat_history_for_context (List[dict]): The list of conversation history with user and AI messages.
        confirmation_message (str): The confirmation message the user responded 'no' to.
        llm: The language model instance.

    Returns:
        str: The dynamically generated fallback message.
    """
    
    # Prepare the conversation history context
    recent_history = "\n".join(chat_history_for_context)

    # Define the prompt
    prompt = """
    You are a professional assistant specializing in creating formal, engaging, and contextually relevant fallback messages.
    Your goal is to craft a polite and professional response when the user indicates that the confirmation message was incorrect.

    ---

    Key Instructions
    1. The message should naturally convey that the provided details may not fully align with the user's needs. 
       - Use phrasing like "It seems the provided details may not fully align with your needs" or a similar, contextually natural variation.
       - Avoid copying the exact phrasing from the prompt unless it fits naturally in the response.
    2. Politely ask the user to specify the correct or missing details without using direct apologies.
    3. Avoid language that implies fault, such as 'I apologize.' Instead, use neutral and professional phrasing.
    4. Do NOT assume or infer details that were not explicitly provided.
    5. Ensure the tone is empathetic, professional, and user-friendly.
    6. The response must be concise (no more than 3 lines) and encourage the user to provide the correct details.

    ---

    Inputs
    1. Recent Conversation History:
    - {recent_history}

    2. Previous Confirmation Message:
    - "{confirmation_message}"

    ---

    Final Response Guidelines:
    - Begin with a sentence that naturally conveys that the provided details may not fully align with the user's needs.
    - Use variations like "It seems..." or "It appears..." to keep the tone conversational and engaging.
    - Politely ask the user to specify the correct or missing details.
    - Maintain a professional, engaging, and empathetic tone.
    - Do NOT infer or assume details not mentioned in the chat history or confirmation message.
    - Keep the response concise (within 3 lines).
    - Do NOT use phrases like 'I apologize.'

    """

    # Prepare input to the model
    prompt_template = PromptTemplate(
        input_variables=["recent_history", "confirmation_message"],
        template=prompt
    )
    chain = prompt_template | llm
    message = chain.invoke({
        "recent_history": recent_history,
        "confirmation_message": confirmation_message
    })

    return message.content.strip()

@frappe.whitelist()
def extract_incentive_details_using_ai(description: str, llm=llm_70b_vers_creative) -> Dict[str, List[str]]:
    """
    Uses an AI model to extract structured incentive details dynamically.

    Parameters:
        description (str): The incentive description provided by the user.
        llm: The language model instance.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are category names, 
                              and values are lists of relevant points.
    """
    
    prompt = """
    You are an expert in analyzing government and business incentive descriptions. 
    Your task is to extract structured information from the following incentive description 
    and categorize it under relevant sections. Only include categories that are explicitly mentioned.

    Categories to consider:
    - Eligibility: Who can apply or qualify for the incentive.
    - Benefits: Financial support, subsidies, tax exemptions, or any direct advantages.
    - Requirements: Conditions or criteria that must be met to receive the incentive.
    - Process: Steps or application procedures involved.
    - Other Details: Any additional relevant information.

    Description:
    {description}

    Output format (only include categories present in the text):
    {{
        "Eligibility": ["..."],
        "Benefits": ["..."],
        "Requirements": ["..."],
        "Process": ["..."],
        "Other Details": ["..."]
    }}

    Do not add any explanations, notes, or additional text. Only return valid JSON.
    - Ensure each category is formatted as a list of short points.
    - Exclude any category if it is not explicitly mentioned in the description.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["description"],
        template=prompt
    )

    chain = prompt_template | llm
    response = chain.invoke({"description": description})
    update_llm_token(response)
    return response.content.strip()

def respond_to_negative_query(
    user_message: str,
    append_user_to_history: bool,
    append_AI_to_history: bool,
    llm,
    chatId,
    update_intention = True
) -> str:
    """
    Reacts to negative intent in user queries by acknowledging it and 
    politely redirecting users to supported industry-related alternatives.

    Parameters:
    - user_message (str): The most recent user input.
    - append_user_to_history (bool): Flag to determine whether to add the user message to chat history.
    - llm: A language model instance that supports the `.invoke()` method for prompt completion.

    Returns:
    - str: A short, polite AI-generated redirection message (max two lines).
    """
    chat_history = get_chat(f"chat_{chatId}") or []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-4:]]
    if append_user_to_history:
        chat_history.append(HumanMessage(content=user_message))
        save_chat(chat_history,f"chat_{chatId}")

    prompt_template = """
    You are a professional AI assistant designed to help users with industry-related queries. 
    Sometimes users may express that they do not want to proceed with a certain type of query, 
    such as searching for vendors, incentives, employment, approvals, or land.

    Your task is to:
    - Politely acknowledge the user's intent to not continue with the current path.
    - Respect their decision without repeating the rejected topic.
    - Encourage them to explore other areas the platform supports — but limit suggestions to one or two concise, relevant alternatives.
    - Keep the response short, natural, and conversational — a maximum of two lines.
    
    Input Usage Guidelines:
    - Use the latest user message to understand the user’s current concern or direction.
    - Refer to the recent conversation history only when needed to maintain context, avoid repetition, or recognize prior negative expressions.
    - Do not restate or repeat what was already covered unless it helps clarify or smoothly redirect the conversation.

    Important Instructions:
    - Do NOT mention or re-suggest the category the user rejected — even in a different location, product, or form.
    - If the user’s rejection appears to be specific to a location, product, or context, you may offer assistance in other locations or products — but only if it does not reintroduce the rejected category.
    - Suggest one alternative direction naturally (two if needed) based on platform capabilities:
        - Building an industry from scratch
        - Searching for employment in a city or state
        - Inquiring about incentives
        - Finding vendors for their industry
        - Searching for the approvals
    - Never use "how to build an industry" or anything that implies your platform teaches or trains users. 
    You are assisting them in setting up or building, not educating them.
    - Keep the response strictly within two lines, using concise and polite phrasing.

    Inputs:
    - Latest user message: {user_message}
    - Recent conversation history: {chat_history}

    Output Requirements:
    - The message should be in one short paragraph with no more than two lines.
    - It must feel polite, helpful, and actionable — inviting the user to continue exploring relevant options.
    - Do NOT list all supported categories. Suggest only 1–2 in natural language, avoiding list-like structure.
    """

    prompt = PromptTemplate(
        input_variables=["user_message", "chat_history"],
        template=prompt_template
    )
    chain = prompt | llm

    result = chain.invoke({
        "user_message": user_message,
        "chat_history": "\n".join(Chat_history_normal)
    })
    message_from_ai = result.content.strip()
    if append_AI_to_history:
        chat_history.append(AIMessage(content=message_from_ai))
        save_chat(chat_history,f"chat_{chatId}")
    if update_intention:
        update_user_intension("Negatively Intended Query", chatId)
    return message_from_ai

def generate_redirect_message(
    llm,
    latest_user: str,
    chat_history: list[str],
    feasibility_industry: str | None,
    detected_industry: str | None,
    mode: str,  # "redirect_notice" or "stay_fallback"
    options: list[dict],  # [{"label": "...", "value": "..."}]
) -> str:
    from json import dumps

    REDIRECT_RESPONDER_SYSTEM_PROMPT = """
You are MarsAIX’s expert industrial consultant.

PERSONA & TONE
- Sound like a seasoned, client-facing consultant (10+ years). Warm, confident, helpful.
- Short sentences. Clear wording. Human rhythm. One exclamation max if truly warranted.
- Open with one short, natural acknowledgment line that RESPONDS to the user (do NOT repeat their words verbatim or paraphrase their message).

CONTEXT YOU WILL RECEIVE
- LATEST_USER_MESSAGE: the user’s most recent text.
- CHAT_HISTORY: recent turns for tone/continuity cues.
- FEASIBILITY_INDUSTRY: the industry tied to this chat’s feasibility.
- DETECTED_INDUSTRY: the industry implied in the latest user message (may differ or be unknown).
- MODE: either "redirect_notice" (we recommend new chat) or "stay_fallback" (user chose to stay).
- OPTIONS: the UI will render action buttons. You may reference them by label, but do not invent new ones.

WHAT TO WRITE (STRICT)
- One concise Markdown message, nothing else, **as a single paragraph** (no lists, no line breaks), target ~40–60 words.
- Be explicit that this chat is connected to the **Feasibility Study** feature.
- If industries differ, name both (bold them) and briefly explain why we recommend moving the query: **to keep each thread within a single industry and aligned with the uploaded study**. (Regular chats may span topics; feasibility threads should stay scoped.)
- Use natural connectors (“but”, “however”) for flow; avoid robotic pivots like “so you can:”.
- Do not add promises or timelines. Never ask for details already decided upstream.

MODE BEHAVIOR
- redirect_notice:
  • Start with a short, friendly response (no parroting).
  • In the same paragraph, say this chat is linked to the **Feasibility Study** for **{FEASIBILITY_INDUSTRY}**, **but** the latest request appears to be about **{DETECTED_INDUSTRY}** (or “a different industry”). Recommend **moving this query to a new chat so each thread stays within a single industry and aligns with the uploaded study**.
  • In the same flow, guide action with Yes/No (do not list buttons): tell the user they can choose **Yes** to start a new chat to run this **{DETECTED_INDUSTRY}** query, or **No** to stay here and continue with **{FEASIBILITY_INDUSTRY}**.
  • End with: **Please choose from below.**

- stay_fallback:
  • One warm, single-paragraph line confirming we’ll continue in **{FEASIBILITY_INDUSTRY}** and proceed with the request here, ending with a natural forward-looking close (no confirmation phrase).

LANGUAGE GUARDRAILS
- Avoid: “note”, “please note”, “as an AI”, “based on your query”, “assist you better”.
- Use standard international number formatting only if USD appears.
- Output must be valid Markdown.
- Avoid robotic pivots like “so you can:”; weave actions naturally into the sentence.

STYLE EXAMPLE (redirect_notice, single paragraph — do not copy verbatim):
“Thanks for the update. This chat is tied to the **Feasibility Study** for **{FEASIBILITY_INDUSTRY}**, but your latest request concerns **{DETECTED_INDUSTRY}**; we recommend moving this query to a new chat so each thread stays within a single industry and aligns with your uploaded study. Choose **Yes** to start that chat, or **No** to continue here with **{FEASIBILITY_INDUSTRY}**. **Please choose from below.**”

OUTPUT
- Return exactly one concise Markdown message and nothing else.
    """


    REDIRECT_RESPONDER_USER_TEMPLATE = """<CHAT_HISTORY>
{chat_history}
</CHAT_HISTORY>

<LATEST_USER_MESSAGE>
{latest_user}
</LATEST_USER_MESSAGE>

<FEASIBILITY_INDUSTRY>
{feasibility_industry}
</FEASIBILITY_INDUSTRY>

<DETECTED_INDUSTRY>
{detected_industry}
</DETECTED_INDUSTRY>

<MODE>
{mode}   <!-- "redirect_notice" or "stay_fallback" -->
</MODE>

<OPTIONS>
{options_json}
</OPTIONS>
    """


    def _brace_escape(s: str) -> str:
        # Double all braces so str.format() won't treat them as placeholders
        return s.replace("{", "{{").replace("}", "}}")

    # ...inside generate_redirect_message (before .format):
    options_json = json.dumps(options, ensure_ascii=False)   # 1) to string
    options_json_escaped = _brace_escape(options_json)       # 2) escape braces

    user_prompt = REDIRECT_RESPONDER_USER_TEMPLATE.format(
        chat_history="\n".join(chat_history or []),
        latest_user=latest_user,
        feasibility_industry=feasibility_industry or "the industry in your feasibility study",
        detected_industry=detected_industry or "a different industry",
        mode=mode,  # "redirect_notice" or "stay_fallback"
        options_json=options_json_escaped,                   # <-- use escaped value
    )
    resp = llm.invoke([
        {"role": "system", "content": REDIRECT_RESPONDER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])
    return getattr(resp, "content", str(resp)).strip()

