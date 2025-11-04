import re
import json
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Union
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from frontend_app.Ai_module.Query_Classification_And_Analysis import *
import frappe
from frontend_app.Management_Class.Redis_management.Redis_chat import save_chat,get_chat,save_state,get_state
from frontend_app.Management_Class.helpers.utility import update_llm_token
from frontend_app.Management_Class.Ai_management.AI import *

def classify_industry_setup_query(query: str, llm) -> dict:
    """
    Classifies a user's query related to industrial setup assistance into one of five categories:

    Categories:
        1: Intent to Build Industry from Scratch
        2: Intent to Acquire Existing Industrial Infrastructure
        3: Intent to Set Up Industry with Unspecified Build or Buy Intent
        4: Other Intent
        5: Negatively Intended Query

    Args:
        query (str): The user's input query.
        llm: A language model interface that supports `.invoke()`

    Returns:
        dict: A dictionary containing:
            - "raw_prompt" (str): The full prompt used to query the LLM.
            - "classification_number" (int): The classification number (1–5).
            - "classification_category" (str): Description of the classification category.
    """
    import re
    from langchain.prompts import PromptTemplate

    category_mapping = {
        1: "Intent to Build Industry from Scratch",
        2: "Intent to Acquire Existing Industrial Infrastructure",
        3: "Intent to Set Up Industry with Unspecified Build or Buy Intent",
        4: "Other Intent",
        5: "Negatively Intended Query",
        6: "Intent to Evaluate Both Building from Scratch and Acquiring Existing Infrastructure",
    }
    raw_prompt = """
You are an expert in analyzing user queries related to setting up or acquiring an industrial business. Your task is to classify the user's intention into one of the following categories:

1. Intent to Build Industry from Scratch:
    - The user expresses interest in finding or acquiring empty land to construct industrial infrastructure (e.g., factories, plants) from the ground up.
    - Includes queries about land acquisition for industrial purposes or building new facilities, even if not explicitly phrased as "build on empty land."
    - Example queries:
        - "I want to build a pharmaceutical industry which produces 1 Million Tablets per annum."
        - "I need land to set up a textile factory."
        - "Where can I build a cement plant?"
        - "Looking for a site to construct a 1 MTPA fly ash plant."
        - "Need help finding land for a dairy industry in Gujarat."
        - "I’m planning to construct a new food processing unit in Punjab."
        - "Where can I find a plot to build an electronics manufacturing plant?"
        - "Need a site for a new steel factory in Maharashtra."

2. Intent to Acquire Existing Industrial Infrastructure:
    - The user expresses interest in purchasing or acquiring an existing industrial facility, auction property, or pre-built infrastructure to start operations without constructing new facilities.
    - Includes queries about buying factories, plants, or auctioned properties, even if not explicitly phrased as "existing infrastructure."
    - Example queries:
        - "I want to buy a cement factory."
        - "Any factories for sale in Maharashtra?"
        - "Looking for an auctioned industrial plant."
        - "Need a steel plant to purchase in Gujarat."
        - "I’m interested in acquiring an existing textile mill."
        - "Where can I find a chemical plant for sale?"
        - "Looking to buy a pre-built packaging facility."
        - "Any auction properties for industrial use in Tamil Nadu?"

3. Intent to Set Up Industry with Unspecified Build or Buy Intent:
    - The user expresses a desire to set up an industry but does not clearly specify whether they want to build from scratch or acquire existing infrastructure, or they indicate uncertainty about the approach.
    - Includes vague or general queries about starting an industry without clear preference for building or buying.
    - Example queries:
        - "I want to setup a plastic factory."
        - "I want to start a dairy industry."
        - "How to set up a pharma plant?"
        - "Looking to establish an EV battery factory."
        - "I want to set up a textile industry, not sure if I should buy or build."
        - "How can I start a food processing business?"
        - "Interested in launching a solar panel manufacturing unit."
        - "What’s the process to set up a cement industry?"
        - "I want to buy or build a cement factory."
        - "I am open to buying land or acquiring an existing industrial unit."
        - "Need help with either buying a plant or finding land for my factory."
        - "Looking to set up a unit — open to either building from scratch or purchasing."
        - "Can I get land or buy an existing shed for a packaging unit?"
        - "I want to buy or build a cement factory."
        - "Looking to either purchase or develop a plant, whichever is easier."
        - "I’m open to both options, building or buying, not decided yet."
        - "I want to buy or build a cement plant."

4. Other Intent:
    - The query is clearly related to something else — such as vendors, approvals, employment, incentives — but NOT about industry setup.
    - The query may also be completely unrelated to industrial context (e.g., tourism, politics, daily news, etc.).
    - Example queries:
        - "What are the vendor options in Gujarat?"
        - "Employment statistics for Baroda?"
        - "Tell me about textile incentives in Maharashtra."
        - "What is the weather in Delhi?"
        - "I don’t want to build a factory but need vendors."
        - "Not interested in buying a plant, but what are the job opportunities?"

5. Negatively Intended Query:
    - The user clearly expresses disinterest or refusal to engage in anything related to setting up or acquiring an industry, including building from scratch, acquiring existing infrastructure, or general setup.
    - This includes queries where all mentioned factors (e.g., vendors, incentives, employment, approvals) are also negated.
    - Example queries:
        - "I don’t want to build a factory."
        - "I’m not looking to buy any land or set up an industry."
        - "Please don’t show me anything about industrial setup."
        - "Not interested in buying a factory or building one."
        - "Not interested in acquiring a plant or getting incentives."
        - "I don’t want to set up a factory or deal with suppliers."

6. Intent to Evaluate Both Building from Scratch and Acquiring Existing Infrastructure:
    - The user explicitly indicates interest in **actively exploring both options** — building a new facility from scratch **and** acquiring an existing one — as part of their industrial setup planning.
    - This is distinct from Class 3, where the user is vague, unsure, or open to either path without clearly requesting both.
    - Queries expressing general openness to "either building or buying" without clear dual exploration should be classified as Class 3.
    - Class 6 does NOT include queries that simply mention "buy or build", "either option", or "open to both" in a vague or disjunctive way. These indicate openness or uncertainty, not an active search for both.
    - The distinction between "buy or build" and "buy and build" is important:
        - Queries using **"or"** imply one of the two and reflect uncertainty → classify as Class 3.
        - Queries using **"and"** imply the user intends to pursue or explore **both paths** → classify as Class 6.
    - Example queries:
        - "Looking for land or existing industrial facility for a textile unit in Gujarat."
        - "Need options to either buy an operational plastic factory or find land to build one."
        - "Searching for auction plants or empty plots to set up an EV battery plant."
        - "Want to explore both land plots and running food processing units in Madhya Pradesh."
        - "I am open to either purchasing a chemical factory or acquiring land for greenfield development."
        - "Interested in buying a running paper mill or land suitable to set up one in Maharashtra."
        - "I want to buy and build a plastic industry."
        - "We are planning to buy and build facilities for our textile business."


Extended Classification Logic for Consistency:

- Positive Intent Priority:
    - If the query indicates positive intent *solely* for building from scratch, classify as Class 1, even if other factors (vendors, incentives, etc.) are mentioned.
    - If the query indicates positive intent *solely* for acquiring existing infrastructure, classify as Class 2.
    - If the query indicates positive intent for setting up an industry without specifying build or buy, classify as Class 3.
    - If the query clearly expresses active intent to explore both building from scratch *and* acquiring existing infrastructure — for example, by separately describing both options or stating a need to evaluate/search for both types — classify as Class 6.
    - However, if the user phrases it as a choice, uncertainty, or openness using “or”, “either”, “any one”, “whichever is available”, or “open to both”, then it reflects unspecified intent and must be classified as Class 3.
    - If the query says “buy or build”, “buy or acquire”, “construct or purchase”, or similar disjunctive structures → classify as Class 3.
    - If the query says “buy and build”, “construct and acquire”, “exploring both purchase and development”, or similar conjunctive structures → classify as Class 6.
    - Class 3 indicates general setup intent without a committed exploration of both paths.
    - Examples of Class 3 phrasing (not Class 6):
        - "I want to buy or build a cement factory."
        - "Open to either purchasing or constructing a plant."
        - "I want either a running unit or land to set up."
        - "I want either land or existing factory"
        - "Any one of land or running unit is fine"
        - "I am open to buying or building"
        - "Whichever is available for setting up my unit"


- Negative Intent Logic:
    - If building from scratch, acquiring existing infrastructure, or general setup is mentioned negatively AND no other factors (vendors, incentives, employment, approvals) are present, classify as Class 5.
    - If any of these intents is mentioned negatively AND all other mentioned factors are also negative, classify as Class 5.
    - If any of these intents is mentioned negatively BUT at least one other factor is mentioned positively, classify as Class 4.

- Contextual Understanding for Vague Queries:
    - Do not rely solely on specific keywords like “land,” “build,” “buy,” “factory,” “approvals,” “vendors,” etc.
    - Analyze the full context to determine intent, even if the query is vague or uses synonyms/implied meanings.
    - Examples of contextual phrases:
        - For Class 1: “site for factory,” “construct a plant,” “new industrial unit.”
        - For Class 2: “purchase a plant,” “acquire a factory,” “auctioned industrial property.”
        - For Class 3: “start an industry,” “establish a factory,” “set up operations.”
        - For Class 4: “permissions,” “suppliers,” “jobs,” “subsidies,” “weather.”
        - For Class 5: “don’t want to build,” “not interested in buying,” “no industry setup.”

Short or Follow-up Style Responses:
    - If the user provides only a capacity figure, unit of measurement, or time period (e.g., “5000 TPA,” “2000 tonnes per annum,” “liters per day,” “Yearly,” “Kilograms”), classify as Class 3.
    - If the user only mentions an industry name, product, or manufacturing-related term (e.g., “pharma,” “steel,” “packaging,” “cement”) — even without verbs or full sentences — treat it as Class 3.
    - These inputs often reflect answers to previous follow-up questions or abbreviated expressions of general setup intent.
    - If the query mentions “land” or “site” without explicit construction intent, lean toward Class 1 unless context suggests otherwise.
    - If the query mentions “buy” or “purchase” with a factory or plant, lean toward Class 2 unless context suggests otherwise.

Additional Understanding Requirement:
    - Do not rely solely on specific keywords like “approvals,” “vendors,” “employment,” “incentives,” or “building industry from scratch.”
    - Always analyze the full context of the query to determine whether these intents are present — even if users use alternative phrasing or synonyms.
    - Examples:
        - “Permissions,” “licenses,” “NOCs,” or “clearances” should be interpreted as approval-related.
        - “Suppliers,” “distributors,” or “raw material sources” may indicate vendor search.
        - “Jobs,” “workforce,” “manpower,” or “recruitment” may imply employment intent.
        - “Subsidies,” “tax breaks,” “grants,” or “financial support” may suggest incentives.
        - “Starting operations,” “setting up a factory,” “establishing infrastructure,” or “launching a new unit” may indicate building industry from scratch.
        - “Site for factory,” “new plant construction” → build from scratch (Class 1).
        - “Purchase a factory,” “acquire a plant” → acquire infrastructure (Class 2).
        - “Start operations,” “establish a unit” → unspecified setup (Class 3).
    - Understand user intent even if the sentence is vague, mixed, or includes implied meanings rather than explicit phrases.

Final Output Instructions:
    - Strictly return only the classification number (1, 2, 3, 4, 5, or 6).
    - Do NOT include explanations or summaries.

Query:
{query}

Output:
(Return only one classification number)
    """

    prompt_template = PromptTemplate(input_variables=["query"], template=raw_prompt)
    chain = prompt_template | llm

    response = chain.invoke({"query": query})
    match = re.search(r"^\s*([1-6])\s*$", response.content.strip())

    if match:
        classification_number = int(match.group(1))
        classification_category = category_mapping[classification_number]
        return {
            "raw_prompt": raw_prompt,
            "classification_number": classification_number,
            "classification_category": classification_category,
        }
    else:
        raise ValueError(f"Invalid classification from LLM: {response}")

