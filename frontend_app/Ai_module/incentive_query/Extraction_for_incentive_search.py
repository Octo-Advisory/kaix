import re 
import pandas as pd
from typing import List, Dict, Tuple, Union
from click import prompt
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from frontend_app.Ai_module.Query_Classification_And_Analysis import refine_query_with_history, llm_70b_vers,llm_70b_vers_creative,extract_location_from_query,extract_main_industry_and_product_universal,extract_comparison_locations,extract_segment_and_product_universal,extract_sub_sector_and_product_universal
from langchain.schema import HumanMessage, AIMessage
import frappe
from frontend_app.Management_Class.Redis_management.Redis_chat import save_chat,save_state,get_chat,get_state
from datetime import datetime
import json

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
def refine_query_with_history_for_incentive(history, latest_query, llm):
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

    4. Strictly do not infer or carry forward any industry or location from past AI responses unless the user explicitly acknowledges, agrees to, or repeats them in their latest input.  

    5. Strictly do not infer or carry forward any industry or location from past user inputs unless they are explicitly mentioned in the latest user input.  

    6. If the latest user input mentions only one industry or one location, ensure only that industry or location appears in the reformulated query.  
    - Do not include multiple industries or locations unless the user explicitly mentions multiple ones in their latest query.  

    7. Do not add any explanations, reasoning, or justifications in the reformulated standalone query. The output must be a **clean and direct** reformulation of the user’s intent without unnecessary elaboration.  

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

