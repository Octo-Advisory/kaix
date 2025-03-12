from frontend_app.Analytics_module.emplyement_query.employment_search_algorith import employment_search_algo

def handle_employement_query(aiResponse,chatId):
    try:
        user_intention = aiResponse.get('User Intention')
    
        if user_intention == "Individual employment status":
            city = aiResponse['Validation Data']['City'][0]
            state = aiResponse['Validation Data']['State'][0]
            result = {"user_intention": user_intention, "city": city, "state": state}
            return employment_search_algo(user_intention,{"state":state , "city_name":city },chatId)
        elif user_intention == "Comparison between cities, states, or areas":
            city = aiResponse['Validation Data']['City']
            result = {"user_intention": user_intention, "city": city}
            return employment_search_algo(user_intention,{"cities":city },chatId)
        else:
            # Handle unknown user intention
            result = {"error": "Unknown user intention"}
            return result
       
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}