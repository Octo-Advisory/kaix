import re
from typing import List, Dict, Tuple, Union
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from frontend_app.Ai_module.Query_Classification_And_Analysis import refine_query_with_history, llm_70b_vers
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
    }

    # Define the raw prompt string
    raw_prompt = """
    You are an expert in analyzing user queries related to employment searches. Your task is to classify the user's intention into one of the following categories:

    1. Individual employment status.
    2. Comparison between cities, states, or areas.

    Additional Guidelines:
    - Consider districts, towns, and cities as the same level (city).
    - If the query involves comparisons (e.g., "compare Ahmedabad and Baroda" or "employment status in Gujarat vs Maharashtra"), classify it as category 2.
    - If the query focuses on one specific location (e.g., "employment status in Ahmedabad" or "job statistics for Gujarat"), classify it as category 1.

    Query: {query}

    Output:
    Classify the query into one of the categories (1 or 2). Provide the classification number only.
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
    match = re.search(r"^\s*([1-2])\s*$", response.content.strip())
    if match:
        classification_number = int(match.group(1))
        classification_category = category_mapping[classification_number]
        return {
            "raw_prompt": raw_prompt,
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
    Based on the user's query, identify the area, city, or state they are referring to.

    Instructions:
    - You are provided with the following lists of available locations:
    - Areas: {areas_string}
    - Cities: {cities_string}
    - States: {states_string}
    - Use these lists as a reference to identify and classify the user's query. Match the input with the closest location name from these lists when possible.

    Guidelines:
    1. If the user mentions an area, city, or state, classify it with the highest precision possible:
    - If it is an area, put the name in the "Area" field and set "City" and "State" fields to "None."
    - If it is a city, put the name in the "City" field and set "Area" and "State" fields to "None."
    - If it is a state, put the name in the "State" field and set "Area" and "City" fields to "None."
    2. Use similarity-based matching to identify the nearest location name from the provided lists, considering minor variations, typos, or phonetic similarities.
    - For example, if the query contains "Shubhanpura" and the closest match in the available list is "Subhanpura," classify it using "Subhanpura."
    3. If the location name identified from the query does not match any entry in the provided lists:
    - Keep the location name as it is and classify it under the most appropriate field ("Area," "City," or "State").
    4. If no identifiable area, city, or state is mentioned, set all fields to "None."

    User Query: {query}

    Provide the output as a JSON object in the following format:
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
    Based on the user's query, identify all areas, cities, and states they are referring to.

    Instructions:
    - You are provided with the following lists of available locations:
    - Areas: {areas_string}
    - Cities: {cities_string}
    - States: {states_string}
    - Use these lists as a reference to identify and classify the user's query. Match the input with the closest location names from these lists when possible.

    Guidelines:
    1. Extract all mentions of areas, cities, and states from the query and classify them appropriately:
    - If multiple areas are mentioned, list them all in the "Area" field, separated by commas, and ensure they are enclosed in double quotes as a string.
    - If multiple cities are mentioned, list them all in the "City" field, separated by commas, and ensure they are enclosed in double quotes as a string.
    - If multiple states are mentioned, list them all in the "State" field, separated by commas, and ensure they are enclosed in double quotes as a string.
    2. Use similarity-based matching to identify the nearest location names from the provided lists, considering minor variations, typos, or phonetic similarities.
    3. If a location name identified from the query does not match any entry in the provided lists:
    - Keep the location name as it is and classify it under the most appropriate field ("Area," "City," or "State").
    4. If no identifiable area, city, or state is mentioned, set all fields to "None" as a string (e.g., "None").

    Strict Formatting Rules:
    - Generate the output in a strictly deterministic manner, ensuring identical results for the same input every time.
    - Output the final result strictly in the JSON format described below, ensuring all values are strings enclosed in double quotes:
    {{
        "Area": "<Extracted Areas (comma-separated) or 'None'>",
        "City": "<Extracted Cities (comma-separated) or 'None'>",
        "State": "<Extracted States (comma-separated) or 'None'>"
    }}
    - Do not provide intermediate results, notes, alternative outputs, or any other text. Only provide the final JSON object as described.

    User Query: {query}

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
chat_history = get_chat("chat_history") if get_chat("chat_history") else []

def generate_dynamic_message(chat_history_for_context: List[dict], static_follow_up: str, llm) -> str:
    """
    Generate a dynamic follow-up message using LLM based on the latest context and static follow-up requirement.
    
    Parameters:
        chat_history (List[dict]): The list of conversation history with user and AI messages.
        static_follow_up (str): The static follow-up message to send to the user.
        llm: The language model instance.
    
    Returns:
        str: The dynamically generated follow-up message.
    """
    # Prepare the conversation history context
    recent_history = "\n".join(
        chat_history_for_context
    )  # Limit history to the last 6 messages for brevity
    
    prompt = r"""
    You are an assistant generating contextually appropriate and conversational messages for a user query. 
    Below is the recent conversation history:
    
    {recent_history}
    
    The static follow-up message to send is:
    "{static_follow_up}"
    
    Your task:
    1. Analyze the recent conversation context to ensure the follow-up feels natural and conversational.
    2. If the user's recent messages are off-topic or irrelevant, handle that gracefully and redirect the conversation to focus on the requirement in the static follow-up message.
    3. Ensure the response is concise, professional, and user-friendly.
    
    Generate the final response as a conversational message, incorporating the static follow-up.
    """
    
    # Prepare input to the model
    prompt_template = PromptTemplate(
        input_variables=["recent_history", "static_follow_up"],
        template=prompt
    )
    chain = prompt_template | llm
    message = chain.invoke({
        "recent_history": recent_history,
        "static_follow_up": static_follow_up
    })
    
    # Append AI message to chat history
    chat_history.append(AIMessage(content=f"{message.content.strip()}"))
    # logging.info(f"actual aarray3 {chat_history}")
    save_chat(chat_history)
    return message.content.strip()

def check_user_intent(response: str, follow_up_question: str, llm) -> str:
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
    save_chat(chat_history)

    return classified_intent

def handle_employment_query(
    user_input: str,
    available_areas,
    available_cities,
    available_states,
    city_to_area_mapping: Dict[str, str],
    state_to_city_mapping: Dict[str, str],
    llm
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
    # logging.debug(f"come here with {user_input}")
    result = classify_employment_query(user_input, llm_70b_vers)
    # logging.info(f"REsult {result}")
    user_intention = result["classification_category"]
    # logging.info(f"user_intention {user_intention}")
    chat_history = get_chat("chat_history") if get_chat("chat_history") else []
    # logging.info(f"cached chat_history {chat_history}")
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    # logging.info(f"Chat_history_normal {Chat_history_normal}")
    refined_user_input = refine_query_with_history(Chat_history_normal, user_input)
    # logging.info(f"refined_user_input {refined_user_input}")
    chat_history.append(HumanMessage(content=refined_user_input))  # Log user query
    # logging.info(f"actual aarray1 {chat_history}")
    save_chat(chat_history)
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
                context = f"The data for {area} is not available, but it falls under the city {parent_city}. Ask the user if they want to see data for {parent_city}."
                message = generate_dynamic_message(Chat_history_normal,context, llm)
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

                response = {
                    "Ai_response": "We Found Somthing For Your Query",
                    "Is_confirmation" : None,
                    "Extracted Data": classification_data_to_send,
                    "Validation Data": validated_data_to_send,
                    "User Intention": user_intention
                }
                return response
        
            else:
                response = {
                    "Ai_response": "Not Available",
                    "Is_confirmation" : None,
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
            context = "I am unable to determine the location you are referring to for employment-related information. Could you please provide more specific details in your query?"
            message = generate_dynamic_message(Chat_history_normal,context,llm)
            # logging.info(f"chat history 30 {chat_history}")
            response = {
                "Ai_response": message,
                "Is_confirmation" : None,
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
            context = "I am unable to determine the location you are referring to for employment-related information. Could you please provide more specific details in your query?"
            message = generate_dynamic_message(Chat_history_normal,context,llm)
            response = {
                "Ai_response": message,
                "Is_confirmation" : None,
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
                "Is_confirmation" : None,
                "Extracted Data": classification_data_to_send,
                "Validation Data": validated_data_to_send,
                "User Intention": user_intention
            }
            return response
    else:
        context = "I am unable to understand the exact location or intent related to your query on employment information. Kindly provide the name of a specific city or state, or clarify your request further to assist you better."
        message = generate_dynamic_message(Chat_history_normal,context, llm)
        response = {
                "Ai_response": message,
                "Is_confirmation" : None,
                "Extracted Data": None,
                "Validation Data": None,
                "User Intention": None
            }
        return response
    

def call_handle_employment_query(input):

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

    response = handle_employment_query(input,unique_area_list, unique_city_list, unique_state_list, city_area_mapped_dict, state_city_mapped_dict, llm_70b_vers)

    return response