def extract_json_main_industry_details(output: str) -> Dict[str, str]:
    """
    Extracts structured industry-related details from LLM output.

    Ensures:
    - Proper parsing of various JSON formats (valid JSON, inside code blocks, or loose text).
    - Default values for missing fields.
    - Forced mapping handling for industry categorization.

    Returns:
    -------
    dict:
        {
            "Main-Industry": str,
            "Original-Inferred-Main-Industry": str,
            "Forced-Mapping": str ("Yes" or "No"),
            "Product": str
        }
    """

    # -- 1) Direct JSON Parsing --
    try:
        data_entire = json.loads(output.strip())
        if isinstance(data_entire, dict) and "Main-Industry" in data_entire:
            return {
                "Main-Industry": data_entire.get("Main-Industry", "None"),
                "Original-Inferred-Main-Industry": data_entire.get("Original-Inferred-Main-Industry", "None"),
                "Forced-Mapping": data_entire.get("Forced-Mapping", "No"),
                "Product": data_entire.get("Product", "None"),
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # JSON parsing failed

    # -- 2) Extract JSON blocks inside triple backticks --
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', output, flags=re.DOTALL)
    for block in code_blocks:
        text_block = block.strip()
        try:
            block_data = json.loads(text_block)
            if isinstance(block_data, dict) and "Main-Industry" in block_data:
                return {
                    "Main-Industry": block_data.get("Main-Industry", "None"),
                    "Original-Inferred-Main-Industry": block_data.get("Original-Inferred-Main-Industry", "None"),
                    "Forced-Mapping": block_data.get("Forced-Mapping", "No"),
                    "Product": block_data.get("Product", "None"),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # JSON parsing failed

    # -- 3) Fallback: Regex-based extraction --
    #    a) Pattern with curly braces (full JSON structure)
    fallback_pattern_braces = re.compile(
        r'\{\s*"Main-Industry"\s*:\s*"([^"]+)"\s*,\s*"Original-Inferred-Main-Industry"\s*:\s*"([^"]+)"\s*,'
        r'\s*"Forced-Mapping"\s*:\s*"([^"]+)"\s*,\s*"Product"\s*:\s*"([^"]+)"\s*\}',
        flags=re.DOTALL
    )
    match_braces = fallback_pattern_braces.search(output)
    if match_braces:
        return {
            "Main-Industry": match_braces.group(1),
            "Original-Inferred-Main-Industry": match_braces.group(2),
            "Forced-Mapping": match_braces.group(3),
            "Product": match_braces.group(4),
        }

    #    b) Pattern without curly braces (loose JSON structure)
    fallback_pattern_no_braces = re.compile(
        r'"Main-Industry"\s*:\s*"([^"]+)"|'
        r'"Original-Inferred-Main-Industry"\s*:\s*"([^"]+)"|'
        r'"Forced-Mapping"\s*:\s*"([^"]+)"|'
        r'"Product"\s*:\s*"([^"]+)"',
        flags=re.DOTALL
    )
    matches = fallback_pattern_no_braces.findall(output)

    extracted_values = {
        "Main-Industry": "None",
        "Original-Inferred-Main-Industry": "None",
        "Forced-Mapping": "No",
        "Product": "None"
    }
    
    for match in matches:
        if match[0]: extracted_values["Main-Industry"] = match[0]
        if match[1]: extracted_values["Original-Inferred-Main-Industry"] = match[1]
        if match[2]: extracted_values["Forced-Mapping"] = match[2]
        if match[3]: extracted_values["Product"] = match[3]

    # -- If nothing worked, return a default response --
    return extracted_values

def extract_main_industry_and_product_for_scratch(user_query: str, main_industries: List[str], llm) -> Dict[str, str]:
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
    
    # Define the prompt
    prompt_template = """
You are an expert in analyzing industry-building queries and extracting specific details.

**CRITICAL INSTRUCTION: When determining Main-Industry classification, focus ONLY on the product, service, or industry terms mentioned in the query. Completely ignore geographic locations (cities, states, countries) for industry inference. Location information should not influence industry selection in any way.**

Based on the user's query, identify the following details:

1. Main-Industry: First, infer or predict the main industry based on the context of the query.  
    - Users may phrase their queries in various ways, such as "I want to set up a spectacle factory," "I want to set up a spectacle industry," or simply "Spectacles." In all such cases, assume they are referring to manufacturing the product mentioned unless it is clearly illogical.  
    - Do not rely on specific words like "factory," "industry," or similar terms to infer manufacturing intent. The product name alone (e.g., "Spectacles") is sufficient to deduce that the query is about manufacturing that product.  
    - The query may sometimes be vague, incomplete, or consist of just the product name. In such cases, logically infer the appropriate main industry.  
    - **Focus exclusively on product/service/industry keywords - NOT on location.**
    - If the inferred main industry can logically match any category from the provided list of Main-Industries, return the matched category from the list and set `"Forced-Mapping": "No"`.  
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred main industry to the closest match from the provided list and set `"Forced-Mapping": "Yes"`.  
    - If no main industry can be inferred from the query, return `"None"` for both `"Original-Inferred-Main-Industry"` and `"Main-Industry"`.  

2. Product: Identify the specific product the query refers to (e.g., "Cement", "Steel Rods").  
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
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.  

**Product-to-Industry Mapping Rules (Location-Independent):**
- Spectacles/Eyeglasses → "Healthcare & Pharmaceuticals" (medical devices)
- Chalk/Calcium Carbonate → "Mining" (manufacturing/processing)
- Steel/Iron → "Capital Goods" 
- Pharmaceuticals/Medicines → "Healthcare & Pharmaceuticals"
- Cement/Concrete → "Cement"
- Food items → "Foods and Beverages"

Logical Matching for Main Industries:
    - A logical match occurs when the inferred main industry and an available main industry from the list are conceptually or functionally similar.  
    - Examples of logical matches:  
        - Inferred: "Chemical Processing" → Available: "Chemical Manufacturing" (`Forced-Mapping`: "No").  
        - Inferred: "Electronics Production" → Available: "Electronics Manufacturing" (`Forced-Mapping`: "No").  
    - Examples of forced mappings:  
        - Inferred: "Nanotechnology Production" → Available: "Advanced Manufacturing" (`Forced-Mapping`: "Yes").  
        - Inferred: "Eco-friendly Systems Design" → Available: "Green Manufacturing" (`Forced-Mapping`: "Yes").  

Provided List of Main-Industries:  
{main_industries}  

Important Notes:
    - Always assume that the user is referring to manufacturing unless the context explicitly suggests otherwise.  
    - Ensure that the output is strictly limited to the required JSON format and contains no explanations, reasoning, or comments.  
    - Do not provide additional text, explanations, or reasoning within the fields of the JSON object. For example, avoid including reasoning like "This matches because..." or "Assumed manufacturing based on context."  
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
    
    result_text = result.content.strip()

    # Extract JSON industry details using the new function
    extracted_details = extract_json_main_industry_details(result_text)

    # Validate against the provided list of Main Industries
    validated_data = copy.deepcopy(extracted_details)
    if extracted_details["Main-Industry"] not in main_industries and extracted_details["Main-Industry"] != "None":
        validated_data["Main-Industry"] = "Not Available in List"

    return extracted_details, validated_data

def extract_json_sub_sector_product(output: str) -> Dict[str, str]:
    """
    Extracts Sub-Sector and Product-related details from an LLM-generated response.

    Ensures:
    - Parsing of multiple JSON formats (valid JSON, inside code blocks, or loose text).
    - Properly structured and validated output.
    - Fallback handling in case of missing values.

    Returns:
    -------
    dict:
        {
            "Sub-Sector": str,
            "Original-Inferred-Sub-Sector": str,
            "Forced-Mapping": str,
            "Product": str
        }
    """

    # -- 1) Direct JSON Parsing --
    try:
        data_entire = json.loads(output.strip())
        if isinstance(data_entire, dict) and "Sub-Sector" in data_entire:
            return {
                "Sub-Sector": data_entire.get("Sub-Sector", "None"),
                "Original-Inferred-Sub-Sector": data_entire.get("Original-Inferred-Sub-Sector", "None"),
                "Forced-Mapping": data_entire.get("Forced-Mapping", "No"),
                "Product": data_entire.get("Product", "None"),
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # -- 2) Extract JSON blocks inside triple backticks --
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', output, flags=re.DOTALL)
    for block in code_blocks:
        text_block = block.strip()
        try:
            block_data = json.loads(text_block)
            if isinstance(block_data, dict) and "Sub-Sector" in block_data:
                return {
                    "Sub-Sector": block_data.get("Sub-Sector", "None"),
                    "Original-Inferred-Sub-Sector": block_data.get("Original-Inferred-Sub-Sector", "None"),
                    "Forced-Mapping": block_data.get("Forced-Mapping", "No"),
                    "Product": block_data.get("Product", "None"),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # -- 3) Fallback: Regex-based extraction --
    #    a) Pattern with curly braces (full JSON structure)
    fallback_pattern_braces = re.compile(
        r'\{\s*"Sub-Sector"\s*:\s*"([^"]+)"\s*,\s*"Original-Inferred-Sub-Sector"\s*:\s*"([^"]+)"\s*,\s*"Forced-Mapping"\s*:\s*"([^"]+)"\s*,\s*"Product"\s*:\s*"([^"]+)"\s*\}',
        flags=re.DOTALL
    )
    match_braces = fallback_pattern_braces.search(output)
    if match_braces:
        return {
            "Sub-Sector": match_braces.group(1),
            "Original-Inferred-Sub-Sector": match_braces.group(2),
            "Forced-Mapping": match_braces.group(3),
            "Product": match_braces.group(4),
        }

    #    b) Pattern without curly braces (loose JSON structure)
    fallback_pattern_no_braces = re.compile(
        r'"Sub-Sector"\s*:\s*"([^"]+)"|'
        r'"Original-Inferred-Sub-Sector"\s*:\s*"([^"]+)"|'
        r'"Forced-Mapping"\s*:\s*"([^"]+)"|'
        r'"Product"\s*:\s*"([^"]+)"',
        flags=re.DOTALL
    )
    matches = fallback_pattern_no_braces.findall(output)

    extracted_values = {
        "Sub-Sector": "None",
        "Original-Inferred-Sub-Sector": "None",
        "Forced-Mapping": "No",
        "Product": "None"
    }

    for match in matches:
        if match[0]: extracted_values["Sub-Sector"] = match[0]
        if match[1]: extracted_values["Original-Inferred-Sub-Sector"] = match[1]
        if match[2]: extracted_values["Forced-Mapping"] = match[2]
        if match[3]: extracted_values["Product"] = match[3]

    return extracted_values

def extract_sub_sector_and_product_for_scratch(
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

    # Define the prompt
    prompt_template = """
You are an expert in analyzing industry-building queries and extracting specific details.  

**CRITICAL INSTRUCTION: When determining Sub-Sector classification, focus ONLY on the product, service, or industry terms mentioned in the query. Completely ignore geographic locations (cities, states, countries) for sub-sector inference. Location information should not influence sub-sector selection in any way.**

Sub-Sector is the functional or operational category that immediately follows the Main-Industry in the hierarchy.  
It encompasses broader categories of related activities, processes, or areas of focus that form part of the Main-Industry.  

For example:  
- In the "Automobile" Main-Industry, possible Sub-Sectors include "Vehicle Assembly," "Automotive Components," or "Electric Vehicles."
- In the "Pharmaceuticals" Main-Industry, possible Sub-Sectors include "Allopathic Medicines," "Ayurvedic Medicines," or "Biotechnology."
- Sub-Sectors are not specific to individual products; they represent broader categories within the Main-Industry.

{context}

**MANDATORY CONSTRAINT: You MUST select the Sub-Sector value ONLY from the provided list below. You cannot create or invent sub-sector names that are not in this exact list.**

Provided List of Sub-Sectors (THESE ARE YOUR ONLY OPTIONS):  
{sub_sectors_str}  

**Product-to-Sub-Sector Mapping Rules (Location-Independent):**
For Manufacturing Industries:
- Spectacles/Eyeglasses → Look for "Medical Devices", "Optical Equipment", or closest precision manufacturing category
- Chalk/Calcium Carbonate → Look for "Basic Chemicals", "Construction Materials", or closest chemical processing category  
- Steel/Iron → Look for "Metal Processing", "Heavy Manufacturing", or closest metals category
- Textiles → Look for "Textile Manufacturing", "Fabric Production", or closest textile category
- Electronics → Look for "Electronics Manufacturing", "Components", or closest technology category

Based on the user's query, identify the following details:

1. Sub-Sector: First, infer or predict the sub-sector based on the context of the query.  
    - **Focus exclusively on product/service/industry keywords - NOT on location.**
    - In the majority of cases, users may not explicitly mention "manufacturing" or related terms but are still referring to manufacturing-related sub-sectors. Assume the query is about a manufacturing-related sub-sector unless it is clearly illogical to do so.  
    - The query may sometimes be vague or incomplete. In such cases, try to understand the implied intent and context to infer the appropriate sub-sector.  
    
    **STEP-BY-STEP PROCESS:**
    a) Identify what industry segment the query refers to (e.g., "spectacles" → "optical equipment manufacturing")
    b) Check if this exactly matches any item in the provided list above
    c) If YES: Use that exact match and set `"Forced-Mapping": "No"`
    d) If NO: Find the closest related option from the provided list and set `"Forced-Mapping": "Yes"`
    
    - If the inferred sub-sector can logically match any category from the provided list of Sub-Sectors, return the matched category from the list and set `"Forced-Mapping"` to `"No"`.  
    - If no exact logical match exists, identify the CLOSEST available sub-sector based on:
        * Raw materials used
        * Manufacturing processes
        * End-use applications
        * Product category
        * Industry segment overlap
    - **MANDATORY: Always attempt a forced mapping before returning "None"**
    - **Only return "None" if the query contains absolutely no industry/product context whatsoever**

