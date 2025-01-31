import frappe
# from frontend_app.Ai_module.Query_Classification_And_Analysis import classify_query
from frontend_app.Ai_module.Extraction_for_employement_search import call_handle_employment_query
from frontend_app.Ai_module.build_from_scratch.Extraction_for_Building_from_Scratch import entry_build_from_scratch


@frappe.whitelist(allow_guest=True)
def ai_module_call(input,chatId):
    # category = classify_query(input)
    # logging.info(f"category {category}")
    # if category == 'Query to Get Employee Search':
    try:
        # response = call_handle_employment_query(input,chatId)  # Employeement call
        response = entry_build_from_scratch(input,chatId) # Build from scratch
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