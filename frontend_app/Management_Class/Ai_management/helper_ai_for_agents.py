import os
import copy
import frappe
import json
from langchain.prompts import PromptTemplate
from frontend_app.Ai_module.Query_Classification_And_Analysis import *
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
# --- AI.py (imports) ---
from frontend_app.Ai_module.responder_consultant import (
    consultant_response_from_langchain,
    consultant_response_from_strings,
)

def polish_ai_response_if_possible(
    raw_response: dict,
    chat_history_messages,           # List[BaseMessage]  (your LangChain history)
    chat_history_strings: list,      # Optional[List[str]] if you already built it
    latest_user:str = None
) -> dict:
    """
    Rewrites Ai_response via the Responder-Consultant. Falls back gracefully.
    Pass either 'chat_history_messages' OR 'chat_history_strings'.
    """
    try:
        if not raw_response or raw_response.get("Error"):
            return raw_response

        ai_response = raw_response,get("AI_response")

        ai_resp = (raw_response.get("Ai_response") or "").strip()
        is_confirmation = raw_response.get("Is_confirmation")
        trigger_lead_generation = raw_response.get("Trigger_Lead_Generation", False)

        with open("testlog.txt", "a") as file:
                file.write(f"\n############### RESPONDER LLM: \n\t\t\t Precious ai_resp: {ai_resp} \n\t\t\tis_confirmation:{is_confirmation} \n\t\t\ttrigger_lead_generation:{trigger_lead_generation} ")

        if not ai_resp:
            return raw_response

        polished = None
        if chat_history_strings is not None:
            # Use the string path if you already built Chat_history_normal
            polished = consultant_response_from_strings(
                llm=RESPONDER_LLM,
                chat_history_strings=chat_history_strings,
                module_ai_response=ai_resp,
                max_history_entries=11,
                is_confirmation=is_confirmation,
                latest_user=latest_user,
                trigger_lead_generation=trigger_lead_generation
            )
        else:
            # Default: use the LangChain message objects directly
            polished = consultant_response_from_langchain(
                llm=RESPONDER_LLM,
                chat_history=chat_history_messages,
                module_ai_response=ai_resp,
                max_history_entries=11,
                is_confirmation=is_confirmation,
                latest_user=latest_user,
                trigger_lead_generation=trigger_lead_generation
            )
            

        if polished:
            raw_response["Ai_response"] = polished
            
        return raw_response
    except Exception:
        return raw_response