2. Product: Identify the specific product the query refers to (e.g., "Cement," "Steel Rods").  
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
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.  

**VALIDATION RULES:**
- Your "Sub-Sector" field MUST contain EXACTLY one of these values from the provided list OR "None"
- If you cannot find any reasonable connection to the provided sub-sectors, only then return "None"
- If the "Sub-Sector" matches exactly what you inferred, set `"Forced-Mapping": "No"`
- If the "Sub-Sector" is different from what you initially inferred, set `"Forced-Mapping": "Yes"`

Logical Matching for Sub-Sectors:
    - A logical match occurs when the inferred sub-sector and an available sub-sector from the list are conceptually or functionally similar.  
    - Examples of logical matches:  
        - Inferred: "Electric Cars" → Available: "Electric Vehicles" (`Forced-Mapping`: `"No"`).  
        - Inferred: "Biological Research" → Available: "Biotechnology" (`Forced-Mapping`: `"No"`).  
    - Examples of forced mappings:  
        - Inferred: "Optical Equipment" → Available: "Precision Manufacturing" (`Forced-Mapping`: `"Yes"`).
        - Inferred: "Clean Energy Solutions" → Available: "Renewable Energy" (`Forced-Mapping`: `"Yes"`).  
        - Inferred: "Pharma Research Labs" → Available: "Biotechnology" (`Forced-Mapping`: `"Yes"`).  

**Examples:**
- Query: "spectacles manufacturing setup" 
  - Inferred: "Optical Equipment Manufacturing" 
  - Closest Available: "Precision Manufacturing" (if available)
  - Output: `"Sub-Sector": "Precision Manufacturing", "Original-Inferred-Sub-Sector": "Optical Equipment Manufacturing", "Forced-Mapping": "Yes"`

Output Constraints:  
    - The "Sub-Sector" field can ONLY contain values from the provided list or "None"
    - Do not create new sub-sector names
    - Ensure that the output is strictly limited to the required JSON format and contains no explanations, reasoning, or comments.  
    - Do not provide additional text, explanations, or reasoning within the fields of the JSON object. For example, avoid including reasoning like "This matches because..." or "Assumed manufacturing based on context."  
    - Each field in the JSON must only contain the exact extracted information or the specified fallback values (e.g., `"None"`).  

Output Format:  
Output the result strictly as a JSON object in the following format:  
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
    
    # Extract JSON response using the new function
    extracted_details = extract_json_sub_sector_product(result.content.strip())

    # Validation: Check if the extracted sub-sector exists in the provided list
    validated_data = copy.deepcopy(extracted_details)
    if extracted_details["Sub-Sector"] not in sub_sectors and extracted_details["Sub-Sector"] != "None":
        validated_data["Sub-Sector"] = "Not Available in List"

    return extracted_details, validated_data

def extract_json_segment_and_product(output: str) -> Dict[str, str]:
    """
    Extracts segment and product details from an LLM-generated response.

    Ensures:
    - Parsing of multiple JSON formats (valid JSON, inside code blocks, or loose text).
    - Fields return "None" if missing.
    
    Returns:
    -------
    dict:
        {
            "Segment": str,
            "Original-Inferred-Segment": str,
            "Forced-Mapping": str,
            "Product": str
        }
    """

    # -- 1) Direct JSON Parsing --
    try:
        data_entire = json.loads(output.strip())
        if isinstance(data_entire, dict) and "Segment" in data_entire:
            return {
                "Segment": data_entire.get("Segment", "None"),
                "Original-Inferred-Segment": data_entire.get("Original-Inferred-Segment", "None"),
                "Forced-Mapping": data_entire.get("Forced-Mapping", "No"),
                "Product": data_entire.get("Product", "None"),
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # -- 2) Extract JSON blocks inside triple backticks --
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', output, flags=re.DOTALL)
    for block in code_blocks:
        text_block = block.strip()
        try:
            block_data = json.loads(text_block)
            if isinstance(block_data, dict) and "Segment" in block_data:
                return {
                    "Segment": block_data.get("Segment", "None"),
                    "Original-Inferred-Segment": block_data.get("Original-Inferred-Segment", "None"),
                    "Forced-Mapping": block_data.get("Forced-Mapping", "No"),
                    "Product": block_data.get("Product", "None"),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # -- 3) Fallback: Regex-based extraction --
    #    a) Pattern with curly braces (full JSON structure)
    fallback_pattern_braces = re.compile(
        r'\{\s*"Segment"\s*:\s*"([^"]+)"\s*,\s*"Original-Inferred-Segment"\s*:\s*"([^"]+)"\s*,\s*"Forced-Mapping"\s*:\s*"([^"]+)"\s*,\s*"Product"\s*:\s*"([^"]+)"\s*\}',
        flags=re.DOTALL
    )
    match_braces = fallback_pattern_braces.search(output)
    if match_braces:
        return {
            "Segment": match_braces.group(1),
            "Original-Inferred-Segment": match_braces.group(2),
            "Forced-Mapping": match_braces.group(3),
            "Product": match_braces.group(4),
        }

    #    b) Pattern without curly braces (loose JSON structure)
    fallback_pattern_no_braces = re.compile(
        r'"Segment"\s*:\s*"([^"]+)"|'
        r'"Original-Inferred-Segment"\s*:\s*"([^"]+)"|'
        r'"Forced-Mapping"\s*:\s*"([^"]+)"|'
        r'"Product"\s*:\s*"([^"]+)"',
        flags=re.DOTALL
    )
    matches = fallback_pattern_no_braces.findall(output)

    extracted_values = {
        "Segment": "None",
        "Original-Inferred-Segment": "None",
        "Forced-Mapping": "No",
        "Product": "None"
    }

    for match in matches:
        if match[0]: extracted_values["Segment"] = match[0]
        if match[1]: extracted_values["Original-Inferred-Segment"] = match[1]
        if match[2]: extracted_values["Forced-Mapping"] = match[2]
        if match[3]: extracted_values["Product"] = match[3]

    # -- If nothing worked, return a default response --
    return extracted_values

def extract_segment_and_product_for_scratch(
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
You are an expert in analyzing industry-building queries and extracting specific details.

**CRITICAL INSTRUCTION: When determining Segment classification, focus ONLY on the product, service, or industry terms mentioned in the query. Completely ignore geographic locations (cities, states, countries) for segment inference. Location information should not influence segment selection in any way.**

Segment is the logical grouping of products, which comes immediately next in the hierarchy after the Sub-Sector.
Sub-Sector itself is the functional or operational category following the Main-Industry in the hierarchy.

For example:
- In the "Automobile" Main-Industry, a Sub-Sector like "Automotive Components" may have Segments such as "Engines," "Batteries," or "Tires."
- In the "Pharmaceuticals" Main-Industry, a Sub-Sector like "Allopathic Medicines" may have Segments like "Antibiotics" or "Analgesics."

{context}

**MANDATORY CONSTRAINT: You MUST select the Segment value ONLY from the provided list below. You cannot create or invent segment names that are not in this exact list.**

Provided List of Segments (THESE ARE YOUR ONLY OPTIONS):  
{segments_str}

**Product-to-Segment Mapping Rules (Location-Independent):**
For Manufacturing Industries:
- Chalk/Calcium Carbonate → Look for "Basic Chemicals", "Chemical Products", or closest chemical manufacturing segment
- Metal products → Look for "Metalworking Machinery", "Metal Products", or closest metal processing segment
- Machinery/Equipment → Look for "Industrial Machinery", "Manufacturing Equipment", or closest equipment segment
- Electronics → Look for "Electronic Components", "Electronic Equipment", or closest electronics segment

Based on the user's query, identify the following details:

1. Segment: First, infer or predict the segment based on the context of the query.
    - **Focus exclusively on product/service/industry keywords - NOT on location.**
    - In the majority of cases, users may not explicitly mention "manufacturing" or related terms but are still referring to manufacturing-related segments. Assume the query is about manufacturing unless it is clearly illogical to do so.
    - The query may sometimes be vague or incomplete. In such cases, try to understand the implied intent and context to infer the appropriate segment.
    
    **STEP-BY-STEP PROCESS:**
    a) Identify what specific product/manufacturing activity the query refers to
    b) Check if this exactly matches any item in the provided list above
    c) If YES: Use that exact match and set `"Forced-Mapping": "No"`
    d) If NO: Find the closest related option from the provided list and set `"Forced-Mapping": "Yes"`
    
    - If the inferred segment can logically match any category from the provided list of Segments, return the matched category from the list and set `"Forced-Mapping"` to `"No"`.
    - If no exact logical match exists, identify the CLOSEST available segment based on:
        * Product category similarity
        * Manufacturing process type
        * Raw materials used
        * End-use application
        * Industry segment overlap
    - **MANDATORY: Always attempt a forced mapping before returning "None"**
    - **Only return "None" if the query contains absolutely no industry/product/manufacturing context whatsoever**

2. Product: Identify the specific product the query refers to (e.g., "Cement," "Steel Rods").  
    - **Focus exclusively on product terms - NOT on location.**
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
    - If no product is mentioned or the term does not logically fit as a product, return `"None"`.  

**VALIDATION RULES:**
- Your "Segment" field MUST contain EXACTLY one of these values from the provided list OR "None"
- If you cannot find any reasonable connection to the provided segments, only then return "None"
- If the "Segment" matches exactly what you inferred, set `"Forced-Mapping": "No"`
- If the "Segment" is different from what you initially inferred, set `"Forced-Mapping": "Yes"`

Logical Matching for Segments:
- A logical match occurs when the inferred segment and an available segment from the list are conceptually or functionally similar.
- Examples of logical matches:
    - Inferred: "Metal Equipment" → Available: "Metalworking Machinery" (`Forced-Mapping`: "No").
    - Inferred: "Metal Fabrication Tools" → Available: "Metalworking Machinery" (`Forced-Mapping`: "No").
- Examples of forced mappings:
    - Inferred: "Basic Chemical Manufacturing" → Available: "Industrial Chemicals" (if closest match) (`Forced-Mapping`: "Yes").
    - Inferred: "Advanced Robotics Systems" → Available: "Automation Equipment" (`Forced-Mapping`: "Yes").
    - Inferred: "Metal Gear Production" → Available: "Metalworking Machinery" (`Forced-Mapping`: "Yes").

**Examples:**
- Query: "chalk manufacturing setup in Delhi" 
  - Inferred: "Basic Chemical Manufacturing" 
  - Closest Available: "Chemical Products" (if available in list)
  - Output: `"Segment": "Chemical Products", "Original-Inferred-Segment": "Basic Chemical Manufacturing", "Forced-Mapping": "Yes"`

Output Format:
- The "Segment" field can ONLY contain values from the provided list or "None"
- Do not create new segment names
- Ensure that the output strictly adheres to the specified JSON format without any additional reasoning, explanations, or comments.
- Do not include any reasoning or justification in the fields. For example, avoid entries such as `"This matches because..."` or `"Assumed based on the context..."`.
- Each field should only contain the extracted information or the specified fallback values (e.g., "None").
- If the query mentions only a location but no specific industry or product context, do not infer the segment from prior knowledge of the location. Instead, return None.

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

    # Extract JSON response using the robust function
    result_content = result.content.strip()
    extracted_data = extract_json_segment_and_product(result_content)

    # Validate against the provided list of Segments
    validated_data = copy.deepcopy(extracted_data)
    if extracted_data["Segment"] not in segments and extracted_data["Segment"] != "None":
        validated_data["Segment"] = "Not Available in List"

    return extracted_data, validated_data