def classify_incentive_query(query, llm):
    """
    Classify the user's incentive search query into the following categories:
    1. Incentive Search for individual area, city, or state.
    2. Comparison between cities, states, or areas.
    3. Comparison between industries or sub-sectors.
    4. Incentive Search for individual industry without location.
    5. Other Intent.

    Args:
        query (str): The user's input query.
        llm: The language model object.

    Returns:
        dict: A dictionary with the raw prompt, classification category, and explanation if needed.
    """
    # Define the category mapping
    category_mapping = {
        1: "Incentive Search for area, city, or state without industry",
        2: "Incentive Search for industry without location",
        3: "Incentive Search for area, city, or state with industry",
        4: "Other Intent",
    }

    # Define the raw prompt string
    raw_prompt = """
    You are an expert in analyzing user queries related to incentive searches. Your task is to classify the user's intention into one of the following categories:

    1. Incentive Search for area, city, or state without industry.
    2. Incentive Search for individual industry without location.
    3. Incentive Search for area, city, or state with industry.
    4. Other Intent.

    Additional Guidelines:
    - If the query is focused on one specific location (e.g., "incentives in Ahmedabad" or "incentives for Gujarat"), classify it as category 1.
    - If the query is specific to one industry but does not reference any location (e.g., "incentives for paracetamol production" or "benefits for textile industry"), classify it as category 2.
    - If the query mentions both a location and an industry (e.g., "incentives for IT in Gujarat" or "manufacturing benefits in Maharashtra"), classify it as category 3.
    - If the query does not clearly fall into the above categories or is unrelated, classify it as category 4.

    Query: {query}

    Output:
    Classify the query into one of the categories (1, 2, 3, or 4). Provide the classification number only.
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
    match = re.search(r"^\s*([1-4])\s*$", response.content.strip())
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

def generate_dynamic_message_for_incentive(chat_history_for_context: List[dict], static_follow_up: str, user_message: str, llm,chatId) -> str:
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
    ) 

    # Define the prompt
    prompt = """
    You are a highly skilled assistant specializing in creating professional, engaging, and contextually relevant messages.
    Your goal is to craft a polished follow-up message that seamlessly incorporates the provided static follow-up message while aligning with the tone and context of the recent conversation.

    ---

    Key Instructions

    1. Strict Focus on Incentive-Related Queries  
    - Only include incentive-related details in the follow-up message, even if the user query mentions multiple topics.  
    - If the user mentions employment, approvals, vendors, or any other unrelated terms, completely exclude them from the response.  
    - Regardless of any other mentioned topics, incentive-related words should always appear in the response.  

    Example Correction:  
    - User Query: "I want to search for incentives and employment."  
    - Wrong Response: "I can assist with incentives and employment-related searches."  
    - Correct Response: "Could you specify the industry or location for which you're looking for incentives?"  

    2. Strict Industry & Location Handling  
    - Do NOT infer, assume, or use any Industry (Industry, Sub-Sector, Product) or location (Area, City, State) from the user’s message or conversation history.  
    - Only include these details if they are explicitly mentioned in the static follow-up message.  
    - If no industry or location is provided in the static follow-up, do NOT include one in the generated response.  

    3. Handling Placeholders Like "None" or "Not Available in List"  
    - If the static message contains placeholders such as `"None"` or `"Not Available in List"`, ignore these terms completely.  
    - NEVER include them in the response.  

    4. Handling Off-Topic Queries  
    - If the user’s query is **completely unrelated to incentives**, politely inform them:  
    - "I specialize in assisting with incentive-related queries for industries and locations."  
    - However, **DO NOT include this statement if the user query is partially relevant to incentives** or if incentives are mentioned alongside other topics.  
    - Instead, generate a relevant response by **only focusing on the incentive-related part of the query** while ignoring unrelated topics.  
    - DO NOT attempt to answer fully off-topic queries. Instead, smoothly transition to the static follow-up message.

    Example Correction:  
    - User Query: "Tell me about tourism in Paris."  
    - Correct Response: "I specialize in assisting with incentive-related queries for industries and locations."  
    - User Query: "I want to search for incentives and vendors."  
    - Correct Response: "Could you specify the industry or location for which you're looking for incentives?" (Vendor mention ignored)  

    5. Handling Missing Information  
    - If only industry-related details (Industry, Sub-Sector, or Product) are missing, politely ask the user to provide them.  
    - If only location details (Area, City, or State) are missing, politely ask the user for the location.  
    - If both industry and location details are missing, request both in a natural and concise manner.  
    - Ensure the request for missing details is seamlessly connected to the static follow-up message.  

    6. Ensuring Smooth Transitions with Proper Conjunctions  
    - Analyze the static follow-up message before adding conjunctions.  
    - If the message already has a natural transition, do not add unnecessary conjunctions.  
    - If the static message consists of two distinct parts (acknowledgment + request for details), use a conjunction where appropriate, such as:  
    - "Additionally, Furthermore, To proceed further, To assist you better, On another note, As a next step, In addition, Also"  

    7. Natural and Engaging Tone  
    - The response should feel like a smooth continuation of the conversation without sounding mechanical or scripted.  
    - Avoid robotic acknowledgments or unnecessary phrases such as:  
    - "I wanted to follow up on..."  
    - "I am here to assist with..."  
    - "It seems you are asking about..."  

    8. Handling Greetings  
    - If the user greets (e.g., "Hi", "Hello", "Good morning"), respond with an appropriate greeting.  
    - Ensure the transition to the follow-up message is smooth and natural using proper conjunctions.  

    9. Handling Special Events  
    - If the user mentions a special occasion (e.g., birthday, anniversary), acknowledge and celebrate it first.  
    - Then, transition smoothly into the static follow-up message using proper conjunctions.  

    10. Handling Negative Emotions  
    - If the user expresses sadness, frustration, or anger, address their emotions with empathy first.  
    - Then, transition seamlessly into the static follow-up message using a natural, logical flow.  

    11. Ensuring Conciseness (Maximum 3 Lines)  
    - The response must be concise—a maximum of 3 lines while fully incorporating the static follow-up message.  
    - Ensure the message is professional, user-friendly, and free of unnecessary elaboration or additional context.  

    ---

    Inputs  
    1. User’s Latest Message  
    - This is the most recent message from the user. Use this to determine the appropriate tone, greetings, or redirection.  
    - {user_message}  

    2. Recent Conversation History  
    - This contains past exchanges between the user and the assistant.  
    - Chat history is only for reference. Do NOT infer, assume, or use any details about industry or location unless explicitly mentioned in the static follow-up message.  
    - {recent_history}  

    3. Static Follow-Up Message  
    - This is the reference message containing the key details to be included in the final response.  
    - Your task is to reword and refine this message into a polished, professional, and conversational follow-up.  
    - Static Message: "{static_follow_up}"  

    ---

    Final Output Requirements  
    - Do NOT copy the static follow-up message word-for-word.  
    - Do NOT include placeholders like `"None"` or `"Not Available in List"`.  
    - Do NOT infer or use industry/location details unless explicitly mentioned in the static follow-up message.  
    - Do NOT answer off-topic queries—redirect them properly.  
    - Only use "I specialize in assisting with incentive-related queries" if the query is truly off-topic.  
    - If the query mentions incentives but also includes unrelated topics, ignore the unrelated topics and **only focus on incentives** in the response.  
    - Craft a clear, polished response that aligns with the user’s latest message.  
    - Ensure a smooth and engaging conversational flow with proper conjunctions.  
    - Keep the response concise (maximum 3 lines).  
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
    chat_history = get_chat(f"QINC_chat_{chatId}") or []
    chat_history.append(AIMessage(content=f"{message.content.strip()}"))
    save_chat(chat_history,f"QINC_chat_{chatId}")
    return message.content.strip()