def run_ai_module_flow_core(input,chatId,refine_user_input, user_intension,):
    try:
        additional_response = None
        with open("testlog.txt", "a") as file:
            file.write(f"\n<<<<<<<<<<<>>>>>>>>>>>>>>>>> OUTSIDE IF User Intention : \n\t\t\t{user_intension} for chatId {chatId}") 
        if user_intension not in ["Valueless queries","Other industry-related queries","Negatively Intended Query","Follow-up Query",None]:
            with open("testlog.txt", "a") as file:
                file.write(f"\n<<<<<<<<<<<>>>>>>>>>>>>>>>>> INSIDE IF User Intention : \n\t\t\t{user_intension} for chatId {chatId}")
            
            chat_history = get_chat(f"chat_{chatId}") or []
            Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-6:]]
            # refine_user_input = refine_query_with_history(Chat_history_normal,input,llm_70b_vers)
            response = detect_module_switch_intent(
                # refine_user_input,
                input,
                user_intension,
                llm_70b_vers,
                Chat_history_normal
            )
            temp_out = response["switch_module"]
            
            log(chatId,'debug','response',f"ABCDEFG {temp_out}",'AI.py','ai')
            if response["switch_module"]:
                log(chatId,'debug','response',f"{user_intension} changed to None",'AI.py','ai')
                user_intension = None
                update_user_intension(user_intension,chatId)
            else:
                pass

        # chat_history = get_chat(f"chat_{chatId}") or []
        # Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-11:]]
        # aggressive_config = {
        #     'fresh_turns': 3,
        #     'recent_turns': 6,
        #     'aging_turns': 10,
        #     'stale_turns': 12
        # }
        # refine_user_input = refine_query_with_history(Chat_history_normal,input,llm_gpt_oos_120b,aggressive_config)
        # chat_history.append(HumanMessage(content=refine_user_input))  # Log user query
        # save_chat(chat_history,f"chat_{chatId}")

        if user_intension in ["Valueless queries","Other industry-related queries","Negatively Intended Query", "Follow-up Query",None]:
            # user_intension = classify_query(refine_user_input, chatId)
            multifactor_classification = classify_user_intent(refine_user_input, llm_gpt_oos_120b, chatId)

            main_class = multifactor_classification['main_class']
            sub_queries = multifactor_classification['sub_queries']
            additional_response = multifactor_classification['additional_response']
            new_input = sub_queries.get(main_class, input)

            with open("testlog.txt", "a") as file:
                file.write(f"\nMultifactor_classification found: \n\t\t\tmain_class: {main_class} \n\t\t\tsub_queries:{sub_queries} \n\t\t\tadditional_response:{additional_response} \n\t\t\tnew_input: {new_input} \n\t\t\tprevious_input: {input} \n\t\t\trefined_input: {refine_user_input} for chatId {chatId}")

            user_intension = main_class
            input = new_input
            # user_intension = classify_query(refine_user_input, llm_70b_vers, chatId)
            # user_intension_multilabel = classify_query_multilabel(refine_user_input, llm_70b_vers, chatId)
            with open("testlog.txt", "a") as file:
                file.write(f"\nuser_intension found {user_intension} for chatId {chatId}")
            # with open("testlog.txt", "a") as file:
            #     file.write(f"\nMulti Label user_intension found: \n\t\t\t{user_intension_multilabel} for chatId {chatId}")
            update_user_intension(user_intension,chatId)  # Store the classified intention for future use
            frappe.log_error("user intension",f"{user_intension,str(user_intension)}")
            log(chatId,'debug','user_intension',str(user_intension),'AI.py','ai')
        else:
            input = refine_user_input

        # Handle different user intentions
        with open("testlog.txt", "a") as file:
            file.write(f"\nBefore IF Additional response testing {additional_response} for chatId {chatId}")
            
        if user_intension == "Query to build industry from Scratch":
            with open("testlog.txt", "a") as file:
                file.write(f"\nAfter IF Additional response testing {additional_response} for chatId {chatId}")
            try:
                response = entry_build_from_scratch(input,chatId, additional_class_response=additional_response)
                response_message = response.get('Ai_response', '')
                response_message += f"<br/><br/>**Note**: {additional_response}" if additional_response else ""
                response["Ai_response"] = response_message
                log(chatId,'debug','response',str(response),'AI.py','ai')
                # return response
            
            except Exception as e:
                response = { 
                    "Ai_response": f"Something went wrong while processing your request. Please try again shortly.",
                    "Is_confirmation" : None,
                    "Error":e,
                }
                log(chatId,'error','error',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to Get Employee Search":
            try:
                response = call_handle_employment_query(input,chatId, additional_class_response=additional_response)
                response_message = response.get('Ai_response', '')
                response_message += f"<br/><br/>**Note**: {additional_response}" if additional_response else ""
                response["Ai_response"] = response_message
                log(chatId,'debug','response',str(response),'AI.py','ai')
                # return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly",
                    "Is_confirmation" : None,
                    "Error":e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to search Vendors":
            try:
                response = call_handle_vendor_query(input,chatId, additional_class_response=additional_response)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                response_message = response.get('Ai_response', '')
                response_message += f"<br/><br/>**Note**: {additional_response}" if additional_response else ""
                response["Ai_response"] = response_message
                # return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to search Incentives":
            try:
                with open("testlog.txt", "a") as file:
                    file.write(f"current_input: {input} for chatId {chatId}")
                response = call_incentive_search(input,chatId, additional_class_response=additional_response)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                response_message = response.get('Ai_response', '')
                response_message += f"<br/><br/>**Note**: {additional_response}" if additional_response else ""
                response["Ai_response"] = response_message
                # return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly",
                    "Is_confirmation" : None,
                    "Error":e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Query to Get Approvals":
            try:
                response = call_handle_approval_query(input,chatId, additional_class_response=additional_response)
                log(chatId,'debug','response',str(response),'AI.py','ai')
                response_message = response.get('Ai_response', '')
                response_message += f"<br/><br/>**Note**: {additional_response}" if additional_response else ""
                response["Ai_response"] = response_message
                # return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
            
        elif user_intension == "Negatively Intended Query":
            try:
                message = respond_to_negative_query(
                    user_message=refine_user_input,
                    append_user_to_history=False,
                    append_AI_to_history=False,
                    llm=llm_70b_vers,
                    chatId=chatId,
                    update_intention=False
                    )
                response = { 
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Trigger_Lead_Generation":False
                }
                log(chatId,'debug','response',str(response),'AI.py','ai')
                # return response
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
        
        elif user_intension == "Follow-up Query":
            try:
                response_message = generate_followup_response(input, llm_70b_vers_creative, chatId)
                response = { 
                        "Ai_response": response_message,
                        "Is_confirmation" : None,
                        "Trigger_Lead_Generation":False
                    }
                
                log(chatId,'debug','response',str(response),'AI.py','ai')
                # return response
            
            except Exception as e:
                response = { 
                    "Ai_response": "Something went wrong while processing your request. Please try again shortly.",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
            return response

        else:
            try:
                with open("log2.txt", "a") as file:
                    file.write(f"\nerror_details from AI dynamic func {user_intension}, & {refine_user_input}, {chatId}")
            
                message = generate_dynamic_message(refine_user_input,user_intension,chatId,llm_70b_vers_creative)
                response = { 
                    "Ai_response": message,
                    "Is_confirmation" : None,
                    "Trigger_Lead_Generation":False
                }
                log(chatId,'debug','response',str(response),'AI.py','ai') 
                # return response
            except Exception as e:
                response = {
                    "Ai_response": f"Something went wrong while processing your request. Please try again shortly.",
                    "Is_confirmation" : None,
                    "error": e
                }
                log(chatId,'debug','response',f"{str(response)} error is {str(e)}",'AI.py','ai')
                return response
        if (response["Ai_response"].lower() != "Not Available in List".lower()):
            chat_history = get_chat(f"chat_{chatId}") or []
            with open("testlog.txt", "a") as file:
                file.write(f"\nI am about to call responder llm :::::::::[][][]][][[]>]")
            response = polish_ai_response_if_possible(
            raw_response=response,
            chat_history_messages=chat_history[-11:],            # LangChain objects
            chat_history_strings=None,      # orf None if you don't want to use this path
            latest_user=input
            )
            # chat_history.append(AIMessage(content=response["Ai_response"]))
            # save_chat(chat_history,f"chat_{chatId}")

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
        doc = frappe.get_doc({
            'doctype': 'AIX Diagnostics Hub',
            'type': 'Ai Error',
            'note': f"Internal Server Error! {str(error_details)}",
            'session': chatId,
        })
        doc.insert(ignore_permissions=True)  # ignore_permissions=True if creating from a server script
        frappe.db.commit()
        log(chatId,'debug','response',f"{str(response)} error is {str(error_details)}",'AI.py','ai')
        return response


import json

def get_feasibility_json(feasibility_id):
    """
    Returns parsed JSON (dict/list) for the given feasibility_id.
    Raises FeasibilityJSONError (or JSONDecodeError) on any problem.
    """
    query = f'''SELECT result_data 
                FROM `tabFeasibility Report` 
                WHERE name = "{feasibility_id}"'''
    result = frappe.db.sql(query)

    if not result or not result[0][0]:
        return {}

    json_data = result[0][0]
    try:
        return json.loads(json_data)
    except json.JSONDecodeError as e:
        raise FeasibilityJSONError(f"Invalid JSON for feasibility_id={feasibility_id}: {e}") from e

def update_user_intension(user_intension,chatId):
    query = "UPDATE `tabSession` SET user_intension = %s WHERE name = %s"
    with open("log2.txt", "a", encoding="utf-8") as file:
            file.write(f" USER_INTENTION IN SESSION =============>>>>>>>>>>>>>>>> \n {query} \n user_intension :-> {user_intension} \n chatId :-> {chatId} \n")
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
    with open("log3.txt", "a") as file:
            file.write(f"\nerror_details from AI dynamic func {user_intention}, & {user_message}, {chatId}")
    chat_history = get_chat(f"chat_{chatId}") or []
    
    Chat_history_normal = [f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}" for m in chat_history[-4:]]
    # chat_history.append(HumanMessage(content=user_message))
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
    # chat_history.append(AIMessage(content=message_from_ai))
    # save_chat(chat_history,f"chat_{chatId}")
    
    return message_from_ai

