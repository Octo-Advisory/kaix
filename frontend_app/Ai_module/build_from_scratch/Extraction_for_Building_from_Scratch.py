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
    main_industries_str = ", ".join(main_industries)
    
    # Define the prompt
    prompt_template = """
    You are an expert in analyzing industry-building queries and extracting specific details.
    Based on the user's query, identify the following details:

    1. Main-Industry: First, infer or predict the main industry based on the context of the query.  
    - Users may phrase their queries in various ways, such as "I want to set up a spectacle factory," "I want to set up a spectacle industry," or simply "Spectacles." In all such cases, assume they are referring to manufacturing the product mentioned unless it is clearly illogical.  
    - Do not rely on specific words like "factory," "industry," or similar terms to infer manufacturing intent. The product name alone (e.g., "Spectacles") is sufficient to deduce that the query is about manufacturing that product.  
    - The query may sometimes be vague, incomplete, or consist of just the product name. In such cases, logically infer the appropriate main industry.  
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
    validated_data = extracted_details.copy()
    if extracted_details["Main-Industry"] not in main_industries and extracted_details["Main-Industry"] != "None":
        validated_data["Main-Industry"] = "Not Available in list"

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
    sub_sectors_str = ", ".join(sub_sectors)

    # Define additional context for Main-Industry and Product if available
    context_lines = []
    if main_industry and main_industry not in ["None", "Not Available in list"]:
        context_lines.append(f"Inferred Main-Industry: {main_industry}")
    if product and product != "None":
        context_lines.append(f"Inferred Product: {product}")
    context = "\n".join(context_lines)

    # Define the prompt
    prompt_template = """
    You are an expert in analyzing industry-building queries and extracting specific details.  
    Sub-Sector is the functional or operational category that immediately follows the Main-Industry in the hierarchy.  
    It encompasses broader categories of related activities, processes, or areas of focus that form part of the Main-Industry.  

    For example:  
    - In the "Automobile" Main-Industry, possible Sub-Sectors include "Vehicle Assembly," "Automotive Components," or "Electric Vehicles."
    - In the "Pharmaceuticals" Main-Industry, possible Sub-Sectors include "Allopathic Medicines," "Ayurvedic Medicines," or "Biotechnology."
    - Sub-Sectors are not specific to individual products; they represent broader categories within the Main-Industry.

    {context}

    Based on the user's query, identify the following details:

    1. Sub-Sector: First, infer or predict the sub-sector based on the context of the query.  
    - In the majority of cases, users may not explicitly mention "manufacturing" or related terms but are still referring to manufacturing-related sub-sectors. Assume the query is about a manufacturing-related sub-sector unless it is clearly illogical to do so.  
    - The query may sometimes be vague or incomplete. In such cases, try to understand the implied intent and context to infer the appropriate sub-sector.  
    - If the inferred sub-sector can logically match any category from the provided list of Sub-Sectors, return the matched category from the list and set `"Forced-Mapping"` to `"No"`.  
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred sub-sector to the closest match from the provided list and set `"Forced-Mapping"` to `"Yes"`.  
    - If no sub-sector can be inferred from the query, return `"None"` for the `"Original-Inferred-Sub-Sector"` and `"Sub-Sector"`.  

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

    Logical Matching for Sub-Sectors:
    - A logical match occurs when the inferred sub-sector and an available sub-sector from the list are conceptually or functionally similar.  
    - Examples of logical matches:  
        - Inferred: "Electric Cars" → Available: "Electric Vehicles" (`Forced-Mapping`: `"No"`).  
        - Inferred: "Biological Research" → Available: "Biotechnology" (`Forced-Mapping`: `"No"`).  
    - Examples of forced mappings:  
        - Inferred: "Clean Energy Solutions" → Available: "Renewable Energy" (`Forced-Mapping`: `"Yes"`).  
        - Inferred: "Pharma Research Labs" → Available: "Biotechnology" (`Forced-Mapping`: `"Yes"`).  
    - If no logical match exists, set `"Forced-Mapping"` to `"Yes"`.  

    Output Constraints:  
    - Ensure that the output is strictly limited to the required JSON format and contains no explanations, reasoning, or comments.  
    - Do not provide additional text, explanations, or reasoning within the fields of the JSON object. For example, avoid including reasoning like "This matches because..." or "Assumed manufacturing based on context."  
    - Each field in the JSON must only contain the exact extracted information or the specified fallback values (e.g., `"None"`).  

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
    
    # Extract JSON response using the new function
    extracted_details = extract_json_sub_sector_product(result.content.strip())

    # Validation: Check if the extracted sub-sector exists in the provided list
    validated_data = extracted_details.copy()
    if extracted_details["Sub-Sector"] not in sub_sectors and extracted_details["Sub-Sector"] != "None":
        validated_data["Sub-Sector"] = "Not Available in list"

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
    You are an expert in analyzing industry-building queries and extracting specific details.
    Segment is the logical grouping of products, which comes immediately next in the hierarchy after the Sub-Sector.
    Sub-Sector itself is the functional or operational category following the Main-Industry in the hierarchy.

    For example:
    - In the "Automobile" Main-Industry, a Sub-Sector like "Automotive Components" may have Segments such as "Engines," "Batteries," or "Tires."
    - In the "Pharmaceuticals" Main-Industry, a Sub-Sector like "Allopathic Medicines" may have Segments like "Antibiotics" or "Analgesics."

    Based on the user's query, identify the following details:

    {context}

    1. Segment: First, infer or predict the segment based on the context of the query.
    - In the majority of cases, users may not explicitly mention "manufacturing" or related terms but are still referring to manufacturing-related segments. Assume the query is about manufacturing unless it is clearly illogical to do so.
    - The query may sometimes be vague or incomplete. In such cases, try to understand the implied intent and context to infer the appropriate segment.
    - If the inferred segment can logically match any category from the provided list of Segments, return the matched category from the list and set `Forced-Mapping` to `No`.
    - If no logical match is possible but a mapping must still be provided, forcefully map the inferred segment to the closest match from the provided list and set `Forced-Mapping` to `Yes`.
    - If no segment can be inferred from the query, return `"None"` for both `"Original-Inferred-Segment"` and `"Segment"`.

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

    Important Notes:

    Logical Matching for Segments:
    - A logical match occurs when the inferred segment and an available segment from the list are conceptually or functionally similar.
    - Examples of logical matches:
        - Inferred: "Metal Equipment" → Available: "Metalworking Machinery" (`Forced-Mapping`: No).
        - Inferred: "Metal Fabrication Tools" → Available: "Metalworking Machinery" (`Forced-Mapping`: No).
    - Examples of forced mappings:
        - Inferred: "Advanced Robotics Systems" → Available: "Automation Equipment" (`Forced-Mapping`: Yes).
        - Inferred: "Metal Gear Production" → Available: "Metalworking Machinery" (`Forced-Mapping`: Yes).
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

    # Extract JSON response using the robust function
    result_content = result.content.strip()
    extracted_data = extract_json_segment_and_product(result_content)

    # Validate against the provided list of Segments
    validated_data = extracted_data.copy()
    if extracted_data["Segment"] not in segments and extracted_data["Segment"] != "None":
        validated_data["Segment"] = "Not Available in list"

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

    - Handling Industry-Related Guidance:  
    - If the user seeks guidance for an industry-related question (e.g., "What is the ideal capacity for a 10 crore investment?"), provide a realistic estimate or a general suggestion based on industry norms and context.  
    - If exact figures cannot be determined, offer an indicative starting point or general direction (e.g., "Capacities for investments like this typically range based on the production scale and the industry.").  
    - Clearly state that the decision depends on various factors, such as risk appetite, investment plans, production strategies, and market demand.  
    - After providing guidance, smoothly transition to request the missing details needed for further assistance.

    - Handling Greetings:  
    - If the user greets (e.g., "Hi", "Hello", "Good morning"), warmly acknowledge the greeting (e.g., "Hello! It’s great to connect with you.")  
    - Transition directly to ask for the missing details without including disclaimers or unrelated guidance.

    - Handling Special Days:  
    - If the user mentions a special occasion (e.g., birthday, anniversary), warmly acknowledge it (e.g., "Happy Birthday! Wishing you all the best.")  
    - Transition smoothly to request the missing details without including disclaimers or unrelated guidance.

    - Handling Negative Emotions:  
    - If the user expresses frustration, anger, or sadness, respond empathetically (e.g., "I’m sorry to hear that. I’m here to help in any way I can.")  
    - Transition smoothly to request the missing details while maintaining a supportive tone.

    - Transitioning to Missing Information:  
    - Ensure the transition to the missing details request feels natural and engaging.  
    - Use clear and professional phrases like "To proceed further," "Additionally," or "To help you better" to connect the response seamlessly to the missing details request.

    - First Three Attempts:  
    - Focus solely on asking for the missing details concisely and clearly.  
    - Do not acknowledge or repeat the provided information during the first Three attempts.  

    - After Three Attempts:  
    - Briefly acknowledge the details already provided by the user but without robotic phrasing.  
    - Request the missing details concisely and clearly.

    - Asking for Specific Missing Details:  
    - If "Main-Industry" or "Sub-Sector" (or both) are missing, ask about the product or service the user deals with, but do NOT refer to them as "Main-Industry" or "Sub-Sector" in the message.  

    Output Requirements:  
    - The message must be concise, clear, and in a single paragraph.  
    - Do NOT include any explanations, reasoning, or assumptions about the missing details, user input, or context.  
    - For the first Three attempts, focus only on requesting the missing details.  
    - After Three attempts, briefly acknowledge the provided details, then request the missing details concisely.  
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

