import re
from typing import List, Dict, Tuple, Union
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from frontend_app.Ai_module.Query_Classification_And_Analysis import llm_70b_vers, llm_70b_vers_creative
from langchain.schema import HumanMessage, AIMessage
import pandas as pd
import frappe
import logging
from frontend_app.Management_Class.Redis_management.Redis_chat import save_chat,get_chat

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
    refined_text = refined_query.content.strip()
    
    # Extract the reformulated standalone query
    match = re.search(r'reformulated standalone query:\s*(?:"(.*?)"|\'(.*?)\'|(.*))$', refined_text, re.IGNORECASE)
    if match:
        # Return the captured group that is not None
        return next(group for group in match.groups() if group)
    
    # Fallback to the entire response if no match is found
    return refined_text

def classify_employment_query(query, llm):
    """
    Classify the user's employment search query into two categories:
    1. Individual employment status.
    2. Comparison between cities, states, or areas.

    Args:
        query (str): The user's input query.
        llm: The language model object.

    Returns:
        dict: A dictionary with the raw prompt, classification category, and explanation if needed.
    """
    # Define the category mapping
    category_mapping = {
        1: "Individual employment status",
        2: "Comparison between cities, states, or areas",
        3: "Other Intention"
    }

    # Define the refined prompt string
    refined_prompt = """
    You are an expert in analyzing user queries related to employment searches. Your task is to classify the user's intention into one of the following categories:

    1. Individual Employment Status:
    - Queries focusing on employment statistics, job availability, or unemployment rates in a specific location (e.g., "employment status in Ahmedabad" or "job statistics for Gujarat").
    - Includes queries targeting districts, towns, or cities (considered as equivalent to cities) or states individually.

    2. Comparison Between Locations:
    - Queries involving a comparison of employment-related metrics between multiple locations (e.g., "compare Ahmedabad and Baroda" or "employment status in Gujarat vs Maharashtra").
    - Multiple locations must be explicitly mentioned in the query for it to fall into this category.

    3. Other Intentions:
    - Any query that does not pertain to employment searches or falls outside the scope of categories 1 and 2.

    Additional Classification Guidelines:
    - Treat districts, towns, and cities as equivalent to cities when interpreting queries.
    - If the query mentions multiple locations explicitly and seeks comparison, classify it as category 2, regardless of the phrasing.
    - For vague or unclear queries, classify into category 3 (Other Intentions).

    Query: {query}

    Output:
    Classify the query into one of the categories (1, 2, or 3). Provide the classification number only, with no explanations or additional text.
    """


    # Create a PromptTemplate for chaining
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template=refined_prompt,
    )

    # Use the prompt in a chain
    chain = prompt_template | llm
    # Run the chain and capture the response
    response = chain.invoke({"query": query})

    # Use regex to extract a valid classification number
    match = re.search(r"^\s*([1-3])\s*$", response.content.strip())
    if match:
        classification_number = int(match.group(1))
        classification_category = category_mapping[classification_number]
        return {
            "raw_prompt": refined_prompt,
            "classification_number": classification_number,
            "classification_category": classification_category,
        }
    else:
        raise ValueError(f"Unexpected or invalid response from LLM: {response}")