# Get available area, city, state
def get_available_area_city_state():
    query = """
    select acmapped.area_name, acmapped.city_name, st.state_name
    from (
        select at.name as a_id, at.area_name, ct.name as c_id, ct.city_name, ct.state
        from `tabArea` as at
        join `tabCity` as ct
        on at.city_id = ct.name
    ) as acmapped
    join `tabState` as st
    on acmapped.state = st.name
    """

    result_of_query = fetch_query_results(query)

    # Create a DataFrame from the result
    columns = ["area_name", "city_name", "state_name"]
    df_area_for_incentive_extraction = pd.DataFrame(result_of_query, columns=columns)
    df_area_for_incentive_extraction = df_area_for_incentive_extraction.drop_duplicates()

    city_area_mapped_dict =  df_area_for_incentive_extraction.groupby("city_name")["area_name"].apply(list).to_dict()
    state_city_mapped_dict =  df_area_for_incentive_extraction.groupby("state_name")["city_name"].apply(lambda x: list(x.unique())).to_dict()

    unique_area_list = list(df_area_for_incentive_extraction.area_name.unique())

    unique_city_list = list(df_area_for_incentive_extraction.city_name.unique())

    unique_state_list = list(df_area_for_incentive_extraction.state_name.unique())

    return unique_area_list,unique_city_list,unique_state_list,city_area_mapped_dict,state_city_mapped_dict

# Entry point of Incentive search
def call_incentive_search(input,chatId):
    log_to_file("----","--------------")
    chat_history = get_chat(f"QINC_chat_{chatId}") or []
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    refine_user_input = refine_query_with_history_for_incentive(Chat_history_normal,input,llm_70b_vers)
    chat_history.append(HumanMessage(content=refine_user_input))
    save_chat(chat_history,f"QINC_chat_{chatId}")
    state = get_state(f"QINC_state_{chatId}") or None
    if not state:
        state = {'Area':'None','City':'None','State':'None','Product':'None','Main-Industry':'None','Sub-Sector':'None'}
        save_state(state,f"QINC_state_{chatId}")
    log_to_file("state1",state)
    query_intent = classify_incentive_query(refine_user_input,llm=llm_70b_vers)
    query_intent = query_intent['classification_category']
    log_to_file("query intent",query_intent)
    if query_intent == 'Other Intent':
        static_follow_up = "Could you provide specific query?"
        message = generate_dynamic_message_for_incentive(Chat_history_normal,static_follow_up,refine_user_input,llm_70b_vers_creative,chatId)
        response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "State" : state
                }
        return response
    else:
        area_list, city_list, state_list, city_area_mapped_dict, state_city_mapped_dict = get_available_area_city_state()
        final_json = get_json_for_industry()
        main_industries = get_main_industry(final_json)
        location_follow_up = get_location_from_query(refine_user_input,area_list,city_list,state_list,city_area_mapped_dict, state_city_mapped_dict,state,llm_70b_vers,chatId)
        log_to_file("location_follow_up",location_follow_up)
        main_industry_extracted_data,main_industry_validated_data = extract_main_industry_and_product_universal(refine_user_input,main_industries,llm_70b_vers)
        log_to_file("main_industry_validated_data",main_industry_validated_data)
        if main_industry_validated_data['Main-Industry'] != "None":
            if state['Main-Industry'] != main_industry_validated_data['Main-Industry'] or state['Product'] != main_industry_validated_data['Product']:
                state['Main-Industry'] = main_industry_validated_data['Main-Industry'] 
                state['Product'] = main_industry_validated_data['Product']
                save_state(state,f"QINC_state_{chatId}")
            sub_sectors = get_sub_sectors(final_json,state['Main-Industry'])
            sub_sector_extracted_Data,sub_sector_validated_Data = extract_sub_sector_and_product_universal(refine_user_input,sub_sectors,llm_70b_vers,state['Main-Industry'],state['Product'])
            log_to_file("sub_sector_validated_Data",sub_sector_validated_Data)
            state['Sub-Sector'] = sub_sector_validated_Data['Sub-Sector']
            state['Product'] = sub_sector_validated_Data["Product"]
            save_state(state,f"QINC_state_{chatId}")
            if state['Sub-Sector'] == 'None':
                static_follow_up = "Could you share more specific details about the product you're interested in?"
                if location_follow_up != 'None':
                    static_follow_up = f"{location_follow_up} Could you share more specific details about the product you're interested in?"
                message = generate_dynamic_message_for_incentive(Chat_history_normal,static_follow_up,refine_user_input,llm_70b_vers_creative,chatId)
                response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "State" : state
                    }
                return response
            else:
                if location_follow_up == 'None':
                    message = "we have found something for you"
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : True,
                        "State" : state
                    }
                    return response
                else:
                    message = generate_dynamic_message_for_incentive(Chat_history_normal,location_follow_up,refine_user_input,llm_70b_vers_creative,chatId)
                    response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "State" : state
                        }
                    return response
             
        else:
            static_follow_up = "Could you share more specific details about the product you're interested in?"
            if location_follow_up != 'None':
                static_follow_up = f"{location_follow_up} Could you share more specific details about the product you're interested in?"
            message = generate_dynamic_message_for_incentive(Chat_history_normal,static_follow_up,refine_user_input,llm_70b_vers_creative,chatId)
            response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "State" : state
                }
            return response