def extract_json_capacity_details(output: str) -> Dict[str, Union[float, str]]:
    """
    Extracts capacity-related details from an LLM-generated response.

    Ensures:
    - Parsing of multiple JSON formats (valid JSON, inside code blocks, or loose text).
    - Numeric values are properly formatted as valid floats.
    - Fields return "None" if missing.

    Returns:
    -------
    dict:
        {
            "Capacity": float or "None",
            "Capacity Unit": str or "None",
            "Time Period": str or "None"
        }
    """

    def normalize_number(value):
        """
        Ensures extracted capacity values are always valid floats, removing commas if necessary.
        Converts word-based numbers into numeric format when possible.
        """
        if value is None:
            return "None"

        # NEW FIX: If already a number, return as float
        if isinstance(value, (int, float)):
            return float(value)

        # Remove commas and spaces from numeric values
        value = str(value).replace(",", "").strip()

        # Convert to float if possible
        try:
            return float(value)
        except ValueError:
            return "None"  # If conversion fails, return "None"

    # -- 1) Direct JSON Parsing --
    try:
        data_entire = json.loads(output.strip())
        if isinstance(data_entire, dict) and "Capacity" in data_entire:
            return {
                "Capacity": normalize_number(data_entire.get("Capacity", "None")),
                "Capacity Unit": data_entire.get("Capacity Unit", "None"),
                "Time Period": data_entire.get("Time Period", "None"),
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # -- 2) Extract JSON blocks inside triple backticks --
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', output, flags=re.DOTALL)
    for block in code_blocks:
        text_block = block.strip()
        try:
            block_data = json.loads(text_block)
            if isinstance(block_data, dict) and "Capacity" in block_data:
                return {
                    "Capacity": normalize_number(block_data.get("Capacity", "None")),
                    "Capacity Unit": block_data.get("Capacity Unit", "None"),
                    "Time Period": block_data.get("Time Period", "None"),
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # -- 3) Fallback: Regex-based extraction --
    #    a) Pattern with curly braces (full JSON structure)
    fallback_pattern_braces = re.compile(
        r'\{\s*"Capacity"\s*:\s*"([^"]+)"\s*,\s*"Capacity Unit"\s*:\s*"([^"]+)"\s*,\s*"Time Period"\s*:\s*"([^"]+)"\s*\}',
        flags=re.DOTALL
    )
    match_braces = fallback_pattern_braces.search(output)
    if match_braces:
        return {
            "Capacity": normalize_number(match_braces.group(1)),
            "Capacity Unit": match_braces.group(2),
            "Time Period": match_braces.group(3),
        }

    #    b) Pattern without curly braces (loose JSON structure)
    fallback_pattern_no_braces = re.compile(
        r'"Capacity"\s*:\s*"([^"]+)"|'
        r'"Capacity Unit"\s*:\s*"([^"]+)"|'
        r'"Time Period"\s*:\s*"([^"]+)"',
        flags=re.DOTALL
    )
    matches = fallback_pattern_no_braces.findall(output)

    extracted_values = {"Capacity": "None", "Capacity Unit": "None", "Time Period": "None"}
    
    for match in matches:
        if match[0]: extracted_values["Capacity"] = normalize_number(match[0])
        if match[1]: extracted_values["Capacity Unit"] = match[1]
        if match[2]: extracted_values["Time Period"] = match[2]

    # -- If nothing worked, return a default response --
    return extracted_values

def extract_capacity_details(user_query, llm):
    """
    Extracts details related to capacity, capacity unit, and time period from the user query.

    Uses an LLM to analyze the query and return structured details.

    Args:
        user_query (str): The message input from the user.

    Returns:
        dict: A dictionary containing "Capacity" (float), "Capacity Unit" (string), and "Time Period" (string).
    """

    # Define the prompt
    prompt_template = """
    You are an expert in analyzing industry-building queries and extracting specific details. 
    Your task is to analyze the provided query and extract the following information, ensuring accurate interpretation of industry-specific abbreviations and logical inference for missing details.

    Extract the following details from the query:

    1. Capacity: The numeric or descriptive quantity being referred to (e.g., "1", "100", "50000").  
    - This represents the actual quantity or amount the user wants to produce, build, or manufacture.  
    - Extract the numeric part separately from any units or time-related context.  
    - Ensure that numbers are always extracted in plain numeric format (without commas or spaces).  
    - DO NOT return numbers with commas (e.g., "1,000,000"). Convert it to "1000000".  
    - If the capacity is written in words (e.g., "Fifty Thousand", "Five Million"), convert it into numeric format (e.g., "50000", "5000000").  
    - If no capacity is found in the query, return `"None"`.  

    2. Capacity Unit: The unit of measurement associated with the capacity.  
    - For measurable products (e.g., cement, chemicals, oil), identify logical units like "Tonnes", "Liters", "MegaWatts".  
    - For countable products (e.g., bottles, bags, books), use the product name as the unit if explicitly mentioned (e.g., "1000 Bottles").  
    - Recognize and interpret common industry abbreviations:
        - "MTPA" → Capacity Unit: "Million Tonnes", Time Period: "Per Annum".
        - "TPA" → Capacity Unit: "Tonnes", Time Period: "Per Annum".
        - "MW" → Capacity Unit: "MegaWatts", Time Period: "None" (if not explicitly stated).  
    - If no logical unit is specified or the unit is illogical, return `"None"`.  

    3. Time Period: The recurring frequency at which the capacity is achieved.  
    - Examples include "Per Annum" (Yearly), "Per Month", or "Per Day".  
    - If the time period is unconventional but can be inferred from the context (e.g., from abbreviations like "MTPA"), return the inferred value.  
    - If no time period is mentioned or cannot be inferred, return `"None"`.  

    Important Notes:  
    - Strictly enforce numeric formatting: Extract numbers in pure numeric format (no commas or formatting).  
    - If a number is written in words, convert it into numeric format before returning it.  
    - Abbreviations like "MTPA", "TPA", and "MW" must be interpreted correctly, and their components split into Capacity, Capacity Unit, and Time Period.  
    - Handle vague or incomplete queries logically. Example:  
        - Query: `"1 MTPA Cement Factory"` → Capacity: `"1"`, Capacity Unit: `"Million Tonnes"`, Time Period: `"Per Annum"`.  
        - Query: `"100 MW Plant"` → Capacity: `"100"`, Capacity Unit: `"MegaWatts"`, Time Period: `"None"`.  

    Output Format:  
    Return the extracted values strictly as a JSON object:  
    {{
        "Capacity": <Extracted Capacity as float or 'None'>,
        "Capacity Unit": <Extracted Capacity Unit or 'None'>,
        "Time Period": <Extracted Time Period or 'None'>
    }}

    Query: {query}

    Provide only the JSON object in the required format.
    """

    # Create the prompt using the correctly formatted variables
    prompt = PromptTemplate(
        input_variables=["query"],
        template=prompt_template
    )

    # Create the LLM chain
    chain = prompt | llm

    # Invoke the query through the chain
    result = chain.invoke({"query": user_query})
    update_llm_token(result)
    result_text = result.content.strip()

    # Extract JSON capacity details using the new function
    extracted_details = extract_json_capacity_details(result_text)

    return extracted_details

def generate_ai_message(state, history, missing_fields, attempt_count, llm):
    """
    Generate a context-aware AI message for missing fields using the LLM.
    Args:
    - state (dict): Tracks previously provided information.
    - history (list): Chat history for context.
    - missing_fields (list): Fields still missing information.
    - attempt_count (int): The number of attempts made to gather the missing details.

    Returns:
    - str: A dynamically generated message for the user.
    """

    # Create a prompt to generate the message
    message_prompt = """
    You are a professional assistant helping to gather business details for a user query.  
    Based on the provided context and history, create a professional, polite, and clear message  
    to request the missing details from the user. The message should be concise, clear, and easy to understand, while providing all necessary information for the user to respond appropriately.

    Consider the following information:  
    - Provided information: {provided_information}  
    - Missing information: {missing_fields}  
    - Attempt count: {attempt_count} (1 means first attempt, 2 means second, etc.)  
    - Chat history: {chat_history}  

    Guidelines:  
    - Use the latest user message from the chat history to guide your response, ensuring it directly addresses their input.

    - Avoid Explanations or Assumptions:  
    - Do NOT include unnecessary explanations, assumptions, or robotic acknowledgments like "It seems you are asking about..." or "I’ve reviewed your message."  
    - Focus on directly providing value or asking for the missing details without redundant statements.  

    - Single Paragraph Output:  
    - Ensure the response is concise and presented in a single paragraph.  
    - Avoid splitting the message into multiple paragraphs.

    - Strict Hierarchical Reference for Context:  
    - Always refer to only the highest available level of specificity in the provided details, following this hierarchy:  
        1. Product (if available, only mention this and ignore Segment, Sub-Sector, and Main-Industry).  
        2. If Product is missing or "None," then mention Segment.  
        3. If Segment is missing, "None," or "Not Available in List," then mention Sub-Sector.  
        4. If Sub-Sector is missing, "None," or "Not Available in List," then mention Main-Industry.  
    - Do NOT mention or refer to lower hierarchy levels if a higher level (like Product or Segment) is already available.  
    - Avoid mentioning multiple levels in one response; always stick to the highest available level only.

    - Provide Examples for All Missing Details:  
    - If asking for Capacity, provide numeric examples relevant to the context, such as "1000 or 5000."  
    - If asking for Capacity Unit, provide clear examples like "liters or tonnes."  
    - If asking for Time Period, offer examples like "per day, per month, or per annum."  
    - Integrate these examples naturally into the question, making it clear but concise.  

    - Example of a Well-Formulated Question:  
        - "To proceed further, could you please provide the capacity you're considering, such as 1000 or 5000 kilograms, the unit of measurement like kilograms or tonnes, and the time period such as per day, per month, or per annum for your dairy processing business?"  

    - Handling Greetings:  
    - If the user greets (e.g., "Hi", "Hello", "Good morning"), warmly acknowledge the greeting (e.g., "Hello! It’s great to connect with you.")  
    - Transition directly to ask for the missing details without including disclaimers or unrelated guidance.

    - Handling Special Days:  
    - If the user mentions a special occasion (e.g., birthday, anniversary), warmly acknowledge it (e.g., "Happy Birthday! Wishing you all the best.")  
    - Transition smoothly to request the missing details without including disclaimers or unrelated guidance.

    - Handling Negative Emotions:  
    - If the user expresses frustration, anger, or sadness, respond empathetically (e.g., "I’m sorry to hear that. I’m here to help in any way I can.")  
    - Transition smoothly to request the missing details while maintaining a supportive tone.

    - Handling Off-Topic Queries:
    - If the latest user message is unrelated to business, industry, or construction (e.g., entertainment, sports, programming, casual conversation), the assistant must NOT mention, refer to, or attempt to connect that content to any business context.
    - Instead, seamlessly redirect to the task by asking for the required business information, without referencing the user’s message.
    - Example: "Could you please share the product or service you deal with so I can assist you further?"
    - The redirection should be concise (2–3 lines), professional, and focused solely on gathering the missing business details.
    - Under no circumstances should the off-topic content (e.g., movie names, code, sports) be included in or influence the wording of the redirected business-related question.
    - The assistant must always use a clean, general phrasing like: "Could you please share the product or service you deal with so I can assist you further?" without inserting any content from the off-topic user message.

    - Transitioning to Missing Information:  
    - Ensure the transition to the missing details request feels natural and engaging.  
    - Use clear and professional phrases like "To proceed further," "Additionally," or "To help you better" to connect the response seamlessly to the missing details request.

    - First Five Attempts:  
    - Focus solely on asking for the missing details concisely and clearly.  
    - Do not acknowledge or repeat the provided information during the first five attempts.  

    - After Five Attempts:  
    - Briefly acknowledge the details already provided by the user but without robotic phrasing.  
    - Request the missing details concisely and clearly.

    - Asking for Specific Missing Details:  
    - If "Main-Industry" or "Sub-Sector" (or both) are missing, ask about the product or service the user deals with, but do NOT refer to them as "Main-Industry" or "Sub-Sector" in the message.  

    Output Requirements:  
    - The message must be concise, clear, and in a single paragraph.  
    - Do NOT include any explanations, reasoning, or assumptions about the missing details, user input, or context.  
    - For the first five attempts, focus only on requesting the missing details.  
    - After five attempts, briefly acknowledge the provided details, then request the missing details concisely.  
    - The final message should be very concise—no more than 2 to 3 lines—while still being clear, complete, and informative.  
    - Ensure the request includes all the missing details in a professional and easy-to-understand manner, following the prompt’s earlier instructions.  
    - When responding to off-topic inputs, do not mention the off-topic subject—just proceed to ask for the relevant business details as normal.
    """

    # Format the provided details and missing details
    provided_info = {k: v for k, v in state.items() if v != "None"}

    # Create the prompt for the LLM
    prompt = PromptTemplate(
        input_variables=["provided_information", "missing_fields", "attempt_count", "chat_history"],
        template=message_prompt
    )
    chain = prompt | llm

    # Generate the message
    result = chain.invoke({
        "provided_information": provided_info,
        "missing_fields": missing_fields,
        "attempt_count": attempt_count,
        "chat_history": history,
    })
    update_llm_token(result)
    return result.content.strip()

def gather_industry_details(query, main_industries, llm,chatId, additional_class_response = None):
    """
    Gathers industry details from the user query while maintaining a conversation history.
    
    Args:
    - query (str): The latest user query or follow-up response.
    - main_industries (list): List of valid main industries.
    - state (dict): Tracks previously provided information.

    Returns:
    - tuple: A dictionary containing the extracted details and the updated conversation history.
    """
    state = get_state(f"QIND_state_{chatId}") or None
    if state is None:
        state = {'Main-Industry': 'None', 'Sub-Sector': 'None','Segment':'None', 'Capacity': 'None', 'Capacity Unit': 'None', 
                 'Time Period': 'None', 'Product': 'None','product_attempt_count':0,'capacity_attempt_count':0, "KEYWORDS": None, "Additional_class_response": None}
        save_state(state,f"QIND_state_{chatId}")
    chat_history = get_chat(f"chat_{chatId}") or []

    # Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    refined_query = query
    
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    
    result = classify_industry_setup_query(refined_query, llm)
    user_intention = result["classification_category"]
    with open("testlog.txt", "a") as file:
        file.write(f"\nSUB CLASS {user_intention} for chatId {chatId}")
    if user_intention == "Negatively Intended Query":
        message = respond_to_negative_query(
            user_intention, 
            append_user_to_history=False, 
            append_AI_to_history=False, 
            llm=llm,
            chatId=chatId)
        
        response = {
            "Ai_response": message,
            "Is_confirmation" : False,
            "state":state,
            "options": None,
            "User Intention": user_intention,
            "Trigger_Lead_Generation":False
        }
        return response
    else:
        keyword_list = extract_important_words(refined_query, "Query to build industry from Scratch")
        state["KEYWORDS"] = keyword_list
        state["Additional_class_response"] = additional_class_response or state.get("Additional_class_response")

        save_state(state,f"QIND_state_{chatId}")
        
        with open("log.txt", "a") as file:
                file.write(f"\nstate2 {state}")
        # Extract industry details from the refined query
        is_changed = False
        extracted_data,validated_data =  extract_main_industry_and_product_for_scratch(refined_query,main_industries,llm)
        if validated_data['Main-Industry'] != 'None' and validated_data["Main-Industry"] != state['Main-Industry']:
            state["Main-Industry"] = validated_data["Main-Industry"]
            state["Product"] = validated_data["Product"]
            state["Segment"] = 'None'
            state['Capacity'] = 'None'
            state["Capacity Unit"] = 'None'
            state["Time Period"] = 'None'
            state['product_attempt_count'] = 0
            state['capacity_attempt_count'] = 0
            save_state(state,f"QIND_state_{chatId}")
            is_changed = True
        
        if state['Main-Industry'] == 'None' and state['Product'] == 'None':
            capacity_json = extract_capacity_details(refined_query,llm)
            
            # Check if at least one value is not 'None'            
            if any(value != 'None' for value in capacity_json.values()):
                # Update only if the value is different and not 'None'
                for key, value in capacity_json.items():
                    if value != 'None' and state.get(key) != value:
                        state[key] = value
                save_state(state,f"QIND_state_{chatId}")

            chat_history = get_chat(f"chat_{chatId}")
            state['product_attempt_count'] = state['product_attempt_count'] + 1
            save_state(state,f"QIND_state_{chatId}")
            message = generate_ai_message(state,Chat_history_normal,['Product'],state['product_attempt_count'],llm_70b_vers_creative)
            
            return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state":state,
                    "options": None,
                    "User Intention": user_intention,
                    "Trigger_Lead_Generation":False
                    }
        
        elif state["Main-Industry"] == 'Not Available in List':
            capacity_json = extract_capacity_details(refined_query,llm)
            
            if any(value != 'None' for value in capacity_json.values()):
                # Update only if the value is different and not 'None'
                for key, value in capacity_json.items():
                    if value != 'None' and state.get(key) != value:
                        state[key] = value
                save_state(state,f"QIND_state_{chatId}")
            missing_fields = [field for field, value in capacity_json.items() if value == 'None']
            if len(missing_fields) == 0:
                message = INDUSTRY_NOT_AVAILABLE_MSG
                return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state":state,
                    "options": None,
                    "User Intention": user_intention,
                    "Trigger_Lead_Generation":True
                    }
            else:
                chat_history = get_chat(f"chat_{chatId}")
                state['capacity_attempt_count'] = state['capacity_attempt_count'] + 1
                save_state(state,f"QIND_state_{chatId}")
                message = generate_ai_message(state,Chat_history_normal,missing_fields,state['capacity_attempt_count'],llm_70b_vers_creative)
                
                return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state":state,
                    "options": None,
                    "User Intention": user_intention,
                    "Trigger_Lead_Generation":False
                    }
            
        elif state["Main-Industry"] != 'None':
            capacity_json = extract_capacity_details(refined_query,llm)

            if any(value != 'None' for value in capacity_json.values()):
                # Update only if the value is different and not 'None'
                for key, value in capacity_json.items():
                    if value != 'None' and state.get(key) != value:
                        state[key] = value
                save_state(state,f"QIND_state_{chatId}")
            final_json = get_json_for_industry()
            if state['Sub-Sector'] == 'None' or is_changed:
                
                sub_sector = get_sub_sectors(final_json,state["Main-Industry"])
                sub_extracted_data,sub_validated_data = extract_sub_sector_and_product_for_scratch(refined_query,sub_sector,llm,state["Main-Industry"],state["Product"])
            
                state = get_state(f"QIND_state_{chatId}")
                state["Sub-Sector"] = sub_validated_data["Sub-Sector"]
                state["Product"] = sub_validated_data["Product"]
                
                save_state(state,f"QIND_state_{chatId}")
            # state = get_state(f"QIND_state_{chatId}")
            if state['Sub-Sector'] != 'None' and state['Sub-Sector'] != 'Not Available in List':
                segments = get_segments(final_json,state["Main-Industry"],state['Sub-Sector'])

                segment_extracted_data,segment_validated_data = extract_segment_and_product_for_scratch(refined_query,segments,llm,main_industries,state['Sub-Sector'],state["Product"])
                
                state = get_state(f"QIND_state_{chatId}")
                state["Segment"] = segment_validated_data["Segment"] 
                state["Product"] = segment_validated_data["Product"]
                
                save_state(state,f"QIND_state_{chatId}")
                capicity_pending_list = get_keys_for_capicity(chatId)
                if len(capicity_pending_list) > 0:
                    chat_history = get_chat(f"chat_{chatId}")
                    state['capacity_attempt_count'] = state['capacity_attempt_count'] + 1
                    save_state(state,f"QIND_state_{chatId}")
                    message = generate_ai_message(state,Chat_history_normal,capicity_pending_list,state['capacity_attempt_count'],llm_70b_vers_creative)
                    
                    return {"Ai_response": message,
                        "Is_confirmation" : False,
                        "state":state,
                        "options": None,
                        "User Intention": user_intention,
                        "Trigger_Lead_Generation":False
                        }
                else:
                    selected_option = next(
                        (state.get(key) for key in ['Product', 'Segment', 'Sub-Sector', 'Main-Industry'] if state.get(key) not in [None, 'None']),
                        ''
                    )

                    confirmation_message_class_1 = (
                        f"Based on your query, we’ve understood that you are looking for **land options** to **build a new industrial unit** "
                        f"for **{selected_option}** production, with a planned capacity of **{state.get('Capacity')} {state.get('Capacity Unit')} {state.get('Time Period')}**. <br/><br/>"
                        f"Please confirm if this information is correct."
                        )
                    
                    confirmation_buttons_class_1 = [
                        {"label": "Yes, this is correct", "value": "Intent to Build Industry from Scratch"},
                        {"label": "No, this is not correct", "value": None}
                        ]
                    
                    confirmation_message_class_2 = (
                        f"Based on your query, we’ve understood that you are looking to **acquire an existing industrial facility** "
                        f"for **{selected_option}** production, with a planned capacity of **{state.get('Capacity')} {state.get('Capacity Unit')} {state.get('Time Period')}**. <br/><br/>"
                        f"Please confirm if this information is correct."
                    )

                    confirmation_buttons_class_2 = [
                        {"label": "Yes, this is correct", "value": "Intent to Acquire Existing Industrial Infrastructure"},
                        {"label": "No, this is not correct", "value": None}
                    ]

                    confirmation_message_class_3 = (
                        f"Great! We’re ready to assist you in setting up your **{selected_option}** production unit with a planned capacity of "
                        f"**{state.get('Capacity')} {state.get('Capacity Unit')} {state.get('Time Period')}**.<br/><br/>"
                        f"To help you move forward, you can choose to explore **land options**, **existing industrial facilities**, or **both** — whatever suits your plans best.<br/><br/>"
                        f"You may also choose to refine your requirements if you'd like us to reassess the details."
                    )

                    confirmation_buttons_class_3 = [
                        {"label": "Explore Land for New Unit", "value": "Intent to Build Industry from Scratch"},
                        {"label": "Explore Existing Facilities", "value": "Intent to Acquire Existing Industrial Infrastructure"},
                        {"label": "View All Setup Options", "value": "Intent to Evaluate Both Building from Scratch and Acquiring Existing Infrastructure"},
                        {"label": "Refine Requirements", "value": None}
                    ]

                    confirmation_message_class_6 = (
                        f"Based on your query, we’ve understood that you are interested in exploring **both** options — "
                        f"**land for setting up a new industrial unit** as well as **acquiring an existing industrial facility** "
                        f"for **{selected_option}** production, with a planned capacity of **{state.get('Capacity')} {state.get('Capacity Unit')} {state.get('Time Period')}**. <br/><br/>"
                        f"Please confirm if this information is correct."
                    )

                    confirmation_buttons_class_6 = [
                        {"label": "Yes, this is correct", "value": "Intent to Evaluate Both Building from Scratch and Acquiring Existing Infrastructure"},
                        {"label": "No, this is not correct", "value": None}
                    ]

                    class_confirmation_message_mapping = {
                        "Intent to Build Industry from Scratch": {
                            "Message": confirmation_message_class_1, 
                            "Options": confirmation_buttons_class_1
                        },
                        "Intent to Acquire Existing Industrial Infrastructure": {
                            "Message": confirmation_message_class_2,
                            "Options": confirmation_buttons_class_2
                        },
                        "Intent to Set Up Industry with Unspecified Build or Buy Intent": {
                            "Message": confirmation_message_class_3,
                            "Options": confirmation_buttons_class_3
                        },
                        "Intent to Evaluate Both Building from Scratch and Acquiring Existing Infrastructure": {
                            "Message": confirmation_message_class_6,
                            "Options": confirmation_buttons_class_6
                        },
                    }

                    confirmation_message_static_dict = class_confirmation_message_mapping.get(
                        user_intention,
                        class_confirmation_message_mapping["Intent to Set Up Industry with Unspecified Build or Buy Intent"]
                    )

                    confirmation_message_static = confirmation_message_static_dict["Message"]
                    # response_validation = state.get("Additional_class_response")
                    # confirmation_message_static += f"<br/><br/>**Note**: {response_validation}" if response_validation is not None else ""
                    confirmation_message_options = confirmation_message_static_dict["Options"]
                    # dynamic_confirmation_message = generate_dynamic_confirmation_message(confirmation_message_static, llm_70b_vers_creative)
                    
                    response = {
                        "Ai_response" : confirmation_message_static,
                        "Is_confirmation" : True,                                   
                        "validated_data" : segment_validated_data,
                        "state" : state,
                        "options": confirmation_message_options,
                        "User Intention": user_intention,
                        "Trigger_Lead_Generation":False
                    }
                    return response

            elif state['Sub-Sector'] == 'Not Available in List':
                capicity_pending_list = get_keys_for_capicity(chatId)
                if len(capicity_pending_list) > 0:
                    chat_history = get_chat(f"chat_{chatId}")
                    state['capacity_attempt_count'] = state['capacity_attempt_count'] + 1
                    save_state(state,f"QIND_state_{chatId}")
                    message = generate_ai_message(state,Chat_history_normal,capicity_pending_list,state['capacity_attempt_count'],llm_70b_vers_creative)
                    
                    return {"Ai_response": message,
                        "Is_confirmation" : False,
                        "state": state,
                        "options": None,
                        "User Intention": user_intention,
                        "Trigger_Lead_Generation":False
                        }
                else:
                    message = INDUSTRY_NOT_AVAILABLE_MSG
                    return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state":state,
                    "options": None,
                    "User Intention": user_intention,
                    "Trigger_Lead_Generation":True
                    }

            else:
                chat_history = get_chat(f"chat_{chatId}")
                state['product_attempt_count'] = state['product_attempt_count'] + 1
                save_state(state,f"QIND_state_{chatId}")
                message = generate_ai_message(state,Chat_history_normal,['Product'],state['product_attempt_count'],llm_70b_vers_creative)
               
                return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state":state,
                    "options": None,
                    "User Intention": user_intention,
                    "Trigger_Lead_Generation":False}
        
        else:
            response = {
                "Ai_response": "Please enter valid query with some details.",
                "Is_confirmation" : False,
                "state":state,
                "options": None,
                "User Intention": user_intention,
                "Trigger_Lead_Generation":False
            }
            return response

