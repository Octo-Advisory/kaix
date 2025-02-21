import frappe
import json
from frontend_app.Management_Class.Analytics_management.indutry_from_scratch import industry_from_scratch
from frontend_app.Management_Class.Ai_management.AI import check_user_intension
from frontend_app.Management_Class.Analytics_management.employement_query import handle_employement_query

@frappe.whitelist(allow_guest=True)
def analytics_module_call(aiReponse,chatId):
    try:
        user_intension = check_user_intension(chatId)
        aiReponse = json.loads(aiReponse)
        if user_intension == "Query to Get Employee Search":
            result = handle_employement_query(aiReponse,chatId)
            response = {
                **result,
                "user_intension" : user_intension
            }
            return response
        elif user_intension == "Query to build industry from Scratch":
            result =  industry_from_scratch(aiReponse,chatId)
            response = {
                    "Analytics_response" : result,
                    "user_intension" : user_intension
                }
            return response
        elif user_intension == "Query to search Incentives":
            response = {
                "Analytics_response" : "none",
                "user_intension" : user_intension
            }
            return response
        # elif user_intension == "Query to Get Approvals":
        # elif user_intension == "Query to search Vendors":
    except Exception as e:
       return {"error": f"An error occurred: {str(e)}"}
