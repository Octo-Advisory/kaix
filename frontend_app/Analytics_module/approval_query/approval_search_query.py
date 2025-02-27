import frappe
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

name_change_mapping_for_approval = {
    "approval_id": "Approval ID",
    "stages":"Stages",
    "is_dependent": "Is Dependent",
    "time_taken": "Time Taken",
    "dependent_approval_ids": "Dependent Approval IDs",
    "online_or_offline":"Mode", 
}

def fetch_query_results(query):
    """
    Executes a given SQL query and returns the results.
    
    :param query: SQL query to execute
    :return: List of tuples containing query results
    """
    try:
        results = frappe.db.sql(query)
        return results
    except:
        return None
    
def fetch_industry_details(given_industry_by_user):
    # Fetching Industry details
    query = f"""
    SELECT name
    FROM `tabIndustry`
    WHERE industry_name = '{given_industry_by_user}'
    """
    # Call the function and assign results
    results = fetch_query_results(query)

    # Assign variables based on results
    if results:
        industry_id = results[0][0]
    else:
        industry_id = None
    return industry_id

def fetch_sub_sector_details(given_sub_sector_by_user):
    if given_sub_sector_by_user != None:
        query = f"""
        SELECT name
        FROM `tabSub Sector`
        WHERE sub_sector_name = "{given_sub_sector_by_user}"
        """
        results = fetch_query_results(query)
            
        # Assign variables based on results
        if results:
            sub_sector_id = results[0][0]  # Get the first row, first column
            return sub_sector_id
        else:
            sub_sector_id = None
    else:
        sub_sector_id = None
    return sub_sector_id

def fetch_area_details(given_area_by_user):
    # Fetching Area details
    query = f"""
    SELECT DISTINCT name
    FROM `tabArea`
    WHERE area_name = '{given_area_by_user}'
    """

    # Call the function and assign results
    results = fetch_query_results(query)
    # Assign variables based on results
    if results:
        area_id = results[0][0]
    else:
        area_id = None
    return area_id

def fetch_city_details(given_city_by_user):
    # Fetching City details
    query = f"""
    SELECT DISTINCT name
    FROM `tabCity`
    WHERE city_name = '{given_city_by_user}'
    """

    # Call the function and assign results
    results = fetch_query_results(query)
    # Assign variables based on results
    if results:
        city_id = results[0][0]
    else:
        city_id = None
    return city_id

def fetch_state_details(given_state_by_user):
    # Fetching State details
    query = f"""
    SELECT DISTINCT name
    FROM `tabState`
    WHERE state_name  = '{given_state_by_user}'
    """

    # Call the function and assign results
    results = fetch_query_results(query)
    # Assign variables based on results
    if results:
        state_id = results[0][0]
    else:
        state_id = None
    return state_id

