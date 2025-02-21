from frontend_app.Analytics_module.Industry_form_scratch.query_to_build_industry_from_scratch import get_industry,get_subsector,get_segment,integrate_land_calculation,get_list_of_area_id,get_list_of_city_list,get_state_list,get_property_and_employement,get_property_incentive_mapped,transform_dataframes,calculate_property_suitability,calculate_employment_availability_score,get_property_wise_incentive_score,get_property_approval_mapped,get_property_wise_approval_score,get_supply_rule,get_vendor_df,get_supply_scores,calculate_final_supply_mapped_property_scores_with_condition
import frappe
import pandas as pd
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
import time
import numpy as np

def industry_from_scratch(aiResponse,chatId):
    try:
        insert_process(chatId,"Analyzing Your Query","Analyzing Your query","Pending")
        insert_process(chatId,"Fetching Data","Fetching Data Based On Your Query","Pending")
        insert_process(chatId,"Analyzing Data","Analyzing Gathered Data","Pending")   
        insert_process(chatId,"Preparing Result","Preparing Result","Pending")

        update_process(chatId,"Analyzing Your Query","Processing")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete")
        update_process(chatId,"Fetching Data","Processing")
        time.sleep(4)
        found_property = True
        found_employment = True
        found_incentive = True
        found_approval = True
        found_vendor = True

        # AI Response
        aiResponse= {'Main-Industry': 'chemical', 'Sub-Sector': 'Pharma and Biotechnology Chemical','Segment':None, 'Capacity': 30000, 'Capacity Unit': None, 
        'Time Period': None, 'Product': None,'product_attempt_count':0,'capacity_attempt_count':0}
        
        main_industry = aiResponse.get("Main-Industry")
        sub_sector = aiResponse.get("Sub-Sector")
        segment = aiResponse.get("Segment")
        capacity = aiResponse.get("Capacity")
        # capacity_unit = aiResponse.get("Capacity Unit")
        # time_period = aiResponse.get("Time Period")
        # product = aiResponse.get("Product")
        update_process(chatId,"Fetching Data","Complete")

        update_process(chatId,"Analyzing Data","Processing")
        industry = get_industry(main_industry)
        sub_sector,zone_id = get_subsector(sub_sector)
        segment = get_segment(segment)
        # min_land ,max_land = get_land_requirements(industry,sub_sector,segment,capacity)
        result = integrate_land_calculation(capacity,industry,sub_sector,segment)
        required_exact_land_by_user, required_LowerMargin_land_for_user, required_UpperMargin_land_for_user = result["Land_size"], result["Lower_limit_land_size"], result["Upper_limit_land_size"]
        area_list = get_list_of_area_id(zone_id)
        city_list = get_list_of_city_list(area_list)
        state_list = get_state_list(city_list)
        property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment)
        # Incentive_only_df = get_incentive(sub_sector,main_industry,area_list,city_list,state_list)
        property_incentive_mapped_df,found_incentive = get_property_incentive_mapped(industry,sub_sector,area_list,city_list,state_list,property_list,found_incentive)
        df_for_property_wise_individual_score, df_for_property_wise_emp_score = transform_dataframes(property_employment_df)
        df_with_property_wise_individual_score = calculate_property_suitability(df_for_property_wise_individual_score)
        df_with_property_wise_individual_score.sort_values(by=["property_suitability_score"], ascending=False)
        final_property_ranking_for_decision = pd.DataFrame({"Property_ID": list(property_employment_df["property_id"].unique())})
        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_individual_score[["property_id","property_suitability_score"]], left_on="Property_ID", right_on="property_id", how='left').drop(columns=["property_id"])
        
        df_with_property_wise_emp_score = calculate_employment_availability_score(df_for_property_wise_emp_score,sub_sector)
        df_with_property_wise_emp_score.sort_values(by=["employment_availability_score"], ascending=False)


        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_emp_score[["property_id","employment_availability_score","Skill_Type"]], 
         left_on="Property_ID", right_on="property_id", how='left').drop(columns=["property_id"])
        df_with_property_wise_incentive_score = get_property_wise_incentive_score(property_incentive_mapped_df,property_employment_df,found_incentive)

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_incentive_score[["Property ID","Scaled Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Scaled Final Score': 'Property_wise_incentive_score'}, inplace=True)

        property_approval_mapped_df,found_approval = get_property_approval_mapped(main_industry,sub_sector,area_list,city_list,state_list,property_list,found_approval)
        df_with_property_wise_approval_score = get_property_wise_approval_score(found_approval,property_approval_mapped_df,property_employment_df)
        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_approval_score["Property ID"]))

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_approval_score[["Property ID","Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Final Score': 'Property_wise_approval_score'}, inplace=True)

        supply_rules_df = get_supply_rule(main_industry,sub_sector,segment,capacity)
        vendor_df = get_vendor_df(supply_rules_df)
        # vendor_latlong_df = vendor_df[["vendor_id", "latitude_longitude"]].drop_duplicates()
        # columns_to_convert = ["vendor_supply_capacity", "years_of_experience", "no_of_past_clients", "no_of_locations", "no_of_servieces", "no_of_employees"]
        # vendor_df[columns_to_convert] = vendor_df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

        property_latlong_df = property_employment_df[["property_id", "latitude_longitude"]].drop_duplicates()
    
        test_return = get_supply_scores(property_latlong_df,supply_rules_df,vendor_df,prefered_range=(0,250), tolerable_range=(251,500))

        essential_supply_to_show = np.random.choice(list(test_return[test_return["essential"]]["supply_id"].unique()), 5)

        filtered_data = test_return[test_return["supply_id"].isin(essential_supply_to_show)]
 
        # Group by property_id and aggregate supply_id and Distance into arrays
        supply_data_to_show_df = filtered_data.groupby("property_id").agg(
            supply_ids=('supply_id', list),
            distances=('Distance', list)
        ).reset_index()
        
        supply_data_to_show_df.rename(columns= {"distances": "property_supply_distance", "supply_ids": "Supply"}, inplace=True)
            
        if len(test_return) == 2:
            property_mapped_supply_individual_score, property_mapped_supply_alternate_sug= test_return[0], test_return[1]
        else:
            property_mapped_supply_individual_score, property_mapped_supply_alternate_sug = test_return, None
        
        df_with_property_wise_vendor_score = calculate_final_supply_mapped_property_scores_with_condition(property_mapped_supply_individual_score, property_latlong_df)

        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        uncommon_property_ids_accross_supply = list(set(supply_data_to_show_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))

        supply_data_to_show_df = supply_data_to_show_df[
            ~supply_data_to_show_df["property_id"].isin(uncommon_property_ids_accross_supply)
        ]
        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]


        # Step 3: Perform Merging
        final_property_ranking_for_decision = pd.merge(
            final_property_ranking_for_decision,
            df_with_property_wise_vendor_score[["property_id", "final_score"]],
            left_on="Property_ID", right_on="property_id", 
            how='left'
        ).drop(columns=["property_id"])

        # Step 4: Rename Columns
        final_property_ranking_for_decision.rename(columns={
            "final_score": "Property-Wise Vendor Score (PWVS)", 
            "employment_availability_score": "Property-Wise Employment Score (PWES)",
            "Property_wise_incentive_score": "Property-Wise Incentive Score (PWIS)",
            "Property_wise_approval_score": "Property-Wise Approval Score (PWAS)",
            "property_suitability_score": "Property-Wise Suitability Score (PWSS)"
        }, inplace=True)
        
        preference = {
            "Property-Wise Vendor Score (PWVS)":5,
            "Property-Wise Employment Score (PWES)":4,
            "Property-Wise Suitability Score (PWSS)":3,
            "Property-Wise Incentive Score (PWIS)":2,
            "Property-Wise Approval Score (PWAS)":2,
        }
        final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"] = (preference["Property-Wise Vendor Score (PWVS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Vendor Score (PWVS)"]) + (preference["Property-Wise Employment Score (PWES)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Employment Score (PWES)"]) + (preference["Property-Wise Suitability Score (PWSS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Suitability Score (PWSS)"]) + (preference["Property-Wise Approval Score (PWAS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Approval Score (PWAS)"]) + (preference["Property-Wise Incentive Score (PWIS)"] / sum(preference.values())*final_property_ranking_for_decision["Property-Wise Incentive Score (PWIS)"])
        
        final_property_ranking_for_decision = pd.merge(
            final_property_ranking_for_decision,
            supply_data_to_show_df,
            left_on="Property_ID", right_on="property_id",
            how='left'
        ).drop(columns=["property_id"])

        final_property_ranking_for_decision = final_property_ranking_for_decision.sort_values(by=["Aggregate Property Performance Score (APPS)"], ascending=False)

        # final_property_ranking_for_decision_agg_score = final_property_ranking_for_decision[["Property_ID","Aggregate Property Performance Score (APPS)"]]
        # return industry,sub_sector,zone_id,segment,min_land ,max_land,required_exact_land_by_user, required_LowerMargin_land_for_user, required_UpperMargin_land_for_user,area_list,city_list,state_list,property_list,incentive,property_incentive,df_for_property_wise_individual_score, df_for_property_wise_emp_score,df_with_property_wise_individual_score
        # json_data = final_property_ranking_for_decision_agg_score.to_json()
        json_data = final_property_ranking_for_decision.to_json(orient="index")
        update_process(chatId,"Analyzing Data","Complete")
        update_process(chatId,"Preparing Result","Processing")
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete")
        response = {
                "Analytics_response": json_data,
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