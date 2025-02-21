import frappe
import time
from frontend_app.Analytics_module.approval_query.approval_search_query import calculate_efficiency,fetch_area_details,fetch_city_details,fetch_industry_details,fetch_state_details,fetch_sub_sector_details,get_property_approval_data
from frontend_app.Management_Class.helpers.progress import insert_process,update_process

@frappe.whitelist()
def call_approval_query(aiResponse,chatId):
    try:
        # with open("log2.txt", "a") as file:
        #     file.write(f"\naiResponse {aiResponse}")
        insert_process(chatId,"Analyzing Your Query","Analyzing Your query","Pending")
        update_process(chatId,"Analyzing Your Query","Processing")
        insert_process(chatId,"Fetching Data","Fetching Data Based On Your Query","Pending")
        insert_process(chatId,"Analyzing Data","Analyzing Gathered Data","Pending")   
        insert_process(chatId,"Preparing Result","Preparing Result","Pending")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete")
        update_process(chatId,"Fetching Data","Processing")
        time.sleep(4)
        
        Validation_Data = aiResponse.get('Validation Data')
        location_info = Validation_Data.get('Location_info')
        Industry_info = Validation_Data.get('Industry_info')
        given_area = location_info.get('Area')
        given_city = location_info.get('City')
        given_state = location_info.get('State')
        given_main_industry = Industry_info.get('Main-Industry')
        given_sub_sector = Industry_info.get('Sub-Sector')
        update_process(chatId,"Fetching Data","Complete")
        update_process(chatId,"Analyzing Data","Processing")
        time.sleep(4)
        with open("log2.txt", "a") as file:
            file.write(f"\ninformations1 {Validation_Data,}")
            file.write(f"\ninformations2 {location_info,Industry_info}")
            file.write(f"\ninformations3 {given_area, given_city, given_state}")
            file.write(f"\ninformations4 { given_main_industry, given_sub_sector}")

        main_industry = fetch_industry_details(given_main_industry)
        sub_sector_id = fetch_sub_sector_details(given_sub_sector)
        area_id = fetch_area_details(given_area)
        city_id = fetch_city_details(given_city)
        state_id = fetch_state_details(given_state)

        with open("log2.txt", "a") as file:
            file.write(f"\nresults {main_industry,sub_sector_id,area_id,state_id}")
        
        app_df = get_property_approval_data(sub_sector_id, main_industry, area_id, city_id, state_id)
        update_process(chatId,"Analyzing Data","Complete")
        update_process(chatId,"Preparing Result","Processing")
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete")

        final_result = calculate_efficiency(app_df,area_id,city_id,state_id)
        response = {
                "Analytics_response": final_result,
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