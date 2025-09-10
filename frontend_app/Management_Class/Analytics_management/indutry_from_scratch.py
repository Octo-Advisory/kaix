from frontend_app.Analytics_module.Industry_form_scratch.query_to_build_industry_from_scratch import *
import frappe
import pandas as pd
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
import time
import numpy as np
import traceback
from datetime import datetime
import json
from frontend_app.Management_Class.helpers.utility import randomSentences
import gc
from frontend_app.Market_Trends.getting_market_trends import retrieving_market_trends

@frappe.whitelist()
def industry_from_scratch(aiResponse,chatId,selectedOption):
    try:
        analyse_query = randomSentences('industry', 'Analyzing Your Query')
        fetch_data = randomSentences('industry', 'Fetching Data')
        analyse_data = randomSentences('industry', 'Analyzing Data')
        prepare_result = randomSentences('industry', 'Preparing Results')

        insert_process(chatId,"Analyzing Your Query",analyse_query,"Pending")
        update_process(chatId,"Analyzing Your Query","Processing",0)
        insert_process(chatId,"Fetching Data",fetch_data,"Pending")
        insert_process(chatId,"Analyzing Data",analyse_data,"Pending")   
        insert_process(chatId,"Preparing Result",prepare_result,"Pending")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete",1)
        update_process(chatId,"Fetching Data","Processing",0)
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
        keyword_given_by_user = aiResponse.get("KEYWORDS")
        log_to_file("keyword_given_by_user",keyword_given_by_user)
        update_process(chatId,"Fetching Data","Complete",1)

        update_process(chatId,"Analyzing Data","Processing",0)
        industry = get_industry(main_industry)
        sub_sector,zone_id = get_subsector(sub_sector)
        segment = get_segment(segment)
        with open("log2.txt", "a") as file:
            file.write(f"\n Industry, Sub-sector, Segment:::>>>:::>>>:::>>> {industry},{sub_sector}, {segment}, Zone: {zone_id}")
        # min_land ,max_land = get_land_requirements(industry,sub_sector,segment,capacity)
        result = integrate_land_calculation(capacity,industry,sub_sector,segment)
        required_exact_land_by_user, required_LowerMargin_land_for_user, required_UpperMargin_land_for_user = result["Land_size"], result["Lower_limit_land_size"], result["Upper_limit_land_size"]
        area_list = get_list_of_area_id(zone_id)
        city_list = get_list_of_city_list(area_list)
        state_list = get_state_list(city_list)
        with open("log2.txt", "a") as file:
            file.write(f"\n Unique list of areas cities state:::>>>:::>>>:::>>> {area_list},{city_list}, {state_list}")
        property_employment_df,property_list = get_property_and_employement(zone_id,area_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment,selectedOption = selectedOption)
        with open("log2.txt", "a") as file:
            file.write(f"\n PROPERTY DATAAA:::>>>:::>>>:::>>> {property_employment_df.to_string(index=False)}")
        r_insights = {}
        for state in state_list:
            _, r_insights_dict = retrieving_market_trends(industry, industry, industry, state, state, "pan_industry", "pan_state") 
            filtered_data = {
                "market_trends": r_insights_dict.get("market_trends", None),
                "local_laws": r_insights_dict.get("local_laws", None),
                "taxes": r_insights_dict.get("taxes", None)
            }
            r_insights[state] = filtered_data

        with open("log2.txt", "a") as file:
            file.write(f"\n Regulatory Insights Data Final version ][[][][][]] {r_insights}")
        # Convert dictionary to DataFrame for merging
        market_info_df = pd.DataFrame.from_dict(r_insights, orient='index').reset_index()
        market_info_df.rename(columns={'index': 'state'}, inplace=True)
        # Merge on the 'state' column
        property_employment_df = property_employment_df.merge(market_info_df, on='state', how='left')

        columns_to_drop = [
            'distance_from_nearest_railway_station',
            'distance_from_nearest_seaport', 'distance_from_power_source',
            'latitude_longitude', 'road_connectivity',
            'distance_from_nearest_airport', 'employment_area_id',
            'employmenttype_id', 'availability'
        ]
        propert_keyword_df =  property_employment_df.drop(columns=columns_to_drop)
        propert_keyword_df["tree_cutting_involved"] = propert_keyword_df["tree_cutting_involved"].apply(lambda x: "Tree Cutting" if x == "Yes" else "None")
        propert_keyword_df["road_cutting_involved"] = propert_keyword_df["road_cutting_involved"].apply(lambda x: "Road Cutting" if x == "Yes" else "None")
        propert_keyword_df["pole_shifting"] = propert_keyword_df["pole_shifting"].apply(lambda x: "Pole Shifting" if x == "Yes" else "None")
        propert_keyword_df["business_location_type"] = propert_keyword_df["business_location_type"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        propert_keyword_df["land_type"] = propert_keyword_df["land_type"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        propert_keyword_df["vicinity_of"] = propert_keyword_df["vicinity_of"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)
        propert_keyword_df["Cross_the_following"] = propert_keyword_df["Cross_the_following"].apply(lambda x: "None" if str(x).strip() in ["", "None", "No", "Null"] else x)

        propert_keyword_df = propert_keyword_df.rename(columns= {'property_id':'ID'})

        propert_keyword_df.drop_duplicates(subset=["ID"], inplace=True)

        # Incentive_only_df = get_incentive(sub_sector,main_industry,area_list,city_list,state_list)
        property_incentive_mapped_df,found_incentive = get_property_incentive_mapped(industry,sub_sector,area_list,city_list,state_list,property_list,found_incentive)
        Solution_screen_incentive_lookup_df = process_incentive_df_to_send_solution_screen(property_incentive_mapped_df)

        df_for_property_wise_individual_score, df_for_property_wise_emp_score = transform_dataframes(property_employment_df)
        df_with_property_wise_individual_score = calculate_property_suitability(df_for_property_wise_individual_score,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user)
        df_with_property_wise_individual_score.sort_values(by=["property_suitability_score"], ascending=False)
        final_property_ranking_for_decision = pd.DataFrame({"Property_ID": list(property_employment_df["property_id"].unique())})
        cols = ["property_id", "Network Connectivity", "taxes", "local_laws", "market_trends"]

        right = (
            property_employment_df[cols]
            .drop_duplicates(subset=["property_id"])  # <-- key change
        )

        final_property_ranking_for_decision = (
            pd.merge(
                final_property_ranking_for_decision,
                right,
                left_on="Property_ID",
                right_on="property_id",
                how="left",
            )
            .drop(columns=["property_id"])
        )

        with open("log2.txt", "a") as file:
            file.write(f"\n DF WITH SCORES AND MARKET TRENDsssssssssssssssssssssssssssssssS {final_property_ranking_for_decision}")
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

        Solution_screen_approval_lookup_df = pd.merge(Solution_screen_approval_lookup_df, df_with_property_wise_approval_score[["Property ID", "Efficient Approval Time","Online Percentage","Pre-Requisite","Pre-Establishment","Pre-Operation","Others","Mode_Pre-Requisite","Mode_Pre-Establishment","Mode_Pre-Operation","Mode_Others"]], left_on="property_id", right_on="Property ID").drop(columns=["Property ID"])

        final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, df_with_property_wise_approval_score[["Property ID","Final Score"]], 
         left_on="Property_ID", right_on="Property ID", how='left').drop(columns=["Property ID"])
        final_property_ranking_for_decision.rename(columns={'Final Score': 'Property_wise_approval_score'}, inplace=True)

        supply_rules_df = get_supply_rule(main_industry,sub_sector,segment,capacity)
        with open("log2.txt", "a") as file:
            file.write(f"\n Checking Supplies DF  {supply_rules_df}")
        vendor_df = get_vendor_df(supply_rules_df)
        with open("log2.txt", "a") as file:
            file.write(f"\n Checking Vendor DF  {vendor_df}")
   

        property_latlong_df = property_employment_df[["property_id", "latitude_longitude"]].drop_duplicates()
        test_return = get_supply_scores(property_latlong_df,supply_rules_df,vendor_df,prefered_range=(0,250), tolerable_range=(251,500))
        # if len(test_return) == 2:
        #     property_mapped_supply_individual_score, property_mapped_supply_alternate_sug= test_return[0], test_return[1]
        # else:
        #     property_mapped_supply_individual_score, property_mapped_supply_alternate_sug = test_return, None

        property_mapped_supply_individual_score, property_mapped_supply_alternate_sug, property_wise_all_vendor_df= test_return[0], test_return[1], test_return[2]
        
        df_with_property_wise_vendor_score = calculate_final_supply_mapped_property_scores_with_condition(property_mapped_supply_individual_score, property_latlong_df)

        Solution_screen_essential_supply_vendor_lookup_df, Solution_screen_non_essential_supply_vendor_lookup_df = process_supply_vendor_df_to_send_solution_screen(property_mapped_supply_individual_score)
        Solution_screen_essential_supply_all_vendor_lookup_df, Solution_screen_non_essential_supply_all_vendor_lookup_df = process_supply_vendor_df_to_send_solution_screen(property_wise_all_vendor_df, all_vendor=True)
        # Step 1: Identify Uncommon Property IDs
        uncommon_property_ids = list(set(final_property_ranking_for_decision["Property_ID"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        # if (not Solution_screen_essential_supply_vendor_lookup_df.empty) and (not Solution_screen_non_essential_supply_vendor_lookup_df.empty):
        #     uncommon_property_ids_accross_essential_supply = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        #     uncommon_property_ids_accross_non_essential_supply = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ set(df_with_property_wise_vendor_score["property_id"]))
        #             # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        #     Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
        #         ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_property_ids_accross_essential_supply)
        #     ]
        #     # Step 2: Filter out uncommon properties from final_property_ranking_for_decision
        #     Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
        #         ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_property_ids_accross_non_essential_supply)
        #     ]
        # else:
        #     Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
        #         "property_id": list(final_property_ranking_for_decision["Property_ID"].unique()),
        #         "No_of_vendors_found": [0,]*len(final_property_ranking_for_decision)
        #     })
        #     Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
        #         "property_id": list(final_property_ranking_for_decision["Property_ID"].unique()),
        #         "No_of_vendors_found": [0,]*len(final_property_ranking_for_decision)
        #     })

        # Step 0: Get the reference property IDs
        reference_property_ids = set(df_with_property_wise_vendor_score["property_id"])
        final_property_ids = list(final_property_ranking_for_decision["Property_ID"].unique())

        # Case 1: Both DataFrames are non-empty
        if (not Solution_screen_essential_supply_vendor_lookup_df.empty) and (not Solution_screen_non_essential_supply_vendor_lookup_df.empty):
            
            uncommon_essential = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            uncommon_non_essential = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            
            Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
                ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_essential)
            ]
            Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
                ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_non_essential)
            ]

        # Case 2: Essential is empty, Non-essential is not
        elif Solution_screen_essential_supply_vendor_lookup_df.empty and not Solution_screen_non_essential_supply_vendor_lookup_df.empty:
            
            uncommon_non_essential = list(set(Solution_screen_non_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            Solution_screen_non_essential_supply_vendor_lookup_df = Solution_screen_non_essential_supply_vendor_lookup_df[
                ~Solution_screen_non_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_non_essential)
            ]
            
            Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })

        # Case 3: Non-essential is empty, Essential is not
        elif not Solution_screen_essential_supply_vendor_lookup_df.empty and Solution_screen_non_essential_supply_vendor_lookup_df.empty:
            
            uncommon_essential = list(set(Solution_screen_essential_supply_vendor_lookup_df["property_id"]) ^ reference_property_ids)
            Solution_screen_essential_supply_vendor_lookup_df = Solution_screen_essential_supply_vendor_lookup_df[
                ~Solution_screen_essential_supply_vendor_lookup_df["property_id"].isin(uncommon_essential)
            ]
            
            Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })

        # Case 4: Both are empty
        else:
            Solution_screen_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
            })
            Solution_screen_non_essential_supply_vendor_lookup_df = pd.DataFrame({
                "property_id": final_property_ids,
                "No_of_vendors_found": [0] * len(final_property_ids)
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
        Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision)
        Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, final_property_ranking_for_decision)
        Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision)
        if not keyword_given_by_user:
            Final_analytics_results_query_to_build_industry_from_scratch = {
                # "Filtered_final_property_ranking_for_decision" : None,
                # "Filtererd_Solution_screen_employment_lookup_df" : None,
                # "Filtererd_Solution_screen_incentive_lookup_df" : None,
                # "Filtererd_Solution_screen_approval_lookup_df" : None,
                # "Filtererd_Solution_screen_essential_supply_vendor_lookup_df" : None,
                # "Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df" : None,

                # "Unfiltered_final_property_ranking_for_decision" : final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                # "Unfiltered_Solution_screen_employment_lookup_df" : Solution_screen_employment_lookup_df.to_json() if not  Solution_screen_employment_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_incentive_lookup_df" : Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None ,
                # "Unfiltered_Solution_screen_approval_lookup_df" : Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_essential_supply_vendor_lookup_df" : Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df" : Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,


                "final_scoring_df": final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json() if not Solution_screen_employment_lookup_df.empty else None,
                "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None,
                "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                "Essential_supply_all_vendor_lookup_df": Solution_screen_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_all_vendor_lookup_df.empty else None,
                "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,
                "Non_essential_supply_all_vendor_lookup_df": Solution_screen_non_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_all_vendor_lookup_df.empty else None
            }
        else:
            keyword_result = filter_df_by_keywords(keyword_given_by_user, propert_keyword_df)
            filtered_keyword_df, unfiltered_keyword_df = keyword_result[0], keyword_result[1]
            if len(filtered_keyword_df) != 0:

                Filtered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, filtered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                Unfiltered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, unfiltered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["Aggregate Property Performance Score (APPS)"], ascending=False)
                final_property_ranking_for_decision = pd.concat([Filtered_final_property_ranking_for_decision,Unfiltered_final_property_ranking_for_decision], axis = 0, ignore_index=True)
                final_property_ranking_for_decision["aggregated_score"] = (0.3 * final_property_ranking_for_decision["aggregated_score"]) + (0.7 * final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"])
                final_property_ranking_for_decision = final_property_ranking_for_decision.sort_values(by=["aggregated_score"], ascending=False) 
                
                Filtererd_Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                Filtererd_Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, Filtered_final_property_ranking_for_decision, for_final_return=True)
                
                Unfiltered_Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                
                Solution_screen_employment_lookup_df = pd.concat([Filtererd_Solution_screen_employment_lookup_df,Unfiltered_Solution_screen_employment_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_incentive_lookup_df = pd.concat([Filtererd_Solution_screen_incentive_lookup_df,Unfiltered_Solution_screen_incentive_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_approval_lookup_df = pd.concat([Filtererd_Solution_screen_approval_lookup_df,Unfiltered_Solution_screen_approval_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_essential_supply_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_essential_supply_vendor_lookup_df,Unfiltered_Solution_screen_essential_supply_vendor_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_essential_supply_all_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_essential_supply_all_vendor_lookup_df,Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_non_essential_supply_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df,Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df], axis = 0, ignore_index=True)
                Solution_screen_non_essential_supply_all_vendor_lookup_df = pd.concat([Filtererd_Solution_screen_non_essential_supply_all_vendor_lookup_df,Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df], axis = 0, ignore_index=True)
                
                Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, final_property_ranking_for_decision, for_final_return=True)
                # print(type(Filtererd_Solution_screen_employment_lookup_df))
                Final_analytics_results_query_to_build_industry_from_scratch = {

                    # "Filtered_final_property_ranking_for_decision" : Filtered_final_property_ranking_for_decision.to_json() if not Filtered_final_property_ranking_for_decision.empty else None,
                    # "Filtererd_Solution_screen_employment_lookup_df" : Filtererd_Solution_screen_employment_lookup_df.to_json() if not Filtererd_Solution_screen_employment_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_incentive_lookup_df" : Filtererd_Solution_screen_incentive_lookup_df.to_json() if not Filtererd_Solution_screen_incentive_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_approval_lookup_df" : Filtererd_Solution_screen_approval_lookup_df.to_json() if not Filtererd_Solution_screen_approval_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_essential_supply_vendor_lookup_df" : Filtererd_Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Filtererd_Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                    # "Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df" : Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,

                    # "Unfiltered_final_property_ranking_for_decision" : Unfiltered_final_property_ranking_for_decision.to_json() if not Unfiltered_final_property_ranking_for_decision.empty else None,
                    # "Unfiltered_Solution_screen_employment_lookup_df" : Unfiltered_Solution_screen_employment_lookup_df.to_json() if not Unfiltered_Solution_screen_employment_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_incentive_lookup_df" : Unfiltered_Solution_screen_incentive_lookup_df.to_json() if not Unfiltered_Solution_screen_incentive_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_approval_lookup_df" : Unfiltered_Solution_screen_approval_lookup_df.to_json() if not Unfiltered_Solution_screen_approval_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                    # "Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.empty else None

                    "final_scoring_df": final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                    "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json() if not Solution_screen_employment_lookup_df.empty else None,
                    "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None,
                    "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                    "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                    "Essential_supply_all_vendor_lookup_df": Solution_screen_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_all_vendor_lookup_df.empty else None,
                    "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,
                    "Non_essential_supply_all_vendor_lookup_df": Solution_screen_non_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_all_vendor_lookup_df.empty else None
                }
            else:
 
                Unfiltered_final_property_ranking_for_decision = pd.merge(final_property_ranking_for_decision, unfiltered_keyword_df, left_on="Property_ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                Unfiltered_final_property_ranking_for_decision["aggregated_score"] = (0.3 * Unfiltered_final_property_ranking_for_decision["aggregated_score"]) + (0.7 * Unfiltered_final_property_ranking_for_decision["Aggregate Property Performance Score (APPS)"])
                Unfiltered_final_property_ranking_for_decision = Unfiltered_final_property_ranking_for_decision.sort_values(by=["aggregated_score"], ascending=False)
                Unfiltered_Solution_screen_employment_lookup_df = sort_by_scores(Solution_screen_employment_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_incentive_lookup_df = sort_by_scores(Solution_screen_incentive_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_approval_lookup_df = sort_by_scores(Solution_screen_approval_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df = sort_by_scores(Solution_screen_non_essential_supply_all_vendor_lookup_df, Unfiltered_final_property_ranking_for_decision, for_final_return=True)
                
                final_property_ranking_for_decision = Unfiltered_final_property_ranking_for_decision
                Solution_screen_employment_lookup_df = Unfiltered_Solution_screen_employment_lookup_df
                Solution_screen_incentive_lookup_df = Unfiltered_Solution_screen_incentive_lookup_df
                Solution_screen_approval_lookup_df = Unfiltered_Solution_screen_approval_lookup_df
                Solution_screen_essential_supply_vendor_lookup_df = Unfiltered_Solution_screen_essential_supply_vendor_lookup_df
                Solution_screen_essential_supply_all_vendor_lookup_df = Unfiltered_Solution_screen_essential_supply_all_vendor_lookup_df
                Solution_screen_non_essential_supply_vendor_lookup_df = Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df
                Solution_screen_non_essential_supply_all_vendor_lookup_df = Unfiltered_Solution_screen_non_essential_supply_all_vendor_lookup_df
                Final_analytics_results_query_to_build_industry_from_scratch ={
                # "Filtered_final_property_ranking_for_decision" : None,
                # "Filtererd_Solution_screen_employment_lookup_df" : None,
                # "Filtererd_Solution_screen_incentive_lookup_df" : None,
                # "Filtererd_Solution_screen_approval_lookup_df" : None,
                # "Filtererd_Solution_screen_essential_supply_vendor_lookup_df" : None,
                # "Filtererd_Solution_screen_non_essential_supply_vendor_lookup_df" : None,

                # "Unfiltered_final_property_ranking_for_decision" : Unfiltered_final_property_ranking_for_decision.to_json() if not Unfiltered_final_property_ranking_for_decision.empty else None,
                # "Unfiltered_Solution_screen_employment_lookup_df" : Unfiltered_Solution_screen_employment_lookup_df.to_json() if not Unfiltered_Solution_screen_employment_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_incentive_lookup_df" : Unfiltered_Solution_screen_incentive_lookup_df.to_json() if not Unfiltered_Solution_screen_incentive_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_approval_lookup_df" : Unfiltered_Solution_screen_approval_lookup_df.to_json() if not Unfiltered_Solution_screen_approval_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                # "Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df" : Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Unfiltered_Solution_screen_non_essential_supply_vendor_lookup_df.empty else None

                "final_scoring_df": final_property_ranking_for_decision.to_json() if not final_property_ranking_for_decision.empty else None,
                "Employment_lookup_df": Solution_screen_employment_lookup_df.to_json() if not Solution_screen_employment_lookup_df.empty else None,
                "Solution_lookup_df": Solution_screen_incentive_lookup_df.to_json() if not Solution_screen_incentive_lookup_df.empty else None,
                "Approval_lookup_df": Solution_screen_approval_lookup_df.to_json() if not Solution_screen_approval_lookup_df.empty else None,
                "Essential_supply_vendor_lookup_df": Solution_screen_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_vendor_lookup_df.empty else None,
                "Essential_supply_all_vendor_lookup_df": Solution_screen_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_essential_supply_all_vendor_lookup_df.empty else None,
                "Non_essential_supply_vendor_lookup_df": Solution_screen_non_essential_supply_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_vendor_lookup_df.empty else None,
                "Non_essential_supply_all_vendor_lookup_df": Solution_screen_non_essential_supply_all_vendor_lookup_df.to_json() if not Solution_screen_non_essential_supply_all_vendor_lookup_df.empty else None

                }

        response = {
                "Analytics_response": Final_analytics_results_query_to_build_industry_from_scratch,
                "Is_Error" : False
            }
        log_to_file("response",response)
        update_process(chatId,"Analyzing Data","Complete",1)
        update_process(chatId,"Preparing Result","Processing",0)
        time.sleep(5)
        update_process(chatId,"Preparing Result","Complete",1)
        del aiResponse
        del Final_analytics_results_query_to_build_industry_from_scratch
        
        locals().clear()
        gc.collect()
        
        return response
        
    
    except Exception as e:
        update_process(chatId,"Analyzing Data","Fail",0)
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
    
    with open("log2.txt", "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")