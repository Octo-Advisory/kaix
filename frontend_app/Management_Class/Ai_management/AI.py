import frappe
from langchain.prompts import PromptTemplate
from frontend_app.Ai_module.Query_Classification_And_Analysis import classify_query,llm_70b_vers_creative,refine_query_with_history,llm_70b_vers,generate_fallback_message,respond_to_negative_query
from frontend_app.Ai_module.employement_query.Extraction_for_employement_search import call_handle_employment_query
from frontend_app.Ai_module.build_from_scratch.Extraction_for_Building_from_Scratch import entry_build_from_scratch
from frontend_app.Ai_module.incentive_query.Extraction_for_incentive_search import call_incentive_search
from frontend_app.Ai_module.approval_query.Extraction_for_approval_search import call_handle_approval_query
from frontend_app.Ai_module.vendor_query.Extraction_for_vendor_search import call_handle_vendor_query
import traceback
from  frontend_app.Management_Class.Redis_management.Redis_chat import save_chat,get_chat
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from frontend_app.Log_management.createlog import log
from frontend_app.Management_Class.helpers.utility import update_llm_token

@frappe.whitelist(allow_guest=True)
def ai_module_call(input,confirmationMessage,chatId):
    try:
        if input == "NOFROMUSER":
            chat_history = get_chat(f"chat_{chatId}") or []
            Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
            resp = generate_fallback_message(Chat_history_normal,confirmationMessage,llm_70b_vers_creative)
            response = { 
                    "Ai_response": resp,
                    "Is_confirmation" : None,
                    "Error":None
                }
            return response


        # Check if user intention is already determined
        user_intension = check_user_intension(chatId)

        if user_intension in ["Valueless queries","Other industry-related queries","Negatively Intended Query",None]:
            chat_history = get_chat(f"chat_{chatId}") or []
            Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
            refine_user_input = refine_query_with_history(Chat_history_normal,input,llm_70b_vers)
            user_intension = classify_query(refine_user_input)
            with open("testlog.txt", "a") as file:
                file.write(f"\nuser_intension found {user_intension} for chatId {chatId}")
            update_user_intension(user_intension,chatId)  # Store the classified intention for future use
            log(chatId,'debug','user_intension',str(user_intension),'AI.py','ai')
         # Handle different user intentions
        if user_intension == "Query to build industry from Scratch":
            try:
                response = entry_build_from_scratch(input,chatId)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly 6.",
                    "Is_confirmation" : None,
                    "Error":e,
                }
                log(chatId,'error','error',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to Get Employee Search":
            try:
                response = call_handle_employment_query(input,chatId)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly 5.",
                    "Is_confirmation" : None,
                    "Error":e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to search Vendors":
            try:
                response = call_handle_vendor_query(input,chatId)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly 4.",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to search Incentives":
            try:
                response = call_incentive_search(input,chatId)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly 3.",
                    "Is_confirmation" : None,
                    "Error":e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to Get Approvals":
            try:
                response = call_handle_approval_query(input,chatId)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly 2.",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Negatively Intended Query":
            try:
                message = respond_to_negative_query(
                    user_message=refine_user_input,
                    append_user_to_history=True,
                    append_AI_to_history=True,
                    llm=llm_70b_vers,
                    chatId=chatId,
                    update_intention=False
                    )
                response = { 
                    "Ai_response": message,
                    "Is_confirmation" : None,
                }
                log(chatId,'debug','response',str(response),'AI.py','ai')
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly 1.",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response

        else:
            try:
                message = generate_dynamic_message(refine_user_input,user_intension,chatId,llm_70b_vers_creative)
                response = { 
                    "Ai_response": message,
                    "Is_confirmation" : None,
                }
                log(chatId,'debug','response',str(response),'AI.py','ai') 
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly00.",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
         
    except Exception as e:
        error_details = traceback.format_exc()
        with open("log3.txt", "a") as file:
            file.write(f"\nerror_details from AI {error_details}")
        response = { 
            "Ai_response": "Internal Server Error! Please Try After Some Time...",
            "Is_confirmation" : None,
            "Error":error_details
        }
        log(chatId,'debug','response',f"{str(response)} error is {str(error_details)}",'AI.py','ai')
        return response

def check_user_intension(chatId):
    query = f'''select user_intension from `tabSession` where name = "{chatId}"'''
    user_intention = frappe.db.sql(query)
    return user_intention[0][0] or None

def update_user_intension(user_intension,chatId):
    query = "UPDATE `tabSession` SET user_intension = %s WHERE name = %s"
    frappe.db.sql(query, (user_intension, chatId))
    frappe.db.commit() 

def generate_dynamic_message(user_message, user_intention, chatId,llm):

    """
    Handles both valueless queries (e.g., greetings or unrelated queries) and other industry-related queries.
    For valueless queries, it responds politely and redirects the user to industry-building topics.
    For other industry-related queries, it provides relevant guidance while ensuring disclaimers are added only 
    when financial risks or critical decision-making are involved. In all cases, it smoothly transitions the 
    user to ask about the five core industry-building topics.

    Args:
        user_message (str): The user's message.
        user_intention (str): The identified user intent, either "Valueless queries" or "Other industry-related queries."
        chat_history (list): A list containing the last few user-AI interactions to maintain context.
        llm: The language model used to generate responses.

    Returns:
        str: A concise, professional, and context-aware response guiding the user appropriately.
    """
    chat_history = get_chat(f"chat_{chatId}") or []


    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-4:]]
    chat_history.append(HumanMessage(content=user_message))
    if user_intention == "Valueless queries":
        prompt_template = """
        The user has sent the following message: '{user_message}'.
        Below is the recent conversation history to maintain context:
        
        {chat_history}
        
        Respond politely, concisely, and empathetically. Ensure the response does not answer questions that are unrelated to industry-building topics. Keep it short as much as possible. Instead, redirect the conversation to industry-related queries smoothly, precisely, and creatively in a short and unique way.
        
        You are designed only to answer and smoothly round up the topic to industry-building and related topics, so just don't answer any of the questions besides it.
        
        Guidelines for crafting the response:
        1. Relevant Queries: If the user’s message is related to industry-building, provide a helpful and concise answer.
        2. Unrelated Queries: Do not answer questions unrelated to industry-building. Politely inform the user that this platform specializes in industry-related topics and guide them to ask queries like:
        - Building an industry from scratch
        - Searching for employment in a city or state
        - Inquiring about incentives
        - Finding vendors for their industry
        - Understanding the approval process
        Example: "I focus on industry-related topics. Let me know how I can assist with starting an industry or understanding approval processes."
        3. Vague or Emotional Messages: If the user’s message is vague, emotional, or includes frustration, acknowledge their feelings empathetically and redirect them toward relevant topics. For instance:
        - "I hear you. If you need help with industry-related questions, feel free to ask."
        4. Greetings: If the user sends a greeting, respond warmly and briefly, encouraging them to ask about industry-related topics. Example:
        - "Hi there! Let me know how I can assist with industry-related queries."
        5. Tone and Creativity: Always use a friendly and professional tone, keeping the response engaging and unique. Optionally, include an interesting fact about industries to add value to the conversation.

        Remember, do not answer questions outside the scope of industry-building. Focus solely on guiding the user back to relevant topics in a polite and empathetic manner.
        """
    else:
        prompt_template = """
        The user has sent the following industry-related message: '{user_message}'
        
        Below is the recent conversation history to maintain context:
        
        {chat_history}
        
        Respond politely, concisely, and professionally. Provide a helpful and knowledgeable answer based on industry-related best practices. 

        However, include a clear disclaimer where necessary, emphasizing that industry-related decisions depend on multiple factors such as regulations, market conditions, financial constraints, and expert guidance. Always include this disclaimer if needed to ensure the user understands the complexity of industry-related queries.

        Strict Rule: Only include the following disclaimer—"Please note that industry decisions depend on multiple factors, including legal, financial, and market conditions. It is recommended to conduct thorough research and seek expert advice before proceeding."—if and only if the user's query involves financial investment, monetary risks, or any decision that could lead to significant consequences if acted upon without thorough evaluation. Do not include this disclaimer in every response.

        After addressing the user’s query, smoothly redirect them to one of the five core industry-building topics, encouraging them to ask related questions:
        - Building an industry from scratch
        - Searching for employment in a city or state
        - Inquiring about incentives
        - Finding vendors for their industry
        - Understanding the approval process

        Guidelines for Crafting the Response:
        1. Relevant Queries: Provide an informative and concise response while maintaining professionalism.
        2. Disclaimer: When discussing industry-related guidance, include a polite disclaimer such as:
        - "Please note that industry decisions depend on multiple factors, including legal, financial, and market conditions. It is recommended to conduct thorough research and seek expert advice before proceeding."
        Only include this disclaimer if the response involves investment, monetary risk, or significant decision-making that requires careful evaluation. Strictly do not add it otherwise.
        3. Empathy & Engagement: If the user expresses concerns or confusion, acknowledge their feelings with empathy while providing clear guidance.
        - Example: "I understand that industry decisions can be complex. Here's some insight that may help..."
        4. Smooth Redirection: No matter the response, always transition smoothly to the five core industry-building topics.
        - Example: "If you're looking for further guidance, I can also help with topics like setting up an industry, vendor selection, or employment searches. Let me know what you need!"
        5. Professional & Engaging Tone: Keep the response clear, practical, and engaging, ensuring the user feels supported and informed.
        6. Response Length: Always keep the response within one concise paragraph of no more than three lines while ensuring clarity and completeness.

        Remember: While answering the user's question, always guide them back to the five key industry-building topics and ensure they remain the focus of the conversation.
        """


    # Define the prompt template with chat history
    prompt = PromptTemplate(
        input_variables=["user_message", "chat_history"],
        template=prompt_template,
    )

    # Create a chain with the prompt template and LLM
    chain = prompt | llm

    # Generate the response
    response = chain.invoke({"user_message": user_message, "chat_history": "\n".join(Chat_history_normal)})
    update_llm_token(response)
    message_from_ai = response.content.strip()
    chat_history.append(AIMessage(content=message_from_ai))
    save_chat(chat_history,f"chat_{chatId}")
    
    return message_from_ai

