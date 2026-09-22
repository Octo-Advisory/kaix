import warnings
import re
import copy
import pandas as pd
from typing import List, Dict, Tuple, Union, Any, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from kaix.Ai_module.Query_Classification_And_Analysis import *
from langchain.schema import HumanMessage, AIMessage
from rapidfuzz import process, fuzz
import spacy
import frappe
from kaix.Management_Class.Redis_management.Redis_chat import save_chat,get_chat,save_state,get_state
from kaix.Management_Class.helpers.utility import update_llm_token
# from frontend_app.Management_Class.Ai_management.AI import *
from kaix.Ai_module.parsers import parse_llm_response

warnings.filterwarnings("ignore")


def fetch_query_results(query):
    """
    Executes a given SQL query and returns the results.
    
    :param query: SQL query to execute
    :return: List of tuples containing query results
    """
    try:
        results = frappe.db.sql(query)
        return results

    except:
        return None

# Define a function to refine the query using history for vendor search
def refine_query_with_history_for_vendor(history, latest_query, llm):
    """
    Refine and structure the user's vendor search query using conversational history as reference 
    while ensuring that only explicitly mentioned details (location, industry, supply) are considered.

    Parameters:
    - history (List[str]): The chat history for context, but not for inference.
    - latest_query (str): The most recent user query that needs refinement.
    - llm: The language model instance for query refinement.

    Returns:
    - str: A clean, standalone, and contextually accurate reformulated vendor search query.
    """

    # Define retriever prompt  
    retriever_prompt_template = """  
    Given the chat history and the latest user input, reformulate a standalone query that maintains the intent and structure of the latest user input.  
    Use the AI's messages for context only to understand the user's intent better, but DO NOT take examples, assumptions, or suggestions from AI responses as the user's actual input unless the user explicitly agrees or repeats them.  

    Instructions:
    1. Preserve the Original Structure of the User Input.  
        - If the user’s latest input is a statement, the reformulated query must remain a statement.  
        - If the user’s latest input is a question, the reformulated query must remain a question.  

    2. Strictly Extract Information Only from the Latest User Input.  
        - Do NOT infer, assume, or carry forward any Industry (Main-Industry, Sub-Sector, Segment), Location (Area, City, State), or Supply Details (Raw Material, Service, Equipment) from past conversations unless explicitly mentioned in the latest user input.  
        - If the user does not mention any industry, location, or supply information in the latest query, do NOT include any from past messages.  

    3. Chat History is Only for Reference.  
        - Use the chat history only to understand the flow of the conversation but not to infer missing details.  
        - If the user explicitly refers to a past message (e.g., “same as before” or “like I mentioned earlier”), then and only then consider details from history.  

    4. Handling Multiple Information Types in Vendor Search.  
        - The vendor search query may include any of the following details:  
        - Industry Details: Main-Industry, Sub-Sector, Segment.  
        - Location Details: Area, City, State.  
        - Supply Details: Raw Material, Equipment, or Service.  
        - If the user mentions multiple details, include them exactly as they appear in the latest query.

    5. Do NOT Modify the Intent of the Query.  
        - The reformulated query must retain the user’s original intent without additional modifications.  
        - Do NOT alter the meaning of the query, even if restructuring is required for clarity.  

    6. No Explanations, Reasoning, or Justifications.  
        - The output must be a clean and direct reformulation of the user’s intent without unnecessary elaboration.  
        - Do NOT add any reasons like "Based on your past conversation..."  

    ---

    Inputs:
    - Chat History (for reference only):  
    {history}  

    - Latest User Query:  
    {latest_query}  

    Reformulated Standalone Query:  
    """

    # Create prompt template
    prompt = PromptTemplate(
        input_variables=["history", "latest_query"],
        template=retriever_prompt_template
    )

    # Invoke the LLM chain
    chain = prompt | llm
    refined_query = chain.invoke({"history": "\n".join(history), "latest_query": latest_query})
    update_llm_token(refined_query)
    refined_text = refined_query.content.strip()

    # Extract the reformulated standalone query
    match = re.search(r'reformulated standalone query:\s*(?:"(.*?)"|\'(.*?)\'|(.*))$', refined_text, re.IGNORECASE)
    candidate = next((g for g in match.groups() if g), refined_text) if match else refined_text

    # P1-5 #2/#3: validate at the boundary; one plain-text corrective retry;
    # typed RefinedQueryFailure logged on unrecoverable failure.
    from kaix.Ai_module.query_refinement.schemas import RefinedQuery as _RQ, RefinedQueryFailure as _RQF
    from pydantic import ValidationError as _RQ_VE
    try:
        return _RQ(refined_query=candidate).refined_query
    except _RQ_VE as _first_err:
        try:
            _retry_raw = llm.invoke(
                "Return ONLY a single standalone reformulated query as plain text. "
                "No JSON, no markdown, no quotes, no headers, no explanations, "
                "no paragraph breaks — one single line only.\n\n"
                f"Your previous answer was invalid: {_first_err}\n"
                f"Previous answer:\n{candidate}\n\nOriginal request:\n{latest_query}"
            ).content.strip()
            _m = re.search(r'reformulated standalone query:\s*(?:"(.*?)"|\'(.*?)\'|(.*))$', _retry_raw, re.IGNORECASE)
            _retry_candidate = next((g for g in _m.groups() if g), _retry_raw) if _m else _retry_raw
            return _RQ(refined_query=_retry_candidate).refined_query
        except Exception as _retry_err:
            _f = _RQF(error=str(_retry_err), raw_output=refined_text, refined_query=candidate)
            frappe.log_error(f"{_f.error} | raw: {_f.raw_output}", "refine_query_with_history parse failure")
            return candidate

