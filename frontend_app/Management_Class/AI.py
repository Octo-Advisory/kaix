import frappe
from langchain.prompts import PromptTemplate
from frontend_app.Ai_module.Query_Classification_And_Analysis import classify_query,llm_70b_vers_creative
from frontend_app.Ai_module.Extraction_for_employement_search import call_handle_employment_query
from frontend_app.Ai_module.build_from_scratch.Extraction_for_Building_from_Scratch import entry_build_from_scratch
from frontend_app.Ai_module.incentive_query.Extraction_for_incentive_search import call_incentive_search

@frappe.whitelist(allow_guest=True)
def ai_module_call(input,chatId):
    try:
        # Check user intension if already get
        user_intension = check_user_intension(chatId)
        frappe.log_error(f"user_intension {user_intension}")
        if user_intension == None:    # if user intension already there use it
            user_intension = classify_query(input)
            frappe.log_error(f"cataory found {user_intension}")
            if user_intension != "Valueless queries":   
                update_user_intension(user_intension,chatId)  
            
        frappe.log_error(f"user_intension {user_intension}")
        if user_intension == "Query to build industry from Scratch":
            try:
                response = entry_build_from_scratch(input,chatId)
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Internal Server Error! Please Try After Some Time....",
                    "Is_confirmation" : None,
                    "Error":e
                }
                return response
            
        elif user_intension == "Query to Get Employee Search":
            try:
                response = call_handle_employment_query(input,chatId)
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Internal Server Error! Please Try After Some Time....",
                    "Is_confirmation" : None,
                    "Error":e
                }
                return response
            
        # elif user_intension == "Query to search Vendors":
        #     try:
        #         response = call_handle_employment_query(input,chatId)
        #         return response
        #     except Exception as e:
        #         response = { 
        #             "Ai_response": "Internal Server Error! Please Try After Some Time....",
        #             "Is_confirmation" : None,
        #         }
        #         return response
            
        elif user_intension == "Query to search Incentives":
            try:
                response = call_incentive_search(input,chatId)
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Internal Server Error! Please Try After Some Time....",
                    "Is_confirmation" : None,
                    "Error":e
                }
                return response
            
        # elif user_intension == "Query to Get Approvals":
        #     try:
        #         response = call_handle_employment_query(input,chatId)
        #         return response
        #     except Exception as e:
        #         response = { 
        #             "Ai_response": "Internal Server Error! Please Try After Some Time....",
        #             "Is_confirmation" : None,
        #         }
        #         return response
        else:
            message = generate_dynamic_message(input)
            response = { 
                "Ai_response": message,
                "Is_confirmation" : None,
            } 
            return response
         

    except Exception as e:
        response = { 
            "Ai_response": "Internal Server Error! Please Try After Some Time....",
            "Is_confirmation" : None,
            "Error":e
        }
        return response

def check_user_intension(chatId):
    query = f'''select user_intension from `tabSession` where name = "{chatId}"'''
    user_intention = frappe.db.sql(query)
    return user_intention[0][0] or None

def update_user_intension(user_intension,chatId):
    query = "UPDATE `tabSession` SET user_intension = %s WHERE name = %s"
    frappe.db.sql(query, (user_intension, chatId))
    frappe.db.commit() 

@frappe.whitelist()
def generate_dynamic_message(user_message: str) -> str:
    """
    Generates a concise dynamic response based on user input.
    
    Parameters:
        user_message (str): The latest user input.
    
    Returns:
        str: A refined question, clarification request, or response (short and clear).
    """

    prompt = """
    You are a highly skilled assistant that provides **brief and effective** responses.
    
    Your task:
    1. **Understand the User’s Input**:
       - If the input is vague or incomplete, suggest a **clear and well-formed query (max 10 words).**
       - If the input lacks details, **ask for more specifics in one sentence.**
       - If the input is valid, generate a **concise response in one or two sentences.**

    2. **Ensure Responses Are Short & Direct**:
       - Keep the response **under 20 words.**
       - Avoid unnecessary explanations or long-winded replies.
       - If the query is **off-topic**, politely **redirect in one short sentence.**

    ## User's Input:
    "{user_message}"

    ## Expected Output:
    - If the query is unclear, rewrite it as a **better, shorter question (max 10 words).**
    - If details are missing, **ask for more specifics (max 15 words).**
    - If the query is valid, **respond concisely in 1-2 short sentences (max 20 words).**
    - If the query is off-topic, **redirect politely in one sentence.**
    """

    llm = llm_70b_vers_creative  # Your LLM instance
    prompt_template = PromptTemplate(
        input_variables=["user_message"],
        template=prompt
    )
    chain = prompt_template | llm
    message = chain.invoke({"user_message": user_message})

    return message.content.strip()