# def respond_to_negative_query(
#     user_message: str,
#     append_user_to_history: bool,
#     append_AI_to_history: bool,
#     llm,
#     chatId,
#     update_intention = True
# ) -> str:
#     """
#     Reacts to negative intent in user queries by acknowledging it and 
#     politely redirecting users to supported industry-related alternatives.

#     Parameters:
#     - user_message (str): The most recent user input.
#     - append_user_to_history (bool): Flag to determine whether to add the user message to chat history.
#     - llm: A language model instance that supports the `.invoke()` method for prompt completion.

#     Returns:
#     - str: A short, polite AI-generated redirection message (max two lines).
#     """
#     chat_history = get_chat(f"chat_{chatId}") or []
#     Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-4:]]
#     if append_user_to_history:
#         chat_history.append(HumanMessage(content=user_message))
#         save_chat(chat_history,f"chat_{chatId}")

#     prompt_template = """
#     You are a professional AI assistant designed to help users with industry-related queries. 
#     Sometimes users may express that they do not want to proceed with a certain type of query, 
#     such as searching for vendors, incentives, employment, approvals, or land.

#     Your task is to:
#     - Politely acknowledge the user's intent to not continue with the current path.
#     - Respect their decision without repeating the rejected topic.
#     - Encourage them to explore other areas the platform supports — but limit suggestions to one or two concise, relevant alternatives.
#     - Keep the response short, natural, and conversational — a maximum of two lines.
    