def classify_vendor_query(query: str, llm) -> dict:
    """
    Classifies a user's vendor search query into one of seven defined categories based on contextual understanding.

    Categories:
        1. Vendor Search for location without industry and supply details
        2. Vendor Search for industry without location details
        3. Vendor Search for supply without location details
        4. Vendor Search for industry with location details
        5. Vendor Search for supply with location details
        6. Other Intent
        7. Negative Intent

    Args:
        query (str): The user's input query.
        llm: A language model instance that supports the 'invoke' method, used to classify the query based on a prompt.

    Returns:
        dict: A dictionary containing:
            - 'raw_prompt': The prompt sent to the language model.
            - 'classification_number': An integer from 1 to 7 representing the classification.
            - 'classification_category': A descriptive string corresponding to the classification number.

    Raises:
        ValueError: If the language model response does not contain a valid classification number (1–7).
    """

    # Define the category mapping
    category_mapping = {
        1: "Vendor Search for location without industry and supply details",
        2: "Vendor Search for industry without location details",
        3: "Vendor Search for supply without location details",
        4: "Vendor Search for industry with location details",
        5: "Vendor Search for supply with location details",
        6: "Other Intent",
        7: "Negatively Intended Query",
    }

    # Define the raw prompt string
    raw_prompt = """
    You are an expert in analyzing user queries related to vendor searches. Your task is to classify the user's intention into one of the following categories:

    1. Vendor Search for a Location without Industry or Supply Details  
        - The user only mentions a location but does not specify any industry or supply details.  
        - Example: "I need vendor details in Gujarat."  

    2. Vendor Search for an Industry without a Location  
        - The user mentions an industry, sector, or product but does not specify a location or specific supply details.  
        - Example: "Who are the top vendors for pharmaceuticals?"  

    3. Vendor Search for a Specific Supply without a Location  
        - The user mentions a specific supply (raw material, equipment, or service) but does not provide a location.  
        - Example: "I need a supplier for industrial chemicals."  

    4. Vendor Search for an Industry with a Location  
        - The user mentions both an industry and a location, but does not mention a specific supply.  
        - Example: "Looking for vendors in the textile industry in Surat."  

    5. Vendor Search for a Specific Supply with a Location  
        - The user mentions both a supply and a location.  
        - Example: "Need API suppliers in Gujarat."  

    6. Other Intent  
        - The query is unrelated to vendor search and shows intent toward other topics such as employment, approvals, incentives, or setting up an industry.  
        - Or the query is about general lifestyle, tourism, education (non-industry), politics, etc.  
        - Or vendor intent is negative, but at least one other factor is mentioned positively.

    7. Negative Intent  
        - The query clearly expresses a negative intent toward vendors AND:
        - Either no other topics are mentioned at all, OR
        - All other mentioned topics (employment, approvals, incentives, industry building) are also expressed negatively.

    ---

    Important Classification Guidelines:

    1️. Industry vs. Supply Search - Sentence Structure Matters  
    - If the sentence structure places an industry or product in focus, classify it as Industry Search.  
    - If the sentence structure places a material/service/equipment in focus, classify it as Supply Search.  
    - Example:  
    - "Need vendors for steel manufacturing." → Industry Search  
    - "Need stainless steel for steel manufacturing." → Supply Search  

    2️. Handling Queries That Mention Both a Product & Supply  
    - If a specific supply is explicitly mentioned, it overrides the product mention → Supply Search.  
    - If the product is mentioned without supply details, it means they need all supplies for production → Industry Search.  
    - Example:  
    - "I need rubber for making tires." → Supply Search  
    - "I need vendors for tire production." → Industry Search  

    3️. Handling Raw Materials, Equipment, and Services  
    - If a query says "raw materials for production", classify it as Industry Search.  
    - If a query mentions a specific raw material, classify it as Supply Search.  
    - If a query mentions equipment or services, classify it as Supply Search.  
    - Example:  
    - "I need raw materials for plastic production." → Industry Search  
    - "I need polymer granules for plastic production." → Supply Search  
    - "Where can I find machinery for the pharmaceutical sector?" → Supply Search  

    4️. Ensure Robust Classification for Vague Queries  
    - Even if the query is vague, incomplete, or not in full sentences, attempt to classify it accurately.  
    - Do NOT assume a query is Supply Search by default—always check context.

    ---

    Vendor Classification Rules:

    Rule 1: Positive Vendor or Specific Supply Intent  
    - If vendor-related intent is positive (user wants to find vendors or suppliers or specific supplies), classify into one of Class 1 to 5 depending on the presence of location, industry, or supply details.  
    - This classification must take precedence regardless of mentions of other topics.

    Rule 2: Vendor or Specific Supply Mentioned Negatively  
    - If the user clearly expresses negative intent about vendors or supplies, then:  
    - If NO other topics are present → Class 7  
    - If all other topics are also negatively mentioned → Class 7  
    - If ANY one other topic is mentioned positively → Class 6

    Rule 3: Vendor or Specific Supply Not Mentioned  
    - If vendors or specific supplies are not mentioned at all:  
    - If all other mentioned topics (employment, approvals, incentives, industry-building) are expressed negatively → Class 7  
    - If any one is expressed positively → Class 6

    Contextual Understanding:
    - Do not classify based solely on keywords like "vendor", "supplier", or "approval".
    - Understand contextually similar terms:
    - "dealers", "traders", "sourcing" may imply vendors.
    - "permissions", "licenses" → approvals.
    - "jobs", "workforce", "manpower" → employment.
    - "setup", "launch", "start" → industry building.
    - Use full context and phrasing of the query to decide the intent.

    Other Topic Definition:
    - These refer to the other business-related categories:
    - Approvals
    - Employment
    - Incentives
    - Building an industry from scratch

    Additional Understanding Requirement:
    - Do not rely solely on specific keywords like “approvals,” “vendors,” “employment,” “incentives,” or “building industry from scratch.”
    - Always analyze the full context of the query to determine whether these intents are present — even if users use alternative phrasing or synonyms.
    - Examples:
        - “Permissions,” “licenses,” “NOCs,” or “clearances” should be interpreted as approval-related.
        - “Suppliers,” “distributors,” or “raw material sources” may indicate vendor search.
        - “Jobs,” “workforce,” “manpower,” or “recruitment” may imply employment intent.
        - “Subsidies,” “tax breaks,” “grants,” or “financial support” may suggest incentives.
        - “Starting operations,” “setting up a factory,” “establishing infrastructure,” or “launching a new unit” may indicate building industry from scratch.
    - Understand user intent even if the sentence is vague, mixed, or includes implied meanings rather than explicit phrases.

    ---

    Final Output Instructions:
    - Classify the query into one of the categories (1 to 7).
    - Provide the classification number ONLY.
    - Do NOT include explanations or summaries.

    Query:  
    {query}

    Output:  
    (Provide only one classification number)
    """


    # Create a PromptTemplate for chaining
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template=raw_prompt,
    )

    # Use the prompt in a chain
    chain = prompt_template | llm
    # Run the chain and capture the response
    response = chain.invoke({"query": query})

    # Use regex to extract a valid classification number
    match = re.search(r"^\s*([1-7])\s*$", response.content.strip())
    if match:
        classification_number = int(match.group(1))
        classification_category = category_mapping[classification_number]
        # NEW PYDANTIC LAYER
        # Wraps the extracted integer in VendorClassification.
        # The regex above already enforces 1-7, so validation should
        # never reject in practice. The guard catches any future regex
        # widening that would silently produce out-of-range values.
        try:
            from kaix.Ai_module.vendor_query.schemas import (
                VendorClassification,
            )
            from pydantic import ValidationError as _VE
            try:
                VendorClassification(classification_number=classification_number)
            except _VE as _ve:
                frappe.log_error(
                    f"VendorClassification rejected {classification_number}: {_ve}",
                    "classify_vendor_query pydantic"
                )
        except Exception as _e:
            frappe.log_error(str(_e), "classify_vendor_query pydantic")

        return {
            "raw_prompt": raw_prompt,
            "classification_number": classification_number,
            "classification_category": classification_category,
        }
    else:
        # P1-5: regex did not match — the LLM returned junk (a word, prose,
        # multiple/out-of-range digits, or empty). Instead of raising
        # ValueError, retry once with a corrective prompt and, if that also
        # fails, return a typed VendorClassificationFailure envelope so the
        # caller can degrade gracefully rather than crashing.
        try:
            from kaix.Ai_module.vendor_query.schemas import (
                VendorClassification,
                VendorClassificationFailure,
            )
            _retry_prompt = (
                "Classify the user's vendor-related query into exactly one "
                "category and return ONLY a JSON object of the form "
                '{"classification_number": N}, where N is one integer:\n'
                "1 = vendor search, location only (no industry/supply)\n"
                "2 = vendor search, industry only (no location)\n"
                "3 = vendor search, supply only (no location)\n"
                "4 = vendor search, industry + location\n"
                "5 = vendor search, supply + location\n"
                "6 = other intent\n"
                "7 = negatively intended query\n"
                "No prose, no words, no extra keys.\n\n"
                f"Query: {query}"
            )
            validated = parse_llm_response(
                raw=response.content.strip(),
                model_class=VendorClassification,
                llm_client=llm,
                prompt=_retry_prompt,
            )
            if isinstance(validated, VendorClassification):
                classification_number = validated.classification_number
                return {
                    "raw_prompt": raw_prompt,
                    "classification_number": classification_number,
                    "classification_category": category_mapping[classification_number],
                }
            # Retry also failed — normalise to the typed failure envelope.
            if isinstance(validated, VendorClassificationFailure):
                failure = validated
            elif isinstance(validated, dict):
                failure = VendorClassificationFailure(
                    error=str(validated.get("error", "unparseable LLM output")),
                    raw_output=str(validated.get("raw_output", response.content)),
                )
            else:
                failure = VendorClassificationFailure(
                    error="parse_llm_response returned an unexpected type",
                    raw_output=str(response.content),
                )
            frappe.log_error(
                f"{failure.error} | raw: {failure.raw_output}",
                "classify_vendor_query failure",
            )
            return failure
        except Exception as _e:
            # Never crash the request path: log and degrade to the envelope.
            frappe.log_error(str(_e), "classify_vendor_query pydantic")
            from kaix.Ai_module.vendor_query.schemas import (
                VendorClassificationFailure,
            )
            return VendorClassificationFailure(
                error=str(_e),
                raw_output=str(getattr(response, "content", response)),
            )