def extract_location_for_employment_query(user_input: str, available_areas: List[str], available_cities: List[str], available_states: List[str], llm) -> Dict[str, str]:
    """
    Extract the area, city, or state mentioned in the user query and validate against the available lists.

    Parameters:
        user_input (str): The user-provided query.
        available_areas (List[str]): List of all available areas.
        available_cities (List[str]): List of all available cities.
        available_states (List[str]): List of all available states.
        llm: The language model instance to use for processing.

    Returns:
        Dict[str, str]: A dictionary containing the extracted area, city, and state. Validation for presence
        in the available lists happens outside the model's logic.
    """
    # Convert lists to strings
    areas_string = ", ".join(available_areas)
    cities_string = ", ".join(available_cities)
    states_string = ", ".join(available_states)

    # Define the prompt
    prompt_template = """
    You are an assistant designed to extract location information from user input with precision.
    Your primary goal is to identify and accurately classify the area, city, or state mentioned in the user's query.

    Instructions:
    - Available Location Data:
        - Areas: {areas_string}
        - Cities: {cities_string}
        - States: {states_string}
    - Use these lists as references to classify and validate the user's query. Match the input with the closest location name from these lists whenever possible, accounting for typos or phonetic variations.

    Guidelines:
    1. India-Focused Context:
        - Assume the majority of areas, cities, or states referenced in the user's query are located in India.
        - If the identified location is outside India or does not logically belong to India, return `"None"` for the respective field(s).

    2. Handling Explicit Location Mentions:
        - If the user explicitly mentions a location in their query:
            - Accurately extract and classify it as "Area," "City," or "State."
            - If the location is not in India, return `"None"` for that field.

    3. Vague or Incomplete Queries:
        - Extract location information even when the query is vague, incomplete, or unstructured.
        - Use similarity-based logic to identify the closest match from the provided lists while ensuring accuracy.

    4. Precise Classification Rules:
        - If the location is an area, put the name in the `"Area"` field and set `"City"` and `"State"` fields to `"None"`.
        - If the location is a city, put the name in the `"City"` field and set `"Area"` and `"State"` fields to `"None"`.
        - If the location is a state, put the name in the `"State"` field and set `"Area"` and `"City"` fields to `"None"`.
        - If no identifiable area, city, or state is mentioned, set all fields to `"None"`.

    5. Unmatched Locations:
        - If a location cannot be matched to any entry in the provided lists but logically belongs to India, classify it under the most appropriate field.
        - If it cannot be classified and does not belong to India, return `"None"`.

    User Query:
    {query}

    Output Format:
    Provide the output strictly as a JSON object in the following format:
    {{
        "Area": <Extracted Area or 'None'>,
        "City": <Extracted City or 'None'>,
        "State": <Extracted State or 'None'>
    }}
    """
    
    # Create a PromptTemplate and LLM chain
    prompt = PromptTemplate(
        input_variables=["query", "areas_string", "cities_string", "states_string"],
        template=prompt_template
    )
    chain = prompt | llm
    
    # Run the LLM chain
    response = chain.invoke({
        "query": user_input,
        "areas_string": areas_string,
        "cities_string": cities_string,
        "states_string": states_string
    })

    # Use regex to extract Area, City, and State values
    area_match = re.search(r'"Area":\s*"([^"]+)"', response.content.strip())
    city_match = re.search(r'"City":\s*"([^"]+)"', response.content.strip())
    state_match = re.search(r'"State":\s*"([^"]+)"', response.content.strip())
    
    # Extract the matched values or default to "None"
    area = area_match.group(1) if area_match else "None"
    city = city_match.group(1) if city_match else "None"
    state = state_match.group(1) if state_match else "None"
    
    # Create initial classification dictionary
    classification = {
        "Area": area,
        "City": city,
        "State": state
    }

    # Validate against the available lists
    validated_classification = {
        key: (value if value in available_areas + available_cities + available_states else "Not Available in List")
        if value != "None" else "None"
        for key, value in classification.items()
    }

    return classification,validated_classification

