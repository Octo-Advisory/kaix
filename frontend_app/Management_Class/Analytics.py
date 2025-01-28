import frappe
import logging
import json
from frontend_app.Analytics_module.employment_search_algorith import employment_search_algo

@frappe.whitelist(allow_guest=True)
def analytics_module_call(aiReponse,chatId):
    try:
        # Parse the JSON string to a Python dictionary
        aiReponse = json.loads(aiReponse)
        # logging.info(f"Analytics input: {aiReponse}")
        
        # Extract user intention
        user_intention = aiReponse.get('User Intention')
        logging.info(f"User Intention: {user_intention}")
        
        # Handle based on user intention
        if user_intention == "Individual employment status":
            city = aiReponse['Validation Data']['City'][0]
            state = aiReponse['Validation Data']['State'][0]
            result = {"user_intention": user_intention, "city": city, "state": state}
            logging.info(f"Result: {result}")
            return employment_search_algo(user_intention,{"state":state , "city_name":city },chatId)
        elif user_intention == "Comparison between cities, states, or areas":
            city = aiReponse['Validation Data']['City']
            result = {"user_intention": user_intention, "city": city}
            logging.info(f"Result: {result}")
            return employment_search_algo(user_intention,{"cities":city },chatId)
        else:
            # Handle unknown user intention
            result = {"error": "Unknown user intention"}
            return result
       

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {"error": f"An error occurred: {str(e)}"}