def extract_json_time_conversion(output):
    """
    Extracts the "Multiplier" value from the LLM output for time conversion.
    
    It handles multiple cases:
    1) Direct JSON parsing of the entire output (if it's valid JSON).
    2) Extracting code blocks enclosed in triple backticks and parsing as JSON.
    3) Regex fallbacks:
       - (a) JSON-like pattern with curly braces
       - (b) Partial JSON without curly braces

    Returns:
    -------
    dict:
        {
            "Multiplier": float
        }

    If extraction fails, returns a safe fallback:
        {"Multiplier": 1.0}
    """

    # --- 1) Direct JSON parsing (entire output) ---
    try:
        entire_data = json.loads(output.strip())
        if isinstance(entire_data, dict) and "Multiplier" in entire_data:
            return {"Multiplier": float(entire_data["Multiplier"])}
    except json.JSONDecodeError:
        pass  # Not valid JSON in the entire string

    # --- 2) Extract code blocks (wrapped in triple backticks) and parse as JSON ---
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', output, flags=re.DOTALL)
    for block in code_blocks:
        text_block = block.strip()
        try:
            block_data = json.loads(text_block)
            if isinstance(block_data, dict) and "Multiplier" in block_data:
                return {"Multiplier": float(block_data["Multiplier"])}
        except json.JSONDecodeError:
            pass  # Not valid JSON in this block

    # --- 3) Fallback approaches ---

    # --- 3a) Regex for JSON-like structure with curly braces ---
    pattern_with_braces = re.compile(
        r'\{\s*"Multiplier"\s*:\s*([\-\+\deE\.]+)\s*\}',
        flags=re.DOTALL
    )
    match_braces = pattern_with_braces.search(output)
    if match_braces:
        multiplier_str = match_braces.group(1)
        try:
            return {"Multiplier": float(multiplier_str)}
        except ValueError:
            pass  # Could not convert to float

    # --- 3b) Regex for partial JSON (no curly braces) ---
    # Example: `"Multiplier": 8760`
    pattern_no_braces = re.compile(
        r'"Multiplier"\s*:\s*([\-\+\deE\.]+)',
        flags=re.DOTALL
    )
    match_no_braces = pattern_no_braces.search(output)
    if match_no_braces:
        multiplier_str = match_no_braces.group(1)
        try:
            return {"Multiplier": float(multiplier_str)}
        except ValueError:
            pass  # Could not convert to float

    # --- 4) If all methods fail, return a default fallback multiplier of 1.0 ---
    return {"Multiplier": 1.0}

