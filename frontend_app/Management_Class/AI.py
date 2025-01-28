import frappe
import logging
from frontend_app.Ai_module.Query_Classification_And_Analysis import classify_query
from frontend_app.Ai_module.Extraction_for_employement_search import call_handle_employment_query

logging.basicConfig(
    filename='AIerror.log',  # Log file name
    level=logging.INFO,  # Minimum log level to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S'  # Date format in logs
)

@frappe.whitelist(allow_guest=True)
def ai_module_call(input,chatId):
    logging.info(f"input {input}")
    # category = classify_query(input)
    # logging.info(f"category {category}")
    # if category == 'Query to Get Employee Search':
    try:
        response = call_handle_employment_query(input,chatId)
        return response
    except Exception as e:
        response = {
            "Ai_response": e,
            "Is_confirmation" : None,
        }
        return response
    # else:
    #   return { "Ai_response": "Invalid Query",
    #                 "Is_confirmation" : None,}