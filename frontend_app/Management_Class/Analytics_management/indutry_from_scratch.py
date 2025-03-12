from frontend_app.Analytics_module.Industry_form_scratch.query_to_build_industry_from_scratch import get_industry,get_subsector,get_segment,integrate_land_calculation,get_list_of_area_id,get_list_of_city_list,get_state_list,get_property_and_employement,get_property_incentive_mapped,transform_dataframes,calculate_property_suitability,calculate_employment_availability_score,get_property_wise_incentive_score,get_property_approval_mapped,get_property_wise_approval_score,get_supply_rule,get_vendor_df,get_supply_scores,calculate_final_supply_mapped_property_scores_with_condition,process_incentive_df_to_send_solution_screen,process_approval_df_to_send_solution_screen,process_supply_vendor_df_to_send_solution_screen,sort_by_scores
import frappe
import pandas as pd
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
import time
import numpy as np
import traceback
from datetime import datetime
import json

@frappe.whitelist()
def industry_from_scratch(aiResponse,chatId):
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
        found_property = True
        found_employment = True
        found_incentive = True
        found_approval = True
        # found_vendor = True
        
        main_industry = aiResponse.get("Main-Industry")
        sub_sector = aiResponse.get("Sub-Sector")
        segment = aiResponse.get("Segment")
        capacity = aiResponse.get("Capacity")
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
        Solution_screen_incentive_lookup_df = process_incentive_df_to_send_solution_screen(property_incentive_mapped_df)

        df_for_property_wise_individual_score, df_for_property_wise_emp_score = transform_dataframes(property_employment_df)
        df_with_property_wise_individual_score = calculate_property_suitability(df_for_property_wise_individual_score)
        df_with_property_wise_individual_score.sort_values(by=["property_suitability_score"], ascending=False)
        final_property_ranking_for_decision = pd.DataFrame({"Property_ID": list(property_employment_df["property_id"].unique())})
        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_individual_score[["property_id","property_suitability_score"]], left_on="Property_ID", right_on="property_id", how='left').drop(columns=["property_id"])
        
        df_with_property_wise_emp_score = calculate_employment_availability_score(df_for_property_wise_emp_score,sub_sector)
        df_with_property_wise_emp_score.sort_values(by=["employment_availability_score"], ascending=False)
        Solution_screen_employment_lookup_df = df_for_property_wise_emp_score[["property_id","Semi-skilled", "Skilled", "Unskilled", "Skill_Type"]]


        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_emp_score[["property_id","employment_availability_score"]], 
         left_on="Property_ID", right_on="property_id", how='left').drop(columns=["property_id"])
        df_with_property_wise_incentive_score = get_property_wise_incentive_score(property_incentive_mapped_df,property_employment_df,found_incentive)
        
        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_incentive_score["Property ID"]))

        uncommon_property_ids_for_sol_incentive = list(set(Solution_screen_incentive_lookup_df["property_id"]) ^ set(df_with_property_wise_incentive_score["Property ID"]))

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        Solution_screen_incentive_lookup_df = Solution_screen_incentive_lookup_df[
            ~Solution_screen_incentive_lookup_df["property_id"].isin(uncommon_property_ids_for_sol_incentive)
        ]

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_incentive_score[["Property ID","Scaled Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Scaled Final Score': 'Property_wise_incentive_score'}, inplace=True)

        property_approval_mapped_df,found_approval = get_property_approval_mapped(main_industry,sub_sector,area_list,city_list,state_list,property_list,found_approval)
        Solution_screen_approval_lookup_df = process_approval_df_to_send_solution_screen(property_approval_mapped_df)
        df_with_property_wise_approval_score = get_property_wise_approval_score(found_approval,property_approval_mapped_df,property_employment_df)
       # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_approval_score["Property ID"]))

        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
        ]

        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids_for_sol_approval = list(set(Solution_screen_approval_lookup_df["property_id"]) ^ set(df_with_property_wise_approval_score["Property ID"]))

        # Step 2: Filter out uncommon properties from Solution_screen_approval_lookup_df
        Solution_screen_approval_lookup_df = Solution_screen_approval_lookup_df[
            ~Solution_screen_approval_lookup_df["property_id"].isin(uncommon_property_ids_for_sol_approval)
        ]

        Solution_screen_approval_lookup_df = pd.merge(Solution_screen_approval_lookup_df, df_with_property_wise_approval_score[["Property ID", "Efficient Approval Time"]], left_on="property_id", right_on="Property ID").drop(columns=["Property ID"])

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_approval_score[["Property ID","Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Final Score': 'Property_wise_approval_score'}, inplace=True)

        supply_rules_df = get_supply_rule(main_industry,sub_sector,segment,capacity)
        with open("log.txt", "a") as file:
            file.write(f"\nsupply_rules_df {supply_rules_df}")
        vendor_df = get_vendor_df(supply_rules_df)

        property_latlong_df = property_employment_df[["property_id", "latitude_longitude"]].drop_duplicates()
        with open("log.txt", "a") as file:
            file.write(f"\nvendor_df {vendor_df}")
        test_return = get_supply_scores(property_latlong_df,supply_rules_df,vendor_df,prefered_range=(0,250), tolerable_range=(251,500))
            
        if len(test_return) == 2:
            property_mapped_supply_individual_score, property_mapped_supply_alternate_sug= test_return[0], test_return[1]
        else:
            property_mapped_supply_individual_score, property_mapped_supply_alternate_sug = test_return, None
        
        df_with_property_wise_vendor_score = calculate_final_supply_mapped_property_scores_with_condition(property_mapped_supply_individual_score, property_latlong_df)

        Solution_screen_essential_supply_vendor_lookup_df, Solution_screen_non_essential_supply_vendor_lookup_df = process_supply_vendor_df_to_send_solution_screen(property_mapped_supply_individual_score)

        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        if (not Solution_screen_essential_supply_vendor_lookup_df.empty) and (not Solution_screen_non_essential_supply_vendor_lookup_df.empty):
            uncommon_property_ids_accross_essential_supply = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
            uncommon_property_ids_accross_non_essential_supply = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
                    # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
            Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
                ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_property_ids_accross_essential_supply)
            ]
            # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
            Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
                ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_property_ids_accross_non_essential_supply)
            ]
        else:
            Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": list(final_property_ranking_for_decision["Property_ID"].unique()),
                "No_of_vendors_found": [0,]*len(final_property_ranking_for_decision)
            })
            Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": list(final_property_ranking_for_decision["Property_ID"].unique()),
                "No_of_vendors_found": [0,]*len(final_property_ranking_for_decision)
            })



        # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        final_property_ranking_for_decision = final_property_ranking_for_decision[
            ~final_property_ranking_for_decision["Property_ID"].isin(uncommon_property_ids)
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
        
        final_property_ranking_for_decision = final_property_ranking_for_decision.sort_values(by=["Aggregate Property Performance Score (APPS)"], ascending=False)

        # Sorting all dataframes based on scores_df order
        Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, final_property_ranking_for_decision)
        Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, final_property_ranking_for_decision)
        Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, final_property_ranking_for_decision)
        Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, final_property_ranking_for_decision)
        Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, final_property_ranking_for_decision)

        Final_analytics_results_query_to_build_industry_from_scratch = {
            "final_scoring_df": final_property_ranking_for_decision.to_json(),
            "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json(),
            "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json(),
            "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json(),
            "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json(),
            "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json()
        }
        time.sleep(2)
        update_process(chatId,"Analyzing Data","Complete")
        update_process(chatId,"Preparing Result","Processing")
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete")
        response = {
                "Analytics_response": Final_analytics_results_query_to_build_industry_from_scratch,
                "Is_Error" : False
            }
        return response
    
    except Exception as e:
        update_process(chatId,"Analyzing Data","Fail")
        error_details = traceback.format_exc()
        log_to_file("main error",str(error_details))
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
    
    with open("log.txt", "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")