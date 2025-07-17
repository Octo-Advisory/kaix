import frappe
import time
import json
import pandas as pd
from frontend_app.Analytics_module.vendor_search.vendor_search_query import fetch_supply_data,vendor_df,get_supply_scores
import traceback
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
from frontend_app.Management_Class.helpers.utility import randomSentences

def call_vendor_query(aiResponse,chatId,validationResult):
    try:
        with open("log.txt", "a") as file:
            file.write(f"\nvalidationResult1 {validationResult} for now the latitude and longitude value are set static for any false scenarios (can be changed in vendor_validation.py location_and_supply() and location_and_industry())")
        # Validation Result from validation

        analyse_query = randomSentences('vendors', 'Analyzing Your Query')
        fetch_data = randomSentences('vendors', 'Fetching Data')
        analyse_data = randomSentences('vendors', 'Analyzing Data')
        prepare_result = randomSentences('vendors', 'Preparing Results')

        insert_process(chatId,"Analyzing Your Query",analyse_query,"Pending")
        update_process(chatId,"Analyzing Your Query","Processing",0)
        insert_process(chatId,"Fetching Data",fetch_data,"Pending")
        insert_process(chatId,"Analyzing Data",analyse_data,"Pending")   
        insert_process(chatId,"Preparing Result",prepare_result,"Pending")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete",1)
        update_process(chatId,"Fetching Data","Processing",0)
        time.sleep(4)
        validationResult = json.loads(validationResult)
        validationResult = validationResult[0][1]
        with open("log.txt", "a") as file:
            file.write(f"\nvalidationResult2 {validationResult} for now the latitude and longitude value are set static for any false scenarios (can be changed in vendor_validation.py location_and_supply() and location_and_industry())")
        Validation_Data = aiResponse.get('Validation Data')
        Industry_info = Validation_Data.get('Industry_info')
        Location_info = Validation_Data.get('Location_info')
        Supply_info = Validation_Data.get('Supply_info')
        keyword_given_by_user = Validation_Data.get('KEYWORDS')

        main_industry = Industry_info.get('Main-Industry')
        Supplies = Supply_info.get('Supplies')
        segment = Industry_info.get('Segment')
        sub_sector = Industry_info.get('Sub-Sector')
        property_id = Location_info.get('Location')
        # Fetch Lat_long  from validation result
        # location_check = validationResult.get('location_check')
        latitude_longitude = validationResult.get('latitude_longitude')
        latitude_longitude = [latitude_longitude]
        update_process(chatId,"Fetching Data","Complete",1)
        update_process(chatId,"Analyzing Data","Processing",0)
        time.sleep(4)
        with open("log.txt", "a") as file:
            file.write(f"\nlatitude_longitude {latitude_longitude} for now the latitude and longitude value are set static for any false scenarios (can be changed in vendor_validation.py location_and_supply() and location_and_industry())")
        results = fetch_supply_data(main_industry,sub_sector,segment,Supplies)
        with open("log.txt", "a") as file:
            file.write(f"\n Checking New Error Results..... {results} {main_industry} {sub_sector} {segment} {Supplies}")
        if results:
            supply_rules_df = pd.DataFrame(results, columns=['supply_id', 'essential_items'])
        else:
            None

        all_supply_id_list = list(supply_rules_df["supply_id"].values)
        supply_id_str = ', '.join(f"'{supply_id}'" for supply_id in all_supply_id_list)

        get_vendor_df = vendor_df(supply_id_str)
        with open("log.txt", "a") as file:
            file.write(f"\n Checking New Error DROP..... {supply_id_str} {get_vendor_df.columns}")
        columns_to_drop = [
            'supply_id', 'vendor_supply_capacity',
            'years_of_experience', 'no_of_locations', 'no_of_past_clients',
            'no_of_servieces', 'no_of_employees', 'latitude_longitude'
        ]

        vendor_keyword_df =  get_vendor_df.drop(columns=columns_to_drop)

        vendor_keyword_df["vendor_name"] = vendor_keyword_df["vendor_name"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        vendor_keyword_df["Certifications"] = vendor_keyword_df["Certifications"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        vendor_keyword_df["Description"] = vendor_keyword_df["Description"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)

        vendor_keyword_df = vendor_keyword_df.rename(columns= {'vendor_id':'ID'})

        columns_to_convert = ["vendor_supply_capacity", "years_of_experience", "no_of_past_clients", "no_of_locations", "no_of_servieces", "no_of_employees"]
        get_vendor_df[columns_to_convert] = get_vendor_df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

        location_latlong_data = {'property_id':property_id,"latitude_longitude":latitude_longitude}

        property_latlong_df = pd.DataFrame(location_latlong_data)
    
        combined_data = get_supply_scores(property_latlong_df, supply_rules_df, get_vendor_df, prefered_range=(0,250), tolerable_range=(251,500),keyword_given_by_user=keyword_given_by_user,vendor_keyword_df=vendor_keyword_df)
       
        response = {
                "Analytics_response": combined_data,
                "Is_Error" : False,
                "latitude_longitude" : latitude_longitude or []
            }
        time.sleep(1)
        update_process(chatId,"Analyzing Data","Complete",1)
        update_process(chatId,"Preparing Result","Processing",0)
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete",1)
        return response
    except Exception as e:
        error_message = traceback.format_exc()
        with open("log.txt", "a") as file:
            file.write(f"\nerror_message {error_message}")
        response = {
                "Analytics_response": e,
                "Is_Error" : True,
                "latitude_longitude" : latitude_longitude or []
            }
        update_process(chatId,"Analyzing Data","Fail",0)
        return response