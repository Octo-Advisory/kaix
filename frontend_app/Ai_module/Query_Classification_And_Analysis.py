import os
import re
import json 
from typing import List, Dict, Tuple, Union
# from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from rapidfuzz import fuzz, process
import frappe
from frontend_app.Management_Class.helpers.utility import update_llm_token  
import configparser
# from langchain_openai import ChatOpenAI
config_file = '/home/mars/frappe-bench/apps/frontend_app/frontend_app/Log_management/mars.ini'
config = configparser.ConfigParser()
config.read(config_file)
groq_api_key = config['Key']['groq_key']

# Initialize LLM    
llm_70b_vers = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0.0)
llm_70b_vers_creative = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0.7)
llm_8b_inst=ChatGroq(groq_api_key=groq_api_key,model_name="llama-3.3-8b-instant", temperature=0.0)
llm_deepseek = ChatGroq(groq_api_key=groq_api_key, model_name="deepseek-r1-distill-llama-70b", temperature=0.0)
# llm_openai = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, api_key=openai_key)
# llm_openai_inf_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_key)
# llm_openai_inf_4o = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=openai_key)
# llm_openai_inf_4 = ChatOpenAI(model="gpt-4", temperature=0.0, api_key=openai_key)
# llm_openai_inf_3_5 = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.0, api_key=openai_key)

# Define a function to refine the query using history
def refine_query_with_history(history, latest_query, llm):
    # Define retriever prompt
    retriever_prompt_template = """  
    Given the chat history and the latest user input, reformulate a standalone query that maintains the intent and structure of the latest user input.  
    Use the AI's messages for context only to understand the user's intent better, but do not take examples or suggestions from AI responses as the user's actual input unless the user explicitly agrees or repeats them.  

    Instructions:  
    1. Preserve the original structure of the user input.  
    - If the user’s latest input is a statement, the reformulated query must remain a statement.  
    - If the user’s latest input is a question, the reformulated query must remain a question.  

    2. If the latest user input is completely different and unrelated to the past conversation, return it as-is without modification.  

    3. If the latest user input is related to the past conversation, refine it by integrating relevant details from the chat history while ensuring clarity.  

    4. Strictly do NOT infer or modify any numerical values, units, or metrics.  
    - If the user provides a metric value (e.g., "1 TPA", "500 MW"), retain it exactly as it is.  
    - Do NOT expand, convert, or modify abbreviations of units (e.g., keep "TPA" as "TPA" and do not change it to "Ton Per Annum").  
    - If no metric is provided by the user, do NOT infer one.  

    5. Strictly do not infer or carry forward any industries, products, or metrics from past AI responses unless the user explicitly acknowledges, agrees to, or repeats those industries, products, or metrics in their latest input.  

    6. Strictly do not infer or carry forward any industries, products, or metrics from past user inputs unless they are explicitly mentioned in the latest user input.  

    7. If the latest user input mentions only one industry or product, ensure only that industry or product appears in the reformulated query.  
    - Do not include multiple industries or products unless the user explicitly mentions multiple ones in their latest query.  

    8. Do NOT add any explanations, reasoning, or justifications in the reformulated standalone query.  
    - The output must be a clean and direct reformulation of the user’s intent without unnecessary elaboration.  

    Chat History:  
    {history}  

    Latest User Input:  
    {latest_query}  

    Reformulated Standalone Query:  
    """
    
    prompt = PromptTemplate(
        input_variables=["history", "latest_query"],
        template=retriever_prompt_template
    )
    chain = prompt | llm
    refined_query = chain.invoke({"history": "\n".join(history), "latest_query": latest_query})
    update_llm_token(refined_query)
    refined_text = refined_query.content.strip()
    
    # Extract the reformulated standalone query
    match = re.search(r'reformulated standalone query:\s*(?:"(.*?)"|\'(.*?)\'|(.*))$', refined_text, re.IGNORECASE)
    if match:
        # Return the captured group that is not None
        return next(group for group in match.groups() if group)
    
    # Fallback to the entire response if no match is found
    return refined_text