def extract_location_from_vendor_query(user_input: str, llm) -> Dict[str, str]:
    """
    Extract the location mentioned in the user query and classify it into Area, City, State, or Country.
    Additionally, determine if the extracted location is within India.

    Parameters:
        user_input (str): The user-provided query.
        llm: The language model instance to use for processing.

    Returns:
        Dict[str, str]: A dictionary containing the extracted location, classification, and country check.
    """

    # Define the updated prompt
    prompt_template = """
    You are an expert in analyzing user queries and accurately extracting location information.  
    Your task is to identify and extract the most relevant location from the user query and classify it into one of the following categories:
    - Area: A specific sub-region or locality within a city.
    - City: A well-known city.
    - State: A state or province.
    - Country: A country.

    Key Extraction Rules:

    1. Extract the Most Relevant Location Based on Context:
    - If the query contains multiple locations, analyze the intent and extract only the most relevant.
    - Ignore locations mentioned for personal reference or additional context (e.g., "I live in X but want to know about Y" → Extract only Y).
    - Even if multiple locations are mentioned, extract only one that best aligns with the user's intent.

    2. Do NOT Auto-Correct or Modify Spelling Unnecessarily:
    - If the location name is extracted but uncertain, keep it as it is instead of attempting a correction.
    - Some locations have similar names, and automatic correction can introduce errors (e.g., "Rinali" should not become "Ranoli").
    - Only apply spelling corrections if the misspelling is obvious and widely known.

    3. Preserve Abbreviations & Contextual Terms:
    - If a location includes an abbreviation (e.g., "SEZ", "GIDC", "MIDC"), always retain it in the extracted name.
    - Examples:
        - "Dahej SEZ" → Extract as "Dahej SEZ" (not just "Dahej").
        - "Sanand GIDC" → Extract as "Sanand GIDC" (not just "Sanand").
    - Do not remove or alter these abbreviations.

    4. Classify the Location Correctly (Default to Area if Unclear):
    - Based on sentence structure and logical context, determine if the extracted location is an Area, City, State, or Country.
    - Example Classifications:
        - "Looking for vendors in Andheri" → Area: Andheri
        - "Need approvals in Ahmedabad" → City: Ahmedabad
        - "What are the rules for businesses in Maharashtra?" → State: Maharashtra
        - "What are the import duties in Germany?" → Country: Germany
    - If the classification is unclear, default to `"Area"` instead of making incorrect assumptions.

    5. Check if the Location is from India:
    - If the extracted location belongs to India, set `"From_India": "Yes"`.
    - If the location is outside India, set `"From_India": "No"`.
    - Assume that most locations mentioned will be from India.

    6. Ensure the Official Location Name is Used:
    - If the location has multiple variants, always return the official name of the location instead of alternative or outdated names.
    - Some common examples:
        - "Bombay" → "Mumbai"
        - "Baroda" → "Vadodara"
        - "Kashi" → "Varanasi"
        - "Calcutta" → "Kolkata"
        - "Bangalore" → "Bengaluru"
        - "Pondicherry" → "Puducherry"
    - Ensure all locations are recognized and standardized to their official designation.
    - Do NOT change names that are already valid and contextually correct.

    7. Only Return a Location if One is Mentioned:
    - If no location is found in the query, return `"None"` as the value.

    8. No Additional Explanations:
    - The output must only contain the extracted location, classification, and country check.
    - Do NOT provide reasoning, context, or explanations.

    User Query:
    {query}

    Output Format:
    Provide the extracted location, classification, and India check in the following JSON format:
    {{
        "Extracted_Location": "<Location or 'None'>",
        "Classification": "<Area | City | State | Country | None>",
        "From_India": "<Yes | No>"
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

    # Extract the response content
    extracted_data = response.content.strip()

    from kaix.Ai_module.vendor_query.schemas import (
        VendorLocationExtraction,
        VendorLocationExtractionFailure,
    )
    _retry_prompt = (
        "Extract location info from the user query and return ONLY a "
        "JSON object with these three string keys: "
        '{"Extracted_Location": "<location text, or None if none>", '
        '"Classification": "<one of: Area, City, State, Country, None>", '
        '"From_India": "<Yes or No>"}. '
        "No prose, no markdown fences, no extra keys.\n\n"
        f'User query: "{user_input}"'
    )
    _result = parse_llm_response(
        raw=extracted_data,
        model_class=VendorLocationExtraction,
        llm_client=llm,
        prompt=_retry_prompt,
    )
    if isinstance(_result, VendorLocationExtraction):
        return {
            "Extracted_Location": _result.Extracted_Location,
            "Classification": _result.Classification,
            "From_India": _result.From_India,
        }
    # P1-5: parse failed even after one corrective retry. Return the TYPED
    # envelope — do NOT fall back to the wrong-but-plausible default this
    # schema exists to eliminate — so callers can distinguish a real
    # "no location" answer from a parse fail.
    if isinstance(_result, VendorLocationExtractionFailure):
        failure = _result
    elif isinstance(_result, dict):
        failure = VendorLocationExtractionFailure(
            error=str(_result.get("error", "unparseable LLM output")),
            raw_output=str(_result.get("raw_output", extracted_data)),
        )
    else:
        failure = VendorLocationExtractionFailure(
            error="parse_llm_response returned an unexpected type",
            raw_output=str(extracted_data),
        )
    frappe.log_error(
        f"{failure.error} | raw: {failure.raw_output}",
        "extract_location_from_vendor_query failure",
    )
    return failure

def get_best_supply_match(extracted_supplies: List[str], available_supplies: List[str], fuzzy_threshold: int = 95, spacy_threshold: float = 0.80) -> List[str]:
    """
    Finds the best matches for extracted supplies using both SpaCy similarity and fuzzy matching.

    Parameters:
        extracted_supplies (List[str]): List of extracted supplies from user query.
        available_supplies (List[str]): List of known available supplies.
        fuzzy_threshold (int): Minimum score for fuzzy matching.
        spacy_threshold (float): Minimum similarity threshold for SpaCy matching.

    Returns:
        List[str]: List of best-matching supplies from available choices.
    """
    validated_supplies = []
    
    for supply in extracted_supplies:
        if not supply.strip():
            validated_supplies.append("Not Available in List")
            continue

        # Fuzzy Matching
        best_fuzzy_match = process.extractOne(supply, available_supplies, scorer=fuzz.ratio)
        fuzzy_match_name, fuzzy_score = best_fuzzy_match[:2] if best_fuzzy_match else (None, 0)

        # SpaCy Similarity Matching
        supply_doc = nlp(supply.lower())
        spacy_match_name = None
        best_spacy_score = 0

        for available_supply in available_supplies:
            available_doc = nlp(available_supply.lower())
            similarity_score = supply_doc.similarity(available_doc)

            if similarity_score > best_spacy_score:
                best_spacy_score = similarity_score
                spacy_match_name = available_supply

        # Use the best matching method
        if best_spacy_score >= spacy_threshold:
            validated_supplies.append(spacy_match_name)
        # elif fuzzy_score >= fuzzy_threshold:
        #     validated_supplies.append(fuzzy_match_name)
        else:
            validated_supplies.append("Not Available in List")

    return validated_supplies

def extract_supplies_from_query(user_input: str, available_supplies: List[str], llm) -> Dict[str, List[str]]:
    """
    Extracts multiple supplies mentioned in the user query and validates them against a provided list of available supplies.

    Parameters:
        user_input (str): The user-provided query.
        available_supplies (List[str]): List of all available supplies.
        llm: The language model instance to use for processing.

    Returns:
        Dict[str, List[str]]: A dictionary containing lists of extracted and validated supplies.
    """

    # Define the prompt
    prompt_template = """
    You are an expert in analyzing user queries and accurately extracting supply-related information.  
    Your task is to identify and extract all relevant supplies (raw materials, equipment, or services) mentioned in the user's query with the highest level of precision.  

    ---
    Key Extraction Rules:
    
    1. Extract All Relevant Supplies as Comma-Separated Values:
    - If multiple supplies are mentioned, extract them as a comma-separated list.
    - Ignore supplies that are mentioned only for example or comparison, unless they are part of the actual request.
    - Example:  
        - Query: "I need vendors for chemicals, machinery, and glass vials."  
        - Extracted Output: `"Chemicals, Machinery, Glass Vials"`

    2. Correct Spelling Mistakes & Typing Errors:
    - Ensure high accuracy in recognizing supply names even if the user makes typos, spelling mistakes, or keyboard proximity errors.
    - Example:
        - Query: "I need vensors for steeel plates and cermic coatings."
        - Extracted Output: `"Steel Plates, Ceramic Coatings"`
    
    3. Preserve Abbreviations & Standard Industry Names:
    - If a supply has a widely used abbreviation, extract both full name and abbreviation together.
    - Example:
        - Query: "Need suppliers for HDPE and industrial ethanol."
        - Extracted Output: `"High-Density Polyethylene (HDPE), Industrial Ethanol"`

    4. Use Industry-Standard Naming Conventions:
    - If a supply is mentioned using a lesser-known name, return the widely used industry name instead.
    - Example:
        - Query: "Suppliers for ethen and ethenol."
        - Extracted Output: `"Ethylene, Ethanol"`

    5. Do NOT Modify Correctly Spelled Supplies:
    - If a supply is already correct, retain its exact name.
    - Do NOT autocorrect or reword names unless an industry-standard term exists.

    6. Retain Contextually Relevant Abbreviations & Short Forms:
    - If an abbreviation is commonly used in the industry, extract both full name and abbreviation together.
    - Example:
        - Query: "Looking for PET resin suppliers."
        - Extracted Output: `"Polyethylene Terephthalate (PET)"`

    7. Ensure Consistent Extraction Format:
    - The extracted supplies must always be comma-separated.
    - If no supplies are found, return an empty list.

    ---
    User Query:
    {query}

    Output Format:
    Provide only the extracted supplies in the following JSON format:
    {{
        "Supplies": "<Comma-Separated Extracted Supplies or Empty String>"
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

    # Extract supplies from the model response
    supplies_match = re.search(r'"Supplies":\s*"([^"]*)"', response.content.strip())
    
    # Convert the extracted text into a list, ensuring comma separation
    extracted_supplies = (
        [s.strip() for s in supplies_match.group(1).split(",") if s.strip()] if supplies_match else []
    )

    # NEW PYDANTIC LAYER — SANITY CHECK ONLY
    # VendorSuppliesExtraction has a mode="before" validator that does
    # CSV string → clean list[str] coercion. We use it as a sanity check
    # against the manual CSV split above. If Pydantic produces a
    # different list, log the divergence but DO NOT override
    # extracted_supplies — downstream get_best_supply_match() must run
    # on the original split, and Validated_Supplies in the return dict
    # must come from that path (not from this layer).
    try:
        from kaix.Ai_module.vendor_query.schemas import (
            VendorSuppliesExtraction,
        )
        if supplies_match:
            _csv = supplies_match.group(1)
            _validated = VendorSuppliesExtraction(Supplies=_csv)
            _pydantic_supplies = list(_validated.Supplies)
            if _pydantic_supplies != extracted_supplies:
                frappe.log_error(
                    f"Supplies divergence — CSV split: {extracted_supplies}, "
                    f"Pydantic: {_pydantic_supplies}",
                    "extract_supplies_from_query pydantic"
                )
    except Exception as _e:
        frappe.log_error(str(_e), "extract_supplies_from_query pydantic")
    # P1-5: regex found no "Supplies" key at all — the LLM didn't return
    # the expected shape (omitted key, markdown-fenced, or a nested dict).
    # This is a genuine parse failure (distinct from a valid empty-supplies
    # answer). Retry once; on success adopt the recovered supplies, on
    # unrecoverable failure return the TYPED envelope — do NOT collapse to
    # the empty-supplies success shape, which is indistinguishable from a
    # real "no supplies" answer — so callers can tell a parse fail apart.
    if supplies_match is None:
        try:
            from kaix.Ai_module.vendor_query.schemas import (
                VendorSuppliesExtraction,
                VendorSuppliesExtractionFailure,
            )
            _retry_prompt = (
                'Return ONLY a JSON object of the form '
                '{"Supplies": "<comma-separated supplies, or empty string>"}. '
                "No prose, no markdown fences, no nested objects, no extra keys."
            )
            _recovered = parse_llm_response(
                raw=response.content.strip(),
                model_class=VendorSuppliesExtraction,
                llm_client=llm,
                prompt=_retry_prompt,
            )
            if isinstance(_recovered, VendorSuppliesExtraction):
                extracted_supplies = list(_recovered.Supplies)
            else:
                if isinstance(_recovered, VendorSuppliesExtractionFailure):
                    failure = _recovered
                elif isinstance(_recovered, dict):
                    failure = VendorSuppliesExtractionFailure(
                        error=str(_recovered.get("error", "unparseable LLM output")),
                        raw_output=str(_recovered.get("raw_output", response.content)),
                    )
                else:
                    failure = VendorSuppliesExtractionFailure(
                        error="parse_llm_response returned an unexpected type",
                        raw_output=str(response.content),
                    )
                frappe.log_error(
                    f"{failure.error} | raw: {failure.raw_output}",
                    "extract_supplies_from_query failure",
                )
                return failure
        except Exception as _e:
            # Never crash the request path: log and degrade to the envelope.
            frappe.log_error(str(_e), "extract_supplies_from_query pydantic")
            from kaix.Ai_module.vendor_query.schemas import (
                VendorSuppliesExtractionFailure,
            )
            return VendorSuppliesExtractionFailure(
                error=str(_e),
                raw_output=str(getattr(response, "content", response)),
            )

    # Return immediately if no supplies were extracted
    if not extracted_supplies:
        return {"Extracted_Supplies": [], "Validated_Supplies": []}


    # Validate using fuzzy matching
    validated_supplies = get_best_supply_match(extracted_supplies, available_supplies)

    # Return extracted and validated supplies
    return {
        "Extracted_Supplies": extracted_supplies,
        "Validated_Supplies": validated_supplies
    }

def generate_dynamic_message_for_vendor(chat_history_for_context: List[dict], static_follow_up: str, user_message: str, llm) -> str:
    """
    Generate a dynamic follow-up message using LLM based on the latest context and static follow-up requirement for Vendor-related queries.

    Parameters:
        chat_history_for_context (List[dict]): The list of conversation history with user and AI messages.
        static_follow_up (str): The static follow-up message to send to the user.
        llm: The language model instance.

    Returns:
        str: The dynamically generated follow-up message.
    """

    # Prepare the conversation history context
    recent_history = "\n".join(chat_history_for_context)  

    # Define the prompt
    prompt = """
    You are a highly skilled assistant specializing in creating professional, engaging, and contextually relevant messages.
    Your goal is to craft a polished follow-up message that seamlessly incorporates the provided static follow-up message while aligning with the tone and context of the recent conversation.

    Key Instructions  
    - The static follow-up message is only a reference.  
    - Do NOT copy it word-for-word—instead, use it as guidance to create a well-crafted, natural response that follows all instructions.  
    - Ignore placeholders like "None" or "Not Available in List"—they should NEVER be included in the final response.  
    - Do NOT reference any industry (Main-Industry, Sub-Sector, Segment), location (Area, City, State), or supply (Raw Material, Equipment, Service) details from chat history or user messages unless explicitly mentioned in the static follow-up message.  
    - In no circumstances should the model respond to off-topic queries. If a query is unrelated, handle it according to the specified instructions.  

    STRICT RULE:  
    - Only vendor- and supply-related words should appear in the response, even if the user query mentions additional topics.  
    - If the user query includes employment, approvals, incentives, or any other unrelated terms, completely exclude them from the response.  
    - Regardless of what else is mentioned, vendor- and supply-related words must always appear in the response.  

    Example Correction:  
    - User Query: "I want to search for incentives and vendors."  
    - Wrong Response: "I can assist with vendor and incentive-related searches."  
    - Correct Response: "Could you specify the industry or location for which you're looking for vendors?"  

    Inputs
    1. User’s Latest Message  
    - This is the most recent message from the user. Use this to determine the appropriate tone, greetings, or redirection.  
    - {user_message}  

    2. Recent Conversation History  
    - This contains past exchanges between the user and the assistant.  
    - Chat history is only for reference. Do NOT infer, assume, or use any details about industry, supply, or location unless explicitly mentioned in the static follow-up message.  
    - {recent_history}  

    3. Static Follow-Up Message  
    - This is the reference message containing the key details to be included in the final response.  
    - Your task is to reword and refine this message into a polished, professional, and conversational follow-up.  
    - Static Message: "{static_follow_up}"  

    Response Guidelines  

    1. Proper Acknowledgment of Provided Details  
    - If the user has already provided Industry details (Main-Industry, Sub-Sector, or Segment), Location (Area, City, or State), or Supply (Raw Material, Equipment, Service), acknowledge them clearly and explicitly.  
    - Do NOT make a vague or partial acknowledgment—always specify exactly what was provided.  
    - Example:  
    - Correct: "You're looking for vendors for Cement in Mumbai."  
    - Wrong: "You're looking for vendors." (Too vague)  
    - If multiple details are provided, combine them logically:  
    - Example: "You're looking for vendors for Steel (Armor Grade) in Chennai."  

    2. Clearly Differentiate Between Searching for Supplies vs. Vendors for a Product  
    - If the static message implies a distinction between looking for vendors of a specific supply vs. looking for all supplies required for a product, ensure this is conveyed naturally.  
    - Example Message Integration:  
    - "You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors."  

    3. If Details Are Missing, Request Them Separately  
    - If Industry details (Main-Industry, Sub-Sector, or Segment) are missing, ask for them in a natural, concise way.  
    - If Location details (Area, City, or State) are missing, ask the user to specify.  
    - If Supply details (Raw Material, Equipment, or Service) are missing, request them politely.  
    - Ensure missing details are requested AFTER acknowledgment.  
    - Example:  
    - Correct: "You're looking for vendors for Cement. Could you share the location—whether it's an area, city, or state—so we can find the best options for you?"  
    - Wrong: "Could you confirm if you're looking for vendors for Cement and provide a location?" (Confirmation not needed)  

    4. Ensure Acknowledgment & Request for Missing Details Are Clearly Separated  
    - If acknowledgment is present, add a smooth transition before asking for missing details.  
    - Example:  
    - Correct: "You're looking for vendors for Industrial Chemicals. To find the best options, could you share the location where you're looking for them?"  
    - Wrong: "You're looking for vendors for Industrial Chemicals. Could you confirm that and provide a location?" (Confirmation not required)  

    5. Do NOT Copy the Static Message As-Is  
    - Instead, use it as a reference to create a well-structured, smooth, and conversational response.  
    - The final response must not sound robotic or overly formal.  
    - Ensure the message is clear, natural, and engaging.  

    6. Intelligent Use of Conjunctions  
    - Analyze the static follow-up message before adding conjunctions.  
    - If the message already has a natural transition, do not add an unnecessary conjunction.  
    - If the static message consists of two distinct parts (acknowledgment + request for missing details), place a proper conjunction between them where appropriate.  
    - The conjunction should not be at the very beginning of the message unless it naturally requires it.  

    7. Do NOT Address Off-Topic Queries  
    - If the user’s query is unrelated to industry, supply, or vendor searches, politely inform them:  
    - "I specialize in assisting with vendor-related queries for industries, supplies, and locations."  
    - DO NOT attempt to answer off-topic queries—instead, redirect to the static follow-up message with a smooth transition.  

    8. Handling Greetings  
    - If the user greets (e.g., "Hi", "Hello", "Good morning"), respond with an appropriate greeting.  
    - Ensure the transition to the follow-up message is smooth and natural using proper conjunctions.  

    9. Handling Special Events  
    - If the user mentions a special occasion (e.g., birthday, anniversary), acknowledge and celebrate it first.  
    - Then transition smoothly into the static follow-up message using proper conjunctions.  

    10. Handling Negative Emotions  
    - If the user expresses sadness, frustration, or anger, address their emotions with empathy first.  
    - Then transition seamlessly into the static follow-up message using a natural, logical flow.  

    Final Output Requirements  
    - Do NOT copy the static follow-up message word-for-word.  
    - Craft a clear, polished response that aligns with the user’s latest message.  
    - Ensure a smooth and engaging conversational flow.  
    - NEVER include placeholders like "None" or "Not Available in List" in the response.  
    - NEVER infer or use industry, supply, or location details unless they appear in the static follow-up message.  
    - NEVER address off-topic queries—redirect them properly.  
    - Keep the response concise (maximum 3 lines) while fully incorporating the static follow-up message.  
    - Ensure the message is professional, user-friendly, and free of unnecessary elaboration or additional context.  
    """


    # Prepare input to the model
    prompt_template = PromptTemplate(
        input_variables=["user_message", "recent_history", "static_follow_up"],
        template=prompt
    )
    chain = prompt_template | llm
    message = chain.invoke({
        "user_message": user_message,
        "recent_history": recent_history,
        "static_follow_up": static_follow_up
    })
    update_llm_token(message)

    # Append AI message to chat history
    chat_history_for_context.append(AIMessage(content=f"{message.content.strip()}"))
    return message.content.strip()

def get_static_follow_up_for_vendor(vendor_state: Dict[str, Dict[str, Optional[str]]], user_intention: str) -> str:
    """
    Generates a follow-up message based on available vendor search details.
    
    Ensures that at least one of the two required sets of information is provided:
    1. (Industry Info + Location Info) or
    2. (Supply Info + Location Info).

    If any key details are missing, it constructs a natural and engaging message asking for them.

    Parameters:
        vendor_state (Dict[str, Dict[str, Optional[str]]]): The state containing extracted vendor search details.

    Returns:
        str: A refined follow-up message prompting the user for missing details.
    """

    # Extract state details
    location_info = vendor_state.get("Location_info", {})
    industry_info = vendor_state.get("Industry_info", {})
    supply_info = vendor_state.get("Supply_info", {})

    # Extract values
    location = location_info.get("Location")
    location_category = location_info.get("Location Category")

    main_industry = industry_info.get("Main-Industry")
    sub_sector = industry_info.get("Sub-Sector")
    segment = industry_info.get("Segment")
    product = industry_info.get("Product")

    supplies = supply_info.get("Supplies", [])

    # Check missing details
    location_missing = location is None
    industry_missing = main_industry is None
    supply_missing = not supplies  # True if no supplies provided
    sub_sector_missing = sub_sector is None

    # Store provided details for acknowledgment
    provided_details = []
    missing_details = []
    if user_intention == "Vendor Search for location without industry and supply details":
        # **Handling Provided Information**
        if location:
            provided_details.append(f"You're looking for vendors in {location}.")
        
        if supplies:
            provided_details.append(f"You're searching for vendors supplying {', '.join(supplies)}.")

        if main_industry and sub_sector:
            if product:
                provided_details.append(f"You're looking for vendors for {product}.")
            else:
                provided_details.append(f"You're searching for vendors in the {sub_sector} sector under {main_industry}.")

        # **Handling Missing Information**
        
        # **Case 1: If only Main-Industry is present, ask for product (which leads to sub-sector identification)**
        if main_industry and sub_sector_missing:
            if product is None:
                return (
                    f"We see that you're looking for vendors in the {main_industry} industry. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            else:
                return (
                    f"We see that you're looking for vendors for {product}. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            
        # **Case 2: If Industry is provided but Location is missing**
        if not location and main_industry:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 3: If Supply is provided but Location is missing**
        if not location and supplies:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 4: If only Location is provided, ask whether they need vendors for an Industry or Specific Supply**
        if location and industry_missing and supply_missing:
            missing_details.append(
                "To help you find the right vendors, please share what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors"
            )

        # **Case 5: No details provided at all**
        if location_missing and industry_missing and supply_missing:
            return (
                "To help you find the right vendors, please share the location (area or city) and what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll find all the necessary supplies and their vendors for you."
                )

        # **Constructing the Follow-Up Message**
        message = " ".join(provided_details)

        if missing_details:
            if len(missing_details) == 2:
                message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
            else:
                message += f" But {missing_details[0]}"

        return message

    elif user_intention == "Vendor Search for industry without location details":
        # **Handling Provided Information**
        if location:
            provided_details.append(f"You're looking for vendors in {location}.")

        if main_industry and sub_sector:
            if product:
                provided_details.append(f"You're looking for vendors for {product}.")
            else:
                provided_details.append(f"You're searching for vendors in the {sub_sector} sector under {main_industry}.")

        # **Handling Missing Information**
        
        # **Case 1: If only Main-Industry is present, ask for product (which leads to sub-sector identification)**
        if main_industry and sub_sector_missing:
            if product is None:
                return (
                    f"We see that you're looking for vendors in the {main_industry} industry. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            else:
                return (
                    f"We see that you're looking for vendors for {product}. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            
        # **Case 2: If Industry is provided but Location is missing**
        if not location and main_industry:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 3: If only Location is provided, ask whether they need vendors for an Industry or Specific Supply**
        if location and industry_missing and supply_missing:
            missing_details.append(
                "To help you find the right vendors, please share what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors"
            )

        # **Case 4: No details provided at all**
        if location_missing and industry_missing and supply_missing:
            return (
                "To help you find the right vendors, please share the location (area or city) and what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll find all the necessary supplies and their vendors for you."
                )

        # **Constructing the Follow-Up Message**
        message = " ".join(provided_details)

        if missing_details:
            if len(missing_details) == 2:
                message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
            else:
                message += f" But {missing_details[0]}"

        return message
    
    elif user_intention == "Vendor Search for supply without location details":
        # **Handling Provided Information**
        if location:
            provided_details.append(f"You're looking for vendors in {location}.")
        
        if supplies:
            provided_details.append(f"You're searching for vendors supplying {', '.join(supplies)}.")


        # **Handling Missing Information**

        # **Case 1: If Supply is provided but Location is missing**
        if not location and supplies:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 2: If only Location is provided, ask whether they need vendors for an Industry or Specific Supply**
        if location and industry_missing and supply_missing:
            missing_details.append(
                "To help you find the right vendors, please share what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors"
            )

        # **Case 3: No details provided at all**
        if location_missing and industry_missing and supply_missing:
            return (
                "To help you find the right vendors, please share the location (area or city) and what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll find all the necessary supplies and their vendors for you."
                )

        # **Constructing the Follow-Up Message**
        message = " ".join(provided_details)

        if missing_details:
            if len(missing_details) == 2:
                message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
            else:
                message += f" But {missing_details[0]}"

        return message
    
    elif user_intention == "Vendor Search for industry with location details":
                # **Handling Provided Information**
        if location:
            provided_details.append(f"You're looking for vendors in {location}.")

        if main_industry and sub_sector:
            if product:
                provided_details.append(f"You're looking for vendors for {product}.")
            else:
                provided_details.append(f"You're searching for vendors in the {sub_sector} sector under {main_industry}.")

        # **Handling Missing Information**
        
        # **Case 1: If only Main-Industry is present, ask for product (which leads to sub-sector identification)**
        if main_industry and sub_sector_missing:
            if product is None:
                return (
                    f"We see that you're looking for vendors in the {main_industry} industry. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            else:
                return (
                    f"We see that you're looking for vendors for {product}. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            
        # **Case 2: If Industry is provided but Location is missing**
        if not location and main_industry:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 3: If only Location is provided, ask whether they need vendors for an Industry or Specific Supply**
        if location and industry_missing and supply_missing:
            missing_details.append(
                "To help you find the right vendors, please share what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors"
            )

        # **Case 4: No details provided at all**
        if location_missing and industry_missing and supply_missing:
            return (
                "To help you find the right vendors, please share the location (area or city) and what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll find all the necessary supplies and their vendors for you."
                )

        # **Constructing the Follow-Up Message**
        message = " ".join(provided_details)

        if missing_details:
            if len(missing_details) == 2:
                message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
            else:
                message += f" But {missing_details[0]}"

        return message
    
    elif user_intention == "Vendor Search for supply with location details":
        # **Handling Provided Information**
        if location:
            provided_details.append(f"You're looking for vendors in {location}.")
        
        if supplies:
            provided_details.append(f"You're searching for vendors supplying {', '.join(supplies)}.")


        # **Handling Missing Information**

        # **Case 1: If Supply is provided but Location is missing**
        if not location and supplies:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 2: If only Location is provided, ask whether they need vendors for an Industry or Specific Supply**
        if location and industry_missing and supply_missing:
            missing_details.append(
                "To help you find the right vendors, please share what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors"
            )

        # **Case 3: No details provided at all**
        if location_missing and industry_missing and supply_missing:
            return (
                "To help you find the right vendors, please share the location (area or city) and what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll find all the necessary supplies and their vendors for you."
                )

        # **Constructing the Follow-Up Message**
        message = " ".join(provided_details)

        if missing_details:
            if len(missing_details) == 2:
                message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
            else:
                message += f" But {missing_details[0]}"

        return message
    
    else:
        # **Handling Provided Information**
        if location:
            provided_details.append(f"You're looking for vendors in {location}.")
        
        if supplies:
            provided_details.append(f"You're searching for vendors supplying {', '.join(supplies)}.")

        if main_industry and sub_sector:
            if product:
                provided_details.append(f"You're looking for vendors for {product}.")
            else:
                provided_details.append(f"You're searching for vendors in the {sub_sector} sector under {main_industry}.")

        # **Handling Missing Information**
        
        # **Case 1: If only Main-Industry is present, ask for product (which leads to sub-sector identification)**
        if main_industry and sub_sector_missing:
            if product is None:
                return (
                    f"We see that you're looking for vendors in the {main_industry} industry. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            else:
                return (
                    f"We see that you're looking for vendors for {product}. Could you share more details about the specific product or service you need? This will help us refine our search and connect you with the most relevant vendors."
                )
            
        # **Case 2: If Industry is provided but Location is missing**
        if not location and main_industry:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 3: If Supply is provided but Location is missing**
        if not location and supplies:
            missing_details.append(
                "Could you share the location—whether it's an area, city, or state—where you're looking for vendors? This will help us find the best options for you."
                )

        # **Case 4: If only Location is provided, ask whether they need vendors for an Industry or Specific Supply**
        if location and industry_missing and supply_missing:
            missing_details.append(
                "To help you find the right vendors, please share what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll identify all the necessary supplies and connect you with the right vendors"
            )

        # **Case 5: No details provided at all**
        if location_missing and industry_missing and supply_missing:
            return (
                "To help you find the right vendors, please share the location (area or city) and what you need. You can either specify a particular supply or simply tell us the product you want to produce—we’ll find all the necessary supplies and their vendors for you."
                )

        # **Constructing the Follow-Up Message**
        message = " ".join(provided_details)

        if missing_details:
            if len(missing_details) == 2:
                message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
            else:
                message += f" But {missing_details[0]}"

        return message

def build_supply_confirmation_message_human_tone(extracted_state: dict, validated_state: dict) -> str:
    extracted_supplies = (extracted_state or {}).get("Supply_info", {}).get("Supplies", []) or []
    validated_supplies = (validated_state or {}).get("Supply_info", {}).get("Supplies", []) or []
    location = (
        (validated_state or {}).get("Location_info", {}) or
        (extracted_state or {}).get("Location_info", {})
    ).get("Location", "your selected area")

    # Pair extracted with validated for mapping
    pairs = list(zip(extracted_supplies, validated_supplies)) \
            if len(validated_supplies) == len(extracted_supplies) \
            else [(e, validated_supplies[i] if i < len(validated_supplies) else "Not Available in List")
                  for i, e in enumerate(extracted_supplies)]

    exact_matches = []
    close_matches = []
    unavailable = []

    for extracted, validated in pairs:
        e = (extracted or "").strip()
        v = (validated or "").strip()
        if not v or v.lower() == "not available in list":
            unavailable.append(e)
        elif v.lower() == e.lower():
            exact_matches.append(v)
        else:
            close_matches.append((e, v))

    # Build natural conversational message
    parts = []

    if extracted_supplies:
        parts.append(f"You mentioned you’re looking for **{', '.join(extracted_supplies)}** in **{location}**.")

    if exact_matches:
        parts.append(f"We have vendors for **{', '.join(exact_matches)}**, exactly as you requested.")

    if close_matches:
        close_texts = []
        for src, dst in close_matches:
            close_texts.append(f"we couldn’t find vendors for **{src}** exactly, but we do have vendors for **{dst}**, which is a very close match to your requirement")
        parts.append("For " + " and ".join(close_texts) + ".")

    if unavailable:
        parts.append(f"Unfortunately, we couldn’t find any vendors at all for **{', '.join(unavailable)}**.")

    # More natural closing line
    parts.append("Would you like me to go ahead and connect you with vendors for everything we can source for you right now?")

    return " ".join(parts)


# Entry Point
def handle_vendor_query(
    user_input: str,
    main_industry_to_subsector_mapped_dict: Dict[str, Dict[str, List[str]]],
    available_supplies: List[str],
    extracted_state: Dict[str, Dict[str, Any]],
    state: Dict[str, Dict[str, Any]],
    llm: Any,
    chatId,
    additional_class_response =None
) -> Union[Dict[str, Any], str]:
    """
    Handles vendor queries by analyzing user input, extracting relevant data, and responding accordingly.

    Parameters:
        user_input (str): The user query related to vendor search.
        main_industry_to_subsector_mapped_dict (Dict[str, Dict[str, List[str]]]): Mapping of main industries to their respective subsectors and segments.
        available_supplies (List[str]): List of available supplies.
        extracted_state (Dict[str, Dict[str, Any]]): A dictionary containing extracted information about the query.
        state (Dict[str, Dict[str, Any]]): A dictionary maintaining the state of the conversation.
        llm (Any): The language model used for query refinement and classification.

    Returns:
        Union[Dict[str, Any], str]: A response containing AI-generated messages and extracted data.
    """
    
    if state["Location_info"]["Location"] is not None:
        perfect_location_data = True
    else:
        perfect_location_data = False
    if state["Industry_info"]["Main-Industry"] is not None and state["Industry_info"]["Sub-Sector"] is not None:
        perfect_industry_data = True
    else:
        perfect_industry_data = False
    if not state["Supply_info"]["Supplies"]:
        perfect_supply_data = False
    else:
        perfect_supply_data = True
    
    chat_history = get_chat(f"chat_{chatId}") or []

    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]

    refined_user_input = user_input
    
    result = classify_vendor_query(refined_user_input, llm)
    # VendorClassificationFailure envelope instead of raising when the LLM
    # output cannot be parsed even after one corrective retry.
    from kaix.Ai_module.vendor_query.schemas import (
        VendorClassificationFailure,
        VendorLocationExtractionFailure,
        VendorSuppliesExtractionFailure,
    )
    if isinstance(result, VendorClassificationFailure):
        return {
            "Ai_response": (
                "Sorry, I couldn't quite understand your vendor request. "
                "Could you rephrase it — for example, mention the industry, "
                "the supplies, and/or the location you need vendors for?"
            ),
            "Is_confirmation": None,
            "State": state,
            "User Intention": "Other Intent",
            "options": None,
            "Trigger_Lead_Generation": False,
        }

    user_intention = result["classification_category"]
    frappe.log_error(f"user _intesnion {user_intention}")

    if user_intention == "Negatively Intended Query":
        message = respond_to_negative_query(
            user_intention, 
            append_user_to_history=False, 
            append_AI_to_history=False, 
            llm=llm,
            chatId=chatId)
       
        response = {
            "Ai_response": message,
            "Is_confirmation" : None,
            "State" : state,
            "User Intention": user_intention,
            "options": None,
            "Trigger_Lead_Generation":False
        }
        return response
    else:
        keyword_list = extract_important_words(refined_user_input, "Query to search Vendors")
        state["KEYWORDS"] = keyword_list
        state["Additional_class_response"] = additional_class_response or state.get("Additional_class_response")
        save_state(state,f"QVND_state_{chatId}")
        
        if user_intention == "Vendor Search for location without industry and supply details":
            extracted_data = extract_location_from_vendor_query(refined_user_input, llm)
            if isinstance(extracted_data, VendorLocationExtractionFailure):
                # P1-5: location parse unrecoverable even after one retry.
                # Do not proceed with the wrong-but-plausible "Area" default —
                # ask the user to restate the location explicitly.
                frappe.log_error(
                    f"{extracted_data.error} | raw: {extracted_data.raw_output}",
                    "handle_vendor_query location failure",
                )
                return {
                    "Ai_response": (
                        "Sorry, I couldn't determine the location from your "
                        "request. Could you restate it — for example the "
                        "specific area, city, state, or country?"
                    ),
                    "Is_confirmation": None,
                    "State": state,
                    "User Intention": "Other Intent",
                    "options": None,
                    "Trigger_Lead_Generation": False,
                }
            given_loacation = extracted_data["Extracted_Location"]
            given_location_category = extracted_data["Classification"]
            location_from_india = extracted_data["From_India"]

            extracted_state["Location_info"]["Location"] = given_loacation if given_loacation != "None" else None
            extracted_state["Location_info"]["Location Category"] = given_location_category if given_location_category != "None" else None
            extracted_state["Location_info"]["From_India"] = location_from_india if (given_loacation != "None" and given_location_category != "None") else None
            state["Location_info"] = copy.deepcopy(extracted_state["Location_info"])
            save_state(state,f"QVND_state_{chatId}")

            if state["Location_info"]["Location"] is not None:
                perfect_location_data = True
            else:
                perfect_location_data = False
            
            if (perfect_industry_data or perfect_supply_data) and perfect_location_data:
                if (state["Industry_info"]["Main-Industry"] != "Not Available in List" and state["Industry_info"]["Sub-Sector"] != "Not Available in List") or (not all(item == "Not Available in List" for item in state["Supply_info"]["Supplies"])):
                    if not state["Supply_info"]["Supplies"]:
                        selected_option = next(
                        (state.get("Industry_info").get(key) for key in ['Product', 'Segment', 'Sub-Sector', 'Main-Industry'] if state.get("Industry_info").get(key) not in [None, 'None']),
                        ''
                        )
                        message = (
                            f"You're searching for **all essential suppliers** to support your **{selected_option}** production in **{state.get('Location_info').get('Location')}**. <br/><br/>"
                            f"Please confirm if this is correct so we can connect you with the most relevant vendors."
                        )
                        # dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)          
                        confirmation_buttons = [
                            {"label": "Yes, show relevant suppliers", "value": user_intention},
                            {"label": "No, I want to update the request", "value": None}
                        ]
                    else:
                        message = (
                            f"You're looking for suppliers that provide **{', '.join(state['Supply_info']['Supplies'])}** in **{state.get('Location_info').get('Location')}**. <br/><br/>"
                            f"Please confirm if this is correct so we can help you find the right vendors."
                        )
                        confirmation_buttons = [
                            {"label": "Yes, show relevant suppliers", "value": user_intention},
                            {"label": "No, I want to update the request", "value": None}
                        ]

                    # response_validation = state.get("Additional_class_response")
                    # message += f"<br/><br/>**Note**: {response_validation}" if response_validation is not None else ""

                        # dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)  

                    

                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : True,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": confirmation_buttons,
                        "Trigger_Lead_Generation":False
                    }
                    return response
                else:
                    if state["Supply_info"]["Supplies"] and all(item == "Not Available in List" for item in state["Supply_info"]["Supplies"]):
                        message = SUPPLIES_NOT_AVAILABLE_MSG
                       
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention,
                            "options": None,
                            "Trigger_Lead_Generation":True
                        }
                        return response
                    
                    elif state["Industry_info"]["Main-Industry"] == "Not Available in List" or state["Industry_info"]["Sub-Sector"] == "Not Available in List":
                        message = INDUSTRY_NOT_AVAILABLE_MSG
                        
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention,
                            "options": None,
                            "Trigger_Lead_Generation":True
                        }
                        return response
                    else:                        
                        message = SUPPLIES_NOT_AVAILABLE_MSG + "AND" + INDUSTRY_NOT_AVAILABLE_MSG
                        
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention,
                            "options": None,
                            "Trigger_Lead_Generation":True
                        }
                        return response
            else:
                response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                
                response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention,
                            "options": None,
                            "Trigger_Lead_Generation":False
                        }
                return response
        
        elif user_intention == "Vendor Search for industry without location details":
            state["Supply_info"]["Supplies"] = []
            save_state(state,f"QVND_state_{chatId}")
            main_industry_list = list(main_industry_to_subsector_mapped_dict.keys())
            extracted_data, validated_data = extract_main_industry_and_product_universal(refined_user_input, main_industry_list, llm)
            main_industry_name = validated_data["Main-Industry"]
            product_name = validated_data["Product"]
            extracted_state["Industry_info"]["Main-Industry"] = extracted_data["Main-Industry"]
            extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
            if main_industry_name != "Not Available in List":
                if main_industry_name != "None":
                    state["Industry_info"]["Main-Industry"] = main_industry_name
                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                    save_state(state,f"QVND_state_{chatId}")
                    sub_sector_list = list(main_industry_to_subsector_mapped_dict[main_industry_name].keys())
                    extracted_data, validated_data = extract_sub_sector_and_product_universal(refined_user_input, sub_sector_list, llm, main_industry_name, product_name)
                    sub_sector_name = validated_data["Sub-Sector"]
                    product_name = validated_data["Product"]
                    extracted_state["Industry_info"]["Sub-Sector"] = extracted_data["Sub-Sector"]
                    extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
                    if sub_sector_name != "Not Available in List":
                        if sub_sector_name != "None":
                            state["Industry_info"]["Sub-Sector"] = sub_sector_name
                            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                            save_state(state,f"QVND_state_{chatId}")
                            segment_list = main_industry_to_subsector_mapped_dict[main_industry_name][sub_sector_name]
                            extracted_data, validated_data = extract_segment_and_product_universal(refined_user_input, segment_list, llm, main_industry_name, sub_sector_name, product_name)
                            segment_name = validated_data["Segment"]
                            product_name = validated_data["Product"]
                            extracted_state["Industry_info"]["Segment"] = extracted_data["Segment"]
                            if segment_name != "Not Available in List":
                                if segment_name != "None":
                                    state["Industry_info"]["Segment"] = segment_name
                                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                                    save_state(state,f"QVND_state_{chatId}")
                                else:
                                    state["Industry_info"]["Segment"] = None
                                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                                    save_state(state,f"QVND_state_{chatId}")
                            else:
                                state["Industry_info"]["Segment"] = "Not Available in List"
                                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                                save_state(state,f"QVND_state_{chatId}")
                        else:
                            state["Industry_info"]["Sub-Sector"] = None
                            state["Industry_info"]["Segment"] = None
                            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                            save_state(state,f"QVND_state_{chatId}")
                                    
                        if state["Industry_info"]["Main-Industry"] is not None and state["Industry_info"]["Sub-Sector"] is not None:
                            perfect_industry_data = True
                        else:
                            perfect_industry_data = False
                        
                        if perfect_industry_data and perfect_location_data:
                            selected_option = next(
                            (state.get("Industry_info").get(key) for key in ['Product', 'Segment', 'Sub-Sector', 'Main-Industry'] if state.get("Industry_info").get(key) not in [None, 'None']),
                            ''
                            )
                            message = (
                                f"You're searching for **all essential suppliers** to support your **{selected_option}** production in **{state.get('Location_info').get('Location')}**. <br/><br/>"
                                f"Please confirm if this is correct so we can connect you with the most relevant vendors."
                            )

                            # response_validation = state.get("Additional_class_response")
                            # message += f"<br/><br/>**Note**: {response_validation}" if response_validation is not None else ""

                            # dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)
                            
                            confirmation_buttons = [
                                {"label": "Yes, show relevant suppliers", "value": user_intention},
                                {"label": "No, I want to update the request", "value": None}
                            ]
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : True,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": confirmation_buttons,
                                "Trigger_Lead_Generation":False
                            }
                            return response
                            
                        else:
                            response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                            message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                           
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                            return response
    
                    else:
                        state["Industry_info"]["Sub-Sector"] = "Not Available in List"
                        state["Industry_info"]["Segment"] = "Not Available in List"
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QVND_state_{chatId}")
                        if perfect_location_data:
                            message = INDUSTRY_NOT_AVAILABLE_MSG
                            
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":True
                            }
                            return response
                        else:
                            response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                            message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                            
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                            return response
                else:
                    state["Industry_info"]["Main-Industry"] = None
                    state["Industry_info"]["Sub-Sector"] = None
                    state["Industry_info"]["Segment"] = None
                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                    save_state(state,f"QVND_state_{chatId}")
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":False
                    }
                    return response
            else:
                state["Industry_info"]["Main-Industry"] = "Not Available in List"
                state["Industry_info"]["Sub-Sector"] = "Not Available in List"
                state["Industry_info"]["Segment"] = "Not Available in List"
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QVND_state_{chatId}")
                if perfect_location_data:
                    message = INDUSTRY_NOT_AVAILABLE_MSG
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":True
                    }
                    return response
                else:
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":False
                    }
                    return response

        elif user_intention == "Vendor Search for supply without location details":

            state["Industry_info"] = {
                "Main-Industry": None,
                "Sub-Sector": None,
                "Segment": None,
                "Product": None,
            }
            save_state(state,f"QVND_state_{chatId}")

            supply_query_result = extract_supplies_from_query(refined_user_input, available_supplies, llm)
            if isinstance(supply_query_result, VendorSuppliesExtractionFailure):
                # P1-5: supplies parse unrecoverable even after one retry.
                # Do not proceed with empty supplies (indistinguishable from a
                # real "no supplies" answer) — ask the user to restate them.
                frappe.log_error(
                    f"{supply_query_result.error} | raw: {supply_query_result.raw_output}",
                    "handle_vendor_query supplies failure",
                )
                return {
                    "Ai_response": (
                        "Sorry, I couldn't determine the supplies or products "
                        "from your request. Could you restate them — for "
                        "example the specific materials, parts, or products "
                        "you need vendors for?"
                    ),
                    "Is_confirmation": None,
                    "State": state,
                    "User Intention": "Other Intent",
                    "options": None,
                    "Trigger_Lead_Generation": False,
                }
            extracted_supply = supply_query_result["Extracted_Supplies"]
            validated_supply = supply_query_result["Validated_Supplies"]

            extracted_state["Supply_info"]["Supplies"] = extracted_supply
            state["Supply_info"]["Supplies"] = validated_supply
            save_state(state,f"QVND_state_{chatId}")

            if not all(supply == "Not Available in List" for supply in state["Supply_info"]["Supplies"]):
                if state["Supply_info"]["Supplies"]:
                    if perfect_location_data:
                        # message = (
                        #     f"You're looking for suppliers that provide **{', '.join(state['Supply_info']['Supplies'])}** in **{state.get('Location_info').get('Location')}**. <br/><br/>"
                        #     f"Please confirm if this is correct so we can help you find the right vendors."
                        # )

                        # response_validation = state.get("Additional_class_response")
                        # message += f"<br/><br/>**Note**: {response_validation}" if response_validation is not None else ""

                        # available_supplies = state['Supply_info']['Supplies']
                        # requested_supplies = extracted_state['Supply_info']['Supplies']

                        # # Find items not available
                        # unavailable_supplies = [item for item in requested_supplies if item not in available_supplies]

                        # # Build the main message
                        # message_parts = []

                        # if available_supplies:
                        #     message_parts.append(
                        #         f"You're looking for suppliers that provide **{', '.join(available_supplies)}** in **{state.get('Location_info', {}).get('Location', 'your selected area')}**."
                        #     )

                        # if unavailable_supplies:
                        #     message_parts.append(
                        #         f"<br/><br/>Currently no vendors available for the following item(s): **{', '.join(unavailable_supplies)}**"
                        #     )

                        # # Add confirmation request
                        # message_parts.append("<br/><br/>Please confirm if this is correct so we can help you find the right vendors.")

                        # # Final message
                        message = build_supply_confirmation_message_human_tone(extracted_state=extracted_state, validated_state=state)

                        # dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)  
                       
                        confirmation_buttons = [
                            {"label": "Yes, show relevant suppliers", "value": user_intention},
                            {"label": "No, I want to update the request", "value": None}
                        ]
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : True,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention,
                            "options": confirmation_buttons,
                            "Trigger_Lead_Generation":False
                        }
                        return response
                    else:
                        response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                        
                        message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                        
                        response = {
                                    "Ai_response": message,
                                    "Is_confirmation" : None,
                                    "Extracted Data": extracted_state,
                                    "Validation Data": state,
                                    "User Intention": user_intention,
                                    "options": None,
                                    "Trigger_Lead_Generation":False
                                }
                        return response
                else:
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                    return response
            else:
                if perfect_location_data: 
                    message = SUPPLIES_NOT_AVAILABLE_MSG
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":True
                    }
                    return response
                else:
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                    return response
                
        elif user_intention == "Vendor Search for industry with location details":
            state["Supply_info"]["Supplies"] = []
            save_state(state,f"QVND_state_{chatId}")
            extracted_data = extract_location_from_vendor_query(refined_user_input, llm)
            if isinstance(extracted_data, VendorLocationExtractionFailure):
                # P1-5: location parse unrecoverable even after one retry.
                # Do not proceed with the wrong-but-plausible "Area" default —
                # ask the user to restate the location explicitly.
                frappe.log_error(
                    f"{extracted_data.error} | raw: {extracted_data.raw_output}",
                    "handle_vendor_query location failure",
                )
                return {
                    "Ai_response": (
                        "Sorry, I couldn't determine the location from your "
                        "request. Could you restate it — for example the "
                        "specific area, city, state, or country?"
                    ),
                    "Is_confirmation": None,
                    "State": state,
                    "User Intention": "Other Intent",
                    "options": None,
                    "Trigger_Lead_Generation": False,
                }
            given_loacation = extracted_data["Extracted_Location"]
            given_location_category = extracted_data["Classification"]
            location_from_india = extracted_data["From_India"]
            extracted_state["Location_info"]["Location"] = given_loacation if given_loacation != "None" else None
            extracted_state["Location_info"]["Location Category"] = given_location_category if given_location_category != "None" else None
            extracted_state["Location_info"]["From_India"] = location_from_india if (given_loacation != "None" and given_location_category != "None") else None
            state["Location_info"] = copy.deepcopy(extracted_state["Location_info"])
            save_state(state,f"QVND_state_{chatId}")

            if state["Location_info"]["Location"] is not None:
                perfect_location_data = True
            else:
                perfect_location_data = False

            main_industry_list = list(main_industry_to_subsector_mapped_dict.keys())
            ind_extracted_data, ind_validated_data = extract_main_industry_and_product_universal(refined_user_input, main_industry_list, llm)
            main_industry_name = ind_validated_data["Main-Industry"]
            product_name = ind_validated_data["Product"]
            extracted_state["Industry_info"]["Main-Industry"] = ind_extracted_data["Main-Industry"]
            extracted_state["Industry_info"]["Product"] = ind_extracted_data["Product"] if ind_extracted_data["Product"] != "None" else None

            if main_industry_name != "Not Available in List":
                if main_industry_name != "None":
                    state["Industry_info"]["Main-Industry"] = main_industry_name
                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                    save_state(state,f"QVND_state_{chatId}")
                    sub_sector_list = list(main_industry_to_subsector_mapped_dict[main_industry_name].keys())
                    extracted_data, validated_data = extract_sub_sector_and_product_universal(refined_user_input, sub_sector_list, llm, main_industry_name, product_name)
                    sub_sector_name = validated_data["Sub-Sector"]
                    product_name = validated_data["Product"]
                    extracted_state["Industry_info"]["Sub-Sector"] = extracted_data["Sub-Sector"]
                    extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
                    if sub_sector_name != "Not Available in List":
                        if sub_sector_name != "None":
                            state["Industry_info"]["Sub-Sector"] = sub_sector_name
                            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                            save_state(state,f"QVND_state_{chatId}")
                            segment_list = main_industry_to_subsector_mapped_dict[main_industry_name][sub_sector_name]
                            extracted_data, validated_data = extract_segment_and_product_universal(refined_user_input, segment_list, llm, main_industry_name, sub_sector_name, product_name)
                            segment_name = validated_data["Segment"]
                            product_name = validated_data["Product"]
                            extracted_state["Industry_info"]["Segment"] = extracted_data["Segment"]
                            if segment_name != "Not Available in List":
                                if segment_name != "None":
                                    state["Industry_info"]["Segment"] = segment_name
                                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                                    save_state(state,f"QVND_state_{chatId}")
                                else:
                                    state["Industry_info"]["Segment"] = None
                                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                                    save_state(state,f"QVND_state_{chatId}")
                            else:
                                state["Industry_info"]["Segment"] = "Not Available in List"
                                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                                save_state(state,f"QVND_state_{chatId}")
                        else:
                            state["Industry_info"]["Sub-Sector"] = None
                            state["Industry_info"]["Segment"] = None
                            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                            save_state(state,f"QVND_state_{chatId}")
                                    
                        if state["Industry_info"]["Main-Industry"] is not None and state["Industry_info"]["Sub-Sector"] is not None:
                            perfect_industry_data = True
                        else:
                            perfect_industry_data = False
                        
                        if perfect_industry_data and perfect_location_data:
                            selected_option = next(
                            (state.get("Industry_info").get(key) for key in ['Product', 'Segment', 'Sub-Sector', 'Main-Industry'] if state.get("Industry_info").get(key) not in [None, 'None']),
                            ''
                            )
                            message = (
                                f"You're searching for **all essential suppliers** to support your **{selected_option}** production in **{state.get('Location_info').get('Location')}**. <br/><br/>"
                                f"Please confirm if this is correct so we can connect you with the most relevant vendors."
                            )

                            # response_validation = state.get("Additional_class_response")
                            # message += f"<br/><br/>**Note**: {response_validation}" if response_validation is not None else ""

                            # dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)
                            

                            confirmation_buttons = [
                                {"label": "Yes, show relevant suppliers", "value": user_intention},
                                {"label": "No, I want to update the request", "value": None}
                            ]

                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : True,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": confirmation_buttons,
                                "Trigger_Lead_Generation":False
                            }
                            return response
                            
                        else:
                            response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                            message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                            
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                            return response
                    else:
                        state["Industry_info"]["Sub-Sector"] = "Not Available in List"
                        state["Industry_info"]["Segment"] = "Not Available in List"
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QVND_state_{chatId}")
                        if perfect_location_data:
                            message = INDUSTRY_NOT_AVAILABLE_MSG
                            
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":True
                            }
                            return response
                        else:
                            response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                            message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                            
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                            return response
                else:
                    state["Industry_info"]["Main-Industry"] = None
                    state["Industry_info"]["Sub-Sector"] = None
                    state["Industry_info"]["Segment"] = None
                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                    save_state(state,f"QVND_state_{chatId}")
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":False
                    }
                    return response

            else:
                state["Industry_info"]["Main-Industry"] = "Not Available in List"
                state["Industry_info"]["Sub-Sector"] = "Not Available in List"
                state["Industry_info"]["Segment"] = "Not Available in List"
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QVND_state_{chatId}")
                if perfect_location_data: 
                    message = INDUSTRY_NOT_AVAILABLE_MSG
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":True
                    }
                    return response
                else:
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                    return response

        elif user_intention == "Vendor Search for supply with location details":
            state["Industry_info"] = {
                "Main-Industry": None,
                "Sub-Sector": None,
                "Segment": None,
                "Product": None,
            }
            save_state(state,f"QVND_state_{chatId}")
            extracted_data = extract_location_from_vendor_query(refined_user_input, llm)
            if isinstance(extracted_data, VendorLocationExtractionFailure):
                # P1-5: location parse unrecoverable even after one retry.
                # Do not proceed with the wrong-but-plausible "Area" default —
                # ask the user to restate the location explicitly.
                frappe.log_error(
                    f"{extracted_data.error} | raw: {extracted_data.raw_output}",
                    "handle_vendor_query location failure",
                )
                return {
                    "Ai_response": (
                        "Sorry, I couldn't determine the location from your "
                        "request. Could you restate it — for example the "
                        "specific area, city, state, or country?"
                    ),
                    "Is_confirmation": None,
                    "State": state,
                    "User Intention": "Other Intent",
                    "options": None,
                    "Trigger_Lead_Generation": False,
                }
            given_loacation = extracted_data["Extracted_Location"]
            given_location_category = extracted_data["Classification"]
            location_from_india = extracted_data["From_India"]

            extracted_state["Location_info"]["Location"] = given_loacation if given_loacation != "None" else None
            extracted_state["Location_info"]["Location Category"] = given_location_category if given_location_category != "None" else None
            extracted_state["Location_info"]["From_India"] = location_from_india if (given_loacation != "None" and given_location_category != "None") else None
            state["Location_info"] = copy.deepcopy(extracted_state["Location_info"])
            save_state(state,f"QVND_state_{chatId}")

            if state["Location_info"]["Location"] is not None:
                perfect_location_data = True
            else:
                perfect_location_data = False

            supply_query_result = extract_supplies_from_query(refined_user_input, available_supplies, llm)
            if isinstance(supply_query_result, VendorSuppliesExtractionFailure):
                # P1-5: supplies parse unrecoverable even after one retry.
                # Do not proceed with empty supplies (indistinguishable from a
                # real "no supplies" answer) — ask the user to restate them.
                frappe.log_error(
                    f"{supply_query_result.error} | raw: {supply_query_result.raw_output}",
                    "handle_vendor_query supplies failure",
                )
                return {
                    "Ai_response": (
                        "Sorry, I couldn't determine the supplies or products "
                        "from your request. Could you restate them — for "
                        "example the specific materials, parts, or products "
                        "you need vendors for?"
                    ),
                    "Is_confirmation": None,
                    "State": state,
                    "User Intention": "Other Intent",
                    "options": None,
                    "Trigger_Lead_Generation": False,
                }
            extracted_supply = supply_query_result["Extracted_Supplies"]
            validated_supply = supply_query_result["Validated_Supplies"]

            extracted_state["Supply_info"]["Supplies"] = extracted_supply
            state["Supply_info"]["Supplies"] = validated_supply
            save_state(state,f"QVND_state_{chatId}")

            if not state["Supply_info"]["Supplies"]:
                perfect_supply_data = False
            else:
                perfect_supply_data = True
            
            
            if not all(supply == "Not Available in List" for supply in state["Supply_info"]["Supplies"]):
                if state["Supply_info"]["Supplies"]:
                    if perfect_location_data and perfect_supply_data:
                        # message = (
                        #     f"You're looking for suppliers that provide **{', '.join(state['Supply_info']['Supplies'])}** in **{state.get('Location_info').get('Location')}**. <br/><br/>"
                        #     f"Please confirm if this is correct so we can help you find the right vendors."
                        # )

                        # response_validation = state.get("Additional_class_response")
                        # message += f"<br/><br/>**Note**: {response_validation}" if response_validation is not None else ""

                        # available_supplies = state['Supply_info']['Supplies']
                        # requested_supplies = extracted_state['Supply_info']['Supplies']

                        # # Find items not available
                        # unavailable_supplies = [item for item in requested_supplies if item not in available_supplies]

                        # # Build the main message
                        # message_parts = []

                        # if available_supplies:
                        #     message_parts.append(
                        #         f"You're looking for suppliers that provide **{', '.join(available_supplies)}** in **{state.get('Location_info', {}).get('Location', 'your selected area')}**."
                        #     )

                        # if unavailable_supplies:
                        #     message_parts.append(
                        #         f"<br/><br/>Currently no vendors available for the following item(s): **{', '.join(unavailable_supplies)}**"
                        #     )

                        # # Add confirmation request
                        # message_parts.append("<br/><br/>Please confirm if this is correct so we can help you find the right vendors.")

                        # Final message
                        message = build_supply_confirmation_message_human_tone(extracted_state=extracted_state, validated_state=state)


                        # dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)  
                       
                        
                        confirmation_buttons = [
                            {"label": "Yes, show relevant suppliers", "value": user_intention},
                            {"label": "No, I want to update the request", "value": None}
                        ]

                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : True,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention,
                            "options": confirmation_buttons,
                            "Trigger_Lead_Generation":False
                        }
                        return response
                    else:
                        response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    
                        message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                        
                        response = {
                                    "Ai_response": message,
                                    "Is_confirmation" : None,
                                    "Extracted Data": extracted_state,
                                    "Validation Data": state,
                                    "User Intention": user_intention,
                                    "options": None,
                                    "Trigger_Lead_Generation":False
                                }
                        return response
                else:
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                    return response
            else:
                if perfect_location_data and perfect_supply_data: 
                    message = SUPPLIES_NOT_AVAILABLE_MSG
                    
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":True
                    }
                    return response
                else:
                    response_static_message = get_static_follow_up_for_vendor(state, user_intention)
                    message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                    
                    response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention,
                                "options": None,
                                "Trigger_Lead_Generation":False
                            }
                    return response

        else:
            response_static_message = get_static_follow_up_for_vendor(state, user_intention)
            
            message = generate_dynamic_message_for_vendor(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
            
            response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention,
                        "options": None,
                        "Trigger_Lead_Generation":False
                    }
            return response