def get_property_approval_data(sub_sector_id=None, industry_id=None, area_id=None, city_id=None, state_id=None):
    # Initialize the query string with the common parts
    query = f"""
    SELECT a.name, a.license_approval,a.business_location_type as ABLT, a.land_type as ALT, a.vicinity_detail as AVD, a.cross_following_details as ACFD,a.road_cutting, a.delivery_schedule_in_working_days, a.mode_of_application, a.stage, a.is_dependent, a.depends_on, a.area, a.city, a.city_level, a.state, a.state_level, a.country_level, a.sub_sector, a.industry, a.pan_industries
    FROM `tabLicenses and Approvals Type` a
    WHERE
    """

    # Condition 1: All inputs are provided
    if sub_sector_id and industry_id and area_id and city_id and state_id:
        query += f"""
        (a.sub_sector = '{sub_sector_id}' OR (a.sub_sector IS NULL AND a.industry = '{industry_id}') OR (a.pan_industries = "Yes"))
        AND
        ((a.area IN ('{area_id}'))  
        OR (a.area IS NULL AND a.city IN ('{city_id}') AND a.city_level = 1)
        OR (a.area IS NULL AND a.city IS NULL AND a.state IN ('{state_id}') AND a.state_level = 1)
        OR (a.country_level = 1))
        """
    
    # Condition 2: sub_sector_id is not given, other factors are given
    elif not sub_sector_id and industry_id and area_id and city_id and state_id:
        query += f"""
        (a.sub_sector IS NULL AND a.industry = '{industry_id}' OR (a.pan_industries = "Yes"))
        AND
        ((a.area IN ('{area_id}'))  
        OR (a.area IS NULL AND a.city IN ('{city_id}') AND a.city_level = 1)
        OR (a.area IS NULL AND a.city IS NULL AND a.state IN ('{state_id}') AND a.state_level = 1)
        OR (a.country_level = 1))
        """
    
    # Condition 3: area_id is not given, other factors are given
    elif sub_sector_id and industry_id and not area_id and city_id and state_id:
        query += f"""
        (a.sub_sector = '{sub_sector_id}' OR (a.sub_sector IS NULL AND a.industry = '{industry_id}') OR (a.pan_industries = "Yes"))
        AND
        ((a.city IN ('{city_id}') OR a.city_level = 1)
        OR (a.area IS NULL AND a.city IS NULL AND a.state IN ('{state_id}') AND a.state_level = 1)
        OR (a.country_level = 1))
        """
    
    # Condition 4: area_id and city_id are not given, other factors are given
    elif sub_sector_id and industry_id and not area_id and not city_id and state_id:
        query += f"""
        (a.sub_sector = '{sub_sector_id}' OR (a.sub_sector IS NULL AND a.industry = '{industry_id}') OR (a.pan_industries = "Yes"))
        AND
        ((a.state IN ('{state_id}') AND a.state_level = 1)
        OR (a.country_level = 1))
        """
    
    # Condition 5: sub_sector_id and area_id are not given, other factors are given
    elif not sub_sector_id and industry_id and not area_id and city_id and state_id:
        query += f"""
        (a.sub_sector IS NULL AND a.industry = '{industry_id}' OR (a.pan_industries = "Yes"))
        AND
        ((a.city IN ('{city_id}') AND a.city_level = 1)
        OR (a.area IS NULL AND a.city IS NULL AND a.state IN ('{state_id}') AND a.state_level = 1)
        OR (a.country_level = 1))
        """
    
    # Condition 6: sub_sector_id, area_id, and city_id are not given, other factors are given
    elif not sub_sector_id and not area_id and not city_id and industry_id and state_id:
        query += f"""
        (a.sub_sector IS NULL AND a.industry = '{industry_id}' OR (a.pan_industries = "Yes"))
        AND
        ((a.state IN ('{state_id}') AND a.state_level = 1)
        OR (a.country_level = 1))
        """
    
    # Execute the query
    results = fetch_query_results(query)
    
    # Convert the results into a DataFrame
    if results:
        property_approval_mapped_df = pd.DataFrame(results, columns=['approval_id', 'approval_name','Approval_business_location', 'Approval_land_type', 'Approval_vicinity_detail', 'Approval_cross_following', 'Approval_Road_cutiing', 'time_taken', 'online_or_offline', 
                                         'stages', 'is_dependent', 'dependent_approval_ids', 
                                         'area_id', 'city_id', 'city_level', 'state', 'state_level', 'country_level', 'sub_sector', 'industry', 'pan_industries'])
        return property_approval_mapped_df
    else:
        return None
    
def normalize_series(series, highest_is_worst=False):
    min_val, max_val = series.min(), series.max()
    if min_val == max_val:
        return pd.Series([5] * len(series), index=series.index)  # Default to 5 if all values are the same
    scale = 1 if highest_is_worst else -1
    return ((series - min_val) / (max_val - min_val) * 9 + 1) * scale