# Define the function
@frappe.whitelist()
def classify_query(user_query):
    # Define the refined prompt template 
    prompt_template = """
    You are an expert in understanding business-related queries and classifying them into a **single most relevant category**.
    Your task is to strictly assign the query to only one category, even if multiple classes seem applicable.  
    Analyze the context carefully and ensure that you return only one category that best fits the query.  

    Categories & Their Definitions:

    1. Query to build industry from Scratch:  
        - Example: *I want to build a 1 TPA Cement Factory.*  
        - This refers to queries about establishing an industry from the ground up, including land purchase, infrastructure setup, or capacity planning.  
        - Only assign this category if the user's query explicitly indicates an intent to build a new industry or factory.  
        - Do NOT classify a query under this category if it only mentions approvals, incentives, vendors, or employee searches—these should be classified under their respective categories.  
        - If the intent to build is unclear or mixed with other topics, do NOT assign this category.

    2. Query to search Vendors:  
        - Example: *I am searching for a vendor who supplies pharmaceutical-grade raw chemicals for drug manufacturing.*  
        - This category is used for queries about finding suppliers, manufacturers, or vendors for raw materials, equipment, or services.

    3. Query to search Incentives:  
        - Example: *What benefits are available for setting up a cement manufacturing plant in XYZ area?*  
        - This category is used for queries asking about government incentives, grants, or subsidies related to setting up or expanding an industry.

    4. Query to Get Approvals:  
        - Example: *I want to get approval for my Cement Factory.*  
        - This category is used for queries about obtaining permits, licenses, or regulatory approvals for a business or industry.

    5. Query to Get Employee Search:  
        - Example: *What is the availability of employment in XYZ area for the Pharmaceutical industry?*  
        - This category is used for queries about recruiting or finding employees for an industry or in a specific location.

    If None of the Above Apply, Use These Two Categories:

    6. Other industry-related queries:  
        - Example: *What is the role of AI in manufacturing?*  
        - This refers to general industry discussions, trends, or innovations that do not fit into the above categories.

    7. Valueless queries:  
        - Example: *Who is Donald Trump?*  
        - This refers to queries that are irrelevant to business, industry setup, or supply chains.  
        - If the query contains industry-related words but the intent is not meaningful, classify it here.  
        - Example: *I'm going to buy a new bike, for that which approvals do I need?* (Not relevant to industry-building)

    Strict Classification Rules:

    1. Return Only One Class:  
        - If the query seems to match multiple categories, analyze the overall intent and assign it to the single most appropriate category.  

    2. Assign "Query to build industry from Scratch" ONLY if Confident:  
        - Strictly assign this category only if the user clearly states they want to establish a new industry.  
        - If the query only contains mentions of vendors, incentives, approvals, or employee searches, do NOT classify it as industry-building.  
        - If the intent to build is unclear or mixed with other topics, do NOT assign this category.

    3. Do NOT Assign "Query to build industry from Scratch" If the Query Contains Only Approvals, Incentives, Vendors, or Employee Searches:  
        - If the user is asking about any combination of these categories (Approvals, Incentives, Vendors, or Employee Searches) but does NOT explicitly mention setting up a new industry, assign the most relevant category among them.  
        - Example: *"I need vendors for raw materials and want to know about required approvals and incentives."* → Correct classification: Either "Query to search Vendors" or "Query to Get Approvals" based on context.  
        - Example: *"I want to search vendors, approvals, and also check employment availability in my city."* → Correct classification: Choose the most dominant category based on intent.  

    4. Prioritize Meaningful Context, Not Just Keywords:  
        - Do NOT assign a category just because it contains words like "approval," "vendor," or "incentive."  
        - Analyze the full context of the query before assigning a category.  

    Final Output Instructions:
    - Strictly return only the category name from the list above.  
    - Do not include multiple categories.  
    - Do not provide explanations, justifications, or extra details.  

    Query:  
    {query}

    Output:  
    (Return only one category name from the list)
    """

    # Initialize the LLM
    # Create the prompt
    prompt = PromptTemplate(
        input_variables=["query"],
        template=prompt_template
    )

    # Create the LLM chain
    chain = prompt | llm_70b_vers

    # Run the query through the chain
    category = chain.invoke({"query": user_query})
    update_llm_token(category)

    return category.content.strip()

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
    You are an expert in analyzing user queries and accurately extracting location information.  
    Your task is to identify and extract the **most relevant location** from the user query.  
    Do not classify the location into area, city, or state. Simply extract the correct location name.

    Key Extraction Rules:

    1. Extract the Most Relevant Location Based on Context:
    - If the query contains multiple locations, analyze the intent and extract only the one location that is most relevant for the user's request.
    - Ignore locations that are mentioned for personal reference or additional context (e.g., "I live in X but want to know about Y" → Extract only Y).
    - Even if multiple locations are mentioned, extract only one location that is most relevant to the user's search intent.

    2. Preserve Location Abbreviations:
    - If a location is followed by an abbreviation (e.g., "SEZ", "PCPIR", "GIDC", "MIDC", etc.), always extract the full location name including the abbreviation.
    - Do not remove or separate the abbreviation from the location name under any circumstances.

    3. Handle Spelling Errors & Variations:
    - If a location contains spelling mistakes, correct it and return the corrected value.

    4. Ensure the Official Location Name is Used:
    - If the location has multiple variants, always return the official name of the location instead of alternative or outdated names.
    - Some common examples:
        - "Bombay" → "Mumbai"
        - "Baroda" → "Vadodara"
        - "Kashi" → "Varanasi"
        - "Calcutta" → "Kolkata"
        - "Bangalore" → "Bengaluru"
        - "Pondicherry" → "Puducherry"
    - Ensure all locations are recognized and standardized to their official designation.

    5. Only Return a Location if One is Mentioned:
    - If no location is found, return `"None"` as the value.

    6. Majority of Locations Will Be from India:
    - Assume most locations will be from India.
    - If the location is outside India, still extract and return it.

    7. No Additional Explanations:
    - The output must only contain the extracted location.
    - Do not provide reasoning, context, or explanations.

    User Query:
    {query}

    Output Format:
    Provide only the extracted location in the following JSON format:
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
        print("="*100,"\nFuzz Result: \n",result, "\n","="*100)
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
    - If a location is followed by an abbreviation (e.g., "SEZ", "PCPIR", "GIDC", "MIDC", etc.), always extract the full location name including the abbreviation.
    - Do not remove or separate the abbreviation from the location name under any circumstances.

    3. Handle Spelling Errors & Variations:
    - If a location contains spelling mistakes, correct it and return the corrected value.

    4. Ensure the Official Location Name is Used:
    - If a location has multiple variants, always return the official name of the location instead of alternative or outdated names.
    - Some common examples:
        - "Bombay" → "Mumbai"
        - "Baroda" → "Vadodara"
        - "Kashi" → "Varanasi"
        - "Calcutta" → "Kolkata"
        - "Bangalore" → "Bengaluru"
        - "Pondicherry" → "Puducherry"
    - Ensure all locations are recognized and standardized to their official designation.

    5. Only Return Locations if Mentioned:
    - If no locations are found, return `"None"` as the value.

    6. Majority of Locations Will Be from India:
    - Assume most locations will be from India.
    - If a location is outside India, still extract and return it.

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
            "List of Certifications": "Certifications held by the vendor that validate compliance with industry standards (e.g., ISO 9001, BIS Certification, GMP Certification, ASME Certification, AS9100 (for aerospace, FDA Approval (US)))."
      },
      "Query to search Incentives": {
            "Incentive Name": "The official title of the financial or non-financial support program available (e.g., Startup India Seed Fund, MSME Credit Guarantee Scheme).",
            "Incentive Type": "The category of the incentive based on the type of support it provides (e.g., Equity Support, Sustenance Allowance, Tax Exemption, Interest Subsidy, Capital Investment Subsidy, Incentive in Power Tariff and Electricity Duty).",
            "Quantum of Assistance": "The amount or percentage of financial assistance or benefit provided (e.g., 'Seed support up to Rs. 30 Lakh' or 'Capital subsidy of 25% on plant and machinery cost', 'Exemption of electicity duty')."
      },
      "Query to Get Approvals": {
            "Name of License / Approval": "The specific name of the required approval for business operations (e.g., Environmental Clearance, Fire NOC, Factory License).",
            "Government Department": "The regulatory body or authority issuing the license (e.g., Pollution Control Board, Directorate of Industrial Safety and Health).",
            "Land Type": "The classification of land where the approval applies (e.g., Agricultural Land, Non-Agricultural Land - Urban, Industrial Land).",
            "Business Location": "The specific area or industrial zone where the business operates (e.g., GIDC, Non GIDC, DSIRDA, MBSIRDA, GPCP SIRDA).",
            "Stage": "The phase during which approval is required (e.g., Pre-establishment, Pre-requisite, Pre-operation).",
            "Mode of Application": "The method by which the approval is obtained (e.g., Online, Offline).",
            "Vicinity Detail": "Additional details on surroundings that may impact approval (e.g., Forest, Archaeological site, Mineral bearing site (for a non-mining business)).",
            "Cross Following Details": "Checks if the industry site crosses important utilities (Notified rivers/ nalas/ canals/ drains, Pipeline of Gujarat Gas, Pipeline of Sabarmati Gas, Pipeline of GSPL, Water bodies).",
            "Tree Cutting": "Indicates whether tree cutting is required (eg: Tree Cutting).",
            "Road Cutting": "Indicates whether road cutting is required (eg: Road Cutting).",
            "Require Pole Shifting": "Specifies if shifting of electricity or communication poles is needed (eg: Pole Shifting)."
      },
      "Query to build industry from Scratch": {
            "Property Type": "The type of land based on usage (Non-Agricultural Land, Agricultural Land, Industrial Land, Industrial Park Plot, GIDC Plot, Warehouse, Industrial Plant, Auction Property, Industrial Park).",
            "Business Location Type": "The classification of the business location (GIDC, Non GIDC, DSIRDA, MBSIRDA, GPCP SIRDA).",
            "Land Type": "The specific classification of land (Agricultural Land, Non-Agricultural Land (Rural), Non-Agricultural Land (Urban)).",
            "Location": "The specific area, city, or state where the property is located (e.g., Gujarat, Surat, Waghodia).",
            "Vicinity of": "Environmental or geographical features nearby (Forest, Archaeological site, Mineral bearing site).",
            "Tree Cutting Involved": "Indicates whether tree cutting is required for the project (Tree cutting).",
            "Road Cutting Involved": "Specifies if road cutting is required to establish infrastructure (Road Cutting).",
            "Will your industry cross the following?": "Checks whether the industry site intersects with important geographical or utility structures (Pipeline of Gujarat Gas, Pipeline of Sabarmati Gas, Pipeline of GSPL, Water bodies, Notified rivers/ nalas/ canals/ drains)."
      },
}