def call_handle_vendor_query(input,chatId, additional_class_response = None):

    query = """
    select distinct supply
    from `tabVendor Supply Capacity`
    """

    results = fetch_query_results(query=query)
    unique_supply_list = [row[0] for row in results]

    query = """
    SELECT sgt.segment, indmappedsst.sub_sector_name, indmappedsst.industry_name
    FROM `tabSegment` as sgt
    JOIN (
        SELECT sst.name,sst.sub_sector_name, indt.industry_name
        FROM `tabSub Sector` as sst
        JOIN `tabIndustry` as indt
        WHERE sst.industry_id = indt.name
    ) as indmappedsst
    WHERE sgt.sub_sector = indmappedsst.name
    """

    Industry_data_results = fetch_query_results(query)

    Industry_data_df_for_vendor = pd.DataFrame(Industry_data_results, columns=["Segment","Sub-Sector", "Main-Industry"])

    # Initialize an empty dictionary
    Industry_data_for_vendor = {}

    # Iterate through each row of the DataFrame
    for _, row in Industry_data_df_for_vendor.iterrows():
        main_industry = row["Main-Industry"]
        sub_sector = row["Sub-Sector"]
        segment = row["Segment"]
        
        # Create the hierarchy step by step
        if main_industry not in Industry_data_for_vendor:
            Industry_data_for_vendor[main_industry] = {}
        if sub_sector not in Industry_data_for_vendor[main_industry]:
            Industry_data_for_vendor[main_industry][sub_sector] = []
        if segment not in Industry_data_for_vendor[main_industry][sub_sector]:
            Industry_data_for_vendor[main_industry][sub_sector].append(segment)

    state = get_state(f"QVND_state_{chatId}") or None

    if not state:
        state = {
            "Location_info":{
                "Location":None,
                "Location Category": None,
                "From_India": None
            },
            "Industry_info":{
                "Main-Industry": None,
                "Sub-Sector": None,
                "Segment": None,
                "Product": None,
            },
            "Supply_info": {
                "Supplies": []
            },
            "KEYWORDS": None,
            "Additional_class_response": None
        }
        save_state(state,f"QVND_state_{chatId}")

    extracted_state = copy.deepcopy(state)

    response_of_ven_query = handle_vendor_query(input, Industry_data_for_vendor, unique_supply_list, extracted_state, state, llm_70b_vers,chatId, additional_class_response)

    return response_of_ven_query
