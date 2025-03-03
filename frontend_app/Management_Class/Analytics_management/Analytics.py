import frappe
import json
from frontend_app.Management_Class.Analytics_management.indutry_from_scratch import industry_from_scratch
from frontend_app.Management_Class.Ai_management.AI import check_user_intension
from frontend_app.Management_Class.Analytics_management.employement_query import handle_employement_query
from frontend_app.Management_Class.Analytics_management.incentive_query import call_incentive_query 
from frontend_app.Management_Class.Analytics_management.approval_query import call_approval_query
from frontend_app.Management_Class.Analytics_management.vendor_query import call_vendor_query

@frappe.whitelist(allow_guest=True)
def analytics_module_call(aiResponse,chatId,validationResult):
    try:
        # with open("log2.txt", "a") as file:
        #     file.write(f"\naiReponse from analytics {aiReponse}")
        user_intension = check_user_intension(chatId)
        # with open("log2.txt", "a") as file:
        #     file.write(f"\nuser intension {user_intension}")
        aiResponse = json.loads(aiResponse)
        aiResponse = aiResponse[0]
        if user_intension == "Query to Get Employee Search":
            result = handle_employement_query(aiResponse,chatId)
            response = {
                **result,
                "user_intension" : user_intension
            }
            return response
        elif user_intension == "Query to build industry from Scratch":
            result =  industry_from_scratch(aiResponse['state'],chatId)
            response = {
                    **result,
                    "user_intension" : user_intension
                }
            return response
        elif user_intension == "Query to search Incentives":
            result = call_incentive_query(aiResponse,chatId)
            response = {
                    **result,
                    "user_intension" : user_intension
                }
            return response
        elif user_intension == "Query to Get Approvals":
            result = call_approval_query(aiResponse,chatId)
            response = {
                    **result,
                    "user_intension" : user_intension
                }
            return response
        elif user_intension == "Query to search Vendors":
             result = call_vendor_query(aiResponse,chatId,validationResult)
             with open("log.txt", "a") as file:
                file.write(f"\nresult {result}{user_intension}")
             response = {
                    **result,
                    "user_intension" : user_intension
                }
             return response
    except Exception as e:
       return {"error": f"An error occurred: {str(e)}"}