def extract_json_from_llm_response(raw_output: str, json_key: str) -> Dict[str, Union[List[str], None]]:
    """
    Extracts a JSON object containing the specified key from an LLM response.

    Supports:
    - Direct JSON responses.
    - JSON blocks enclosed in triple backticks.
    - Loosely structured JSON in plain text.

    Handles cases where:
    - The key's value is explicitly `null` or `None`.
    - The key contains a list of values.
    
    Parameters:
    -----------
    raw_output : str
        The raw text output from the LLM.

    json_key : str
        The expected key in the JSON response (e.g., "KEYWORDS").

    Returns:
    --------
    Dict[str, Union[List[str], None]]:
        A dictionary with the extracted values, ensuring a structured JSON output.
    """

    # --- Case 1: Direct JSON Parsing ---
    try:
        data_entire = json.loads(raw_output.strip())
        if isinstance(data_entire, dict) and json_key in data_entire:
            extracted_value = data_entire.get(json_key, None)
            return {json_key: extracted_value if isinstance(extracted_value, list) else None}
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # JSON parsing failed

    # --- Case 2: Extract JSON inside triple backticks ---
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', raw_output, flags=re.DOTALL)
    for block in code_blocks:
        try:
            block_data = json.loads(block.strip())
            if isinstance(block_data, dict) and json_key in block_data:
                extracted_value = block_data.get(json_key, None)
                return {json_key: extracted_value if isinstance(extracted_value, list) else None}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # JSON parsing failed

    # --- Case 3: Regex-based Extraction ---
    
    #    a) Pattern with curly braces (full JSON structure)
    pattern_braces = re.compile(r'\{\s*"' + json_key + r'"\s*:\s*(\[[^]]*\]|null|None)\s*\}', flags=re.DOTALL)
    match_braces = pattern_braces.search(raw_output)
    if match_braces:
        keyword_list = match_braces.group(1).strip()

        # If the extracted value is explicitly "null" or "None", return None
        if keyword_list.lower() in ["null", "none"]:
            return {json_key: None}

        extracted_values = [kw.strip('" ') for kw in keyword_list.strip("[]").split(',') if kw.strip('" ')]
        return {json_key: extracted_values if extracted_values else None}

    #    b) Loose JSON structure extraction (if above didn't work)
    pattern_no_braces = re.compile(r'"' + json_key + r'"\s*:\s*(\[[^]]*\]|null|None)', flags=re.DOTALL)
    match_no_braces = pattern_no_braces.search(raw_output)
    if match_no_braces:
        keyword_list = match_no_braces.group(1).strip()

        if keyword_list.lower() in ["null", "none"]:
            return {json_key: None}

        extracted_values = [kw.strip('" ') for kw in keyword_list.strip("[]").split(',') if kw.strip('" ')]
        return {json_key: extracted_values if extracted_values else None}

    # -- If nothing worked, return a default response --
    return {json_key: None}