def get_dependent_approval_time(testing_df1, dep_approval, approval_hierarchy, current_approval_main_stage, current_approval_id, effecient_time = None, infinity_loop_lst=None):
    if not infinity_loop_lst:
        infinity_loop_lst = []
        current_approval_id_independent = current_approval_id
        infinity_loop_lst.append(current_approval_id_independent)
    infinity_loop_lst.append(dep_approval)
    dep_approval_df = testing_df1[testing_df1["Approval ID"] == dep_approval]
    lst_dep_appr = []
    if current_approval_main_stage != "Others":
        if not dep_approval_df.empty:
            if dep_approval_df["Stages"].values[0] != current_approval_main_stage:
                pass
            else:
                if dep_approval_df["Is Dependent"].values[0] == "No":
                    lst_dep_appr.append(dep_approval_df["Time Taken"].values[0])
                    return lst_dep_appr
                else:
                    lst_dep_appr.append(dep_approval_df["Time Taken"].values[0])
                    dep_approval_lst = dep_approval_df["Dependent Approval IDs"].values[0]
                    if dep_approval_lst is not None:
                        dep_approval_lst = [id_get.strip() for id_get in dep_approval_lst.split(',')]
                        temp_lst_for_max = []
                        for dep_dep_lst in dep_approval_lst:
                            if dep_dep_lst in infinity_loop_lst:
                                temp_lst_for_max.append(0)
                                continue
                            temp_placeholder = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_dep_lst, approval_hierarchy=approval_hierarchy, current_approval_main_stage=current_approval_main_stage, current_approval_id=current_approval_id, infinity_loop_lst=infinity_loop_lst)
                            temp_lst_for_max.append(sum(temp_placeholder))
                        lst_dep_appr.append(max(temp_lst_for_max))
        return lst_dep_appr
    else:
        if not dep_approval_df.empty:
            if dep_approval_df["Stages"].values[0] == "Others":
                if dep_approval_df["Is Dependent"].values[0] == "No":
                        lst_dep_appr.append(dep_approval_df["Time Taken"].values[0])
                        return lst_dep_appr
                else:
                    lst_dep_appr.append(dep_approval_df["Time Taken"].values[0])
                    dep_approval_lst = dep_approval_df["Dependent Approval IDs"].values[0]
                    if dep_approval_lst is not None:
                        dep_approval_lst = [id_get.strip() for id_get in dep_approval_lst.split(',')]
                        temp_lst_for_max = []
                        for dep_dep_lst in dep_approval_lst:
                            if dep_dep_lst in infinity_loop_lst:
                                temp_lst_for_max.extend(0)
                                continue
                            temp_placeholder = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_dep_lst, approval_hierarchy=approval_hierarchy, current_approval_main_stage="Others", effecient_time=effecient_time, current_approval_id=current_approval_id, infinity_loop_lst=infinity_loop_lst)
                            temp_lst_for_max.append(sum(temp_placeholder))
                        lst_dep_appr.append(max(temp_lst_for_max))
            else:
                if dep_approval_df["Stages"].values[0] == "Pre-Requisite":
                    time_taken_for_dep_approval = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_approval,  approval_hierarchy=approval_hierarchy, current_approval_main_stage="Pre-Requisite", current_approval_id=current_approval_id, infinity_loop_lst=infinity_loop_lst)
                    lst_dep_appr.append(sum(time_taken_for_dep_approval))
                    return lst_dep_appr
                else:
                    till_index = approval_hierarchy.index(dep_approval_df["Stages"].values[0])
                    temp_app_hierarchy = approval_hierarchy[:till_index]
                    total_time_taken_till = 0
                    for temp_app in temp_app_hierarchy:
                        total_time_taken_till += max(effecient_time[temp_app])
                    time_taken_for_dep_approval = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_approval,  approval_hierarchy=approval_hierarchy, current_approval_main_stage=dep_approval_df["Stages"].values[0], current_approval_id=current_approval_id, infinity_loop_lst=infinity_loop_lst)
                    total_time_taken_till = total_time_taken_till + sum(time_taken_for_dep_approval)
                    lst_dep_appr.append(total_time_taken_till)
                    return lst_dep_appr
          
        return lst_dep_appr
    