def get_json_for_industry():
    final_json = {}
    query = """
            SELECT sgt.segment, indmappedsst.sub_sector_name, indmappedsst.industry_name
            FROM `tabSegment` AS sgt
            JOIN (
                SELECT sst.name, sst.sub_sector_name, indt.industry_name
                FROM `tabSub Sector` AS sst
                JOIN `tabIndustry` AS indt
                WHERE sst.industry_id = indt.name
            ) AS indmappedsst
            WHERE sgt.sub_sector = indmappedsst.name
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

def get_sub_sectors(final_json,main_industry):
    """Returns a list of sub-sectors for a given main industry."""
    return  list(final_json.get(main_industry, {}).keys())

def get_location_from_query(user_query,area_list,city_list,state_list,city_area_mapped_dict, state_city_mapped_dict,state,llm,chatId):   
    loc_extracted_data,loc_validated_data = extract_location_from_query(user_query,area_list,city_list,state_list,llm)
    log_to_file("loc_validated_data",loc_validated_data)
    if loc_validated_data["Area"] != 'None' or loc_validated_data["City"] != 'None' or loc_validated_data["State"] != 'None':
        state["Area"] = loc_validated_data["Area"] 
        state['City'] = loc_validated_data["City"]
        state['State'] = loc_validated_data["State"]
        save_state(state,f"QINC_state_{chatId}")
        if state["Area"] != 'Not Available in List' and state["Area"] != 'None' :
            parent_city = next((key for key, value in city_area_mapped_dict.items() if state["Area"] in value), None)
            parent_state = next((key for key, value in state_city_mapped_dict.items() if parent_city in value), None)
            log_to_file("parent_city",parent_city)
            log_to_file("parent_state1",parent_state)
            state['City'] = parent_city
            state['State'] = parent_state
        if state['City'] != 'Not Available in List' and state["City"] != 'None' :
            parent_state = next((key for key, value in state_city_mapped_dict.items() if state["City"] in value), None)
            log_to_file("parent_state2",parent_state)
            state['State'] = parent_state
        save_state(state,f"QINC_state_{chatId}")
        if state['Area'] == state['City'] == state['State'] == "Not Available in List":
            return "Could you provide the area, city, or state? This will help me give you better details."
        if state['Area'] == 'None' and state['City'] == 'None':
            if state['State'] != 'None':
                return "Got the state! Could you specify the city or area for more details?"
            else:
                return "Could you provide the area, city, or state? This will help me give you better details."
        else:
            return 'None'
    else:
        if state['Area'] == state['City'] == state['State'] == 'None':
            return "Could you provide the area, city, or state? This will help me give you better details."
        else:
            return 'None'
        
def log_to_file(key,value):
    """
    Logs key-value data to a file with a timestamp.
    
    :param filename: Name of the log file.
    :param data: Key-value pairs to log.
    """
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f"{key}" : value
    }
    
    with open("log2.txt", "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")