def extract_keywords_from_query(
    user_input: str,
    fields: Dict[str, str],
    module_names: List[str],
    llm,
    current_module: str
) -> Dict[str, Union[List[str], None]]:
    """
    Extracts relevant single-word keywords from the user's query based on the provided field descriptions, 
    excluding words that are part of predefined module names or restricted categories.

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

    Returns:
    -------
    Dict[str, Union[List[str], None]]
        A dictionary with the key "KEYWORDS" mapping to a list of extracted keywords. 
        If no valid keywords are found, returns {"KEYWORDS": None}.
    """

    # 1) Build a text block enumerating each field with its meaning
    field_lines = []
    for idx, (fname, fdesc) in enumerate(fields.items(), start=1):
        field_lines.append(f"{idx}) {fname}: {fdesc}")
    fields_explained = "\n".join(field_lines)

    # 2) We must ensure each module name is split into single words
    #    so we can exclude them individually (e.g., "Vendor Management" => "Vendor", "Management").
    #    We'll store them in a set to remove duplicates and allow quick membership checks.
    module_words = set()
    for mod_name in module_names:
        # split on whitespace
        for token in mod_name.split():
            module_words.add(token.strip().lower())

    # Turn the module_names into a user-facing string for the prompt
    # (though we'll do final filtering in Python as well).
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
        Example 2: "Wanna build car industry in Vadodara" → ["Vadoadara"] (Because "car" and "industry" are restricted)

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
        Examples: "Delhi", "Mumbai", "Surat", "Gujarat", "Andhra Pradesh", "USA", "industrial zone"

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
        Example 2: "Find subsidies power Gujarat" → ["power"]
        Example 3: "Wanna build car industry in Vadodara" → null (Because "car", "Vadodara" and "industry" are restricted)

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


    # 4) Create the PromptTemplate and run the LLM
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
    # print(raw_output)

    data = extract_json_from_llm_response(raw_output, "KEYWORDS")
    keywords = data.get("KEYWORDS", None)
    ####################################################################
    # 6) Final Cleanup in Python
    #    - Remove empty or whitespace-only
    #    - Convert to lowercase and compare with module_words
    ####################################################################
    if isinstance(keywords, list):
        cleaned = []
        for kw in keywords:
            # Ensure single word
            # (If the LLM accidentally gives us multi-word phrases, we could optionally split them here,
            #  but ideally the LLM is already returning single words.)
            # We do a simple split, in case the LLM gave something like "power incentive" in one item.
            for token in kw.split():
                token_stripped = token.strip()
                if token_stripped:
                    # Exclude module words
                    if token_stripped.lower() not in module_words:
                        cleaned.append(token_stripped)
        # Remove duplicates (if desired) by converting to an Ordered set, or just leave them
        cleaned = list(dict.fromkeys(cleaned))  # preserves order, removes duplicates

        if cleaned:
            keywords = cleaned
        else:
            keywords = None
    else:
        keywords = None

    return {"KEYWORDS": keywords}

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
    main_industries_str = ", ".join(main_industries)
    
    # Define the universal prompt
    prompt_template = """
    You are an expert in analyzing industry-related queries and extracting specific details.
    Based on the user's query, identify the following details:

    1. Main-Industry: Infer or predict the main industry based on the context of the query.  
    - Users may phrase their queries in different ways, such as:
        - "What incentives are available for the automobile sector?"
        - "Which approvals are needed for the pharmaceutical industry?"
        - "I am looking for steel vendors."
    - In all such cases, identify the relevant industry even if the query is vague or incomplete.  
    - If the inferred main industry can logically match any category from the provided list of Main-Industries, return the matched category from the list and set `"Forced-Mapping": "No"`.  
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred main industry to the closest match from the provided list and set `"Forced-Mapping": "Yes"`.  
    - If no main industry can be inferred from the query, return `"None"` for both `"Original-Inferred-Main-Industry"` and `"Main-Industry"`.  

    2. Product (if applicable): Identify the specific product mentioned in the query (e.g., "Cement," "Steel Rods").  
    - If the inferred term logically represents a product, include it in the output.  
    - If no product is mentioned or it does not logically fit as a product, return `"None"`.  

    Logical Matching for Main Industries:
    - A logical match occurs when the inferred main industry and an available main industry from the list are conceptually or functionally similar.  
    - Examples of logical matches:  
        - Inferred: "Chemical Processing" → Available: "Chemical Manufacturing" (`Forced-Mapping`: "No`).  
        - Inferred: "Electronics Production" → Available: "Electronics Manufacturing" (`Forced-Mapping`: "No`).  
    - Examples of forced mappings:  
        - Inferred: "Nanotechnology Development" → Available: "Advanced Manufacturing" (`Forced-Mapping`: "Yes`).  
        - Inferred: "Eco-friendly Energy Solutions" → Available: "Green Manufacturing" (`Forced-Mapping`: "Yes`).  

    Provided List of Main-Industries:  
    {main_industries}  

    Important Notes:
    - Always assume that the query is related to an industry-specific inquiry, whether it is about incentives, approvals, or vendors.
    - Ensure that the output is strictly limited to the required JSON format and contains no explanations, reasoning, or comments.  
    - Do not provide additional text, explanations, or reasoning within the fields of the JSON object.  
    - Each field in the JSON must only contain the exact extracted information or the specified fallback values (e.g., "None").  

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
    validated_data = extracted_data.copy()
    if main_industry not in main_industries and main_industry != "None":
        validated_data["Main-Industry"] = "Not Available in list"

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
    sub_sectors_str = ", ".join(sub_sectors)

    # Define additional context for Main-Industry and Product if available
    context_lines = []
    if main_industry and main_industry not in ["None", "Not Available in list"]:
        context_lines.append(f"Inferred Main-Industry: {main_industry}")
    if product and product != "None":
        context_lines.append(f"Inferred Product: {product}")
    context = "\n".join(context_lines)

    # Define the universal prompt
    prompt_template = """
    You are an expert in analyzing industry-related queries and extracting specific details.  
    Sub-Sector is the functional or operational category that immediately follows the Main-Industry in the hierarchy.  
    It encompasses broader categories of related activities, processes, or areas of focus that form part of the Main-Industry.  

    For example:  
    - In the "Automobile" Main-Industry, possible Sub-Sectors include "Vehicle Assembly," "Automotive Components," or "Electric Vehicles."
    - In the "Pharmaceuticals" Main-Industry, possible Sub-Sectors include "Allopathic Medicines," "Ayurvedic Medicines," or "Biotechnology."
    - In the "Renewable Energy" Main-Industry, possible Sub-Sectors include "Solar Energy," "Wind Power," or "Hydropower."
    - Sub-Sectors are broad categories and are not tied to individual products but rather industry segments.

    {context}

    Based on the user's query, identify the following details:

    1. Sub-Sector Extraction:  
    - The query may relate to industry incentives, approvals, or vendor searches. Identify the most relevant sub-sector.  
    - If the inferred sub-sector can logically match any category from the provided list, return the matched category from the list and set `"Forced-Mapping"` to `"No"`.  
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred sub-sector to the closest match from the provided list and set `"Forced-Mapping"` to `"Yes"`.  
    - If no sub-sector can be inferred from the query, return `"None"` for `"Original-Inferred-Sub-Sector"` and `"Sub-Sector"`.  

    2. Product Extraction (if applicable):  
    - If the product context is provided, return the same product in the output JSON exactly as mentioned in the query.  
    - If the inferred term logically represents a product, include it in the output.  
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.  

    Important Notes:
    - Do NOT assume that all queries are related to manufacturing. Queries may relate to incentives, approvals, or vendors across various industries.  
    - Logical Matching for Sub-Sectors:  
    - A logical match occurs when the inferred sub-sector and an available sub-sector from the list are conceptually or functionally similar.  
    - Examples of Logical Matches:  
        - Incentives: "Tax Benefits for Renewable Energy" → Available: "Renewable Energy" (`Forced-Mapping`: `"No"`).  
        - Approvals: "Environmental Clearance for Chemical Plants" → Available: "Chemical Manufacturing" (`Forced-Mapping`: `"No"`).  
        - Vendors: "Suppliers of Medical Equipment" → Available: "Medical Devices" (`Forced-Mapping`: `"No"`).  
    - Examples of Forced Mappings:  
        - "Government Grants for AI Startups" → Available: "Technology & IT Services" (`Forced-Mapping`: `"Yes"`).  
        - "Supply Chain for Nano-Materials" → Available: "Advanced Materials" (`Forced-Mapping`: `"Yes"`).  
    - If no logical match exists, set `"Forced-Mapping"` to `"Yes"`.

    Output Constraints:  
    - Strictly limit the output to the required JSON format and ensure that it contains no explanations, reasoning, or additional text.  
    - Do not provide reasoning like *"This matches because..."* or *"Assumed based on context."*  
    - Each field in the JSON must contain only the extracted information or the specified fallback values (`"None"`).  

    Provided List of Sub-Sectors:  
    {sub_sectors_str}  

    Output Format:  
    Output the result strictly as a JSON object in the following format:  
    {{
        "Sub-Sector": <Mapped Sub-Sector>,
        "Original-Inferred-Sub-Sector": <Inferred Sub-Sector or 'None'>,
        "Forced-Mapping": <'Yes' or 'No'>,
        "Product": <Extracted Product or 'None'>
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
    validated_data = extracted_data.copy()
    if sub_sector not in sub_sectors and sub_sector != "None":
        validated_data["Sub-Sector"] = "Not Available in list"

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
    segments_str = ", ".join(segments)

    # Define additional context for Main-Industry and Sub-Sector if available
    context_lines = []
    if main_industry and main_industry not in ["None", "Not Available in list"]:
        context_lines.append(f"Inferred Main-Industry: {main_industry}")
    if sub_sector and sub_sector not in ["None", "Not Available in list"]:
        context_lines.append(f"Inferred Sub-Sector: {sub_sector}")
    if product and product != "None":
        context_lines.append(f"Inferred Product: {product}")
    context = "\n".join(context_lines)

    # Define the prompt
    prompt_template = """
    You are an expert in analyzing industry-related queries and extracting specific details.
    A Segment is a logical grouping of products or services that come immediately next in the hierarchy after the Sub-Sector.
    The Sub-Sector itself is a functional or operational category following the Main-Industry in the hierarchy.

    For example:
    - In the "Automobile" industry, a Sub-Sector like "Automotive Components" may have Segments such as "Engines," "Batteries," or "Tires."
    - In the "Pharmaceuticals" industry, a Sub-Sector like "Allopathic Medicines" may have Segments such as "Antibiotics" or "Analgesics."
    - In the "Textile" industry, a Sub-Sector like "Fabric Production" may have Segments such as "Cotton Weaving" or "Synthetic Fiber Manufacturing."

    Based on the user's query, identify the following details:

    {context}

    1. Segment: First, infer or predict the segment based on the context of the query.
    - In most cases, users may not explicitly mention "business activity" or "sector-specific terms," but they are referring to industry-related segments. Assume the query relates to an industry segment unless it is clearly illogical to do so.
    - The query may sometimes be vague or incomplete. In such cases, analyze the implied intent and context to infer the appropriate segment.
    - If the inferred segment can logically match any category from the provided list of Segments, return the matched category from the list and set `Forced-Mapping` to `No`.
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred segment to the closest match from the provided list and set `Forced-Mapping` to `Yes`.
    - If no segment can be inferred from the query, return `"None"` for both `Original-Inferred-Segment` and `Segment`.

    2. Product: If the product context is provided, return the same product in the output JSON as it is in the context.  
    - Identify the specific product or service the query refers to (e.g., "Cement," "Steel Rods," "Industrial Equipment").  
    - If the inferred term logically represents a product or service, include it in the output.  
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.  

    Important Notes:

    Logical Matching for Segments:
    - A logical match occurs when the inferred segment and an available segment from the list are conceptually or functionally similar.
    - Examples of logical matches:
        - Inferred: "Tax Incentives for Startups" → Available: "Government Grants & Subsidies" (Not forced, `Forced-Mapping`: No).
        - Inferred: "Pollution Control Compliance" → Available: "Environmental Approvals" (Not forced, `Forced-Mapping`: No).
    - Examples of forced mappings:
        - Inferred: "Renewable Energy Investment Benefits" → Available: "Green Industry Incentives" (Forced, `Forced-Mapping`: Yes).
        - Inferred: "Vendor Sourcing for Construction" → Available: "Building Materials Suppliers" (Forced, `Forced-Mapping`: Yes).
    - If no logical match exists, set `Forced-Mapping` to `Yes`.

    Provided List of Segments:  
    {segments_str}  

    Output Format:
    - Ensure that the output strictly adheres to the specified JSON format without any additional reasoning, explanations, or comments.
    - Do not include any reasoning or justification in the fields. For example, avoid entries such as `"This matches because..."` or `"Assumed based on the context..."`.
    - Each field should only contain the extracted information or the specified fallback values (e.g., "None").

    Output the result strictly as a JSON object in the following format:
    {{
        "Segment": <Mapped Segment>,
        "Original-Inferred-Segment": <Inferred Segment or 'None'>,
        "Forced-Mapping": <'Yes' or 'No'>,
        "Product": <Extracted Product or 'None'>
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
    validated_data = extracted_data.copy()
    if segment not in segments and segment != "None":
        validated_data["Segment"] = "Not Available in list"

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