def gather_industry_details(query, main_industries, llm,chatId):
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
                 'Time Period': 'None', 'Product': 'None','product_attempt_count':0,'capacity_attempt_count':0, "KEYWORDS": None}
        save_state(state,f"QIND_state_{chatId}")
    chat_history = get_chat(f"QIND_chat_{chatId}") or []

    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    
    refined_query = refine_query_with_history(Chat_history_normal, query, llm)
    chat_history.append(HumanMessage(content=refined_query))
    save_chat(chat_history,f"QIND_chat_{chatId}")
    
    keyword_dict = extract_keywords_from_query(refined_query, field_with_description["Query to build industry from Scratch"], module_names_list, llm, "Query to build industry from Scratch")
    state["KEYWORDS"] = keyword_dict["KEYWORDS"]
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

        chat_history = get_chat(f"QIND_chat_{chatId}")
        state['product_attempt_count'] = state['product_attempt_count'] + 1
        save_state(state,f"QIND_state_{chatId}")
        message = generate_ai_message(state,Chat_history_normal,['Product'],state['product_attempt_count'],llm_70b_vers_creative)
        chat_history.append(AIMessage(content=f"{message}"))
        save_chat(chat_history,f"QIND_chat_{chatId}")
        return {"Ai_response": message,
                "Is_confirmation" : False,
                "state":state}
    
    elif state["Main-Industry"] == 'Not Available in list' and state["Product"] == 'None':
        capacity_json = extract_capacity_details(refined_query,llm)
        
        if any(value != 'None' for value in capacity_json.values()):
             # Update only if the value is different and not 'None'
            for key, value in capacity_json.items():
                if value != 'None' and state.get(key) != value:
                    state[key] = value
            save_state(state,f"QIND_state_{chatId}")
        missing_fields = [field for field, value in capacity_json.items() if value == 'None']
        if len(missing_fields) == 0:
            message = "We've your query, We'll get back to you soon"
            return {"Ai_response": message,
                "Is_confirmation" : False,
                "state":state}
        else:
            chat_history = get_chat(f"QIND_chat_{chatId}")
            state['capacity_attempt_count'] = state['capacity_attempt_count'] + 1
            save_state(state,f"QIND_state_{chatId}")
            message = generate_ai_message(state,Chat_history_normal,missing_fields,state['capacity_attempt_count'],llm_70b_vers_creative)
            chat_history.append(AIMessage(content=f"{message}"))
            save_chat(chat_history,f"QIND_chat_{chatId}")
            return {"Ai_response": message,
                "Is_confirmation" : False,
                "state":state}
        
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
        if state['Sub-Sector'] != 'None' and state['Sub-Sector'] != 'Not Available in list':
            segments = get_segments(final_json,state["Main-Industry"],state['Sub-Sector'])

            segment_extracted_data,segment_validated_data = extract_segment_and_product_for_scratch(refined_query,segments,llm,main_industries,state['Sub-Sector'],state["Product"])
            
            state = get_state(f"QIND_state_{chatId}")
            state["Segment"] = segment_validated_data["Segment"] 
            state["Product"] = segment_validated_data["Product"]
            
            save_state(state,f"QIND_state_{chatId}")
            capicity_pending_list = get_keys_for_capicity(chatId)
            if len(capicity_pending_list) > 0:
                chat_history = get_chat(f"QIND_chat_{chatId}")
                state['capacity_attempt_count'] = state['capacity_attempt_count'] + 1
                save_state(state,f"QIND_state_{chatId}")
                message = generate_ai_message(state,Chat_history_normal,capicity_pending_list,state['capacity_attempt_count'],llm_70b_vers_creative)
                chat_history.append(AIMessage(content=f"{message}"))
                save_chat(chat_history,f"QIND_chat_{chatId}")
                return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state":state}
            else:
                selected_option = next(
                    (state.get(key) for key in ['Product', 'Segment', 'Sub-Sector', 'Main-Industry'] if state.get(key) not in [None, 'None']),
                    ''
                )
                response = {
                    "Ai_response" : f"We have identified that you are looking for {selected_option},{state.get('Capacity')},{state.get('Capacity Unit')},{state.get('Time Period')} based on your query. Please confirm if this information is correct.",
                    "Is_confirmation" : True,                                   
                    "validated_data" : segment_validated_data,
                    "state" : state
                }
                return response

        elif state['Sub-Sector'] == 'Not Available in list':
            capicity_pending_list = get_keys_for_capicity(chatId)
            if len(capicity_pending_list) > 0:
                chat_history = get_chat(f"QIND_chat_{chatId}")
                state['capacity_attempt_count'] = state['capacity_attempt_count'] + 1
                save_state(state,f"QIND_state_{chatId}")
                message = generate_ai_message(state,Chat_history_normal,capicity_pending_list,state['capacity_attempt_count'],llm_70b_vers_creative)
                chat_history.append(AIMessage(content=f"{message}"))
                save_chat(chat_history,f"QIND_chat_{chatId}")
                return {"Ai_response": message,
                    "Is_confirmation" : False,
                    "state": state}
            else:
                message = "We've your query, We'll get back to you soon"
                return {"Ai_response": message,
                "Is_confirmation" : False,
                "state":state}

        else:
            chat_history = get_chat(f"QIND_chat_{chatId}")
            state['product_attempt_count'] = state['product_attempt_count'] + 1
            save_state(state,f"QIND_state_{chatId}")
            message = generate_ai_message(state,Chat_history_normal,['Product'],state['product_attempt_count'],llm_70b_vers_creative)
            chat_history.append(AIMessage(content=f"{message}"))
            save_chat(chat_history,f"QIND_chat_{chatId}")
            return {"Ai_response": message,
                "Is_confirmation" : False,
                "state":state}
    
    else:
        response = {
            "Ai_response": "Please enter valid query with some details.",
            "Is_confirmation" : False,
            "state":state
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
    You are an expert in understanding units of measure and identifying time periods associated with them.

    Instructions:
    1. Analyze the given input string and split it into:
       - "unit": The actual unit without the time period (e.g., "TPA (Ton per Annum)" -> "Ton").
       - "time_period": The time period if specified (e.g., "per annum"). If no time period is present, set it to "per annum".
    2. Ensure the output is always a valid JSON object.

    Input:
    - Unit String: {input_string}

    Output:
    {{
        "unit": "<unit>",
        "time_period": "<time_period>"
    }}
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
 
def entry_build_from_scratch(input,chatId):
    final_json = get_json_for_industry()
    main_industry = get_main_industry(final_json)
    k = gather_industry_details(input,main_industry,llm_70b_vers,chatId)

    if k['Is_confirmation']:
        s = do_unit_conversion(k['state'])
        with open("\nlog2.txt", "a") as file:
            file.write(f"s {s}")
        k['state'].update(s)
        save_state(k['state'],f"QIND_state_{chatId}")
        return k
    else:
        return k

def get_json_for_industry():
    final_json = {}
    query = """
            SELECT sgt.segment, indmappedsst.sub_sector_name, indmappedsst.industry_name
            FROM `tabSegment` AS sgt
            JOIN (
                SELECT sst.name, sst.sub_sector_name, indt.industry_name
                FROM `tabSub Sector` AS sst
                JOIN `tabIndustry` AS indt
                ON sst.industry_id = indt.name
            ) AS indmappedsst
            ON sgt.sub_sector = indmappedsst.name
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
    query = f"""
    select distinct jcrla.capacity_unit
    from (
        select crla.capacity_unit, crla.sub_sector, sst.sub_sector_name, sst.industry_id
        from `tabIndustry Capacity Rule` as crla
        join `tabSub Sector` as sst
        on crla.sub_sector = sst.name
    ) as jcrla
    where jcrla.sub_sector_name = '{state['Sub-Sector']}' and jcrla.industry_id = '{state['Main-Industry']}'
    """

    results = frappe.db.sql(query)
    db_unit_for_ss = results[0][0]
    standard_unit_time = split_unit_and_time_period(db_unit_for_ss, llm_70b_vers)
    product_name = state["Product"]
    user_quantity = state["Capacity"]
    user_unit = state["Capacity Unit"]
    user_time_period = state["Time Period"]
    db_standard_unit = standard_unit_time["unit"]
    db_standard_time_period = standard_unit_time["time_period"]

    converted_output = convert_to_standard_unit(
        user_quantity, user_unit, user_time_period, db_standard_unit, db_standard_time_period, product_name, llm_deepseek
    )

    return converted_output