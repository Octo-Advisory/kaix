import frappe
from langchain.prompts import PromptTemplate
from frontend_app.Ai_module.Query_Classification_And_Analysis import classify_query,llm_70b_vers_creative
from frontend_app.Ai_module.employement_query.Extraction_for_employement_search import call_handle_employment_query
from frontend_app.Ai_module.build_from_scratch.Extraction_for_Building_from_Scratch import entry_build_from_scratch
from frontend_app.Ai_module.incentive_query.Extraction_for_incentive_search import call_incentive_search
from frontend_app.Ai_module.approval_query.Extraction_for_approval_search import call_handle_approval_query
from frontend_app.Ai_module.vendor_query.Extraction_for_vendor_search import call_handle_vendor_query

@frappe.whitelist(allow_guest=True)
def ai_module_call(input,chatId):
    try:
        # Check if user intention is already determined
        user_intension = check_user_intension(chatId)

        if user_intension == None:    # If not, classify the query
            user_intension = classify_query(input)
            
            if user_intension != "Valueless queries":   
                update_user_intension(user_intension,chatId)  # Store the classified intention for future use
        
         # Handle different user intentions
        if user_intension == "Query to build industry from Scratch":
            try:
                response = entry_build_from_scratch(input,chatId)
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Internal Server Error! Please Try After Some Time....",
                    "Is_confirmation" : None,
                    "Error":e,
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
            
        elif user_intension == "Query to search Vendors":
            try:
                response = call_handle_vendor_query(input,chatId)
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Internal Server Error! Please Try After Some Time....",
                    "Is_confirmation" : None,
                    "error": e
                }
                return response
            
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
            
        elif user_intension == "Query to Get Approvals":
            try:
                response = call_handle_approval_query(input,chatId)
                return response
            except Exception as e:
                response = { 
                    "Ai_response": "Internal Server Error! Please Try After Some Time....",
                    "Is_confirmation" : None,
                    "error": e
                }
                return response
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

def generate_dynamic_message(user_message: str) -> str:
    """
    Generates a concise and relevant response based on user input, ensuring the query is valid and within context.
    
    Parameters:
        user_message (str): The latest user input.
    
    Returns:
        str: A refined question, clarification request, or response that ensures user queries remain relevant.
    """
    
    prompt = """
    You are a professional and user-friendly AI assistant. Your goal is to guide users to provide relevant and meaningful queries.
    
    Your task:
    1. **Process the User’s Input**:
       - If the input is a greeting (e.g., "Hello", "Hi", "Hey"), respond with a friendly AI introduction.
       - If the input is vague, incomplete, or off-topic, politely guide the user to provide a valid query.
       - If details are missing, ask for clarification in a friendly and professional manner.
       - If the query is relevant, respond concisely and informatively.
    
    2. **Ensure Responses Are Polite, Clear & On-Topic**:
       - If the input is a greeting: "Hello! How can I assist you today?"
       - If the input is unclear or off-topic: "I'm here to help with relevant queries. Could you provide more details?"
       - If the input lacks details: "Could you clarify your request so I can assist better?"
       - If the input is valid: A short and relevant response (max 20 words).
    
    ## User's Input:
    "{user_message}"
    
    ## Expected Output:
    - If greeting detected: "Hello! How can I assist you today?"
    - If the query is off-topic: "I'm here to assist with [your context]. Please provide a relevant question."
    - If the query is unclear: "Could you clarify your request?"
    - If the query is valid: A short and helpful response.
    """
    
    llm = llm_70b_vers_creative  # Your LLM instance
    prompt_template = PromptTemplate(
        input_variables=["user_message"],
        template=prompt
    )
    chain = prompt_template | llm
    message = chain.invoke({"user_message": user_message})
    
    return message.content.strip()