import frappe
import json
# from frontend_app.Analytics_module.employment_search_algorith import employment_search_algo
from frontend_app.Management_Class.Analytics_management.indutry_from_scratch import industry_from_scratch

@frappe.whitelist(allow_guest=True)
def analytics_module_call(aiReponse,chatId):
    try:
        # Call # Analytics Modulte for Industry from scratch
        # s = indutry_from_scratch(aiReponse)
        aiReponse = json.loads(aiReponse)
        s = industry_from_scratch(aiReponse,chatId)
        return s
    except Exception as e:
       return {"error": f"An error occurred: {str(e)}"}


    # Analytic module for Employement
    # try:
    #     with open("log.txt", "a") as file:
    #         file.write(f"\ncome here with  {aiReponse} and chat id {chatId}")
    #     # frappe.error_log(f"chat is {chatId}")
    #     # Parse the JSON string to a Python dictionary
    #     aiReponse = json.loads(aiReponse)
    #     aiReponse = aiReponse[0]
    #     # logging.info(f"Analytics input: {aiReponse}")
        
    #     # Extract user intention
    #     with open("log.txt", "a") as file:
    #         file.write(f"\naiReponse1  {aiReponse}")
    #     user_intention = aiReponse.get('User Intention')
    #     with open("log.txt", "a") as file:
    #         file.write(f"\nuser_intention  {user_intention}")
    #     # Handle based on user intention
    #     if user_intention == "Individual employment status":
    #         city = aiReponse['Validation Data']['City'][0]
    #         state = aiReponse['Validation Data']['State'][0]
    #         result = {"user_intention": user_intention, "city": city, "state": state}
    #         with open("log.txt", "a") as file:
    #             file.write(f"\ncome here with12  {city},{state},{result}")
    #         return employment_search_algo(user_intention,{"state":state , "city_name":city },chatId)
    #     elif user_intention == "Comparison between cities, states, or areas":
    #         city = aiReponse['Validation Data']['City']
    #         result = {"user_intention": user_intention, "city": city}
    #         return employment_search_algo(user_intention,{"cities":city },chatId)
    #     else:
    #         # Handle unknown user intention
    #         result = {"error": "Unknown user intention"}
    #         return result
       
    # except Exception as e:
    #     return {"error": f"An error occurred: {str(e)}"}
