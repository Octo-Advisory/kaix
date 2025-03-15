import re
import json
from typing import List, Dict, Tuple, Union
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from frontend_app.Ai_module.Query_Classification_And_Analysis import llm_70b_vers, llm_70b_vers_creative,extract_location_from_query,extract_comparison_locations
from langchain.schema import HumanMessage, AIMessage
import pandas as pd
import frappe
import logging
from frontend_app.Management_Class.Redis_management.Redis_chat import save_chat,get_chat
from frontend_app.Management_Class.helpers.utility import update_llm_token

logging.basicConfig(
    filename='AIerror.log',  # Log file name
    level=logging.INFO,  # Minimum log level to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S'  # Date format in logs
)

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

# Define a function to refine the query using history
def refine_query_with_history_for_employment(history, latest_query, llm):
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
    4. Strictly do not infer or carry forward any location from past AI responses unless the user explicitly acknowledges, agrees to, or repeats that location in their latest input.  
    5. Strictly do not infer or carry forward any location from past user inputs unless it is explicitly mentioned in the latest user input.  
    6. If the latest user input mentions only one location, ensure only that location appears in the reformulated query.  
    - Do not include multiple locations unless the user explicitly mentions multiple locations in their latest query.  
    7. Do not add any explanations, reasoning, or justifications in the reformulated standalone query. The output must be a clean and direct reformulation of the user’s intent without unnecessary elaboration.  

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

def extract_json_from_llm_response_employment(raw_output: str, json_key: str) -> Dict[str, Union[List[str], None]]:
    """
    Extracts a JSON object containing the specified key from an LLM response for Employment module.
    Ensures valid JSON output and corrects for any parsing errors.

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
    pattern_braces = re.compile(r'\{\s*"' + json_key + r'"\s*:\s*(\[[^]]*\]|null|None)\s*\}', flags=re.DOTALL)
    match_braces = pattern_braces.search(raw_output)
    if match_braces:
        keyword_list = match_braces.group(1).strip()

        if keyword_list.lower() in ["null", "none"]:
            return {json_key: None}

        extracted_values = [kw.strip('" ') for kw in keyword_list.strip("[]").split(',') if kw.strip('" ')]
        return {json_key: extracted_values if extracted_values else None}

    pattern_no_braces = re.compile(r'"' + json_key + r'"\s*:\s*(\[[^]]*\]|null|None)', flags=re.DOTALL)
    match_no_braces = pattern_no_braces.search(raw_output)
    if match_no_braces:
        keyword_list = match_no_braces.group(1).strip()

        if keyword_list.lower() in ["null", "none"]:
            return {json_key: None}

        extracted_values = [kw.strip('" ') for kw in keyword_list.strip("[]").split(',') if kw.strip('" ')]
        return {json_key: extracted_values if extracted_values else None}

    return {json_key: None}

def extract_employment_keywords_from_query(user_input: str, llm) -> Dict[str, Union[List[str], None]]:
    """
    Extracts employment-related keywords from a user query, ensuring they are classified into:
    - "Skilled"
    - "Semi-Skilled"
    - "Unskilled"

    If the query is a general employment search, return `None`. Otherwise, map the keyword
    to the appropriate skill category.

    Parameters:
    -----------
    user_input : str
        The user-provided query string.

    llm :
        An instance of a language model (such as from LangChain) capable of processing the prompt.

    Returns:
    --------
    Dict[str, Union[List[str], None]]:
        A dictionary with a single key 'KEYWORDS'.
    """

    prompt_template_str = """
    You are an expert in employment search classification.

    Your task:

    1) DETERMINE THE TYPE OF EMPLOYMENT SEARCH:
    - If the query is for general employment without specifying a job role or skill type, return `null`.
    - Example (General Employment): "I want employment opportunities in Surat." → null
    - Example (General Employment): "Looking for jobs in Gujarat." → null

    2) IDENTIFY DIRECT MENTIONS OF SKILL CATEGORIES:
    - If the query explicitly mentions "Skilled", "Semi-Skilled", or "Unskilled", return these directly.
    - Example: "I want to hire skilled and unskilled workers." → ["Skilled", "Unskilled"]

    3) CLASSIFY SPECIFIC JOB ROLES OR BROAD TERMS:
    - If the query mentions a specific job role, classify it into:
        - Skilled: Requires formal training, technical knowledge, or expertise (e.g., electricians, engineers, mechanics).
        - Semi-Skilled: Requires experience or on-the-job guidance (e.g., machine operators, crane operators, construction assistants).
        - Unskilled: Requires minimal training, involves basic physical labor (e.g., loaders, helpers).

    - Extract ONLY the most relevant category based on the job role. Do not include unrelated categories.

    4) HANDLE BROAD TERMS INTELLIGENTLY:
    - If the user mentions broad or ambiguous terms, classify based on logical context.
    - "Technical" Terms Handling:
        - If the context clearly indicates advanced expertise or formal training, classify as "Skilled".
        - If it refers to operators, assistants, or general on-the-job experience, classify as "Semi-Skilled".
        - If context is unclear, classify with the most probable category based on the job description.
        - Do NOT extract multiple categories unless clearly mentioned.

    Examples:
    - "Looking for technical workers." → ["Semi-Skilled"] (as it's likely general)
    - "Looking for technical engineers." → ["Skilled"]
    - "Need technical operators for machines." → ["Semi-Skilled"]
    - "Hiring experienced technical staff." → ["Skilled"]
    - "Hiring crane operators for the construction site." → ["Semi-Skilled"]
    - "Need helpers for packaging work." → ["Unskilled"]
    - "Looking for electricians and plumbers." → ["Skilled"]
    - "I need laborers for shifting work." → ["Unskilled"]
    - "Searching for skilled operators for heavy machinery." → ["Skilled"]
    - "Looking for workers in Surat." → null

    5) MULTIPLE CLASSIFICATIONS:
    - If the query mentions multiple job roles, classify each and return them together.
    - Example: "I need electricians and machine operators." → ["Skilled", "Semi-Skilled"]

    6) FINAL OUTPUT RULES:
    - Only include the following values in the response: "Skilled", "Semi-Skilled", "Unskilled".
    - If no valid classification is possible, return `null`.

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

    prompt = PromptTemplate(
        input_variables=["user_query"],
        template=prompt_template_str
    )
    chain = prompt | llm
    response = chain.invoke({
        "user_query": user_input
    })

    raw_output = response.content.strip()

    return extract_json_from_llm_response_employment(raw_output, "KEYWORDS")