def get_efficient_time_for_land(all_approval_included_df):
    testing_df1 = all_approval_included_df
    testing_df1 = testing_df1.rename(columns= name_change_mapping_for_approval)
    # Convert "Time Taken" to numeric, coercing errors to NaN (in case of invalid strings)
    testing_df1["Time Taken"] = pd.to_numeric(testing_df1["Time Taken"], errors='coerce')
    testing_df1.fillna(0, inplace = True)
    if "Online" in list(testing_df1["Mode"].unique()):
        online_count = (testing_df1["Mode"].value_counts()["Online"] / len(testing_df1)) * 100
    else:
        online_count = 0
    approval_hierarchy = ["Pre-Requisite", "Pre-Establishment", "Pre-Operation", "Others"]
    effecient_time = {
            "Pre-Requisite": [],
            "Pre-Establishment": [],
            "Pre-Operation": [],
            "Others": []
            }

    for current_approval_main_stage in approval_hierarchy:
        effecient_time_list = []
        temp_appr_rank_df = testing_df1[testing_df1["Stages"] == current_approval_main_stage]
        if not temp_appr_rank_df.empty:
            for i,j in temp_appr_rank_df.iterrows():
                current_approval_id_ind = j["Approval ID"]
                if (j["Is Dependent"] == "Yes") and (j["Dependent Approval IDs"] is not None):
                    dependent_approval = [app_id.strip() for app_id in j["Dependent Approval IDs"].split(",")]
                    dependent_approval_time = []
                    for dep_approval in dependent_approval:
                        dep_final_time = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_approval, approval_hierarchy=approval_hierarchy,current_approval_main_stage=current_approval_main_stage, effecient_time=effecient_time, current_approval_id=current_approval_id_ind)
                        dependent_approval_time.append(sum(dep_final_time))
                    if dependent_approval_time:
                        eff_time = j["Time Taken"] + max(dependent_approval_time)
                        effecient_time_list.append(eff_time)
                else:
                    effecient_time_list.append(j["Time Taken"])
        else:
            effecient_time_list.append(0)
        effecient_time[current_approval_main_stage].extend(effecient_time_list)

    total_approval_time_for_given_land = max(max(effecient_time["Pre-Requisite"]) + max(effecient_time["Pre-Establishment"]) + max(effecient_time["Pre-Operation"]), max(effecient_time["Others"]))
    return effecient_time, total_approval_time_for_given_land, online_count

def calculate_efficiency(df, area_id=None, city_id=None, state_id=None):
    _, efficient_time, online_percentage_given = get_efficient_time_for_land(df)
    results = []
    if area_id:
        # Area-level approvals
        area_df = df[df['area_id'] == area_id]
        if not area_df.empty:
            for _, row in area_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Level': 'Area',
                    'Stages': row['stages']
                })
        
        # City-level approvals
        city_df = df[(df['city_level'] == 1) & (df['area_id'].isna())]
        if not city_df.empty:
            for _, row in city_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Level': 'City',
                    'Stages': row['stages']
                })
        
        # State-level approvals
        state_df = df[(df['state_level'] == 1) & (df['city_id'].isna()) & (df['area_id'].isna())]
        if not state_df.empty:
            for _, row in state_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Level': 'State',
                    'Stages': row['stages']
                })
    
    elif city_id:
        # City-level approvals
        city_df = df[(df['city_id'] == city_id) & (df['city_level'] == 1)]
        if not city_df.empty:
            for _, row in city_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Level': 'City',
                    'Stages': row['stages']
                })
        
        # State-level approvals
        state_df = df[(df['state_level'] == 1) & (df['city_id'].isna()) & (df['area_id'].isna())]
        if not state_df.empty:
            for _, row in state_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Level': 'State',
                    'Stages': row['stages']
                })
    elif state_id:
        # State-level approvals
        state_df = df[(df['state_level'] == 1) & (df['city_id'].isna()) & (df['area_id'].isna())]
        if not state_df.empty:
            for _, row in state_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Level': 'State',
                    'Stages': row['stages']
                })
    # Country-level approvals
    country_df = df[(df['country_level'] == 1) & (df['state'].isna()) & (df['city_id'].isna()) & (df['area_id'].isna())]
    if not country_df.empty:
        for _, row in country_df.iterrows():
            results.append({
                'Approval ID': row['approval_id'],
                'Approval Name': row['approval_name'],
                'Level': 'Country',
                'Stages': row['stages']
            })
    
    # Convert to DataFrame
    result_df = pd.DataFrame(results)
    return {"Total Effective Time": efficient_time,
            "Online Percentage":online_percentage_given,
            "Approval Data":result_df.to_json()}