def extract_comparison_locations(
    user_input: str,
    available_areas: List[str],
    available_cities: List[str],
    available_states: List[str],
    llm
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Extract multiple areas, cities, and states from the user's query for comparison purposes.
    """
    # Convert lists to strings
    areas_string = ", ".join(available_areas)
    cities_string = ", ".join(available_cities)
    states_string = ", ".join(available_states)

    # Define the prompt
    prompt_template = """
    You are an assistant designed to extract and classify multiple locations mentioned in a query for comparison purposes.
    Your primary goal is to identify and accurately classify all areas, cities, or states mentioned in the user's query.

    Instructions:
    - Available Location Data:
        - Areas: {areas_string}
        - Cities: {cities_string}
        - States: {states_string}
    - Use these lists as references to classify and validate the user's query. Match the input with the closest location names from these lists whenever possible, accounting for typos or phonetic variations.

    Guidelines:
    1. India-Focused Context:
        - Assume the majority of areas, cities, or states referenced in the user's query are located in India.
        - If the identified location is outside India or does not logically belong to India, return `"None"` for the respective field(s).

    2. Handling Explicit Location Mentions:
        - If the user explicitly mentions locations in their query:
            - Extract and classify them accurately as "Area," "City," or "State."
            - If a location is not in India, return `"None"` for that field.

    3. Vague or Incomplete Queries:
        - Extract location information even when the query is vague, incomplete, or unstructured.
        - Use similarity-based logic to identify the closest matches from the provided lists while ensuring accuracy.

    4. Precise Classification Rules for Multiple Locations:
        - If multiple areas are mentioned, list them all in the `"Area"` field, separated by commas, and enclosed in double quotes as a single string.
        - If multiple cities are mentioned, list them all in the `"City"` field, separated by commas, and enclosed in double quotes as a single string.
        - If multiple states are mentioned, list them all in the `"State"` field, separated by commas, and enclosed in double quotes as a single string.
        - If no identifiable area, city, or state is mentioned, set all fields to `"None"`.

    5. Unmatched Locations:
        - If a location cannot be matched to any entry in the provided lists but logically belongs to India, classify it under the most appropriate field.
        - If it cannot be classified and does not belong to India, return `"None"`.

    Strict Formatting Rules:
    - Ensure the output is deterministic, producing identical results for the same input every time.
    - Output the final result strictly in the JSON format described below, ensuring all values are strings enclosed in double quotes:
    {{
        "Area": "<Extracted Areas (comma-separated) or 'None'>",
        "City": "<Extracted Cities (comma-separated) or 'None'>",
        "State": "<Extracted States (comma-separated) or 'None'>"
    }}

    - Do not provide intermediate results, notes, alternative outputs, or any other text. Only provide the final JSON object as described.

    User Query:
    {query}

    Provide the final result strictly as a JSON object in the required format.
    """

    # Create a PromptTemplate and LLM chain
    prompt = PromptTemplate(
        input_variables=["query", "areas_string", "cities_string", "states_string"],
        template=prompt_template
    )
    chain = prompt | llm

    # Run the LLM chain
    response = chain.invoke({
        "query": user_input,
        "areas_string": areas_string,
        "cities_string": cities_string,
        "states_string": states_string
    })
    # Use regex to extract Area, City, and State values
    area_match = re.search(r'"Area":\s*"([^"]*)"', response.content.strip())
    city_match = re.search(r'"City":\s*"([^"]*)"', response.content.strip())
    state_match = re.search(r'"State":\s*"([^"]*)"', response.content.strip())

    # Extract the matched values or default to "None"
    area = area_match.group(1).strip() if area_match else "None"
    city = city_match.group(1).strip() if city_match else "None"
    state = state_match.group(1).strip() if state_match else "None"

    # Create initial classification dictionary
    classification = {
        "Area": area,
        "City": city,
        "State": state
    }

    # Validate against the available lists
    validated_classification = {
        key: ", ".join(
            [
                loc.strip() if loc.strip() in available_areas + available_cities + available_states else "Not Available in List"
                for loc in value.split(",") if value != "None"
            ]
        ) if value != "None" else "None"
        for key, value in classification.items()
    }

    return classification, validated_classification

# Chat history to maintain context
# chat_history = get_chat(chatId) if get_chat("chat_history") else []

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
    chat_history = get_chat(chatId) if get_chat(chatId) else []
    # Prepare the conversation history context
    recent_history = "\n".join(
        chat_history_for_context
    )  # Limit history to the last 6 messages for brevity
    
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
    - Do NOT infer, assume, or include any location (area, city, or state) from the history or the user’s latest message unless explicitly mentioned in the static follow-up message.
    - {recent_history}

    3. Static Follow-Up Message:
    - This is the core message that must be delivered to the user.
    - Your task is to naturally incorporate this message into the final response.
    - Static Message: "{static_follow_up}"

    Response Guidelines:
    - Strict Location Handling:
    - Under no circumstances should you infer or assume any location (area, city, or state) from the user’s message or the conversation history unless the location is explicitly mentioned in the static follow-up message.
    - If no location is provided in the static follow-up, do NOT include one in the generated response.

    - Natural and Engaging Tone:
    - The response should feel like a smooth continuation of the conversation without sounding mechanical or scripted.
    - Avoid robotic acknowledgments or unnecessary phrases such as "I wanted to follow up on..." or "I am here to assist with..."

    - Handling Greetings:
    - If the user greets (e.g., "Hi", "Hello", "Good morning"), respond with an appropriate greeting and then transition seamlessly into the static follow-up message.

    - Handling Off-Topic Queries:
    - If the user’s query is unrelated to industry or employment topics, politely inform them:  
    "I specialize in assisting with employment queries related to various industries."
    - Do NOT engage with the off-topic query but redirect to the static follow-up message.

    - Handling Special Events:
    - If the user mentions a special occasion (e.g., birthday, anniversary), acknowledge and celebrate it first before transitioning into the static follow-up message.

    - Handling Negative Emotions:
    - If the user expresses sadness, frustration, or anger, address their emotions with empathy first before seamlessly transitioning into the static follow-up message.

    Additional Instructions:
    1. Do NOT include any reasons, explanations, or assumptions about the static follow-up or user query (e.g., "I’ve reviewed our conversation" or "It seems you are asking about...").
    2. Ensure transitions between the user’s input and the static follow-up message are smooth and cohesive, avoiding abrupt changes or unrelated statements.
    3. Keep the response concise, limiting it to two or three short sentences, while fully incorporating the static follow-up message.
    4. Ensure the message is professional, user-friendly, and free of unnecessary elaboration or additional context.

    Output:
    - Generate a concise, polished response that aligns with the tone of the user’s latest message.
    - Seamlessly integrate the static follow-up message while adhering to all guidelines.
    - Do NOT include any locations (area, city, or state) in the response unless explicitly mentioned in the static follow-up message.
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
    
    # Append AI message to chat history
    chat_history.append(AIMessage(content=f"{message.content.strip()}"))
    # logging.info(f"actual aarray3 {chat_history}")
    save_chat(chat_history,chatId=chatId)
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

    chat_history = get_chat(chatId) if get_chat(chatId) else []
    prompt_template = PromptTemplate(
        input_variables=["response", "follow_up_question"],
        template=prompt
    )
    chain = prompt_template | llm
    intent_response = chain.invoke({"response": response, "follow_up_question": follow_up_question})
    intent_text = intent_response.content.strip()


    # Extract the classified intent using regex
    intent_match = re.search(r"Classified intent:\s*(Agree|Disagree|Location Specific Query|Other Intent)", intent_text)
    classified_intent = intent_match.group(1) if intent_match else "Other Intent"

    # Append the follow-up question, user response, and the AI interpretation to the chat history
    chat_history.append(HumanMessage(content=f"User's Response: {response}"))
    chat_history.append(AIMessage(content=f"Classified Intent: {classified_intent}"))
    # logging.info(f"actual aarray2 {chat_history}")
    save_chat(chat_history,chatId=chatId)

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
    result = classify_employment_query(user_input, llm_70b_vers)
    user_intention = result["classification_category"]
    chat_history = get_chat(chatId) if get_chat(chatId) else []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    refined_user_input = refine_query_with_history_for_employment(Chat_history_normal, user_input, llm_70b_vers)
    chat_history.append(HumanMessage(content=refined_user_input))  # Log user query
    save_chat(chat_history,chatId=chatId)
    if user_intention == "Individual employment status":
        classification_data, validated_data = extract_location_for_employment_query(refined_user_input, available_areas= available_areas, available_cities= available_cities, available_states= available_states, llm=llm_70b_vers)
       
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
                    "User Intention": user_intention
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
                    "User Intention": user_intention
                }
                return response

            else:
                response = {
                    "Ai_response": "Not Available",
                    "Is_confirmation" : None,
                    "Extracted Data": None,
                    "Validation Data": None,
                    "User Intention": user_intention
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
                    "User Intention": user_intention
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
                    "User Intention": user_intention
                }
                return response
        
            else:
                response = {
                    "Ai_response": "Not Available",
                    "Is_confirmation" : None,
                    "Extracted Data": None,
                    "Validation Data": None,
                    "User Intention": user_intention
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
                    "User Intention": user_intention
                }
                return response

            elif city == "None":

                response = {
                    "Ai_response": "Not Available in List",
                    "Is_confirmation" : None,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention
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
                "User Intention": user_intention
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
                "User Intention": user_intention
            }
            return response
        
        else:
            classification_data_to_send =  {
                key: [] if value == "None" else [i_value.strip() for i_value in value.split(",")]
                for key, value in classification_data.items()
            }
            validated_data_to_send = {
                key: [] if value == "None" else [i_value.strip() for i_value in value.split(",")]
                for key, value in validated_data.items()
            }
            response = {
                "Ai_response": "We Found Something For your Query",
                "Is_confirmation" : True,
                "Extracted Data": classification_data_to_send,
                "Validation Data": validated_data_to_send,
                "User Intention": user_intention
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
                "User Intention": user_intention
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