def extract_employment_keywords_from_query(user_input: str, llm) -> Dict[str, Union[List[str], None]]:
    """
    Extracts employment-related keywords from a user query, ensuring they are classified into:
    - "Skilled"
    - "Semi-Skilled"
    - "Unskilled"

    If the query is a general employment search, return `None`. Otherwise, map the keyword
    to the appropriate skill category.

    Parameters:
    -----------
    user_input : str
        The user-provided query string.

    llm :
        An instance of a language model (such as from LangChain) capable of processing the prompt.

    Returns:
    --------
    Dict[str, Union[List[str], None]]:
        A dictionary with a single key 'KEYWORDS'.
    """

    prompt_template_str = """
    You are an expert in employment search classification.

    Your task:

    1) DETERMINE THE TYPE OF EMPLOYMENT SEARCH:
    - If the query is for general employment without specifying a job role or skill type, return `null`.
    - Example (General Employment): "I want employment opportunities in Surat." → null
    - Example (General Employment): "Looking for jobs in Gujarat." → null

    2) IDENTIFY DIRECT MENTIONS OF SKILL CATEGORIES:
    - If the query explicitly mentions "Skilled", "Semi-Skilled", or "Unskilled", return these directly.
    - Example: "I want to hire skilled and unskilled workers." → ["Skilled", "Unskilled"]

    3) CLASSIFY SPECIFIC JOB ROLES OR BROAD TERMS:
    - If the query mentions a specific job role, classify it into:
        - Skilled: Requires formal training, technical knowledge, or expertise (e.g., electricians, engineers, mechanics).
        - Semi-Skilled: Requires experience or on-the-job guidance (e.g., machine operators, crane operators, construction assistants).
        - Unskilled: Requires minimal training, involves basic physical labor (e.g., loaders, helpers).

    - Extract ONLY the most relevant category based on the job role. Do not include unrelated categories.

    4) HANDLE BROAD TERMS INTELLIGENTLY:
    - If the user mentions broad or ambiguous terms, classify based on logical context.
    - "Technical" Terms Handling:
        - If the context clearly indicates advanced expertise or formal training, classify as "Skilled".
        - If it refers to operators, assistants, or general on-the-job experience, classify as "Semi-Skilled".
        - If context is unclear, classify with the most probable category based on the job description.
        - Do NOT extract multiple categories unless clearly mentioned.

    Examples:
    - "Looking for technical workers." → ["Semi-Skilled"] (as it's likely general)
    - "Looking for technical engineers." → ["Skilled"]
    - "Need technical operators for machines." → ["Semi-Skilled"]
    - "Hiring experienced technical staff." → ["Skilled"]
    - "Hiring crane operators for the construction site." → ["Semi-Skilled"]
    - "Need helpers for packaging work." → ["Unskilled"]
    - "Looking for electricians and plumbers." → ["Skilled"]
    - "I need laborers for shifting work." → ["Unskilled"]
    - "Searching for skilled operators for heavy machinery." → ["Skilled"]
    - "Looking for workers in Surat." → null

    5) MULTIPLE CLASSIFICATIONS:
    - If the query mentions multiple job roles, classify each and return them together.
    - Example: "I need electricians and machine operators." → ["Skilled", "Semi-Skilled"]

    6) FINAL OUTPUT RULES:
    - Only include the following values in the response: "Skilled", "Semi-Skilled", "Unskilled".
    - If no valid classification is possible, return `null`.

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

    prompt = PromptTemplate(
        input_variables=["user_query"],
        template=prompt_template_str
    )
    chain = prompt | llm
    response = chain.invoke({
        "user_query": user_input
    })

    raw_output = response.content.strip()

    return extract_json_from_llm_response_employment(raw_output, "KEYWORDS")

def generate_dynamic_message(chat_history_for_context: List[dict], static_follow_up: str, user_message: str, llm,chatId) -> str:
    """
    Generate a dynamic follow-up message using LLM based on the latest context and static follow-up requirement.
    
    Parameters:
        chat_history (List[dict]): The list of conversation history with user and AI messages.
        static_follow_up (str): The static follow-up message to send to the user.
        llm: The language model instance.
    
    Returns:
        str: The dynamically generated follow-up message.
    """
    chat_history = get_chat(f"chat_{chatId}") if get_chat(f"chat_{chatId}") else []
    # Prepare the conversation history context
    recent_history = "\n".join(
        chat_history_for_context
    )  # Limit history to the last 6 messages for brevity
    
    # Define the refined prompt
    prompt = """
    You are a highly skilled assistant specializing in creating professional, engaging, and contextually relevant messages.
    Your goal is to craft a polished follow-up message that seamlessly incorporates the provided static follow-up message while aligning with the tone and context of the recent conversation.

    Inputs:
    1. User’s Latest Message:
    - This is the most recent message from the user. Use this to determine the appropriate tone, greetings, or redirection.
    - {user_message}

    2. Recent Conversation History:
    - This contains past exchanges between the user and the assistant.
    - Use this context only to understand the flow of the conversation.
    - Do not infer, assume, or include any location (area, city, or state) from the history or the user’s latest message unless explicitly mentioned in the static follow-up message.
    - {recent_history}

    3. Static Follow-Up Message:
    - This is the core message that must be delivered to the user.
    - Your task is to naturally incorporate this message into the final response.
    - Static Message: "{static_follow_up}"

    Response Guidelines:
    Strict Focus on Employment-Related Queries
    - Only include employment-related details in the follow-up message, even if the user query mentions multiple topics.
    - If the user mentions incentives, approvals, vendors, or any other unrelated terms, completely exclude them from the response.
    - Regardless of any other mentioned topics, employment-related words should appear in the response.

    Example Correction:
    - User Query: "I want to search for incentives and employment."
    - Wrong Response: "I can assist with employment-related searches."
    - Correct Response: "Could you specify the industry or location you're looking for employment opportunities in?"

    Strict Location Handling:
    - Under no circumstances should you infer or assume any location (area, city, or state) from the user’s message or the conversation history unless the location is explicitly mentioned in the static follow-up message.
    - If no location is provided in the static follow-up, do not include one in the generated response.

    Correct Usage of Conjunctions:
    - Do not use conjunctions at the beginning of a sentence unless absolutely necessary.
    - Only use conjunctions like "To find employment" or "To better assist you" when transitioning from an answer to a missing information request.
    - If the response is a direct question, do not add unnecessary conjunctions.

    Example Correction:
    - User Query: "I want employment details in Ankleshwar."
    - Wrong Response: "To find employment in Ankleshwar, employment status details are available for Bharuch, which encompasses the area of Ankleshwar. Would you like to view the information for Bharuch?"
    - Correct Response: "Employment status details are available for Bharuch, which includes Ankleshwar. Would you like to view the information for Bharuch?"

    - User Query: "Where is employment highest in Gujarat?"
    - Wrong Response: "To provide this information, Gujarat has high employment in Ahmedabad and Surat."
    - Correct Response: "Ahmedabad and Surat have the highest employment in Gujarat. Are you looking for details on a specific sector?"

    Natural and Engaging Tone:
    - The response should feel like a smooth continuation of the conversation without sounding mechanical or scripted.
    - Avoid robotic acknowledgments or unnecessary phrases such as "I wanted to follow up on..." or "I am here to assist with..."

    Handling Greetings:
    - If the user greets (e.g., "Hi", "Hello", "Good morning"), respond with an appropriate greeting and then transition seamlessly into the static follow-up message.

    Handling Off-Topic Queries:
    - Only use the phrase "I can assist with employment-related searches." when the user’s query is truly off-topic.
    - If the user query is already employment-related, generate a relevant response without using this phrase.
    - For truly irrelevant queries (not related to employment at all), politely inform the user that employment assistance is the focus.

    Example Correction:
    - User Query: "Can you tell me about tourism in Paris?"
    - Correct Response: "I specialize in employment-related searches. Let me know if you have any employment-related questions."
    - User Query: "What are the job opportunities in Bangalore?"
    - Correct Response: "Could you specify the industry or job category you're looking for in Bangalore?"

    Handling Special Events:
    - If the user mentions a special occasion (e.g., birthday, anniversary), acknowledge and celebrate it first before transitioning into the static follow-up message.

    Handling Negative Emotions:
    - If the user expresses sadness, frustration, or anger, address their emotions with empathy first before seamlessly transitioning into the static follow-up message.

    Additional Instructions:
    1. Do not include any reasons, explanations, or assumptions about the static follow-up or user query (e.g., "I’ve reviewed our conversation" or "It seems you are asking about...").
    2. Ensure transitions between the user’s input and the static follow-up message are smooth and cohesive, avoiding abrupt changes or unrelated statements.
    3. Keep the response concise, limiting it to two or three short sentences while fully incorporating the static follow-up message.
    4. Ensure the message is professional, user-friendly, and free of unnecessary elaboration or additional context.

    Output:
    - Generate a concise, polished response that aligns with the tone of the user’s latest message.
    - Seamlessly integrate the static follow-up message while adhering to all guidelines.
    - Strictly ensure that only employment-related terms appear in the response.
    - Do not mention incentives, approvals, vendors, or any non-employment-related terms, even if they were part of the user query.
    - Only use "I can assist with employment-related searches." when the user query is completely off-topic.
    - Ensure that conjunctions are only used where appropriate—avoid unnecessary conjunctions at the beginning of sentences.
    """
    
    # Prepare input to the model
    prompt_template = PromptTemplate(
        input_variables=["user_message","recent_history", "static_follow_up"],
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
    chat_history.append(AIMessage(content=f"{message.content.strip()}"))
    # logging.info(f"actual aarray3 {chat_history}")
    save_chat(chat_history,f"chat_{chatId}")
    return message.content.strip()

def check_user_intent(response: str, follow_up_question: str, llm,chatId) -> str:
    """
    Check the user's intent in response to a follow-up question or location-specific query.

    Parameters:
        response (str): User's response to a follow-up question.
        follow_up_question (str): The follow-up question that the user is responding to.
        llm: The language model instance.

    Returns:
        str: One of 'Agree', 'Disagree', 'Other Intent', or 'Location Specific Query'.
    """
    prompt = r"""
    You are analyzing a user's response and determining the intent based on the context of a follow-up question and the user's answer. 
    It is mandatory to classify the user's intent into one of the following four categories:
    
    1. "Agree": 
       - The user agrees to proceed or affirms the intent based on the follow-up question.

    2. "Disagree": 
       - The user explicitly disagrees, rejects the intent, or indicates a preference for something different.

    3. "Location Specific Query": 
       - The user's response explicitly focuses on a location, including any mention of an area, city, state, or other geographic entity.
       - Do NOT classify as "Agree" or "Disagree" if the response mentions a location instead of directly addressing the follow-up question.
       - Always classify as "Location Specific Query" if the response includes specific location-related terms, even if it indirectly answers the follow-up question.

    4. "Other Intent": 
       - The user's response is unrelated to the question, ambiguous, off-topic, or does not fit the above categories.

    Key Points:
    - The user's response may be complex, so do not make decisions based solely on simple "yes" or "no" answers or the presence of location names.
    - Analyze the entire context of the follow-up question and the user's response before determining the intent.
    - Strictly classify the intent into one of the above four categories. Do not provide explanations or reasons for your classification.

    Output format:
    Classified intent: <One of 'Agree', 'Disagree', 'Location Specific Query', or 'Other Intent'>

    Follow-Up Question: {follow_up_question}
    User's Response: {response}
    """

    chat_history = get_chat(f"chat_{chatId}") if get_chat(f"chat_{chatId}") else []
    prompt_template = PromptTemplate(
        input_variables=["response", "follow_up_question"],
        template=prompt
    )
    chain = prompt_template | llm
    intent_response = chain.invoke({"response": response, "follow_up_question": follow_up_question})
    update_llm_token(intent_response)
    intent_text = intent_response.content.strip()


    # Extract the classified intent using regex
    intent_match = re.search(r"Classified intent:\s*(Agree|Disagree|Location Specific Query|Other Intent)", intent_text)
    classified_intent = intent_match.group(1) if intent_match else "Other Intent"

    # Append the follow-up question, user response, and the AI interpretation to the chat history
    chat_history.append(HumanMessage(content=f"User's Response: {response}"))
    chat_history.append(AIMessage(content=f"Classified Intent: {classified_intent}"))
    # logging.info(f"actual aarray2 {chat_history}")
    save_chat(chat_history,f"chat_{chatId}")

    return classified_intent

def handle_employment_query(
    user_input: str,
    available_areas,
    available_cities,
    available_states,
    city_to_area_mapping: Dict[str, str],
    state_to_city_mapping: Dict[str, str],
    llm,chatId
) -> Union[Dict[str, Union[str, List[str]]], str]:
    """
    Handles user queries about employment data with dynamic follow-up questions.

    Parameters:
        user_input (str): The user's input query.
        validated_data (Dict[str, str]): Validated data dictionary with 'Area', 'City', and 'State' keys.
        area_to_city_mapping (Dict[str, str]): Mapping of areas to cities.
        city_to_state_mapping (Dict[str, str]): Mapping of cities to states.
        llm: The language model instance.

    Returns:
        Dict[str, Union[str, List[str]]]: A dictionary containing responses or follow-up questions.
    """
    chat_history = get_chat(chatId) if get_chat(chatId) else []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    refined_user_input = refine_query_with_history_for_employment(Chat_history_normal, user_input, llm_70b_vers)
    chat_history.append(HumanMessage(content=refined_user_input))  # Log user query
    save_chat(chat_history,f"chat_{chatId}")
    result = classify_employment_query(refined_user_input, llm_70b_vers)
    user_intention = result["classification_category"]
    keyword_dict = extract_employment_keywords_from_query(refined_user_input, llm)
    if user_intention == "Individual employment status":
        classification_data, validated_data = extract_location_from_query(refined_user_input, available_areas= available_areas, available_cities= available_cities, available_states= available_states, llm=llm_70b_vers)
       
        # Extract validated details
        area = validated_data["Area"]
        city = validated_data["City"]
        state = validated_data["State"]

        # logging.info(f"area {area} and city {city} and state {state} ")

        classification_data_to_send =  {
            key: [] if value == "None" else [i_value.strip() for i_value in value.split(",")]
            for key, value in classification_data.items()
        }
        validated_data_to_send = {
            key: [] if value == "None" else [i_value.strip() for i_value in value.split(",")]
            for key, value in validated_data.items()
        }

        # Scenario 1: Area is specified
        if area != "None":
            city_to_area_mapping_val_list = [i for lst in list(city_to_area_mapping.values()) for i in lst]

            if area == "Not Available in List":
                response = {
                    "Ai_response": "Not Available In List",
                    "Is_confirmation" : None,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response
            
            elif area in city_to_area_mapping_val_list:
                parent_city = next((key for key, value in city_to_area_mapping.items() if area in value), None)
                parent_state = next((key for key, value in state_to_city_mapping.items() if parent_city in value), None)
                context = f"Employment status details are available for {parent_city}, which encompasses the area of {area}. Would you like to view the information for {parent_city}?"
                message = generate_dynamic_message(Chat_history_normal,context, refined_user_input,llm_70b_vers_creative,chatId=chatId)
                classification_data_to_send["Area"] = []
                classification_data_to_send["City"] = [parent_city,]
                classification_data_to_send["State"] = [parent_state,]
                validated_data_to_send["Area"] = []
                validated_data_to_send["City"] = [parent_city,]
                validated_data_to_send["State"] = [parent_state,]
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : True,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response

            else:
                response = {
                    "Ai_response": "Not Available",
                    "Is_confirmation" : None,
                    "Extracted Data": None,
                    "Validation Data": None,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response

        # Scenario 2: City is specified
        if city != "None":
            # logging.info(f"here city is {city}")
            state_to_city_mapping_val_list = [i for lst in list(state_to_city_mapping.values()) for i in lst]
            # logging.info(f"state_to_city_mapping_val_list {state_to_city_mapping_val_list} and city {city}")
            if city == "Not Available in List":
                response = {
                    "Ai_response": "Not Available in List",
                    "Is_confirmation" : None,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response

            elif city in state_to_city_mapping_val_list:
                parent_state = next((key for key, value in state_to_city_mapping.items() if city in value), None)
                classification_data_to_send["Area"] = []
                classification_data_to_send["City"] = [city,]
                classification_data_to_send["State"] = [parent_state,]
                validated_data_to_send["Area"] = []
                validated_data_to_send["City"] = [city,]
                validated_data_to_send["State"] = [parent_state,]
                context = f"We have identified the city as {city} and the state as {parent_state} based on your query. Please confirm if this information is correct"
                message = generate_dynamic_message(Chat_history_normal,context,refined_user_input,llm_70b_vers_creative,chatId=chatId)
                # frappe.error_log(f"new generated message is {message}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : True,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response
        
            else:
                response = {
                    "Ai_response": "Not Available",
                    "Is_confirmation" : None,
                    "Extracted Data": None,
                    "Validation Data": None,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response


        # Scenario 3: State is specified
        if state != "None":
            if state == "Not Available in List":
                response = {
                    "Ai_response": "Not Available in List",
                    "Is_confirmation" : None,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response

            elif city == "None":
                context = f"We have identified the state as {state} based on your query. Please confirm if this information is correct"
                message = generate_dynamic_message(Chat_history_normal,context,refined_user_input,llm_70b_vers_creative,chatId=chatId)
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : True,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention,
                    "KEYWORDS": keyword_dict["KEYWORDS"]
                }
                return response

        # Scenario 4: All fields are None
        if area == city == state == "None":
            context = "I am unable to understand the exact location or intent related to your query on employment information. Kindly provide the name of a specific city or state, or clarify your request further to assist you better."
            message = generate_dynamic_message(Chat_history_normal,context,refined_user_input,llm_70b_vers_creative,chatId=chatId)
            # logging.info(f"chat history 30 {chat_history}")
            response = {
                "Ai_response": message,
                "Is_confirmation" : None,
                "Extracted Data": None,
                "Validation Data": None,
                "User Intention": user_intention,
                "KEYWORDS": keyword_dict["KEYWORDS"]
            }
            return response
        
    elif user_intention == "Comparison between cities, states, or areas":
        # Example Usage
        classification_data, validated_data = extract_comparison_locations(
            user_input= refined_user_input,
            available_areas= available_areas,
            available_cities= available_cities,
            available_states=available_states,
            llm=llm_70b_vers
        )
        if validated_data["Area"] == "None" and validated_data["City"] == "None" and validated_data["State"] == "None":
            context = "I am unable to understand the exact location or intent related to your query on employment information. Kindly provide the name of a specific city or state, or clarify your request further to assist you better."
            message = generate_dynamic_message(Chat_history_normal,context,refined_user_input,llm_70b_vers_creative,chatId=chatId)
            response = {
                "Ai_response": message,
                "Is_confirmation" : None,
                "Extracted Data": None,
                "Validation Data": None,
                "User Intention": user_intention,
                "KEYWORDS": keyword_dict["KEYWORDS"]
            }
            return response
        
        else:
            classification_data_to_send =  {
                key: [] if value == "None" else [i_value.strip() for i_value in value]
                for key, value in classification_data.items()
            }
            validated_data_to_send = {
                key: [] if value == "None" else [i_value.strip() for i_value in value.split(",")]
                for key, value in validated_data.items()
            }
            # Extract and combine all unique locations from the JSON fields
            locations = set(validated_data_to_send.get('Area', []) + validated_data_to_send.get('City', []) + validated_data_to_send.get('State', []))
            # Join locations with commas and 'and' for the last item
            locations_list = list(locations)
            if len(locations_list) == 1:
                locations_str = locations_list[0]
            else:
                locations_str = ', '.join(locations_list[:-1]) + f", and {locations_list[-1]}"
            
            # Construct the confirmation message
            message = f"Kindly confirm if you are seeking to compare the employment status between {locations_str}."
            confirmation_message = generate_dynamic_message(Chat_history_normal, message,refined_user_input, llm_70b_vers_creative)
            response = {
                "Ai_response": confirmation_message,
                "Is_confirmation" : True,
                "Extracted Data": classification_data_to_send,
                "Validation Data": validated_data_to_send,
                "User Intention": user_intention,
                "KEYWORDS": keyword_dict["KEYWORDS"]
            }
            return response
    else:
        context = "I am unable to understand the exact location or intent related to your query on employment information. Kindly provide the name of a specific city or state, or clarify your request further to assist you better."
        message = generate_dynamic_message(Chat_history_normal,context,refined_user_input,llm_70b_vers_creative,chatId=chatId)
        response = {
                "Ai_response": message,
                "Is_confirmation" : None,
                "Extracted Data": None,
                "Validation Data": None,
                "User Intention": user_intention,
                "KEYWORDS": keyword_dict["KEYWORDS"]
            }
        return response
    

def call_handle_employment_query(input,chatId):

    query = """
        select acmapped.area_name, acmapped.city_name, st.state_name
        from (
            select at.name As AT, at.area_name, ct.name as CT, ct.city_name, ct.state
            from `tabArea` as at
            inner join `tabCity` as ct
            on at.city_id = ct.name
        ) as acmapped
        join `tabState` as st
        on acmapped.state = st.name
        """

    result_of_query = fetch_query_results(query)
    # logging.info(f"result_of_query {result_of_query}")

    # Create a DataFrame from the result
    columns = ["area_name", "city_name", "state_name"]
    df = pd.DataFrame(result_of_query, columns=columns)
    df = df.drop_duplicates()

    city_area_mapped_dict = df.groupby("city_name")["area_name"].apply(list).to_dict()
    state_city_mapped_dict = df.groupby("state_name")["city_name"].apply(lambda x: list(x.unique())).to_dict()

    query = """
    select distinct area_name
    from `tabArea`
    """
   
    result_for_d_area = fetch_query_results(query)

    unique_area_list = [row[0] for row in result_for_d_area]

    query = """
    select distinct city_name
    from `tabCity`
    """

    result_for_d_city = fetch_query_results(query)

    unique_city_list = [row[0] for row in result_for_d_city]

    query = """
    select distinct state_name
    from `tabState`
    """
    result_for_d_state = fetch_query_results(query)

    unique_state_list = [row[0] for row in result_for_d_state]

    response = handle_employment_query(input,unique_area_list, unique_city_list, unique_state_list, city_area_mapped_dict, state_city_mapped_dict, llm_70b_vers,chatId)

    return response
