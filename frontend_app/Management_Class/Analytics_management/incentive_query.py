import frappe
import json
import time
from datetime import datetime
from frontend_app.Analytics_module.incentive_query.incentive_search_query import incentive_details,get_incentive_data,fetch_industry_details,fetch_city_details,fetch_area_details,fetch_query_results,fetch_state_details,fetch_sub_sector_details
from frontend_app.Management_Class.helpers.progress import insert_process,update_process

@frappe.whitelist()
def call_incentive_query(aiResponse,chatId):
    try:
        insert_process(chatId,"Analyzing Your Query","Analyzing Your query","Pending")
        update_process(chatId,"Analyzing Your Query","Processing")
        insert_process(chatId,"Fetching Data","Fetching Data Based On Your Query","Pending")
        insert_process(chatId,"Analyzing Data","Analyzing Gathered Data","Pending")   
        insert_process(chatId,"Preparing Result","Preparing Result","Pending")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete")
        update_process(chatId,"Fetching Data","Processing")
        time.sleep(4)

        with open("log2.txt", "a") as file:
            file.write(f"\naiResponse {aiResponse}")
        # aiResponse = json.loads(aiResponse)
        state = aiResponse.get('State')
        given_area = state.get('Area')
        given_city = state.get('City')
        given_state = state.get('State')
        given_main_industry = state.get('Main-Industry')
        given_sub_sector = state.get('Sub-Sector')
        update_process(chatId,"Fetching Data","Complete")
        update_process(chatId,"Analyzing Data","Processing")
        time.sleep(2)
        main_industry = fetch_industry_details(given_main_industry)
        sub_sector = fetch_sub_sector_details(given_sub_sector)
        area = fetch_area_details(given_area)
        city = fetch_city_details(given_city)
        State = fetch_state_details(given_state)
        today_date = datetime.now().strftime('%Y-%m-%d 00:00:00')
 
        Incentive_only_df = get_incentive_data(sub_sector,main_industry,area,city,State,today_date)
        incentive_detail = incentive_details(Incentive_only_df,area,city,State)
        update_process(chatId,"Analyzing Data","Complete")
        update_process(chatId,"Preparing Result","Processing")
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete")
        response = {
                "Analytics_response": incentive_detail,
                "Is_Error" : False
            }
        return response
    except Exception as e:
        update_process(chatId,"Analyzing Data","Fail")
        response = {
                "Analytics_response": f"Error From Analytics :- {e}",
                "Is_Error" : True
            }
        return response


    