def extract_json_unit_conversion(output):
    """
    Extract JSON-like structure specific to unit conversion from an LLM output.

    It handles multiple scenarios:
    1) Direct JSON parsing of the entire output (if the output is valid JSON).
    2) Extracting code blocks within triple backticks and parsing each as JSON.
    3) Fallback to two regex approaches:
       - A pattern with curly braces.
       - A pattern without curly braces (just "Multiplier": ...).

    Returns:
    -------
    dict:
        A dictionary with:
        {
            "Multiplier": float
        }
    
    Notes:
    ------
    - If extraction fails in all methods, **returns a default "Multiplier": 1.0**.
    - Ensures multiplier is always a **valid float**.
    """

    # -- 1) Direct JSON parsing (entire output) --
    try:
        data_entire = json.loads(output.strip())
        if isinstance(data_entire, dict) and "Multiplier" in data_entire:
            return {
                "Multiplier": float(data_entire["Multiplier"])
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # Not valid JSON in the entire output

    # -- 2) Extract code blocks and try JSON parsing on each --
    code_blocks = re.findall(r'```(?:[a-zA-Z0-9_-]+)?(.*?)```', output, flags=re.DOTALL)
    for block in code_blocks:
        text_block = block.strip()
        try:
            block_data = json.loads(text_block)
            if isinstance(block_data, dict) and "Multiplier" in block_data:
                return {
                    "Multiplier": float(block_data["Multiplier"])
                }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # Not valid JSON in this code block

    # -- 3) Fallback: Regex search in the entire output --
    #    a) Pattern with curly braces
    fallback_pattern_braces = re.compile(
        r'\{\s*"Multiplier"\s*:\s*([\-\+\deE\.]+)\s*\}',
        flags=re.DOTALL
    )
    match_braces = fallback_pattern_braces.search(output)
    if match_braces:
        try:
            return {
                "Multiplier": float(match_braces.group(1))
            }
        except ValueError:
            pass  # Couldn't parse float

    #    b) Pattern without curly braces (partial JSON)
    fallback_pattern_no_braces = re.compile(
        r'"Multiplier"\s*:\s*([\-\+\deE\.]+)',
        flags=re.DOTALL
    )
    match_no_braces = fallback_pattern_no_braces.search(output)
    if match_no_braces:
        try:
            return {
                "Multiplier": float(match_no_braces.group(1))
            }
        except ValueError:
            pass  # Couldn't parse float

    # -- If nothing worked, return a default safe multiplier --
    return {"Multiplier": 1.0}
 
def time_conversion(user_quantity, user_time_period, db_standard_time_period, product, llm):
    """
    Convert a given quantity from one time period to another by retrieving a conversion multiplier from LLM.

    Parameters:
        user_quantity (float): The quantity provided by the user.
        user_time_period (str): The time period associated with the user's quantity.
        db_standard_time_period (str): The standard time period to which conversion is required.
        llm: The language model instance to use for processing.

    Returns:
        float: The converted quantity after applying the LLM-provided multiplier.
    """

    # Define the prompt
    time_conversion_prompt = """
    You are an expert in time period conversion. Your task is to determine the multiplier required to convert a given quantity from one time period to another.

    Instructions:
    1. Determine the exact multiplier needed to convert from the user's time period to the standard time period.
    2. Do NOT perform any multiplication with the user quantity. The user quantity is provided for reference only. The actual multiplication will be handled separately in the Python code.
    3. Ensure that the multiplier is logically accurate for various time scales (e.g., per minute to per annum, per week to per decade).
    4. If the conversion is not straightforward (e.g., "per decade to per second"), return the most reasonable multiplier that allows for practical computation.
    5. Do NOT return 0 or an empty value in any case. Always return a logical, usable multiplier.
    6. The output must be strictly numerical, without any units, symbols, or explanations.
    7. Do NOT infer multipliers incorrectly. Use real-world time conversions based on logical calculations.

    Example Conversions:
    - "Per hour" → "Per day" → Multiplier: `24`
    - "Per 3 hours" → "Per annum" → Multiplier: `(3 * 8 * 365) = 8760`
    - "Per second" → "Per year" → Multiplier: `(60 * 60 * 24 * 365) = 31,536,000`
    - "Per decade" → "Per second" → Return a practical approximation.

    Inputs:
    - User Quantity: {user_quantity} (For reference only, do not use it in calculations)
    - User Time Period: {user_time_period}
    - Database Standard Time Period: {db_standard_time_period}
    - Product: {product} (Not needed for time period conversion, ignore)

    Output Format:
    Provide only the extracted multiplier in the following JSON format:
    {{
        "Multiplier": <conversion_multiplier>
    }}
    """

    # Define prompt structure
    prompt = PromptTemplate(
        input_variables=["user_quantity", "user_time_period", "db_standard_time_period", "product"],
        template=time_conversion_prompt
    )
    chain = prompt | llm

    # Invoke LLM for multiplier retrieval
    response = chain.invoke({
        "user_quantity": user_quantity,
        "user_time_period": user_time_period,
        "db_standard_time_period": db_standard_time_period,
        "product": product
    })
    update_llm_token(response,'Deepseek')

    # Extract multiplier using helper function
    multiplier_data = extract_json_time_conversion(response.content.strip())

    return {
        "Quantity": user_quantity * multiplier_data["Multiplier"],
        "Time Period": db_standard_time_period
    }
 
def unit_conversion(user_quantity, user_unit, db_standard_unit, product, llm):
    """
    Convert a given quantity from the user's unit to the standard unit using a multiplier.

    Parameters:
        user_quantity (float): The quantity provided by the user.
        user_unit (str): The unit associated with the user's quantity.
        db_standard_unit (str): The required standard unit for conversion.
        product (str): The product name (if applicable) for density-based conversions.
        llm: The language model instance for determining the conversion multiplier.

    Returns:
        dict: A dictionary containing the converted quantity and standard unit.
    """

    unit_conversion_prompt = """
    You are an expert in unit conversion. Your task is to determine the conversion multiplier required to transform a given unit from the user's unit to the standard unit.

    Instructions:
    1. Return ONLY the multiplier required to convert 1 unit of the user's unit into the standard unit.
    2. DO NOT perform any multiplication with the user quantity. The multiplier must always represent the conversion factor for just 1 unit of the user's unit.
    3. If the product's density affects the unit conversion, carefully factor it into the multiplier.
    4. If the conversion seems illogical, still return a non-zero multiplier that is the most logically valid.
    5. The output must always be a valid numerical multiplier (integer or decimal).  
    - DO NOT return text, explanations, or symbols.  
    - DO NOT modify, infer, or manipulate the user quantity.  
    6. If the conversion requires a product’s density but is missing, return a safe estimated multiplier instead of inferring an inaccurate conversion factor.
    7. Strict JSON Output: Ensure the output follows the exact format.

    Inputs:
    - User Quantity (Reference Only): {user_quantity}
    - User Unit: {user_unit}
    - Standard Unit: {db_standard_unit}
    - Product: {product}

    Output Format:
    {{
        "Multiplier": <conversion_multiplier>
    }}
    """

    prompt = PromptTemplate(
        input_variables=["user_quantity", "user_unit", "db_standard_unit", "product"],
        template=unit_conversion_prompt
    )
    chain = prompt | llm
    response = chain.invoke({
        "user_quantity": user_quantity,
        "user_unit": user_unit,
        "db_standard_unit": db_standard_unit,
        "product": product
    })
    update_llm_token(response,'Deepseek')

    # Extract JSON response from model output
    multiplier_data = extract_json_unit_conversion(response.content.strip())

    # Ensure the extracted multiplier is valid
    multiplier = multiplier_data.get("Multiplier", 1)

    # Final conversion using Python
    converted_quantity = float(user_quantity) * float(multiplier)

    return {
        "Quantity": converted_quantity,
        "Unit": db_standard_unit
    }
 
def convert_to_standard_unit(user_quantity, user_unit, user_time_period, db_standard_unit, db_standard_time_period, product, llm):
    """
    Perform the full conversion in two steps:
    1. Convert unit.
    2. Convert time period.

    Returns:
    - dict: A dictionary with the fully converted quantity and capacity unit.
    """
    # Step 1: Unit Conversion
    unit_converted = unit_conversion(user_quantity, user_unit, db_standard_unit, product, llm)
    unit_converted_quantity = unit_converted["Quantity"]

    # Step 2: Time Conversion
    time_converted = time_conversion(unit_converted_quantity, user_time_period, db_standard_time_period, product, llm)
    return {
        "Capacity": time_converted["Quantity"],
        "Capacity Unit": f"{db_standard_unit}",
        "Time Period": f"{time_converted['Time Period']}"
    }

def extract_json_unit_split(output):
    """
    Extract JSON-like structure specific to unit and time period split.

    Args:
    - output (str): The raw output string from the LLM.

    Returns:
    - dict: A dictionary with 'unit' and 'time_period'.

    Raises:
    - ValueError: If no valid JSON-like structure is found.
    """
    pattern = r'\{\s*"unit":\s*"([^"]+)",\s*"time_period":\s*"([^"]+)"\s*\}'
    match = re.search(pattern, output)

    if match:
        unit = match.group(1)  # Extract the unit as a string
        time_period = match.group(2)  # Extract the time period as a string
        return {
            "unit": unit,
            "time_period": time_period
        }
    else:
        raise ValueError(f"Failed to extract JSON for unit splitting: {output}")

def split_unit_and_time_period(input_string, llm):
    """
    Splits a given unit string into two parts: unit and time period, using an LLM.
    
    If no time period is found, defaults it to "per annum".

    Parameters:
        input_string (str): The input string containing the unit and potentially a time period.
        llm: The LLM instance to use for processing.

    Returns:
        dict: A dictionary with keys "unit" and "time_period".
    """
    split_unit_prompt = """
You are an expert at parsing capacity strings into:
- unit (the physical/commercial unit ONLY), and
- time_period (e.g., per day, per annum).

### Non-negotiable rules
1) **Preserve the unit EXACTLY as written** in the input (keep words, casing, spaces, hyphens, parentheses, and qualifiers like "Million", "Metric", etc.). 
   - Never drop magnitude words (e.g., Million, Thousand, Lakh, Crore).
   - Never normalize/singularize or translate (e.g., do NOT change “Tonne” to “Ton” or “m3” to “m³”).
   - Keep hyphens and bracketed text (e.g., “Tonne-Force(Metric)”) inside the unit.

2) Extract the **time_period** from any explicit time tokens. If none are present, set time_period to **"per annum"**.

3) Return **ONLY** valid JSON with exactly these keys: 
   {{"unit": "...", "time_period": "..."}}

### How to detect time_period
A) Explicit words:
   - Yearly terms → "per annum": {{"per annum","per year","annum","annual","yearly","p.a.","pa","/y"}}
   - Daily terms → "per day":    {{"per day","daily","/day","/d","d^-1"}}
   - Hourly terms → "per hour":  {{"per hour","hourly","/hour","/h","h^-1"}}
   - Monthly → "per month":      {{"per month","monthly","/month","/mo"}}
   - Weekly → "per week":        {{"per week","weekly","/week","/wk"}}
   - Per minute/second/shift/batch follow the same pattern: {{"per minute","/min"}}, {{"per second","/s"}}, {{"per shift"}}, {{"per batch"}}.
   Pick the single canonical label above (e.g., "per day").

B) Slash forms:
   If the string contains "unit/time" (e.g., "kg/day", "m3/h"), everything **after the slash** defines time_period 
   ("/day"→"per day", "/h"→"per hour"), and everything **before the slash** is the unit (preserve as-is).

C) Common industrial acronyms that embed time:
   - TPA/TPY → time_period = "per annum"; unit base = "Tonne" **only if** no explicit unit text exists before/around it.
   - TPD → "per day";   TPH → "per hour";  TPM → "per month";  TPW → "per week".
   - MTPA → "per annum" with magnitude "Million" + "Tonne" **only if** no explicit unit text exists.
   - KTPA → "per annum" with "Thousand Tonne" **only if** no explicit unit text exists.
   - MMTPA → "per annum" with "Million Metric Tonne" **only if** no explicit unit text exists.
   - BPD → "per day" with "Barrel" **only if** no explicit unit text exists.
   Rule for these acronyms: 
     • If the input ALREADY provides a written unit (e.g., "Million Tonne", "Tonne-Force(Metric)"), DO NOT replace or alter it—just set time_period.
     • Only expand to a base unit (e.g., "Tonne", "Million Tonne") when the acronym is the **only** clue to the unit.

### Edge-case safeguards
- If both a written unit and an acronym appear, prefer the written unit text exactly as-is for "unit", and use the acronym **only** to infer time_period.
- Do NOT infer conversions or add/remove words. Keep the unit substring exactly as it appears **after removing** any time tokens.
- If multiple time hints appear, choose the most explicit one (e.g., "per day" beats an implied annual default).

### Output format
Return ONLY:
{{
  "unit": "<exact unit text>",
  "time_period": "<canonical time period>"
}}

### Examples
Input: "Million Tonne"
Output:
{{"unit":"Million Tonne","time_period":"per annum"}}

Input: "Tonne-Force(Metric)"
Output:
{{"unit":"Tonne-Force(Metric)","time_period":"per annum"}}

Input: "kg per hour"
Output:
{{"unit":"kg","time_period":"per hour"}}

Input: "m3/day"
Output:
{{"unit":"m3","time_period":"per day"}}

Input: "TPA"
Output:
{{"unit":"Tonne","time_period":"per annum"}}

Input: "MTPA"
Output:
{{"unit":"Million Tonne","time_period":"per annum"}}

Input: "MMTPA"
Output:
{{"unit":"Million Metric Tonne","time_period":"per annum"}}

Input: "KTPA"
Output:
{{"unit":"Thousand Tonne","time_period":"per annum"}}

Input: "BPD"
Output:
{{"unit":"Barrel","time_period":"per day"}}

Input: "Million Tonne per annum"
Output:
{{"unit":"Million Tonne","time_period":"per annum"}}

Input: "Million Tonne / year"
Output:
{{"unit":"Million Tonne","time_period":"per annum"}}

Input: "Standard Cubic Meter/hour"
Output:
{{"unit":"Standard Cubic Meter","time_period":"per hour"}}

Input: "TPD (Tonne per day)"
Output:
{{"unit":"Tonne","time_period":"per day"}}

Input: "capacity-Unit: Tonne-Force(Metric)"
Output:
{{"unit":"Tonne-Force(Metric)","time_period":"per annum"}}

---

Input:
- Unit String: {input_string}

Return ONLY the JSON as specified.
    """
    
    # Use PromptTemplate to format the input for the LLM
    prompt = PromptTemplate(
        input_variables=["input_string"],
        template=split_unit_prompt
    )
    chain = prompt | llm
    
    # Get response from the LLM
    response = chain.invoke({
        "input_string": input_string
    })
    update_llm_token(response)
    return extract_json_unit_split(response.content.strip())
 
def entry_build_from_scratch(input,chatId, additional_class_response = None):
    final_json = get_json_for_industry()
    main_industry = get_main_industry(final_json)
    k = gather_industry_details(input,main_industry,llm_70b_vers,chatId, additional_class_response=additional_class_response)

    if k['Is_confirmation']:
        s, new_s = do_unit_conversion(k['state'])
        with open("\nlog2.txt", "a") as file:
            file.write(f"s {s}")
        k['state'].update(s)
        save_state(k['state'],f"QIND_state_{chatId}")
        k.update(new_s)
        return k
    else:
        return k

def get_json_for_industry():
    final_json = {}
    # query = """
    #         SELECT sgt.segment, indmappedsst.sub_sector_name, indmappedsst.industry_name
    #         FROM `tabSegment` AS sgt
    #         JOIN (
    #             SELECT sst.name, sst.sub_sector_name, indt.industry_name
    #             FROM `tabSub Sector` AS sst
    #             JOIN `tabIndustry` AS indt
    #             ON sst.industry_id = indt.name
    #         ) AS indmappedsst............................
    #         ON sgt.sub_sector = indmappedsst.name
    #         """

    query = f"""
SELECT
  sgt.segment,
  sst.sub_sector_name,
  indt.industry_name
FROM `tabSegment` AS sgt
JOIN `tabSub Sector` AS sst
  ON sgt.sub_sector = sst.name
 AND COALESCE(sst.exclusion, 0) = 0
JOIN `tabZone` AS z
  ON z.name = sst.zone_id
 AND COALESCE(z.exclusion, 0) = 0
JOIN `tabIndustry` AS indt
  ON sst.industry_id = indt.name
 AND COALESCE(indt.exclusion, 0) = 0
WHERE COALESCE(sgt.exclusion, 0) = 0;
        """
    s = frappe.db.sql(query,as_dict=True)
    for item in s:
        industry = item['industry_name']
        sub_sector = item['sub_sector_name']
        segment = item['segment']

        if industry not in final_json:
            final_json[industry] = {}
        if sub_sector not in final_json[industry]:
            final_json[industry][sub_sector] = []
        
        final_json[industry][sub_sector].append(segment)
    return final_json

def get_main_industry(final_json):
    """Returns a list of main industries."""
    return list(final_json.keys())

def get_all_sub_sectors(final_json):
    """Returns a list of sub-sectors for all main industry."""
    sub_sectors = []
    for industry in final_json.values():
        sub_sectors.extend(industry.keys())
    return sub_sectors

def get_sub_sectors(final_json,main_industry):
    """Returns a list of sub-sectors for a given main industry."""
    return  list(final_json.get(main_industry, {}).keys())

def get_segments(final_json, main_industry, sub_sector):
    """Returns a list of segments for a given main industry and sub-sector."""
    return final_json.get(main_industry, {}).get(sub_sector, [])

def get_keys_for_capicity(chatId):
    keys = ["Capacity","Capacity Unit","Time Period"]
    state = get_state(f"QIND_state_{chatId}")
    filtered_data = {key for key, value in state.items() if key in keys and value == "None" }
    return filtered_data

def do_unit_conversion(state):
    # 1) Try SEGMENT-level rule first (assumes `crla.segment` exists; tweak if your schema differs)
    results = []
    level_check = None

    if state.get("Segment"):
        # query = f"""
        # select distinct jcrla.capacity_unit
        # from (
        #     select crla.capacity_unit, crla.sub_sector, crla.extremity_record, sst.sub_sector_name, seg.segment, IT.industry_name
        #     from `tabIndustry Capacity Rule` as crla
        #     join `tabSub Sector` as sst on crla.sub_sector = sst.name
        #     join `tabSegment`   as seg on crla.segment   = seg.name
        #     join `tabIndustry`  as IT  on crla.industry  = IT.name
        # ) as jcrla
        # where (jcrla.segment = '{state['Segment']}' and jcrla.sub_sector_name = '{state['Sub-Sector']}' and jcrla.industry_name = '{state['Main-Industry']}')
        # AND extremity_record = 0
        # limit 1
        # """

        query = f"""
        SELECT DISTINCT jcrla.capacity_unit
        FROM (
            SELECT
                crla.capacity_unit,
                crla.sub_sector,
                crla.extremity_record,
                sst.sub_sector_name,
                seg.segment,
                IT.industry_name
            FROM `tabIndustry Capacity Rule` AS crla
            JOIN `tabSub Sector` AS sst
            ON crla.sub_sector = sst.name
            AND COALESCE(sst.exclusion, 0) = 0
            JOIN `tabSegment` AS seg
            ON crla.segment = seg.name
            AND COALESCE(seg.exclusion, 0) = 0
            JOIN `tabIndustry` AS IT
            ON crla.industry = IT.name
            AND COALESCE(IT.exclusion, 0) = 0
            WHERE COALESCE(crla.exclusion, 0) = 0
        ) AS jcrla
        WHERE jcrla.segment = '{state['Segment']}'
        AND jcrla.sub_sector_name = '{state['Sub-Sector']}'
        AND jcrla.industry_name = '{state['Main-Industry']}'
        AND jcrla.extremity_record = 0
        LIMIT 1
        """


        results = frappe.db.sql(query)
        if results:
            level_check = "Segment"

    # 2) Fallback: SUB-SECTOR
    if not results:
    #     query = f"""
    #     select distinct jcrla.capacity_unit
    #     from (
    #         select crla.capacity_unit, crla.sub_sector, crla.extremity_record, sst.sub_sector_name, sst.industry_id, IT.industry_name
    #         from `tabIndustry Capacity Rule` as crla
    #         join `tabSub Sector` as sst on crla.sub_sector = sst.name
    #         join `tabIndustry`  as IT  on crla.industry  = IT.name
    #     ) as jcrla
    #     where (jcrla.sub_sector_name = '{state['Sub-Sector']}' and jcrla.industry_name = '{state['Main-Industry']}')
    #     AND extremity_record = 0
    #     limit 1
    #     """

        query = f"""SELECT DISTINCT jcrla.capacity_unit
        FROM (
            SELECT
                crla.capacity_unit,
                crla.sub_sector,
                crla.extremity_record,
                sst.sub_sector_name,
                sst.industry_id,
                IT.industry_name
            FROM `tabIndustry Capacity Rule` AS crla
            JOIN `tabSub Sector` AS sst ON crla.sub_sector = sst.name
            JOIN `tabIndustry`  AS IT  ON crla.industry  = IT.name
            WHERE COALESCE(sst.exclusion, 0) = 0
            AND COALESCE(IT.exclusion, 0) = 0
            AND COALESCE(crla.exclusion, 0) = 0
        ) AS jcrla
        WHERE jcrla.sub_sector_name = '{state['Sub-Sector']}'
        AND jcrla.industry_name   = '{state['Main-Industry']}'
        AND jcrla.extremity_record = 0
        LIMIT 1;"""
        results = frappe.db.sql(query)
        if results:
            level_check = "Sub-Sector"

    # 3) Fallback: INDUSTRY (pick most frequent capacity_unit)
    if not results:
        # query = f"""
        # select jcrla.capacity_unit
        # from (
        #     select crla.capacity_unit, crla.extremity_record, IT.industry_name
        #     from `tabIndustry Capacity Rule` as crla
        #     join `tabIndustry` as IT on crla.industry = IT.name
        # ) as jcrla
        # where jcrla.industry_name = '{state['Main-Industry']}'
        # AND extremity_record = 0
        # group by jcrla.capacity_unit
        # order by count(*) desc
        # limit 1
        # """

        query = f"""SELECT jcrla.capacity_unit
        FROM (
            SELECT crla.capacity_unit, crla.extremity_record, IT.industry_name
            FROM `tabIndustry Capacity Rule` AS crla
            JOIN `tabIndustry` AS IT
            ON crla.industry = IT.name
            AND COALESCE(IT.exclusion, 0) = 0        
            AND COALESCE(crla.exclusion, 0) = 0
        ) AS jcrla
        WHERE jcrla.industry_name = '{state['Main-Industry']}'
        AND jcrla.extremity_record = 0
        GROUP BY jcrla.capacity_unit
        ORDER BY COUNT(*) DESC
        LIMIT 1;
        """
        results = frappe.db.sql(query)
        if results:
            level_check = "Industry"

    if not results:
        raise ValueError(
            f"No capacity unit rule found for Industry='{state.get('Main-Industry')}', "
            f"Sub-Sector='{state.get('Sub-Sector')}', Segment='{state.get('Segment')}'."
        )

    db_unit_for_ss = results[0][0]
    standard_unit_time = split_unit_and_time_period(db_unit_for_ss, llm_70b_vers)

    product_name          = state["Product"]
    user_quantity         = state["Capacity"]
    user_unit             = state["Capacity Unit"]
    user_time_period      = state["Time Period"]
    db_standard_unit      = standard_unit_time["unit"]
    db_standard_time_per  = standard_unit_time["time_period"]

    converted_output = convert_to_standard_unit(
        user_quantity, user_unit, user_time_period,
        db_standard_unit, db_standard_time_per,
        product_name, llm_deepseek
    )

    converted_output_temp = {}
    # record which level resolved the base unit
    converted_output_temp["DBFetchCheck"] = level_check

    # --------------------------
    # Extremity check (exact-unit-first; auto-convert if needed)
    # --------------------------
    converted_output_temp["Trigger_Lead_Generation"] = False
    cap_unit_for_check = str(converted_output.get("Capacity Unit", "")).strip()

    # Predefined messages
    UPPER_MSG = ("Thank you for sharing your requirements. The production scale you’re requesting is beyond "
                 "the maximum we currently support. We have recorded your query details, and our team will review "
                 "them and get in touch with you soon. We truly value your interest in our platform.")
    LOWER_MSG = ("Thank you for sharing your requirements. The production scale you’re requesting is significantly "
                 "below the minimum we currently support. We have recorded your query details, and our team will review "
                 "them and get in touch with you soon. We truly value your interest in our platform.")

    def _to_float(x):
        if x is None:
            return None
        try:
            return float(str(x).replace(",", ""))
        except Exception:
            return None

    def _build_ext_query(level, include_unit):
        unit_clause = " and crla.capacity_unit = %s" if include_unit else ""
        if level == "Segment":
            # q = f"""
            #     select crla.capacity_unit, crla.minimum_extremity_value, crla.maximum_extremity_value
            #     from `tabIndustry Capacity Rule` as crla
            #     join `tabSub Sector` as sst on crla.sub_sector = sst.name
            #     join `tabSegment`   as seg on crla.segment   = seg.name
            #     join `tabIndustry`  as IT  on crla.industry  = IT.name
            #     where seg.segment = %s
            #       and sst.sub_sector_name = %s
            #       and IT.industry_name    = %s
            #       and crla.extremity_record = 1
            #       {unit_clause}
            #     limit 1
            # """

            q = f"""
            SELECT crla.capacity_unit, crla.minimum_extremity_value, crla.maximum_extremity_value
            FROM `tabIndustry Capacity Rule` AS crla
            JOIN `tabSub Sector` AS sst
            ON crla.sub_sector = sst.name
            AND COALESCE(sst.exclusion, 0) = 0
            JOIN `tabSegment` AS seg
            ON crla.segment = seg.name
            AND COALESCE(seg.exclusion, 0) = 0
            JOIN `tabIndustry` AS IT
            ON crla.industry = IT.name
            AND COALESCE(IT.exclusion, 0) = 0
            WHERE seg.segment = %s
            AND sst.sub_sector_name = %s
            AND IT.industry_name = %s
            AND crla.extremity_record = 1
            AND COALESCE(crla.exclusion, 0) = 0
            {unit_clause}
            LIMIT 1
        """

            args = [state["Segment"], state["Sub-Sector"], state["Main-Industry"]]
        elif level == "Sub-Sector":

            # q = f"""
            #     select crla.capacity_unit, crla.minimum_extremity_value, crla.maximum_extremity_value
            #     from `tabIndustry Capacity Rule` as crla
            #     join `tabSub Sector` as sst on crla.sub_sector = sst.name
            #     join `tabIndustry`  as IT  on crla.industry  = IT.name
            #     where sst.sub_sector_name = %s
            #       and IT.industry_name    = %s
            #       and crla.extremity_record = 1
            #       {unit_clause}
            #     limit 1
            # """
            q = f"""
            SELECT crla.capacity_unit, crla.minimum_extremity_value, crla.maximum_extremity_value
            FROM `tabIndustry Capacity Rule` AS crla
            JOIN `tabSub Sector` AS sst
            ON crla.sub_sector = sst.name
            AND COALESCE(sst.exclusion, 0) = 0
            JOIN `tabIndustry` AS IT
            ON crla.industry = IT.name
            AND COALESCE(IT.exclusion, 0) = 0
            WHERE sst.sub_sector_name = %s
            AND IT.industry_name = %s
            AND crla.extremity_record = 1
            AND COALESCE(crla.exclusion, 0) = 0
            {unit_clause}
            LIMIT 1
        """

            args = [state["Sub-Sector"], state["Main-Industry"]]
        else:  # Industry
            # q = f"""
            #     select crla.capacity_unit, crla.minimum_extremity_value, crla.maximum_extremity_value
            #     from `tabIndustry Capacity Rule` as crla
            #     join `tabIndustry` as IT on crla.industry = IT.name
            #     where IT.industry_name = %s
            #       and crla.extremity_record = 1
            #       {unit_clause}
            #     limit 1
            # """

            q = f"""
            SELECT crla.capacity_unit, crla.minimum_extremity_value, crla.maximum_extremity_value
            FROM `tabIndustry Capacity Rule` AS crla
            JOIN `tabIndustry` AS IT
            ON crla.industry = IT.name
            AND COALESCE(IT.exclusion, 0) = 0
            WHERE IT.industry_name = %s
            AND crla.extremity_record = 1
            AND COALESCE(crla.exclusion, 0) = 0
            {unit_clause}
            LIMIT 1
        """

            args = [state["Main-Industry"]]
        if include_unit:
            args.append(cap_unit_for_check)
        return q, tuple(args)

    # If there's no unit in converted output, we can't check ranges safely
    if cap_unit_for_check and level_check:
        # 1) Try an extremity row with the same unit
        q1, a1 = _build_ext_query(level_check, include_unit=True)
        ext_rows = frappe.db.sql(q1, a1)

        # 2) Fallback: any extremity row for this level
        if not ext_rows:
            q2, a2 = _build_ext_query(level_check, include_unit=False)
            ext_rows = frappe.db.sql(q2, a2)

        if ext_rows:
            ext_unit, min_ext, max_ext = ext_rows[0][0], ext_rows[0][1], ext_rows[0][2]

            if str(ext_unit).strip() == cap_unit_for_check:
                # Direct comparison (same unit/time)
                cap_val = _to_float(converted_output.get("Capacity"))
                min_v   = _to_float(min_ext)
                max_v   = _to_float(max_ext)

                if cap_val is not None and min_v is not None and max_v is not None:
                    # fix swapped bounds if any
                    if min_v > max_v:
                        min_v, max_v = max_v, min_v

                    if cap_val < min_v:
                        converted_output_temp["Trigger_Lead_Generation"] = True
                        converted_output_temp["Ai_response"] = LOWER_MSG
                        converted_output_temp["Is_confirmation"] = False
                        converted_output_temp["options"] = None
                    elif cap_val > max_v:
                        converted_output_temp["Trigger_Lead_Generation"] = True
                        converted_output_temp["Ai_response"] = UPPER_MSG
                        converted_output_temp["Is_confirmation"] = False
                        converted_output_temp["options"] = None

                    # else in range -> no trigger/message
                else:
                    # Can't compare reliably; keep prior behavior (no message side)
                    pass
            else:
                # Units differ → convert extremity bounds to the SAME standard unit/time
                try:
                    ext_parsed      = split_unit_and_time_period(str(ext_unit), llm_70b_vers)
                    ext_unit_only   = ext_parsed.get("unit")
                    ext_time_period = ext_parsed.get("time_period")

                    min_num = _to_float(min_ext)
                    max_num = _to_float(max_ext)

                    min_conv = convert_to_standard_unit(
                        min_num, ext_unit_only, ext_time_period,
                        db_standard_unit, db_standard_time_per,
                        product_name, llm_deepseek
                    ) if min_num is not None else None

                    max_conv = convert_to_standard_unit(
                        max_num, ext_unit_only, ext_time_period,
                        db_standard_unit, db_standard_time_per,
                        product_name, llm_deepseek
                    ) if max_num is not None else None

                    cap_val = _to_float(converted_output.get("Capacity"))
                    min_v   = _to_float(min_conv.get("Capacity")) if isinstance(min_conv, dict) else None
                    max_v   = _to_float(max_conv.get("Capacity")) if isinstance(max_conv, dict) else None

                    if cap_val is not None and min_v is not None and max_v is not None:
                        if min_v > max_v:
                            min_v, max_v = max_v, min_v

                        if cap_val < min_v:
                            converted_output_temp["Trigger_Lead_Generation"] = True
                            converted_output_temp["Ai_response"] = LOWER_MSG
                            converted_output_temp["Is_confirmation"] = False
                            converted_output_temp["options"] = None


                        elif cap_val > max_v:
                            converted_output_temp["Trigger_Lead_Generation"] = True
                            converted_output_temp["Ai_response"] = UPPER_MSG
                            converted_output_temp["Is_confirmation"] = False
                            converted_output_temp["options"] = None
                        

                        # else in range -> no trigger/message
                    else:
                        # Can't compare reliably; keep prior behavior (no message side)
                        pass
                except Exception as e:
                    # On conversion failure, keep prior conservative trigger; no side-specific message
                    print("Extremity conversion error:", e)
                    Fall_back_message = ("Thank you for sharing your requirements. There went something wrong "
                    "While Processing your requirements. We have recorded your query details, and our team will review "
                    "them and get in touch with you soon. We truly value your interest in our platform.")

                    converted_output_temp["Trigger_Lead_Generation"] = True
                    converted_output_temp["Ai_response"] = Fall_back_message
                    converted_output_temp["Is_confirmation"] = False

    return converted_output, converted_output_temp
