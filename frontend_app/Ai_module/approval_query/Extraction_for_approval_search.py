import re
import pandas as pd
from typing import List, Dict, Tuple, Union, Any, Optional
from click import prompt
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from frontend_app.Ai_module.Query_Classification_And_Analysis import *
from langchain.schema import HumanMessage, AIMessage
import frappe
from frontend_app.Management_Class.Redis_management.Redis_chat import get_chat,save_chat,get_state,save_state
from frontend_app.Management_Class.helpers.utility import update_llm_token

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

# Define a function to refine the query using history for approval search
def refine_query_with_history_for_approval(history, latest_query, llm):
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
    update_llm_token(refined_query)
    refined_text = refined_query.content.strip()
    
    # Extract the reformulated standalone query
    match = re.search(r'reformulated standalone query:\s*(?:"(.*?)"|\'(.*?)\'|(.*))$', refined_text, re.IGNORECASE)
    if match:
        # Return the captured group that is not None
        return next(group for group in match.groups() if group)
    
    # Fallback to the entire response if no match is found
    return refined_text

def classify_approval_query(query, llm):
    """
    Classify the user's approval search query into the following categories:
    1. Approval Search for area, city, or state without industry.
    2. Approval Search for individual industry without location.
    3. Approval Search for area, city, or state with industry.
    4. Other Intent.

    Args:
        query (str): The user's input query.
        llm: The language model object.

    Returns:
        dict: A dictionary with the raw prompt, classification category, and explanation if needed.
    """
    # Define the category mapping
    category_mapping = {
        1: "Approval Search for area, city, or state without industry",
        2: "Approval Search for industry without location",
        3: "Approval Search for area, city, or state with industry",
        4: "Other Intent",
    }

    # Define the raw prompt string
    raw_prompt = """
    You are an expert in analyzing user queries related to approval searches. Your task is to classify the user's intention into one of the following categories:

    1. Approval Search for area, city, or state without industry.
    2. Approval Search for individual industry without location.
    3. Approval Search for area, city, or state with industry.
    4. Other Intent.

    Additional Guidelines:
    - If the query is focused on one specific location (e.g., "approvals in Ahmedabad" or "approvals for Gujarat"), classify it as category 1.
    - If the query is specific to one industry but does not reference any location (e.g., "approvals for paracetamol production" or "clearances for textile industry"), classify it as category 2.
    - If the query mentions both a location and an industry (e.g., "approvals for IT in Gujarat" or "manufacturing permits in Maharashtra"), classify it as category 3.
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
    update_llm_token(response)

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

def generate_dynamic_message_for_approval(chat_history_for_context: List[dict], static_follow_up: str, user_message: str, llm) -> str:
    """
    Generate a dynamic follow-up message using LLM based on the latest context and static follow-up requirement for approval-related queries.
    
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

    ---

    Key Instructions

    1. Strict Focus on Approval-Related Queries  
    - Only include approval-related details in the follow-up message, even if the user query mentions multiple topics.  
    - If the user mentions incentives, employment, vendors, or any other unrelated terms, completely exclude them from the response.  
    - Regardless of any other mentioned topics, approval-related words must always appear in the response.  

    Example Correction:  
    - User Query: "I want to search for approvals and incentives."  
    - Wrong Response: "I can assist with approvals and incentive-related searches."  
    - Correct Response: "Could you specify the industry or location for which you're looking for approvals?"  

    2. Strict Industry & Location Handling  
    - Do NOT infer, assume, or use any Industry (Industry, Sub-Sector, Product) or location (Area, City, State) from the user’s message or conversation history.  
    - Only include these details if they are explicitly mentioned in the static follow-up message.  
    - If no industry or location is provided in the static follow-up, do NOT include one in the generated response.  

    3. Handling Placeholders Like "None" or "Not Available in List"  
    - If the static message contains placeholders such as "None" or "Not Available in List", ignore these terms completely.  
    - NEVER include them in the response.  

    4. Handling Off-Topic Queries  
    - If the user’s query is completely unrelated to approvals, politely inform them:  
    - "I specialize in assisting with approval-related queries for industries and locations."  
    - However, DO NOT include this statement if the user query is partially relevant to approvals or if approvals are mentioned alongside other topics.  
    - Instead, generate a relevant response by only focusing on the approval-related part of the query while ignoring unrelated topics.  
    - DO NOT attempt to answer fully off-topic queries. Instead, smoothly transition to the static follow-up message.

    Example Correction:  
    - User Query: "Tell me about tourism in Paris."  
    - Correct Response: "I specialize in assisting with approval-related queries for industries and locations."  
    - User Query: "I want to search for approvals and employment."  
    - Correct Response: "Could you specify the industry or location for which you're looking for approvals?" (Employment mention ignored)  

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
    - Do NOT include placeholders like "None" or "Not Available in List".  
    - Do NOT infer or use industry/location details unless explicitly mentioned in the static follow-up message.  
    - Do NOT answer off-topic queries—redirect them properly.  
    - Only use "I specialize in assisting with approval-related queries" if the query is truly off-topic.  
    - If the query mentions approvals but also includes unrelated topics, ignore the unrelated topics and only focus on approvals in the response.  
    - Craft a clear, polished response that aligns with the user’s latest message.  
    - Ensure a smooth and engaging conversational flow with proper conjunctions.  
    - Keep the response concise (maximum 3 lines).  
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

    return message.content.strip()

