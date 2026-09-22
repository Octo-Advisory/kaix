from kaix.Analytics_module.emplyement_query.employment_search_algorith import employment_search_algo
import frappe
import time
import json
import datetime

def log_to_file(key,value):
    """
    Logs key-value data to a file with a timestamp.
    
    :param filename: Name of the log file.
    :param data: Key-value pairs to log.
    """
    log_entry = {
        "t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f"{key}" : value
    }
    
    with open("log2.txt", "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")

def handle_employement_query(aiResponse,chatId):
    try:
        user_intention = aiResponse.get('User Intention')
        keyword_given_by_user = aiResponse.get('KEYWORDS')
        if user_intention == "Individual employment status":
            city = aiResponse['Validation Data']['City'][0]
            with open("log.txt", "a") as file:
                file.write(f"\n I am here at this intention: -> keyword_given_by_user {user_intention}")
            state = aiResponse['Validation Data']['State'][0]
            result = {"user_intention": user_intention, "city": city, "state": state}
            return employment_search_algo(user_intention,{"state":state , "city_name":city },chatId,keyword_given_by_user)
        elif user_intention == "Comparison between cities, states, or areas":
            city = aiResponse['Validation Data']['City']
            result = {"user_intention": user_intention, "city": city}
            return employment_search_algo(user_intention,{"cities":city },chatId,keyword_given_by_user)
        else:
            # Handle unknown user intention
            result = {"error": "Unknown user intention"}
            return result
       
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}