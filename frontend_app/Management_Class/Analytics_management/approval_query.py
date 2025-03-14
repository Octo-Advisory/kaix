import frappe
import time
from frontend_app.Analytics_module.approval_query.approval_search_query import *
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
import traceback
import json

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
        Keywords = Validation_Data.get('KEYWORDS')
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
        columns_to_drop = [
            'Time Taken', 'is_dependent', 'dependent_approval_ids',
            'area_id', 'city_id', 'city_level', 'state', 'state_level',
            'country_level', 'sub_sector', 'industry', 'pan_industries'
        ]

        approval_keyword_df =  app_df.drop(columns=columns_to_drop) 
        approval_keyword_df.rename(columns = {"approval_id": "ID"}, inplace=True)
        approval_keyword_df["Tree Cutting"] = approval_keyword_df["Tree Cutting"].apply(lambda x: "Tree Cutting" if x == "Yes" else "None")
        approval_keyword_df["Road Cutting"] = approval_keyword_df["Road Cutting"].apply(lambda x: "Road Cutting" if x == "Yes" else "None")
        approval_keyword_df["Pole Shifting"] = approval_keyword_df["Pole Shifting"].apply(lambda x: "Pole Shifting" if x == "Yes" else "None")
        approval_keyword_df["Government Department"] = approval_keyword_df["Government Department"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        approval_keyword_df["Business_location"] = approval_keyword_df["Business_location"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        approval_keyword_df["Land_type"] = approval_keyword_df["Land_type"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        approval_keyword_df["Vicinity_detail"] = approval_keyword_df["Vicinity_detail"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        approval_keyword_df["Cross_following"] = approval_keyword_df["Cross_following"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        approval_keyword_df["online_or_offline"] = approval_keyword_df["online_or_offline"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        approval_keyword_df["stages"] = approval_keyword_df["stages"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        update_process(chatId,"Analyzing Data","Complete")
        update_process(chatId,"Preparing Result","Processing")
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete")

        final_result = calculate_efficiency(app_df,area_id,city_id,state_id, keyword_given_by_user= Keywords, approval_keyword_df = approval_keyword_df)
        response = {
                "Analytics_response": final_result,
                "Is_Error" : False
            }
        return response
    except Exception as e:
        error_details = traceback.format_exc()
        log_to_file("error details",error_details)
        update_process(chatId,"Analyzing Data","Fail")
        response = {
                "Analytics_response": f"Error From Analytics :- {e}",
                "Is_Error" : True
            }
        return response

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