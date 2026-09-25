import frappe
import time
from datetime import datetime
from kaix.Analytics_module.incentive_query.incentive_search_query import incentive_details,get_incentive_data,fetch_industry_details,fetch_city_details,fetch_area_details,fetch_query_results,fetch_state_details,fetch_sub_sector_details
from kaix.Management_Class.helpers.progress import insert_process,update_process
import traceback
from kaix.Management_Class.helpers.utility import randomSentences

@frappe.whitelist()
def call_incentive_query(aiResponse,chatId):
    try:
        analyse_query = randomSentences('incentives', 'Analyzing Your Query')
        fetch_data = randomSentences('incentives', 'Fetching Data')
        analyse_data = randomSentences('incentives', 'Analyzing Data')
        prepare_result = randomSentences('incentives', 'Preparing Results')

        insert_process(chatId,"Analyzing Your Query",analyse_query,"Pending")
        update_process(chatId,"Analyzing Your Query","Processing",0)
        insert_process(chatId,"Fetching Data",fetch_data,"Pending")
        insert_process(chatId,"Analyzing Data",analyse_data,"Pending")   
        insert_process(chatId,"Preparing Result",prepare_result,"Pending")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete",1)
        update_process(chatId,"Fetching Data","Processing",0)
        # time.sleep(4)

        with open("log2.txt", "a") as file:
            file.write(f"\naiResponse {aiResponse}")
        # aiResponse = json.loads(aiResponse)
        state = aiResponse.get('State')
        given_area = state.get('Area')
        given_city = state.get('City')
        given_state = state.get('State')
        keywords = state.get('KEYWORDS')
        given_main_industry = state.get('Main-Industry')
        given_sub_sector = state.get('Sub-Sector')
        update_process(chatId,"Fetching Data","Complete",1)
        update_process(chatId,"Analyzing Data","Processing",0)
        time.sleep(2)
        main_industry = fetch_industry_details(given_main_industry)
        sub_sector = fetch_sub_sector_details(given_sub_sector)
        area = fetch_area_details(given_area)
        city = fetch_city_details(given_city)
        State = fetch_state_details(given_state)
        today_date = datetime.now().strftime('%Y-%m-%d 00:00:00')
 
        Incentive_only_df = get_incentive_data(sub_sector,main_industry,area,city,State,today_date)
        columns_to_drop = [
       'Incentive Start Date', 'Incentive End Date', 'sub_sector_id',
       'city_level', 'state_level', 'country_level', 'pan_industries'
        ]
        incentive_keyword_df =  Incentive_only_df.drop(columns=columns_to_drop)
        incentive_keyword_df.rename(columns={"incentive_id":"ID"}, inplace=True)
        incentive_keyword_df["Incentive_name"] = incentive_keyword_df["Incentive_name"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        incentive_keyword_df["Incentive Type"] = incentive_keyword_df["Incentive Type"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        incentive_keyword_df["Incentive Details"] = incentive_keyword_df["Incentive Details"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        incentive_detail = incentive_details(Incentive_only_df,area,city,State,keyword_given_by_user= keywords, incentive_keyword_df = incentive_keyword_df)
        time.sleep(2)    
        update_process(chatId,"Analyzing Data","Complete",1)
        update_process(chatId,"Preparing Result","Processing",0)
        time.sleep(3)
        update_process(chatId,"Preparing Result","Complete",1)
        response = {
                "Analytics_response": incentive_detail,
                "Is_Error" : False
            }
        return response
    except Exception as e:
        update_process(chatId,"Analyzing Data","Fail",0)
        response = {
                "Analytics_response": f"Error From Analytics :- {e}",
                "Is_Error" : True
            }
        return response


    