import os
# from dotenv import load_dotenv
import mimetypes
from typing import List, Dict, Tuple
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader,
    UnstructuredPowerPointLoader, CSVLoader, TextLoader,
    UnstructuredHTMLLoader, UnstructuredFileLoader
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever    
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_transformers import EmbeddingsRedundantFilter, LongContextReorder
from usaix.Ai_module.Query_Classification_And_Analysis import llm_70b_vers_creative,llm_maverik
from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from transformers import pipeline
from IPython.display import display, Markdown
import warnings
import re
import ast
import json
from pathlib import Path
import hashlib
import chromadb  # add this import at top if missing
import configparser
import random

## function imports from FINAL_UNVIERSAL_FUNCTION ##
from frontend_app.Ai_module.Feasibility_Universal_Function.Final_Universal_Function import (
    # fetch_single_doc_by_name, 
    # fetch_doc_fields_by_name, 
    fetch_frappe_doc_universal,
    make_headers, 
    fetch_pdf_to_temp, 
    getting_pdf_from_file_url_in_feasibility_session_id, 
    checking_whether_vector_file_exists_or_not_and_ifnot_then_creating_new_vector_file, 
    ingest_and_persist_with_budget_2, 
    ensure_vector_store, 
    ensure_vector_and_update_record
                    )

FEAS_DOCTYPE = "Feasibility Report"
FOLL_DOCTYPE = "Follow Up"

# storage folders name of follow up and feasibility vectors 
LABEL_FOLLOW = "Follow_Up"
LABEL_FEASIBILITY = "Feasibility_Report"

warnings.filterwarnings("ignore")
base_dir = os.path.expanduser("~")
config_file = os.path.join(base_dir, "frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini")
# config_file = '/home/marsapplication/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
config = configparser.ConfigParser()
config.read(config_file)

api_key = config['Key']['groq_key']
frappe_api_key = config['Frappe_api_key_and_secret']['frappe_api_key']
frappe_api_secret = config['Frappe_api_key_and_secret']['frappe_api_secret']
ritu_local_base_url = config['Frappe_api_key_and_secret']['ritu_local_base_url']
live_base_url = config['Frappe_api_key_and_secret']['live_base_url']

# CHUNKS_STORAGE
CHUNKS_STORAGE = {}

PERSIST_ROOT = "/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/vectors"
os.makedirs(PERSIST_ROOT, exist_ok=True)
# COLLECTION_NAME = "feasibility_docs"   # same name in every per-PDF folder is fine

# CONFIGURATION_STORAGE = 6 # IN GB

def iter_chroma_docs(vs, where=None, batch_size=1000, hard_cap=None):
    """
    Stream documents from a Chroma collection via pagination.
    - where: optional metadata filter dict (e.g., {"stable_doc_id": "..."}).
    - batch_size: page size.
    - hard_cap: max docs to yield (None = no cap).
    """
    col = vs._collection  # underlying chromadb collection
    yielded = 0
    offset = 0
    while True:
        if hard_cap is not None and yielded >= hard_cap:
            break

        ask = batch_size if hard_cap is None else min(batch_size, hard_cap - yielded)
        page = col.get(
            where=where,           # filter by your own metadata if you want
            limit=ask,
            offset=offset,
            include=["documents", "metadatas"]  # <-- valid include items
        )

        ids   = page.get("ids") or []
        docs  = page.get("documents") or []
        metas = page.get("metadatas") or []

        if not ids:
            break

        for t, m in zip(docs, metas):
            yield Document(page_content=t, metadata=m)

        yielded += len(ids)
        offset  += len(ids)