def get_static_follow_up_for_approval(approval_state: Dict[str, Dict[str, Optional[str]]], user_intention: str) -> str:
    """
    Generates a structured static follow-up message based on the user's approval query intent and provided details.

    This function determines the missing and provided details from the approval state and generates a natural and 
    engaging follow-up message accordingly.

    Parameters:
    -----------
    approval_state : Dict[str, Dict[str, Optional[str]]]
        A dictionary maintaining extracted user-provided details, categorized into:
        - "Location_info": Contains "Area", "City", and "State" (can be None if missing).
        - "Industry_info": Contains "Main-Industry", "Sub-Sector", and "Product" (can be None if missing).
        
    user_intention : str
        The classified intent of the user's query, which can be one of the following:
        - "Approval Search for area, city, or state without industry"
        - "Approval Search for industry without location"
        - "Approval Search for area, city, or state with industry"
        - "Other Intent"

    Returns:
    --------
    str
        A structured follow-up message requesting the missing information while acknowledging the provided details.
    """

    if user_intention == "Approval Search for area, city, or state without industry":
            # Extract existing details
        location_info = approval_state.get("Location_info", {})
        industry_info = approval_state.get("Industry_info", {})

        # Check if all details are missing
        all_location_missing = all(value is None for value in location_info.values())
        all_industry_missing = all(value is None for key, value in industry_info.items() if key != "Product")

        # Store provided and missing details
        provided_details = []
        missing_details = []

        # Location handling logic
        if not all_location_missing:
            if location_info["Area"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['Area']}, {location_info['City']}.")
            elif location_info["City"] is not None and location_info["State"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['City']}, {location_info['State']}.")
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] < 2:
                return (
                    f"""{location_info["State"]} has many cities and areas, and approval details can vary based on location. Could you please share the specific city or area within {location_info["State"]}? This will help us provide you with the most accurate information."""
                )
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] >= 2:
                provided_details.append(f"You're looking for approvals in {location_info['State']}.")

        # Industry handling logic
        if not all_industry_missing:
            if industry_info["Main-Industry"] is not None and industry_info["Sub-Sector"] is not None:
                if industry_info["Product"] is None:
                    provided_details.append(f"You're looking approvals for {industry_info['Sub-Sector']} sector under {industry_info['Main-Industry']}.")
                else:
                    provided_details.append(f"You're looking approvals for {industry_info['Product']} product.")
            elif industry_info["Main-Industry"] is not None:
                if industry_info["Product"] is None:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Main-Industry"]}. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )
                else:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Product"]} product. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )

        # Identifying missing details
        if all_location_missing:
            missing_details.append("Also, could you share the location (area or city) you're looking for approvals in?")
        if all_industry_missing:
            missing_details.append("Also, let me know which product or industry you're seeking approvals for.")

        # Construct the follow-up message with proper conjunctions
        if not provided_details:
            # Case 1: No details provided at all
            return (
                "To assist you better, could you share the location (area or city) and the product or industry you're looking for approvals in?"
            )

        else:
            # Case 2: Some details provided, acknowledge them naturally and ask for missing ones with smooth transitions
            message = " ".join(provided_details)

            if missing_details:
                if len(missing_details) == 2:
                    message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
                else:
                    message += f" But {missing_details[0]}"

            return message
        
    elif user_intention == "Approval Search for industry without location":
            # Extract existing details
        location_info = approval_state.get("Location_info", {})
        industry_info = approval_state.get("Industry_info", {})

        # Check if all details are missing
        all_location_missing = all(value is None for value in location_info.values())
        all_industry_missing = all(value is None for key, value in industry_info.items() if key != "Product")

        # Store provided and missing details
        provided_details = []
        missing_details = []

        # Industry handling logic
        if not all_industry_missing:
            if industry_info["Main-Industry"] is not None and industry_info["Sub-Sector"] is not None:
                if industry_info["Product"] is None:
                    provided_details.append(f"You're looking approvals for {industry_info['Sub-Sector']} sector under {industry_info['Main-Industry']}.")
                else:
                    provided_details.append(f"You're looking approvals for {industry_info['Product']} product.")
            elif industry_info["Main-Industry"] is not None:
                if industry_info["Product"] is None:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Main-Industry"]}. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )
                else:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Product"]} product. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )
        # Location handling logic
        if not all_location_missing:
            if location_info["Area"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['Area']}, {location_info['City']}.")
            elif location_info["City"] is not None and location_info["State"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['City']}, {location_info['State']}.")
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] < 2:
                return (
                    f"""{location_info["State"]} has many cities and areas, and approval details can vary based on location. Could you please share the specific city or area within {location_info["State"]}? This will help us provide you with the most accurate information."""
                )
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] >= 2:
                provided_details.append(f"You're looking for approvals in {location_info['State']}.")


        # Identifying missing details
        if all_location_missing:
            missing_details.append("Also, could you share the location (area or city) you're looking for approvals in?")
        if all_industry_missing:
            missing_details.append("Also, let me know which product or industry you're seeking approvals for.")

        # Construct the follow-up message with proper conjunctions
        if not provided_details:
            # Case 1: No details provided at all
            return (
                "To assist you better, could you share the location (area or city) and the product or industry you're looking for approvals in?"
            )

        else:
            # Case 2: Some details provided, acknowledge them naturally and ask for missing ones with smooth transitions
            message = " ".join(provided_details)

            if missing_details:
                if len(missing_details) == 2:
                    message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
                else:
                    message += f" But {missing_details[0]}"

            return message
    
    elif user_intention == "Approval Search for area, city, or state with industry":
        # Extract existing details
        location_info = approval_state.get("Location_info", {})
        industry_info = approval_state.get("Industry_info", {})

        # Check if all details are missing
        all_location_missing = all(value is None for value in location_info.values())
        all_industry_missing = all(value is None for key, value in industry_info.items() if key != "Product")
        
        # Store provided and missing details
        provided_details = []
        missing_details = []

        # Location handling logic
        if not all_location_missing:
            if location_info["Area"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['Area']}, {location_info['City']}.")
            elif location_info["City"] is not None and location_info["State"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['City']}, {location_info['State']}.")
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] < 2:
                return (
                    f"""{location_info["State"]} has many cities and areas, and approval details can vary based on location. Could you please share the specific city or area within {location_info["State"]}? This will help us provide you with the most accurate information."""
                )
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] >= 2:
                provided_details.append(f"You're looking for approvals in {location_info['State']}.")

        # Industry handling logic
        if not all_industry_missing:
            if industry_info["Main-Industry"] is not None and industry_info["Sub-Sector"] is not None:
                if industry_info["Product"] is None:
                    provided_details.append(f"You're looking approvals for {industry_info['Sub-Sector']} sector under {industry_info['Main-Industry']}.")
                else:
                    provided_details.append(f"You're looking approvals for {industry_info['Product']} product.")
            elif industry_info["Main-Industry"] is not None:
                if industry_info["Product"] is None:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Main-Industry"]}. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )
                else:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Product"]} product. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )

        # Identifying missing details
        if all_location_missing:
            missing_details.append("Also, could you share the location (area or city) you're looking for approvals in?")
        if all_industry_missing:
            missing_details.append("Also, let me know which product or industry you're seeking approvals for.")

        # Construct the follow-up message with proper conjunctions
        if not provided_details:
            # Case 1: No details provided at all
            return (
                "To assist you better, could you share the location (area or city) and the product or industry you're looking for approvals in?"
            )

        else:
            # Case 2: Some details provided, acknowledge them naturally and ask for missing ones with smooth transitions
            message = " ".join(provided_details)

            if missing_details:
                if len(missing_details) == 2:
                    message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
                else:
                    message += f" But {missing_details[0]}"

            return message
    
    else:
        # Extract existing details
        location_info = approval_state.get("Location_info", {})
        industry_info = approval_state.get("Industry_info", {})

        # Check if all details are missing
        all_location_missing = all(value is None for value in location_info.values())
        all_industry_missing = all(value is None for key, value in industry_info.items() if key != "Product")

        # Store provided and missing details
        provided_details = []
        missing_details = []

        # Location handling logic
        if not all_location_missing:
            if location_info["Area"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['Area']}, {location_info['City']}.")
            elif location_info["City"] is not None and location_info["State"] is not None:
                provided_details.append(f"You're looking for approvals in {location_info['City']}, {location_info['State']}.")
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] < 2:
                return (
                    f"""{location_info["State"]} has many cities and areas, and approval details can vary based on location. Could you please share the specific city or area within {location_info["State"]}? This will help us provide you with the most accurate information."""
                )
            elif location_info["State"] is not None and location_info["Area"] is None and location_info["City"] is None and approval_state["Only_State_Attempt_Count"] >= 2:
                provided_details.append(f"You're looking for approvals in {location_info['State']}.")

        # Industry handling logic
        if not all_industry_missing:
            if industry_info["Main-Industry"] is not None and industry_info["Sub-Sector"] is not None:
                if industry_info["Product"] is None:
                    provided_details.append(f"You're looking approvals for {industry_info['Sub-Sector']} sector under {industry_info['Main-Industry']}.")
                else:
                    provided_details.append(f"You're looking approvals for {industry_info['Product']} products.")
            elif industry_info["Main-Industry"] is not None:
                if industry_info["Product"] is None:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Main-Industry"]}. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )
                else:
                    return (
                        f"""We see that you're looking approvals for {industry_info["Product"]} product. To provide the most accurate information about approvals, could you share a bit more about what specifically you’re looking for or any key details related to your requirement?"""
                    )
                    

        # Identifying missing details
        if all_location_missing:
            missing_details.append("Also, could you share the location (area or city) you're looking for approvals in?")
        if all_industry_missing:
            missing_details.append("Also, let me know which product or industry you're seeking approvals for.")

        # Construct the follow-up message with proper conjunctions
        if not provided_details:
            # Case 1: No details provided at all
            return (
                "To assist you better, could you share the location (area or city) and the product or industry you're looking for approvals in?"
            )

        else:
            # Case 2: Some details provided, acknowledge them naturally and ask for missing ones with smooth transitions
            message = " ".join(provided_details)

            if missing_details:
                if len(missing_details) == 2:
                    message += f" However, I still need more details. {missing_details[0]} {missing_details[1]}"
                else:
                    message += f" But {missing_details[0]}"

            return message