#     Input Usage Guidelines:
#     - Use the latest user message to understand the user’s current concern or direction.
#     - Refer to the recent conversation history only when needed to maintain context, avoid repetition, or recognize prior negative expressions.
#     - Do not restate or repeat what was already covered unless it helps clarify or smoothly redirect the conversation.

#     Important Instructions:
#     - Do NOT mention or re-suggest the category the user rejected — even in a different location, product, or form.
#     - If the user’s rejection appears to be specific to a location, product, or context, you may offer assistance in other locations or products — but only if it does not reintroduce the rejected category.
#     - Suggest one alternative direction naturally (two if needed) based on platform capabilities:
#         - Building an industry from scratch
#         - Searching for employment in a city or state
#         - Inquiring about incentives
#         - Finding vendors for their industry
#         - Searching for the approvals
#     - Never use "how to build an industry" or anything that implies your platform teaches or trains users. 
#     You are assisting them in setting up or building, not educating them.
#     - Keep the response strictly within two lines, using concise and polite phrasing.

#     Inputs:
#     - Latest user message: {user_message}
#     - Recent conversation history: {chat_history}

#     Output Requirements:
#     - The message should be in one short paragraph with no more than two lines.
#     - It must feel polite, helpful, and actionable — inviting the user to continue exploring relevant options.
#     - Do NOT list all supported categories. Suggest only 1–2 in natural language, avoiding list-like structure.
#     """

#     prompt = PromptTemplate(
#         input_variables=["user_message", "chat_history"],
#         template=prompt_template
#     )
#     chain = prompt | llm

#     result = chain.invoke({
#         "user_message": user_message,
#         "chat_history": "\n".join(Chat_history_normal)
#     })
#     message_from_ai = result.content.strip()
#     if append_AI_to_history:
#         chat_history.append(AIMessage(content=message_from_ai))
#         save_chat(chat_history,f"chat_{chatId}")
#     if update_intention:
#         update_user_intension("Negatively Intended Query", chatId)
#     return message_from_ai