class AdvancedRAGSystem:
    # def __init__(self, llm_model: str = "llama3-70b-8192"):
    def __init__(self, llm_model: str = "openai/gpt-oss-120b"):
    # def __init__(self, llm_model: str = "qwen/qwen3-32b"):
    # def __init__(self, llm_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"):
        # Initialize core components
        # print("✅ API Key value used:", repr(groq_api_key))
        self.llm = ChatGroq(model_name=llm_model, temperature=0.5, api_key = api_key)
        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            query_instruction="Represent this sentence for searching relevant passages:"
        )

        # NEW: persistence settings
        # self.persist_dir = PERSIST_DIR
        # self.collection_name = COLLECTION_NAME
        # os.makedirs(self.persist_dir, exist_ok=True)

        self.current_doc_id = None
        self.current_pdf_dir = None      # <- per-PDF chroma folder

        # self.document_processor = DocumentProcessor(self.embedding_model)
        self.vector_store = None
        self.retriever = None
        
        # Initialize intent classifier
        self.intent_classifier = pipeline("text-classification", 
                                        model="facebook/bart-large-mnli")
        
 

        # Predefined questions for auto-analysis
        self.predefined_questions = ["Give me the capacity range of the product to be manufactured(include exact unit of the product mentioned in the context)?",
                                    "What is the estimated production capacity or quantity described?",  
                                    "What is the unit of time associated with the stated production capacity?",
                                    "Tell me which type of product is to be manufactured by analysing the given context?",
                                    "Can you tell me the main-industry to which the document belongs to?",
                                    "Can you tell me the sub-sector to which the document belongs to?",
                                    "Tell me specific 'area' or 'city' or 'state' from the document in which industry is planning to be built?",
                                    "Tell me all the 'SUPPLIES' and 'EQUIPMENTS' required for the product which is planned to be built in the industry?"]

    def load_document(self, file_path):
        """Universal document loader with enhanced error handling"""
        mime_type, _ = mimetypes.guess_type(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if not os.path.exists(file_path):
                # raise FileNotFoundError(f"File not found: {file_path}")
                return [], "error loading document"
            if os.path.getsize(file_path) == 0:
                # raise ValueError(f"Empty file: {file_path}")
                return [], "error loading document"

            if mime_type == "application/pdf" or file_ext == ".pdf":
                return PyPDFLoader(file_path).load(), "successful loading"
            elif (mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" 
                or file_ext == ".docx"):
                return Docx2txtLoader(file_path).load(), "successful loading"
            elif mime_type in ("application/vnd.ms-excel",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") or file_ext in (".xls", ".xlsx"):
                return UnstructuredExcelLoader(file_path).load(), "successful loading"
            elif mime_type == "text/plain" or file_ext == ".txt":
                return TextLoader(file_path).load(), "successful loading"
            elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation" or file_ext == ".pptx":
                return UnstructuredPowerPointLoader(file_path).load(), "successful loading"
            else:
                return UnstructuredFileLoader(file_path, mode="elements").load(), "successful loading"

        except Exception as e:
            # print(f"Error loading {file_path}: {str(e)}")
            return f"Error loading {file_path}: {str(e)}", "error loading document"


    # def create_advanced_retriever(self, vector_store:dict|str, status:bool doctype:str, docname:str, docs: List[Document]):
    def create_advanced_retriever(self, vector_store:dict|str, status:bool, doctype:str):

        if doctype == FEAS_DOCTYPE:
            # folder_name = LABEL_FEASIBILITY
            folder_name = doctype
        elif doctype == FOLL_DOCTYPE:
            # folder_name = LABEL_FOLLOW
            folder_name = doctype
        folder_name = doctype
        
        if status:
            if isinstance(vector_store, str):
     
                root = os.path.join(PERSIST_ROOT, folder_name, vector_store)
                collection_name = vector_store
            elif isinstance(vector_store, dict):
                # root = os.path.join(PERSIST_ROOT, "vectors", doctype, vector_store["collection_name"])
                # root = os.path.join(PERSIST_ROOT, doctype, vector_store["collection_name"])
                root = os.path.join(PERSIST_ROOT, folder_name, vector_store["collection_name"])
                collection_name = vector_store["collection_name"]
            
            with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
                file.write(f"\COLLECTION NAME 😊:- \n{collection_name}")

        elif not status:
            root = None

        if root:

            PERSIST_DIR = rf"{root}"
            COLLECTION = collection_name  # must match ingestion

            # Re-open the existing store
            vs = Chroma(
                persist_directory=PERSIST_DIR,
                collection_name=COLLECTION,
                embedding_function = self.embedding_model
            )

          
            try:
                total = vs._collection.count()
            except Exception:
                total = None

            if total == 0:
                raise ValueError(
                    "Chroma collection is empty. Re-check persist_directory/collection_name or re-ingest."
                )

            # 2) If you want ALL chunks (child_docs) back as Document objects:
            documents = list(iter_chroma_docs(vs, batch_size=1500, hard_cap=20000))  # cap is optional

            dense_retriever = vs.as_retriever(search_kwargs={"k": 10}) # @@
            # print("DENSE RETRIEVER🤡",dense_retriever)
            
            # # 2. Sparse (BM25) Retriever
            # bm25_retriever = BM25Retriever.from_documents(docs)
            # bm25_retriever.k = 10
            # print(bm25_retriever)

            # 3) Build BM25 index
            bm25 = BM25Retriever.from_documents(documents)
            bm25.k = 10  # top-k
            # print(bm25)
            
            # 3. Multi-Query Retriever
            query_prompt = PromptTemplate(
                input_variables=["question"],
                template="""Generate 3 different versions of the given user question to retrieve relevant documents.
                Original question: {question}"""
            )

            multi_retriever = MultiQueryRetriever.from_llm(
                retriever=dense_retriever,
                llm=self.llm,
                prompt=query_prompt
            )
            
            # Create ensemble (removed SelfQueryRetriever)
            ensemble = EnsembleRetriever(
                retrievers=[dense_retriever, bm25, multi_retriever],
                weights=[0.4, 0.3, 0.3]
            )

            self.retriever = ensemble
            
            print("Cohere reranker not available, using ensemble retriever without reranking")
            return ensemble
        
    # def generate_answer(self, question: str, file_path, verify: bool = True) -> Dict:
    def generate_answer(self, question: str, verify: bool = True) -> Dict:
        """Advanced generation with verification"""
        if not self.retriever:
            raise ValueError("Retriever not initialized. Call analyze_document() first.")
            
        # Step 1: Retrieve context
        retrieved_docs = self.retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        no = 0
        chunks = {}

        for doc in retrieved_docs:
            no += 1
            chunks[f"chunk_{no}"] = doc.page_content
        
        # Step 2: Generate draft answer
        prompt = ChatPromptTemplate.from_template(
            """Answer the question based only on the following context:
            {context}
            
            Question: {question}
            Provide a concise, accurate answer with citations where applicable.If the context is insufficient,just say you don't know. 
            """
        )
        
        chain = prompt | self.llm | StrOutputParser()
        # print("this is the error", "👇")
        draft_answer = chain.invoke({"context": context, "question": question})
        
        # Step 3: Verification
        if verify:
            verification_prompt = """Verify the following answer against the context:
            Context: {context}
            
            Answer to verify: {answer}
            
            Identify any factual inaccuracies or unsupported claims."""
            
            verification = self.llm.invoke(
                verification_prompt.format(context=context, answer=draft_answer)
            ).content
            
            # Generate final verified answer
            final_prompt = """Given the original answer and verification feedback:
            Original Answer: {answer}
            
            Verification Feedback: {feedback}
            
            Generate a corrected and improved answer.
            """
            
            final_answer = self.llm.invoke(
                final_prompt.format(answer=draft_answer, feedback=verification)
            ).content
        else:
            final_answer = draft_answer
            verification = "Skipped"

        # output_data = {
        #  file_path: {question:{
        #     "chunks": {
        #                 "content": chunks,
        #             },
        #     "summary": final_answer
        #     }
        #     },   
        # }

        # for doc_name, questions in output_data.items():
        #     if doc_name not in CHUNKS_STORAGE:
        #         CHUNKS_STORAGE[doc_name] = {}

        #     for q, q_data in questions.items():
        #         CHUNKS_STORAGE[doc_name][q] = q_data
        
        return {
            "question": question,
            "context": retrieved_docs,
            "draft_answer": draft_answer,
            "verified_answer": final_answer,
            "verification": verification,
        }
    
    def extract_keyword(self, question: str, text: str) -> str:
        """Extracts the most relevant keyword from text based on the question"""

        extraction_prompt="""Given a user question and input text, extract the most relevant **2-3 word keyword or numeric value** from the text **only if it directly and unambiguously answers the question**. Follow the specific extraction rules below based on the question type:

---

🔹 **General Semantic Matching Rules**:

1. **Confidence Threshold**:
   - Return an answer **only if you are ≥80% confident** it matches the question’s intent.
   - If confidence <80% or the text lacks sufficient information, return:  
     **Most Relevant Keyword:** I don't know

2. **Relevance Criteria**:
   - The keyword must be:
     - **Explicitly stated** in the text.
     - A **direct answer** (e.g., for "What is the capital of France?", "Paris" is valid).
   - Ignore partial, implied, or speculative matches.

    NOTE:- The following are examples of good and bad answers. Good examples show correct and confident extractions. Bad examples either return unrelated, vague, or incomplete information, or violate formatting or semantic matching rules.

    Good Example:
    Question: "What is the capital of France?"
    Text: "France’s capital is Paris."
    Output: Most Relevant Keyword: Paris

    Bad Example:
    Question: "What is the capital of France?"
    Text: "France has several beautiful cities including Lyon and Marseille."
    Output: Most Relevant Keyword: I don't know   

    ---

3. 🔹 **Special Case A –: Duration Extraction**:
    Apply **only when the question asks for total/completion time** (e.g., "total estimated duration", "completion time"):

    1. Extract the **full numeric duration** (e.g., "18 months", "2 years") when:
    - The duration represents the TOTAL project timeline
    - It's explicitly tied to project completion

    2. For phased timelines:
    - Calculate total duration from first to last phase if clearly stated
    - Return as "[X] months/years" (e.g., "24 months" for Q2 2025-Q4 2026)

    3. If no clear completion duration exists, return:  
    **Most Relevant Keyword:** unknown

    ⚠️ For duration questions, return BOTH number and unit unless explicitly asked for unit-only.

    ---

4. 🔹 **Special Case B –: Time Unit Extraction (Duration-based Questions)**:

    Apply **only when the question asks about time or duration units** (e.g., “How long…?”, “What is the unit of time for…?”).

    1. Extract only the **unit word** (e.g., “months”, “years”) from a numeric duration (e.g., “12 months”, “4-5 years”).
    2. For ranges, use the unit from the **last mentioned value** (“6 weeks to 3 months” → “months”).
    3. If no clear numeric duration with unit is found or it's unrelated to time, return:  
    **Most Relevant Keyword:** unknown

    ⚠️ Do NOT return numeric values (e.g., "18 months" ❌); return only the unit ("months" ✅).  
    ⚠️ Never infer units from vague or unrelated context.

    NOTE:- The following are examples of good and bad answers. Good examples show correct and confident extractions. Bad examples either return unrelated, vague, or incomplete information, or violate formatting or semantic matching rules.

    Good Example:
    Question: "What is the unit of time taken for industrial construction?"
    Text: "Construction usually takes around 12-18 months."
    Output: Most Relevant Keyword: months

    Good Example:
    Question: "How long is the project duration?"
    Text: "The timeline extends from 6 weeks to 3 months."
    Output: Most Relevant Keyword: months

    Bad Example:
    Question: "What is the construction time unit?"
    Text: "The project duration is yet to be finalized."
    Output: Most Relevant Keyword: unknown

    Bad Example:
    Question: "What is the construction time unit?"
    Text: "It will be a lengthy project."
    Output: Most Relevant Keyword: unknown

    ---

5. 🔹 **Special Case C –: Numeric Range Extraction (e.g., capacity, quantity)**:

    Apply only if the question explicitly asks for a **range or quantity of a measurable attribute** (e.g., "What is the capacity range?", "How many units?", "Production quantity?").

    1. Extract the **exact numeric range or single value + unit** (e.g., "100,000–250,000 units", or "2,000 units").
    - **Exclude vague prefixes/suffixes**:  
    - ❌ Remove "beyond," "~," "approximately," "up to," "more than," etc.  
    - ✅ Keep only **absolute values** (e.g., "300 MWh/month" ✅, not "beyond 300 MWh/month" ❌). 
    2. Return the **full exact range** if provided (e.g., "1,000,000 - 2,500,000 units").
    3. **Reject non-absolute values**:  
    - If the text uses vague language (e.g., "scalable beyond X"), return:  
        **Most Relevant Keyword:** I don't know
    - If No clear numeric value is stated:-
        **Most Relevant Keyword:** I don't know
    4. Output format:  
    - Valid: **Most Relevant Keyword:** [number][unit] (e.g., "300 MWh/month" or "150,000-250,000 units").  
    - Invalid: **Most Relevant Keyword:** I don't know.  

    NOTE:- The following are examples of good and bad answers. Good examples show correct and confident extractions. Bad examples either return unrelated, vague, or incomplete information, or violate formatting or semantic matching rules.   

    Good Example:
    Question: "Give me the capacity range of the product to be manufactured?"
    Text: "The facility will initially produce 1,000,000 units per year and can scale to 2,500,000 units."
    Output: Most Relevant Keyword: 1,000,000 to 2,500,000 units

    Good Example:
    Question: "What is the expected production quantity?"
    Text: "Expected output is 200,000 units annually."
    Output: Most Relevant Keyword: 200,000 units

    Bad Example:
    Question: "What is the production capacity?"
    Text: "The production line supports high throughput."
    Output: Most Relevant Keyword: I don't know

    Bad Example:
    Question: "What is the capacity range of the product?"
    Text: "The facility’s capacity is measured in units per year."
    Output: Most Relevant Keyword: I don't know   

    Good Example:  
    Question: "Give me the capacity range of the product to be manufactured?"  
    Text: "A modular setup to support phased manufacturing with potential scalability beyond 300 MWh/month."  
    Output: **Most Relevant Keyword:** 300 MWh/month  

    Bad Example:  
    Question: "What is the production capacity?"  
    Text: "Capacity is approximately 500–700 units, potentially more."  
    Output: **Most Relevant Keyword:** I don't know  
    *(Reason: "approximately" and "potentially more" violate absolute-value rule)* 

    ---

6. 🔹 False Confidence & Unit Confusion

    NOTE:- The following are examples of good and bad answers. Good examples show correct and confident extractions. Bad examples either return unrelated, vague, or incomplete information, or violate formatting or semantic matching rules.

    Bad Example:
    Question: "What is the capacity range of the product?"
    Text: "The factory will produce 1,000,000 units per year."
    Output: Most Relevant Keyword: I don't know

    (Because range is asked, but only one value is given — not a range)

    Bad Example:
    Question: "Give me the capacity range of the product to be manufactured?"
    Text: "The capacity is measured in units per year."
    Output: Most Relevant Keyword: I don't know

    (Because no actual range or quantity is stated)

7. Below are the context of main-industry and sub-sector to take reference from:-    

- Main-Industry: A broad category representing a major segment of economic activity, encompassing various related activities, products, or services. Examples include Technology, Healthcare, Financial Services, Manufacturing, or Retail.
- Sub-Sector: A more specific segment within a main-industry, focusing on a particular niche, product, service, or operational focus. For example, within the Technology main-industry, sub-sectors could include Software Development, Artificial Intelligence, Cybersecurity, or Hardware Manufacturing.    
    
🔹 **Output Format**:
- If confident:  
  **Most Relevant Keyword:** [exact phrase from text]  
- If unsure:  
  **Most Relevant Keyword:** I don't know

---

**User Question:**  
{question}

**Input Text:**  
{text}
    """
        
        response = self.llm.invoke(extraction_prompt.format(question=question, text=text))
        
        # Extract just the keyword from the response
        keyword = response.content.split("**Most Relevant Keyword:**")[-1].strip()
        return keyword

    def prompt_for_supplies_question(self, question: str, text: str) -> str:

        extraction_prompt = """You are given the following text describing a production process. Identify all *physical supplies* and *equipment* mentioned, and list them in JSON format.

        - *Supplies* are physical raw materials or components **consumed** in production (e.g. Lithium Carbonate, Graphite).
        - *Equipment* are physical tools or machines used in production (e.g. Battery Tester, Electrode Coater).
        - **Exclude** any abstract concepts, services, or vague references (for example, do not include software, expertise, logistics, or the generic word "materials" without specifics).

        Output a JSON object with two keys: `"supplies"` and `"equipment"`. Each key should map to a list of item names (strings). Include any optional details from the text in parentheses after the item name. If a category has no items, use an empty list for that key. 

        **Return only the JSON object with no additional text or formatting.**

        ** DO NOT RETURN any information in brackets(). **

        For example, the output should look like:

        ```json
        {{
        "supplies": ["Lithium Carbonate (battery grade)", "Graphite"],
        "equipment": ["Battery Tester", "Electrode Coater"]
        }}

        **User Question:**  
        {question}

        **Input Text:**  
        {text}

"""     
        # Now format only the question and text placeholders
        formatted_prompt = extraction_prompt.format(question=question, text=text)
        
        response = self.llm.invoke(formatted_prompt)
        return response

    # def analyze_document(self, file_path:str, vector_store:dict|str, status:bool, doctype:str):
    def analyze_document(self, vector_store:dict|str, status:bool, doctype:str):
        """Complete document analysis with predefined questions"""
        # Process document
        # docs= self.process_documents(file_path)
        self.retriever = self.create_advanced_retriever(vector_store=vector_store, status=status, doctype=doctype)
        
        # Answer predefined questions
        results = {}
        results_for_supplies_question = {}
        for question in self.predefined_questions:
            if question == "Tell me all the 'SUPPLIES' and 'EQUIPMENTS' required for the product which is planned to be built in the industry?":
                # full_answer = self.generate_answer(question=question, file_path=file_path)
                full_answer = self.generate_answer(question=question)
                keyword = self.prompt_for_supplies_question(question, full_answer['verified_answer'])
                # print(full_answer['verified_answer'])
                results_for_supplies_question[question] = {
                    'full_answer': full_answer,
                    'LIST': keyword
                }
            else:
                # full_answer = self.generate_answer(question=question, file_path=file_path)
                full_answer = self.generate_answer(question=question)
                keyword = self.extract_keyword(question, full_answer['verified_answer'])
                # print(full_answer['verified_answer'])
                results[question] = {
                    'full_answer': full_answer,
                    'keyword': keyword
                }

        # with open(f"{file_path}.json", "w", encoding="utf-8") as f:
        #     json.dump(CHUNKS_STORAGE, f, ensure_ascii=False, indent=4)
        
        # e.g., at the end of analyze_document or process_feasibility_report
        self.vector_store = None
        self.current_doc_id = None
        self.current_pdf_dir = None

        return results, results_for_supplies_question

def extract_time_unit(text: str) -> str:
    """Extracts 'months' or 'years' from text, returns 'unknown' if not found"""
    text_1 = text.lower()
    if text_1 in ["month", "months"]:
        return "per month"
    # elif "year" in text:
    #     return "per year"
    elif text_1 in ["year","years","annually","pa","per year"]:
        return "per annum"
    elif "days" in text_1:
        return "daily"
    elif "quarterly" in text_1:
        return "per quarter"
    return "unknown"

# Function to detect range from the text and calculate mean of the range
def detect_and_extract_range(text: str) -> tuple[bool, list[int] | None]:
    """
    Improved version that handles comma-separated numbers in ranges.
    Returns:
        - (True, [start, end]) if a range is found
        - (False, None) if no range is found
    """
    # Regex to match patterns like "X to Y", "X-Y", or "X - Y" with commas
    range_match = re.search(r'([\d,]+)\s*(?:to|-)\s*([\d,]+)', text)
    if range_match:
        # Remove commas and convert to integers
        start = int(range_match.group(1).replace(',', ''))
        end = int(range_match.group(2).replace(',', ''))
        return True, [start, end]
    return False, None


def cleaning_and_range_cal(dict):
    final_dict = {}

    for key, value in dict.items():
        if isinstance(value, str):  # Only process string values
            has_range, range_values = detect_and_extract_range(value)

            if has_range:
                # print(f"Range detected: {range_values[0]:,} to {range_values[1]:,}")
                mean = sum(range_values) / len(range_values)
                # print(f"Mean of range: {mean:,.2f}")  # Format with commas
                final_dict[key] = mean
            else:
                # Clean non-range values
                segments = [s.strip() for s in value.split('\n') if s.strip()]
                if segments:
                    final_dict[key] = segments[0]
                else:
                    final_dict[key] = value  # Fallback to original value
        else:
            final_dict[key] = value  # Keep non-string values as-is

    return final_dict    

def extracting_unit_from_capacity_range_factor(capacity_range: str|None):
     # Common unit patterns (can extend this list as needed)
    if not capacity_range:
        return None

    common_units = [
        'kWh', 'KW', 'kW', 'MWh','GWh' 'kV',
        'kg',  'mg', 'ton', 'lb', 'lbs',
        'cm', 'mm', 'inch', 'ft', 'feet',
        'liters', 'liter',  'ml',
        'Hz', 'kHz', 'MHz', 'GHz',
        '°C', '°F', '%',
        'bar', 'psi', 'Nm', 'units', 'MT'
    ]

    # Regex pattern: match a number range or single value followed by unit
    pattern = r'(\d+(\.\d+)?\s*(to|-|–)?\s*\d*\s*)?(' + '|'.join(re.escape(unit) for unit in common_units) + r')\b'

    matches = re.findall(pattern, capacity_range, flags=re.IGNORECASE)

    # Extract just the unit from the matched tuples
    units = [match[3].lower() for match in matches]
    with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
        file.write(f"\nSTATUS👌:- /n{units}")
    # final_unit = units[0]
    return units[0] if units else None
    
    # return units

def supply_list_extraction(text):
    supplies = []
    equipment = []

    # Step 1: Match the full JSON dictionary starting with "supplies"
    match = re.search(r'\{[\s\S]*?"supplies"\s*:\s*\[.*?\][\s\S]*?"equipment"\s*:\s*\[.*?\][\s\S]*?\}', text)

    if match:
        json_str_escaped = match.group(0)

        try:
            # Step 2: Unescape string (in case it's double-escaped)
            json_str = json_str_escaped.encode().decode('unicode_escape')

            # Step 3: Parse JSON
            data = json.loads(json_str)
            supplies = data.get("supplies", [])
            equipment = data.get("equipment", [])
            # print("Supplies:", supplies)
            # print("Equipment:", equipment)
        except json.JSONDecodeError as e:
            print("JSON parsing error:", e)
    else:
        print("No JSON-like block found.")

    return supplies, equipment
   

industrial_dict = {}
location_dict = {}
product_and_duration_dict = {}
supply_dict = {}

# Modified Example Usage
# if __name__ == "__main__":
# def process_feasibility_report(file_path, vector_store, doctype, status):    
def process_feasibility_report(vector_store, doctype, status):    
    # Initialize system
    rag = AdvancedRAGSystem()
    
    # analysis_results, supplies_results = rag.analyze_document(file_path=file_path, vector_store=vector_store,doctype=doctype, status=status)
    analysis_results, supplies_results = rag.analyze_document(vector_store=vector_store,doctype=doctype, status=status)

    # Display results
    for question, result in analysis_results.items():
        if question == "Tell me all the 'SUPPLIES' required for the product which is planned to be built in the industry?":
            print('')
        else:    
            print("")
            # display(Markdown(f"### {question}"))
            # display(Markdown(f"**Full Answer:** {result['full_answer']['verified_answer']}"))
            # print(result['full_answer']['verified_answer'])
            # display(Markdown(f"**Key Keyword:** {result['keyword']}"))
            # display(Markdown("---"))

            # Replace the elif chain with:
            if question == rag.predefined_questions[0]:  # Capacity range
                product_and_duration_dict["capacity"] = result['keyword']
            # elif question == rag.predefined_questions[1]:  # capacity unit
            #     product_and_duration_dict["capacity unit"] = result['keyword']
            elif question == rag.predefined_questions[1]:  # Duration
                product_and_duration_dict["time period_0"] = result['keyword'] 
                # unit detection 
                # print("time_period_1🍞",result['keyword'])
                product_and_duration_dict["time period_1"] = extract_time_unit(result['keyword']) 
            elif question == rag.predefined_questions[2]: 
                # print("EXTRACTED TIME UNIT FROM DOCUMENT😊😊😊😊😊😊😊😊😊😊", result['keyword']) 
                if result["keyword"] != "I don't know" :
                    product_and_duration_dict["time period_1"] = extract_time_unit(result['keyword'])
            elif question == rag.predefined_questions[3]:  # product
                product_and_duration_dict["product"] = result['keyword']  
            elif question == rag.predefined_questions[4]:  # Capacity range
                industrial_dict["main_industry"] = result['keyword']
            elif question == rag.predefined_questions[5]:  # capacity unit
                industrial_dict["sub-sector"] = result['keyword']
            elif question == rag.predefined_questions[6]:  # Duration
                location_dict["area_or_city_or_state"] = result['keyword']       
    
    for question, supply_result in supplies_results.items():

        str_list = str(supply_result["LIST"])

        supplies, equipments = supply_list_extraction(str_list)

        supply_dict["supplies"] = supplies
        supply_dict["equipments"] = equipments 

    updated_product_and_duration_dict = cleaning_and_range_cal(product_and_duration_dict)
    unit_extraction = extracting_unit_from_capacity_range_factor(product_and_duration_dict['capacity'])
    updated_product_and_duration_dict["product_unit"] = unit_extraction

    all_dicts = {f'dict_{i}': d for i, d in enumerate([updated_product_and_duration_dict,location_dict,supply_dict,industrial_dict], 1)}

    all_dict_2 = {
    "final_updated_product_and_duration_dict": {},
    "final_location_dict": {},
    "final_supply_dict": {},
    "final_industry_dict": {}
    }

    for dict_name, sub_dict in all_dicts.items():
        # Map to final dictionary names
        if dict_name == "dict_1":
            target_dict = all_dict_2["final_updated_product_and_duration_dict"]
        elif dict_name == "dict_2":
            target_dict = all_dict_2["final_location_dict"]
        elif dict_name == "dict_3":
            target_dict = all_dict_2["final_supply_dict"]
        elif dict_name == "dict_4":
            target_dict = all_dict_2["final_industry_dict"]
        else:
            continue  # Skip unexpected keys

        # Filter and store valid values
        for key, value in sub_dict.items():
            lower_val = str(value).lower()  # Convert to string for safety
            if lower_val not in ["i don't know", "unknown", "", "Most Relevant Keyword: I don't know"]:
                target_dict[key] = value

    def remove_empty_values(data):
        if isinstance(data, dict):
            filtered = {
                k: remove_empty_values(v)
                for k, v in data.items()
                if remove_empty_values(v) not in [None, {}, [], '', "Most Relevant Keyword: I don't know"]
            }
            return filtered if filtered else None
        elif isinstance(data, list):
            filtered_list = [remove_empty_values(item) for item in data if remove_empty_values(item) not in [None, {}, [], '']]
            return filtered_list if filtered_list else None
        else:
            return data       

    final_dict_45 = remove_empty_values(all_dict_2)         

    return all_dicts, all_dict_2, final_dict_45

def generate_questions(dict_45, llm_model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5):
# def generate_questions(dict_45, llm_model="llama-3.3-70b-versatile", temperature=0.5):

    llm = ChatGroq(model_name=llm_model, temperature=temperature, api_key=api_key)

    prompt_template = """You are a domain-aware assistant helping users plan and explore key aspects of setting up an industry in India.

---

📘 PROJECT CAPABILITIES:

You support intelligent decision-making for industrial planning. Your core capabilities include:
• Suggesting land **availability** based on location and industry  
• Recommending suppliers (raw materials, equipment) by proximity  
• Providing labor availability by general skill type  
• Identifying necessary government approvals  
• Suggesting applicable government incentives  

---

📦 MODULE DEFINITIONS:

Each industrial module focuses on specific elements:

**Build from Scratch**  
• Main industry and sub-sector  
• Product name, capacity, unit, and build timeline  
• Suitable locations  
• Labor availability  
• Vendor access  
• Approvals and incentives  

**Employment**  
• Labor availability (skilled/semi/unskilled)  
• Workforce proximity to location  
• City/state-level setup relevance  

**Vendor Search**  
• Raw material/equipment supplier proximity  
• Supplies and equipment required  
• Location and industry sector  

**Incentives**  
• Government incentive schemes  
• Location of industry setup  
• Relevance of product or industry to social goals  

**Approval**  
• Government regulations and permissions  
• Local/state jurisdiction  
• Industry and sub-sector compliance  

---

✅ QUERY STYLE REFERENCE (FORMAT ONLY):

These are examples of how queries should be phrased.  
**Do not use these values** (industries, locations, terms) in your output. Use them only to match the tone and structure.

• What is the vendor availability for cement industry in Vadodara, Gujarat?  
• Tell me all the incentives available for pharmaceutical industry in Surat city?  
• What are the employment options around the Anand city?  
• Locations for LED lighting industry with capacity of 175k units per year?  
• What are the approvals available for building electrochemical storage unit in Bharuch?  
• What are the vendor options for textile industry in Vadodara?

---

🎯 OBJECTIVE:

Based only on the dictionary below, generate **4 to 5 helpful, human-readable follow-up queries** that the user might logically ask next to explore the following areas:
• Land availability  
• Vendor access (supplies, equipment)  
• Labor availability  
• Government approvals  
• Applicable incentives  

---

📥 INPUT DICTIONARY:
Only use the content in the dictionary. You must not invent or infer any new values.

{dictionary}

This dictionary may include:
- Product name  
- Production capacity and unit  
- Time period and time unit  
- Supplies and equipment  
- Location (area, city, state)  
- Main industry and sub-sector  

---

✅ OUTPUT RULES:

• You must generate **4 to 5 diverse queries**  
• Each query must reflect at least one value from the input dictionary  
• If **multiple locations** are present, use **only one location per query**  
• If **capacity** is present, mention it in **at least one query** (e.g., “1.75 million units/year”)  
• If **product capacity and unit are present**, they **must be included in the land availability query**  
• Use product, industry, sub-sector, supplies, and equipment as context wherever possible  
• Mention specific supply or equipment types when generating vendor-related queries  
• Do NOT reuse or rephrase anything from the reference examples — they are format-only  
• Keep each query **≤ 15 words**  
• Format your output as a valid Python list of strings

---

📤 OUTPUT FORMAT:

[
  "Query 1?",
  "Query 2?",
  "Query 3?",
  "Query 4?",
  "Query 5?"
]
"""


    formatted_prompt = prompt_template.format(
        dictionary=dict_45
    )

    response = llm.invoke(formatted_prompt)

    import re

    def extract_questions(text):
        # Pattern to match the list of questions in the output section
        pattern = r'\[\n\s*"(.*?)",\n\s*"(.*?)",\n\s*"(.*?)"\n\]'
        
        # Search for the pattern in the text
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            # Extract and return the three questions
            return [match.group(1), match.group(2), match.group(3)]
        else:
            # Fallback pattern if the first one doesn't match
            fallback_pattern = r'"([^"]+\?)"'
            questions = re.findall(fallback_pattern, text)
            return questions if questions else []

    text_2 = str(response)
    questions = extract_questions(text_2)

    return questions


def display_readable_summary(data):
    if data is None:
        print("⚠️ No data provided.")
        return {}

    product_info = data.get('final_updated_product_and_duration_dict', {})
    location_info = data.get('final_location_dict', {})
    supply_info = data.get('final_supply_dict', {})
    industry_info = data.get('final_industry_dict', {})

    if not (product_info or location_info or supply_info or industry_info):
        return "⚠️ No information is available from the document you provided."

    # output = []
    final_dict = {}

    if product_info or industry_info:
        if product_info.get("product"):
            final_dict["product"] = product_info["product"]
        elif industry_info.get("main_industry"):
            final_dict["main_industry"] = industry_info["main_industry"]
        elif industry_info.get("sub-sector"):
          final_dict["sub-sector"] = industry_info["sub-sector"]

        if product_info.get("capacity"):
            # final_dict["product_capacity"] = product_info["capacity"]
            final_dict["product_capacity_1"] = product_info["time period_0"]
        if product_info.get("product_unit"):     
            final_dict["product_unit"] = product_info["product_unit"]
        # if product_info.get("time period"):     
        #     final_dict["time period"] = product_info["time period"]
        if product_info.get("time period_1"):     
            final_dict["product_time_period"] = product_info["time period_1"]

    if location_info:
        final_dict["Location"] = location_info["area_or_city_or_state"]

    if supply_info:
        supplies = supply_info.get('supplies', [])
        equipments = supply_info.get('equipments', [])

        if supplies:
            final_dict["supplies"] = supply_info["supplies"]
      
        if equipments:
            final_dict["equipments"] = supply_info["equipments"]
    

    return final_dict

def batch_check_relevance_llm(chunks: List[str], prompt_template, llm) -> Tuple[List[bool], List[int]]:
    prompts = [
        [
            SystemMessage(content="You are a smart assistant that checks if PDF content is relevant to industrial setup feasibility."),
            HumanMessage(content=prompt_template.format(pdf_text=chunk.strip()[:3000]))
        ]
        for chunk in chunks
    ]

    results = []
    tokens = []
    for message in prompts:
        try:
            response = llm.invoke(message)
            # print("RESPONSE", response)
            token_count = response.response_metadata["token_usage"]["total_tokens"]
            tokens.append(token_count)
            answer = response.content.strip().lower()
            # print("answer", answer)
            if "relevant pdf" in answer and "irrelevant" not in answer:
                results.append(True)
            elif "irrelevant pdf" in answer:
                results.append(False)
            else:
                results.append(False)  # default to irrelevant if LLM gives unexpected output

        except Exception as e:
            # print("Groq Chat error:", e)
            results.append(False)
    # print(results)
    # print(sum(tokens))
    return results, sum(tokens)

def relevant_document_or_not(file_path: str,
                            fallback_sample_size: int = 17):
    for_document_text = AdvancedRAGSystem()

    prompt_template = """
    You are an intelligent assistant that evaluates whether a given PDF document is relevant to a smart industrial setup assistant platform.

    The platform helps entrepreneurs and businesses plan and execute **new industrial projects**. Its features include:

    🔹 Land & Infrastructure Planning  
    🔹 Raw Material Vendor Identification  
    🔹 Labor & Employment Analysis  
    🔹 Required Government Approvals  
    🔹 Incentives and Subsidies  
    🔹 Technical Feasibility & Financial Viability  
    🔹 Supply Chain Strategy  
    🔹 Market Demand Analysis  
    🔹 Vendor Mapping & Evaluation  
    🔹 Environmental or Legal Compliance  

    ---

    ### ✅ Your Task:

    Given the content extracted from a PDF file, decide **if the document is relevant to the platform’s purpose**.

    A **relevant** document might include:  
    - Feasibility studies  
    - Techno-economic viability reports  
    - Market and vendor analysis  
    - Equipment or raw material sourcing plans  
    - Infrastructure & land requirement planning  
    - Policy or incentive-related industrial content

    An **irrelevant** document might include:  
    - Personal ID proofs, tickets, resumes  
    - Bills, invoices, or plain price quotes  
    - Generic instructions or disclaimers  
    - Empty or unreadable documents

    ---

    ### 📥 Extracted PDF Content:
    ---
    {pdf_text}
    ---
    📤

    ### 🧠 Final Judgment:

    Respond ONLY with one of the following:
    - `Relevant PDF`  
    - `Irrelevant PDF`
    """

    try:
        document_text, success_or_not = for_document_text.load_document(file_path)
        # document_text, success_or_not = ingest_and_persist_with_budget_2.load_document(file_path)
        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\success_or_not:- \n{success_or_not}")
        # print(document_text)
        
        # if document_text == []:  # Explicitly check for empty text
        #     print("irrelevant pdf")
        #     return "irrelevant pdf"
        
        # elif document_text == f"Error loading {file_path}: File has not been decrypted":
        #     print(f"Error loading {file_path}: File has not been decrypted")
        #     # return f"Error loading {file_path}: File has not been decrypted"
        #     return document_text

        if success_or_not == "error loading document":
            if document_text == f"Error loading {file_path}: File has not been decrypted":
                return f"Error loading {file_path}: File has not been decrypted"
            elif document_text == []:
                # print("irrelevant pdf")
                return "irrelevant pdf" 
            else:
                # print(document_text)
                return document_text
                
        tokens_2 = {}

        # Combine all pages into one string
        doc_content = "\n\n".join([doc.page_content for doc in document_text])

        # Chunk the text
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        chunks = splitter.split_text(doc_content)

        # Random Sampling
        sampled_chunks = random.sample(chunks, min(fallback_sample_size, len(chunks)))

        # Batched LLM voting
        relevance_flags_sampled, tokens = batch_check_relevance_llm(chunks=sampled_chunks, 
                                                                    llm=for_document_text.llm, 
                                                                    prompt_template=prompt_template)
        relevance_ratio = sum(relevance_flags_sampled) / len(relevance_flags_sampled)
        final_decision = "Relevant PDF" if relevance_ratio >= 0.6 else "Irrelevant PDF"
        tokens_2["RANDOM SAMPLING TOKENS"] = tokens

        # Token count
        total_token_count = tokens

        # Return result
        final_result =  {
            "final_decision": final_decision,
            "decision_source": "LLM-random-vote",
            "chunks_evaluated": len(sampled_chunks),
            "chunks": sampled_chunks,
            "fallback_used": True,
            "confidence": round(relevance_ratio, 2),
            "token_count": total_token_count,
            "relevance_flags_sampled": relevance_flags_sampled}
        
        return final_result

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}"

# def final_call(file_path, vector_store, doctype, status):
# def final_call(vector_store, doctype, status):
#     # relevance_or_not = relevant_document_or_not(file_path)

#     # if relevance_or_not.lower() == "irrelevant pdf":
#         # return {}, "", []

#     # elif relevance_or_not.lower() == "relevant pdf":
#         # a, b, c= process_feasibility_report(file_path=file_path, vector_store=vector_store, doctype=doctype, status=status)
#     a, b, c= process_feasibility_report(vector_store=vector_store, doctype=doctype, status=status)
#     # print("a",a)
#     # print("b",b)
#     # print("c",c)

#     display_statement = """Below is a structured summary of key information extracted from 
#                             the document you provided. Please review the details for accuracy and 
#                             completeness. Based on this information, we have also generated a set of
#                             follow-up queries from which you may choose the most relevant option to 
#                             proceed further."""

#     result = display_readable_summary(c)
#     if result == {}:
#         # return {}, display_statement, []
#         return {}, "", []
#     else:
#         list_of_queries = generate_questions(result)
#         # list_of_queries = generate_questions(final_display_dict)
#         unique_queries = set(list_of_queries)
#         uniques_list_of_queries = list(unique_queries)
        
#         # print("uniques_list_of_queries", uniques_list_of_queries)
#         # print("display statement", display_statement)

#         return result, display_statement, uniques_list_of_queries
        
#     # elif relevance_or_not == f"Error loading {file_path}: File has not been decrypted":
#     #     error_message_for_password_protected_pdf = f"Error loading {file_path}: File has not been decrypted"
#     #     return {}, error_message_for_password_protected_pdf,  []
        
#     # else:
#     #     return {}, relevance_or_not, []

def final_call(file_path, vector_store, doctype, status):
    relevance_or_not = relevant_document_or_not(file_path)
    # print("relevance_or_not",relevance_or_not)
    with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
        file.write(f"\success_or_not:- \n{relevance_or_not}")

    if isinstance(relevance_or_not, dict):
        relevance_check = relevance_or_not["final_decision"]
        token_count = relevance_or_not["final_decision"]
        relevance_flags_sampled = relevance_or_not["relevance_flags_sampled"] 

        # if relevance_or_not.lower() == "irrelevant pdf":
        if relevance_check.lower() == "irrelevant pdf":
            return {}, "", []
        
        elif relevance_check.lower() == "relevant pdf":
            # a, b, c= process_feasibility_report(file_path)
            a, b, c= process_feasibility_report(vector_store=vector_store, doctype=doctype, status=status)
            # print("a",a)
            # print("b",b)
            # print("c",c)

            display_statement = """Below is a structured summary of key information extracted from 
                                    the document you provided. Please review the details for accuracy and 
                                    completeness. Based on this information, we have also generated a set of
                                    follow-up queries from which you may choose the most relevant option to 
                                    proceed further."""

            result = display_readable_summary(c)
            if result == {}:
                # return {}, display_statement, []
                return {}, "", []
            else:
                list_of_queries = generate_questions(result)
                # list_of_queries = generate_questions(final_display_dict)
                unique_queries = set(list_of_queries)
                uniques_list_of_queries = list(unique_queries)
                
                # print("uniques_list_of_queries", uniques_list_of_queries)
                # print("display statement", display_statement)

                return result, display_statement, uniques_list_of_queries
        
        elif relevance_check == f"Error loading {file_path}: File has not been decrypted":
            error_message_for_password_protected_pdf = f"Error loading {file_path}: File has not been decrypted"
            return {}, error_message_for_password_protected_pdf,  []
        
        else:
            return {}, relevance_check, []

    if isinstance(relevance_or_not, str):
        return {},"",[]


def extract_query_list(message):
    try:
        # Ensure the message is a plain string
        message = str(message)

        # Extract the content inside triple backticks
        match = re.search(r"```(?:python)?\n(.*?)\n```", message, re.DOTALL)
        if match:
            list_str = match.group(1)
            result = ast.literal_eval(list_str)
            if isinstance(result, list):
                return result
            else:
                print("Extracted content is not a list.")
        else:
            print("No valid Python code block found.")
    except Exception as e:
        print(f"Error during extraction: {e}")

    return []

def formatting_doc_info_for_user_comaptibility(json, llm_model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5):
   
    llm = ChatGroq(model_name=llm_model, temperature=0.5, api_key = api_key)
    prompt_template = """You are a professional assistant trained to summarize key industrial project information extracted from documents uploaded by users.

   Your job is to read a structured dictionary (in JSON format) containing extracted information about an industrial setup (such as a feasibility report or investment plan), and generate a **single, intuitive, formal paragraph summary**.

   ---

   📘 **Your Output Must**:

   1. **Narrate** the content like a human-written summary — not just list field names and values.
   2. Use professional tone and natural language — make it suitable for showing on a business dashboard or planning portal.
   3. Respect the **context of the keys** — infer and weave relationships where appropriate:
      - E.g., "battery packs with a capacity of 75.0 kWh are to be manufactured in Region Y..."
   4. Use plain English formatting:
   - Do not use Markdown symbols like `**` for bold or any formatting syntax.
   5. Handle values gracefully:
      - Use commas and conjunctions (e.g., “and”, “as well as”) for lists
      - If values are missing or empty, silently skip them
   6. Be flexible to dynamic JSON:
      - Input keys may vary (some may be missing or new keys may appear)
      - Only describe the keys that exist

   ---

   🧾 **Input Dictionary**:

   ```json
   {structured_summary}
   """

    formatted_prompt = prompt_template.format(
        structured_summary=json
    )

    response = llm.invoke(formatted_prompt)
    # print("response",response)
    # print(response.content)

    return response.content

# # def query_classification(file_path, llm_model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5):
def analysing_documents(file_path, vector_store: dict|str, doctype: str, status:bool, llm_model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5):
# def query_classification(status:bool, llm_model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5):

    # vector_store = "tmpasxlzajf__doc_e75c45b6998d0f66"
    # vector_store = "tmpsz2ltr8v__doc_ccc5dd821406e7d6"
    # vector_store = "tmpf5qx51x1__doc_9734791eb66b1f3b"
    # vector_store = "tmpsswqxx7x__doc_b9948d88c025ce62"
    # doctype = "Feasibility_Report"
    # status = True

    # doc_info, questions_statement, questions_list = final_call(file_path=file_path, vector_store=vector_store, doctype=doctype, status=status)
    doc_info, questions_statement, questions_list = final_call(file_path=file_path, vector_store=vector_store, doctype=doctype, status=status)
    # print("doc_info",doc_info)
    # print("question_statement", questions_statement)
    # print("questions_list",questions_list)
    # print(file_path)

    llm = ChatGroq(model_name=llm_model, temperature=temperature, api_key=api_key)

    # for_user = formatting_doc_info_for_user_comaptibility(doc_info)

    prompt_template = """
    You are an intelligent industrial assistant trained to categorize user queries into the correct **industrial planning module**.

    ---

    📦 MODULE DEFINITIONS:

    Each module focuses on specific types of queries:

    **Build from Scratch**  
    • Queries about starting a new industrial unit from the ground up  
    • Focus on: main industry, sub-sector, product, production capacity, build timelines, suitable locations, labor needs, vendor access, approvals, and incentives  

    **Employment**  
    • Queries about labor or workforce availability  
    • Focus on: skilled, semi-skilled, unskilled labor, location-specific employment potential  

    **Vendor Search**  
    • Queries about finding suppliers or equipment vendors  
    • Focus on: raw materials, supply chain proximity, equipment, supplier availability, and location  

    **Incentives**  
    • Queries about financial or policy-based support from the government  
    • Focus on: government schemes, incentive types, industry benefit relevance, and location  

    **Approval**  
    • Queries about permissions, licenses, or regulatory clearances  
    • Focus on: legal requirements, government compliance, permits at local/state/industry levels  

    ---

    📘 MODULE KEYWORDS (reference only – do not rely solely on these):

    • **Build from Scratch**: build, location, start  
    • **Incentives**: incentive, benefit, subsidy, grant  
    • **Approval**: approval, permission, license, clearance  
    • **Employment**: labor, employment, workforce  
    • **Vendor Search**: vendor, supplier, equipment, raw materials  

    ---

    🎯 TASK:

    Given a list of user queries below, classify each query into one of the **five modules** above. Use both the **keywords** and **semantic understanding** based on the module descriptions.

    Each query must be tagged with **exactly one module** from:  
    ["Build from Scratch", "Employment", "Vendor Search", "Incentives", "Approval"]
    ** DO NOT RETURN ANYTHING ELSE LIKE UNDERSTANDING OR ANY EXTRA KEYWORDS OTHER THAN THE OUTPUT **

    ---
 
    🧾 INPUT QUERIES:
    {query_list}

    ---

    ✅ OUTPUT FORMAT:

    Return a valid Python list of dictionaries with the format:
    ```[
    {{"query": "<query_text>", "module": "<correct_module_name>"}},
    ...
    ]```

    Ensure accurate and intelligent classification based on the content and meaning of the query.
    """

    title_generation_prompt = """
    You are a title generation assistant. Your task is to generate a short and meaningful 2 to 3 word title that summarizes the core theme of an industrial project description.

    Guidelines:
    - Focus on the main industry or product being described.
    - Include the product or manufacturing focus if applicable (e.g., "Battery Manufacturing", "Steel Forging", "Textile Production").
    - Do NOT include numbers, locations, or timeframes.
    - Title must be professional, compact, and relevant to the industrial activity.

    Input:
    {feasibility_description}

    Output Title:

    """

    empty_json = {'product': None, 'main_industry': None, 'sub_sector': None, 'product_capacity': None, 'product_unit': None, 'Location': None, 'supplies': None, 'equipments': None}

    if questions_statement == "" and doc_info == {} and questions_list == []:
        print("not password")
        final_json_0 = {
        "structured_summary": empty_json,
        "user_comaptible_structured_summary": None,
        "summary_display_statement": None,
        "classified_queries": None,
        "feasibility_title": None,
        "error_message": """⚠️ The uploaded document does not contain relevant industrial setup information.
                            Please upload a feasibility report with project details, land, labor, vendors, or approvals.""",
        "relevance": "irrelevant document"
        }
        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nSTATUS👌:- /n{final_json_0}")
        return final_json_0
        # return empty_json

    elif doc_info == {} and questions_list == [] and questions_statement == f"Error loading {file_path}: File has not been decrypted":
        print("password")
        # error_message = f"Error loading {file_path}: File has not been decrypted"
        error_message = questions_statement
        final_json_0 = {
        "structured_summary": empty_json,
        "user_comaptible_structured_summary": None,
        "summary_display_statement": None,
        "classified_queries": None,
        "feasibility_title": None,
        "error_message": error_message,
        "user_friendly_error_message": "The uploaded document is password-protected and could not be read. Please upload an unprotected version of the file to proceed with feasibility analysis.",
        "relevance": "irrelevant document"
        }

        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nSTATUS👌:- /n{final_json_0}")

        return final_json_0
    
    elif doc_info == {} and questions_list == [] and (questions_statement != f"Error loading {file_path}: File has not been decrypted" and questions_statement != ""):
        print("another_error")
        error_message = questions_statement
        final_json_0 = {
        "structured_summary": empty_json,
        "user_comaptible_structured_summary": None,
        "summary_display_statement": None,
        "classified_queries": None,
        "feasibility_title": None,
        "error_message": error_message,
        "user_friendly_error_message": "The document could not be processed due to a technical issue. Please check if the file is corrupted or in an unsupported format, and try uploading again.",
        "relevance": "irrelevant document"
        }
        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nSTATUS👌:- /n{final_json_0}")
 
        return final_json_0

    else:

        for_user = formatting_doc_info_for_user_comaptibility(doc_info)

        formatted_prompt = prompt_template.format(
            query_list=questions_list
        )

        formatted_prompt_1 = title_generation_prompt.format(
                feasibility_description=for_user
        )

        response = llm.invoke(formatted_prompt)
        # print("response",response)
        # str_response = str(response)
        str_response = response.content
        # print("str_response",str_response)
        # Look for the list between triple backticks (```python\n ... \n```)

        response_1 = llm.invoke(formatted_prompt_1)
        # print("title for feasibility", response_1)

        extracting_query = extract_query_list(str_response)
        # print("etracting_query",extracting_query)

        final_json_0 = {
        "structured_summary": doc_info,
        "user_comaptible_structured_summary": for_user,
        "summary_display_statement": questions_statement,
        "classified_queries": extracting_query,
        "feasibility_title": response_1.content,
        "error_message": None,
        "relevance": "relevant document"
        }
        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nSTATUS👌:- /n{final_json_0}")
        return final_json_0

def query_classification(file_path, feasibility_id, vector_id_field, data_source_field, llm_model=llm_maverik, temperature=0.5):

    # doctype = FEAS_DOCTYPE
    doc_name = feasibility_id
    with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nID:- /n{feasibility_id}")

    mko_2, status = ensure_vector_and_update_record( 
                doctype = FEAS_DOCTYPE, 
                doc_name = doc_name,
                vector_id_field=vector_id_field,
                data_source_field=data_source_field)
    with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\nSTATUS👌:- /n{mko_2}")

    try:
        if status:
            if isinstance(mko_2, str):
                final_json = analysing_documents(file_path=file_path, vector_store=mko_2, doctype=FEAS_DOCTYPE, status=status)
            elif isinstance(mko_2, dict):
                final_json = analysing_documents(file_path=file_path, vector_store=mko_2["collection_name"], doctype=FEAS_DOCTYPE, status=status)
            with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
                file.write(f"\nfinal_json:- \n{final_json}")
            return final_json
        else:
            empty_json = {'product': None, 'main_industry': None, 'sub_sector': None, 'product_capacity': None, 'product_unit': None, 'Location': None, 'supplies': None, 'equipments': None}

            final_json = {
                "structured_summary": empty_json,
                "user_comaptible_structured_summary": None,
                "summary_display_statement": None,
                "classified_queries": None,
                "feasibility_title": None,
                "error_message": "check for the budget exceeding problem initially.",
                "user_friendly_error_message": "Something went wrong with the system",
                }
            with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
                file.write(f"\nfinal_json:- \n{final_json}")
            return final_json
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        with open("/home/marsaiae/frappe-bench/apps/frontend_app/frontend_app/Ai_module/Feasibility_study/testlog.txt", "a") as file:
            file.write(f"\n*** EXCEPTION ***\n{tb}\n")
        raise


# final = query_classification()
#                         # doctype=FEAS_DOCTYPE,
#                         # doc_name="Report-13-08-25 -2045")
#                         # doc_name="Report-28-10-25 -2427")
#                         # doc_name="Report-14-08-25 -2054")
#                         # doc_name="Report-14-10-25 -2425")
#                         # doc_name="Report-13-08-25 -2045")
#                         # doc_name="Report-08-08-25 -2030")
#                         # doc_name="Report-15-10-25 -2139")
#                         # doc_name="Report-03-10-25 -2116")
#                         # doc_name="Report-14-08-25 -2050")
#                         # doc_name="Report-17-11-25 -2274")

# print(final)
# tmpxcfgv3kj__doc_b9948d88c025ce62
# tmpsz2ltr8v__doc_ccc5dd821406e7d6
# qwert_34 = query_classification(status=True)
# tmpsf2ruftu__doc_1703688dc9a5de44


















































