def handle_approval_query(
    user_input: str,
    available_areas: List[str],
    available_cities: List[str],
    available_states: List[str],
    main_industry_to_subsector_mapped_dict: Dict[str, List[str]],
    city_to_area_mapping: Dict[str, str],
    state_to_city_mapping: Dict[str, List[str]],
    extracted_state: Dict[str, Dict[str, Any]],
    state: Dict[str, Dict[str, Any]],
    llm,
    chatId
) -> Union[Dict[str, Any], str]:
    """
    Processes user queries related to approval searches by extracting location 
    and industry-related details, classifying user intent, and generating an 
    appropriate response.

    Parameters:
    -----------
    user_input (str): 
        The raw query input from the user regarding approval search.

    available_areas (List[str]): 
        A predefined list of areas that are eligible for approval searches.

    available_cities (List[str]): 
        A predefined list of cities that are eligible for approval searches.

    available_states (List[str]): 
        A predefined list of states that are eligible for approval searches.

    main_industry_to_subsector_mapped_dict (Dict[str, List[str]]): 
        A mapping dictionary that links each main industry to its corresponding sub-sectors.

    city_to_area_mapping (Dict[str, str]): 
        A dictionary mapping cities to their corresponding areas.

    state_to_city_mapping (Dict[str, List[str]]): 
        A dictionary mapping states to their corresponding cities.

    extracted_state (Dict[str, Dict[str, Any]]): 
        A dictionary storing the extracted details from the user query, such as identified locations and industries.

    state (Dict[str, Dict[str, Any]]): 
        A dictionary storing the validated and structured details for approval searches.

    llm:
        The language model instance used for processing and refining user queries.

    Returns:
    --------
    Union[Dict[str, Any], str]:
        - If the query is successfully processed, returns a structured dictionary with:
            - "Ai_response": AI-generated response message.
            - "Is_confirmation": Indicator if confirmation is needed.
            - "Extracted Data": The extracted details from the query.
            - "Validation Data": The validated and structured state.
            - "User Intention": The identified classification of the user’s query.
        
        - If the query does not match any known classification or lacks sufficient 
          information, returns a string containing the dynamically generated response 
          prompting the user for more details.
    """

    chat_history = get_chat(f"chat_{chatId}") or []
    
    if (state["Location_info"]["Area"] is not None or state["Location_info"]["City"] is not None) or (state["Only_State_Attempt_Count"] >= 2):
        perfect_location_data = True
    else:
        perfect_location_data = False
    if state["Industry_info"]["Main-Industry"] is not None and state["Industry_info"]["Sub-Sector"] is not None:
        perfect_industry_data = True
    else:
        perfect_industry_data = False
    
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
    
    refined_user_input = refine_query_with_history_for_approval(Chat_history_normal, user_input, llm)
    chat_history.append(HumanMessage(content=refined_user_input))  # Log user query
    save_chat(chat_history,f"chat_{chatId}")

    result = classify_approval_query(refined_user_input, llm)
    user_intention = result["classification_category"]
    keyword_dict = extract_keywords_from_query(refined_user_input, field_with_description["Query to Get Approvals"], module_names_list, llm, "Query to Get Approvals")
    state["KEYWORDS"] = keyword_dict["KEYWORDS"]
    save_state(state,f"QAPP_state_{chatId}")

    if user_intention == "Approval Search for area, city, or state without industry":
        extracted_data, validated_data = extract_location_from_query(refined_user_input, available_areas, available_cities, available_states, llm)
        area_name = validated_data["Area"]
        city_name = validated_data["City"]
        state_name = validated_data["State"]

        extracted_state["Location_info"] = extracted_data

        if area_name != "Not Available in List":
            if area_name != "None":
                parent_city = next((key for key, value in city_to_area_mapping.items() if area_name in value), None)
                parent_state = next((key for key, value in state_to_city_mapping.items() if parent_city in value), None)
                state["Location_info"]["Area"] = area_name
                state["Location_info"]["City"] = parent_city
                state["Location_info"]["State"] = parent_state
                save_state(state,f"QAPP_state_{chatId}")

            elif city_name != "None":
                parent_state = next((key for key, value in state_to_city_mapping.items() if city_name in value), None)
                state["Location_info"]["Area"] = None
                state["Location_info"]["City"] = city_name
                state["Location_info"]["State"] = parent_state
                save_state(state,f"QAPP_state_{chatId}")

            elif state_name != "None":
                state["Location_info"]["Area"] = None
                state["Location_info"]["City"] = None
                state["Location_info"]["State"] = state_name
                state["Only_State_Attempt_Count"] += 1
                save_state(state,f"QAPP_state_{chatId}")

            else:
                state["Location_info"]["Area"] = None
                state["Location_info"]["City"] = None
                state["Location_info"]["State"] = None
                save_state(state,f"QAPP_state_{chatId}")
            
            if (state["Location_info"]["Area"] is not None or state["Location_info"]["City"] is not None) or (state["Only_State_Attempt_Count"] >= 2):
                perfect_location_data = True
            else:
                perfect_location_data = False
            
            if perfect_industry_data and perfect_location_data:
                if state["Industry_info"]["Main-Industry"] != "Not Available in list" and state["Industry_info"]["Sub-Sector"] != "Not Available in list":
                    selected_option = next(
                    (state.get("Industry_info").get(key) for key in ['Product', 'Sub-Sector', 'Main-Industry'] if state.get("Industry_info").get(key) not in [None, 'None']),
                    ''
                    )
                    message = f"We have identified, you are looking for approvals related to {selected_option} production in {state.get("Location_info").get('Area')} under the city {state.get("Location_info").get("City")} in {state.get("Location_info").get("State")}. Is this information correct?"
                    dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)
                    chat_history.append(AIMessage(content=dynamic_confirmation_message))  # Log user query
                    save_chat(chat_history,f"chat_{chatId}")
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : True,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention
                    }
                    return response
                else:
                    message = "Not Available In List"
                    chat_history.append(AIMessage(content=message))  # Log user query
                    save_chat(chat_history,f"chat_{chatId}")
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention
                    }
                    return response
            else:
                response_static_message = get_static_follow_up_for_approval(state, user_intention)
                message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
        
        else:
            state["Location_info"]["Area"] = "Not Available in List"
            state["Location_info"]["City"] = "Not Available in List"
            state["Location_info"]["State"] = "Not Available in List"
            save_state(state,f"QAPP_state_{chatId}")
            if perfect_industry_data:
                message = "Not Available In List"
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": "Not Available In List",
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
            else:
                response_static_message = get_static_follow_up_for_approval(state, user_intention)
                message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response

    elif user_intention == "Approval Search for industry without location":
        main_industry_list = list(main_industry_to_subsector_mapped_dict.keys())
        extracted_data, validated_data = extract_main_industry_and_product_universal(refined_user_input, main_industry_list, llm)
        main_industry_name = validated_data["Main-Industry"]
        product_name = validated_data["Product"]
        extracted_state["Industry_info"]["Main-Industry"] = extracted_data["Main-Industry"]
        extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
        if main_industry_name != "Not Available in list":
            if main_industry_name != "None":
                state["Industry_info"]["Main-Industry"] = main_industry_name
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                sub_sector_list = list(main_industry_to_subsector_mapped_dict[main_industry_name].keys())
                extracted_data, validated_data = extract_sub_sector_and_product_universal(refined_user_input, sub_sector_list, llm, main_industry_name, product_name)
                sub_sector_name = validated_data["Sub-Sector"]
                product_name = validated_data["Product"]
                extracted_state["Industry_info"]["Sub-Sector"] = extracted_data["Sub-Sector"]
                extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
                if sub_sector_name != "Not Available in list":
                    if sub_sector_name != "None":
                        state["Industry_info"]["Sub-Sector"] = sub_sector_name
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QAPP_state_{chatId}")
                    else:
                        state["Industry_info"]["Sub-Sector"] = None
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QAPP_state_{chatId}")
                    
                    if state["Industry_info"]["Main-Industry"] is not None and state["Industry_info"]["Sub-Sector"] is not None:
                        perfect_industry_data = True
                    else:
                        perfect_industry_data = False
                    
                    if perfect_industry_data and perfect_location_data:
                        if state["Location_info"]["Area"] != "Not Available in List" or state["Location_info"]["City"] != "Not Available in List":
                            selected_option = next(
                            (state.get("Industry_info").get(key) for key in ['Product', 'Sub-Sector', 'Main-Industry'] if state.get("Industry_info").get(key) not in [None, 'None']),
                            ''
                            )
                            message = f"We have identified, you are looking for approvals related to {selected_option} production in {state.get("Location_info").get('Area')} under the city {state.get("Location_info").get("City")} in {state.get("Location_info").get("State")}. Is this information correct?"
                            dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)
                            chat_history.append(AIMessage(content=dynamic_confirmation_message))  # Log user query
                            save_chat(chat_history,f"chat_{chatId}")
                            response = {
                                "Ai_response": dynamic_confirmation_message,
                                "Is_confirmation" : True,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention
                            }
                            return response
                        else:
                            message = "Not Available In List"
                            chat_history.append(AIMessage(content=message))  # Log user query
                            save_chat(chat_history,f"chat_{chatId}")
                            response = {
                                "Ai_response": message,
                                "Is_confirmation" : None,
                                "Extracted Data": extracted_state,
                                "Validation Data": state,
                                "User Intention": user_intention
                            }
                            return response
                    else:
                        response_static_message = get_static_follow_up_for_approval(state, user_intention)
                        message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                        chat_history.append(AIMessage(content=message))  # Log user query
                        save_chat(chat_history,f"chat_{chatId}")
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention
                        }
                        return response
   
                else:
                    state["Industry_info"]["Sub-Sector"] = "Not Available in list"
                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                    save_state(state,f"QAPP_state_{chatId}")
                    if perfect_location_data:
                        message = "Not Available In List"
                        chat_history.append(AIMessage(content=message))  # Log user query
                        save_chat(chat_history,f"chat_{chatId}")
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention
                        }
                        return response
                    else:
                        response_static_message = get_static_follow_up_for_approval(state, user_intention)
                        message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                        chat_history.append(AIMessage(content=message))  # Log user query
                        save_chat(chat_history,f"chat_{chatId}")
                        response = {
                            "Ai_response": message,
                            "Is_confirmation" : None,
                            "Extracted Data": extracted_state,
                            "Validation Data": state,
                            "User Intention": user_intention
                        }
                        return response
            else:
                state["Industry_info"]["Main-Industry"] = None
                state["Industry_info"]["Sub-Sector"] = None
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                response_static_message = get_static_follow_up_for_approval(state, user_intention)
                message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
        else:
            state["Industry_info"]["Main-Industry"] = "Not Available in list"
            state["Industry_info"]["Sub-Sector"] = "Not Available in list"
            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
            save_state(state,f"QAPP_state_{chatId}")
            if perfect_location_data:
                message = "Not Available In List"
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
            else:
                response_static_message = get_static_follow_up_for_approval(state, user_intention)
                message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response

    elif user_intention == "Approval Search for area, city, or state with industry":
        extracted_data, validated_data = extract_location_from_query(refined_user_input, available_areas, available_cities, available_states, llm)
        area_name = validated_data["Area"]
        city_name = validated_data["City"]
        state_name = validated_data["State"]
        extracted_state["Location_info"] = extracted_data
        main_industry_list = list(main_industry_to_subsector_mapped_dict.keys())
        ind_extracted_data, ind_validated_data = extract_main_industry_and_product_universal(refined_user_input, main_industry_list, llm)
        main_industry_name = ind_validated_data["Main-Industry"]
        product_name = ind_validated_data["Product"]
        extracted_state["Industry_info"]["Main-Industry"] = ind_extracted_data["Main-Industry"]
        extracted_state["Industry_info"]["Product"] = ind_extracted_data["Product"] if ind_extracted_data["Product"] != "None" else None

        if area_name != "Not Available in List" and main_industry_name != "Not Available in list":

            if area_name != "None":
                parent_city = next((key for key, value in city_to_area_mapping.items() if area_name in value), None)
                parent_state = next((key for key, value in state_to_city_mapping.items() if parent_city in value), None)
                state["Location_info"]["Area"] = area_name
                state["Location_info"]["City"] = parent_city
                state["Location_info"]["State"] = parent_state
                save_state(state,f"QAPP_state_{chatId}")
            elif city_name != "None":
                parent_state = next((key for key, value in state_to_city_mapping.items() if city_name in value), None)
                state["Location_info"]["Area"] = None
                state["Location_info"]["City"] = city_name
                state["Location_info"]["State"] = parent_state
                save_state(state,f"QAPP_state_{chatId}")
            elif state_name != "None":
                state["Location_info"]["Area"] = None
                state["Location_info"]["City"] = None
                state["Location_info"]["State"] = state_name
                state["Only_State_Attempt_Count"] += 1
                save_state(state,f"QAPP_state_{chatId}")
            else:
                state["Location_info"]["Area"] = None
                state["Location_info"]["City"] = None
                state["Location_info"]["State"] = None
                save_state(state,f"QAPP_state_{chatId}")
            if main_industry_name != "None":
                state["Industry_info"]["Main-Industry"] = main_industry_name
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                sub_sector_list = list(main_industry_to_subsector_mapped_dict[main_industry_name].keys())
                extracted_data, validated_data = extract_sub_sector_and_product_universal(refined_user_input, sub_sector_list, llm, main_industry_name, product_name)
                sub_sector_name = validated_data["Sub-Sector"]
                product_name = validated_data["Product"]
                extracted_state["Industry_info"]["Sub-Sector"] = extracted_data["Sub-Sector"]
                extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
                if sub_sector_name != "Not Available in list":
                    if sub_sector_name != "None":
                        state["Industry_info"]["Sub-Sector"] = sub_sector_name
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QAPP_state_{chatId}")
                    else:
                        state["Industry_info"]["Sub-Sector"] = None
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QAPP_state_{chatId}")
                else:
                    state["Industry_info"]["Sub-Sector"] = "Not Available in list"
                    state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                    save_state(state,f"QAPP_state_{chatId}")
                    message = "Not Available In List"
                    chat_history.append(AIMessage(content=message))  # Log user query
                    save_chat(chat_history,f"chat_{chatId}")
                    response = {
                        "Ai_response": message,
                        "Is_confirmation" : None,
                        "Extracted Data": extracted_state,
                        "Validation Data": state,
                        "User Intention": user_intention
                    }
                    return response

            else:
                state["Industry_info"]["Main-Industry"] = None
                state["Industry_info"]["Sub-Sector"] = None
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                                  
            if state["Industry_info"]["Main-Industry"] is not None and state["Industry_info"]["Sub-Sector"] is not None:
                perfect_industry_data = True
            else:
                perfect_industry_data = False
            if (state["Location_info"]["Area"] is not None or state["Location_info"]["City"] is not None) or (state["Only_State_Attempt_Count"] >= 2):
                perfect_location_data = True
            else:
                perfect_location_data = False
            
            if perfect_industry_data and perfect_location_data:
                selected_option = next(
                (state.get("Industry_info").get(key) for key in ['Product', 'Sub-Sector', 'Main-Industry'] if state.get("Industry_info").get(key) not in [None, 'None']),
                ''
                )
                message = f"We have identified, you are looking for approvals related to {selected_option} production in {state.get("Location_info").get('Area')} under the city {state.get("Location_info").get("City")} in {state.get("Location_info").get("State")}. Is this information correct?"
                dynamic_confirmation_message = generate_dynamic_confirmation_message(message, llm_70b_vers_creative)
                chat_history.append(AIMessage(content=dynamic_confirmation_message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": dynamic_confirmation_message,
                    "Is_confirmation" : True,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
            else:
                response_static_message = get_static_follow_up_for_approval(state, user_intention)
                message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
        
        else:
            if area_name == "Not Available in List" and main_industry_name != "Not Available in List":
                state["Location_info"]["Area"] = "Not Available in List"
                state["Location_info"]["City"] = "Not Available in List"
                state["Location_info"]["State"] = "Not Available in List"
                state["Industry_info"]["Main-Industry"] = main_industry_name if main_industry_name != "None" else None
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                if main_industry_name != "None":
                    sub_sector_list = list(main_industry_to_subsector_mapped_dict[main_industry_name].keys())
                    extracted_data, validated_data = extract_sub_sector_and_product_universal(refined_user_input, sub_sector_list, llm, main_industry_name, product_name)
                    sub_sector_name = validated_data["Sub-Sector"]
                    product_name = validated_data["Product"]
                    extracted_state["Industry_info"]["Sub-Sector"] = extracted_data["Sub-Sector"]
                    extracted_state["Industry_info"]["Product"] = extracted_data["Product"] if extracted_data["Product"] != "None" else None
                    if sub_sector_name != "Not Available in list":
                        if sub_sector_name != "None":
                            state["Industry_info"]["Sub-Sector"] = sub_sector_name
                            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                            save_state(state,f"QAPP_state_{chatId}")
                        else:
                            state["Industry_info"]["Sub-Sector"] = None
                            state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                            save_state(state,f"QAPP_state_{chatId}")
                    else:
                        state["Industry_info"]["Sub-Sector"] = "Not Available in list"
                        state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                        save_state(state,f"QAPP_state_{chatId}")
                message = "Not Available In List"
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
            elif main_industry_name == "Not Available in List" and area_name != "Not Available in List":
                state["Industry_info"]["Main-Industry"] = "Not Available in list"
                state["Industry_info"]["Sub-Sector"] = "Not Available in list"
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                if area_name != "None":
                    parent_city = next((key for key, value in city_to_area_mapping.items() if area_name in value), None)
                    parent_state = next((key for key, value in state_to_city_mapping.items() if parent_city in value), None)
                    state["Location_info"]["Area"] = area_name
                    state["Location_info"]["City"] = parent_city
                    state["Location_info"]["State"] = parent_state
                    save_state(state,f"QAPP_state_{chatId}")

                elif city_name != "None":
                    parent_state = next((key for key, value in state_to_city_mapping.items() if city_name in value), None)
                    state["Location_info"]["Area"] = None
                    state["Location_info"]["City"] = city_name
                    state["Location_info"]["Area"] = parent_state
                    save_state(state,f"QAPP_state_{chatId}")
                
                elif state_name != "None":
                    state["Location_info"]["Area"] = None
                    state["Location_info"]["City"] = None
                    state["Location_info"]["State"] = state_name
                    state["Only_State_Attempt_Count"] += 1
                    save_state(state,f"QAPP_state_{chatId}")

                else:
                    state["Location_info"]["Area"] = None
                    state["Location_info"]["City"] = None
                    state["Location_info"]["State"] = None
                    save_state(state,f"QAPP_state_{chatId}")
                
                message = "Not Available In List"
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
            else:
                state["Location_info"]["Area"] = "Not Available in List"
                state["Location_info"]["City"] = "Not Available in List"
                state["Location_info"]["State"] = "Not Available in List"
                state["Industry_info"]["Main-Industry"] = "Not Available in list"
                state["Industry_info"]["Sub-Sector"] = "Not Available in list"
                state["Industry_info"]["Product"] = product_name if product_name != "None" else None
                save_state(state,f"QAPP_state_{chatId}")
                message = "Not Available In List"
                chat_history.append(AIMessage(content=message))  # Log user query
                save_chat(chat_history,f"chat_{chatId}")
                response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
                return response
            
    else:
        response_static_message = get_static_follow_up_for_approval(state, user_intention)
        message = generate_dynamic_message_for_approval(Chat_history_normal, response_static_message, refined_user_input, llm_70b_vers_creative)
        chat_history.append(AIMessage(content=message))  # Log user query
        save_chat(chat_history,f"chat_{chatId}")
        response = {
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Extracted Data": extracted_state,
                    "Validation Data": state,
                    "User Intention": user_intention
                }
        return response

def call_handle_approval_query(user_input,chatId):
    
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
    df = pd.DataFrame(result_of_query, columns=columns)
    df = df.drop_duplicates()

    city_area_mapped_dict = df.groupby("city_name")["area_name"].apply(list).to_dict()
    state_city_mapped_dict = df.groupby("state_name")["city_name"].apply(lambda x: list(x.unique())).to_dict()

    unique_area_list = list(df.area_name.unique())

    unique_city_list = list(df.city_name.unique())

    unique_state_list = list(df.state_name.unique())


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

    Industry_data_df_for_approval = pd.DataFrame(Industry_data_results, columns=["Segment","Sub-Sector", "Main-Industry"])

    # Initialize an empty dictionary
    Industry_data_for_approval = {}

    # Iterate through each row of the DataFrame
    for _, row in Industry_data_df_for_approval.iterrows():
        main_industry = row["Main-Industry"]
        sub_sector = row["Sub-Sector"]
        segment = row["Segment"]
        
        # Create the hierarchy step by step
        if main_industry not in Industry_data_for_approval:
            Industry_data_for_approval[main_industry] = {}
        if sub_sector not in Industry_data_for_approval[main_industry]:
            Industry_data_for_approval[main_industry][sub_sector] = []
        if segment not in Industry_data_for_approval[main_industry][sub_sector]:
            Industry_data_for_approval[main_industry][sub_sector].append(segment)

    state = get_state(f"QAPP_state_{chatId}") or None

    if not state:
        state = {
            "Location_info":{
                "Area":None,
                "City": None,
                "State": None
            },
            "Industry_info":{
                "Main-Industry": None,
                "Sub-Sector": None,
                "Product": None,
            },
            "KEYWORDS": None,
            "Only_State_Attempt_Count": 0
        }
        save_state(state,f"QAPP_state_{chatId}")
    extracted_state = state.copy()

    
    response_of_app_query = handle_approval_query(user_input, unique_area_list, unique_city_list, unique_state_list, Industry_data_for_approval, city_area_mapped_dict, state_city_mapped_dict, extracted_state, state, llm_70b_vers,chatId)
    return response_of_app_query
        
