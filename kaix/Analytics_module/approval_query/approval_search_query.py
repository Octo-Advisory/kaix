import frappe
import pandas as pd
from datetime import datetime
import warnings
import spacy
from typing import List, Tuple
warnings.filterwarnings('ignore')

nlp = spacy.load("en_core_web_lg")

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
    
def fetch_industry_details(given_industry_by_user: str) -> str:
    """
    Fetches the industry ID from the database based on the given industry name.

    Parameters:
    given_industry_by_user (str): The industry name provided by the user.

    Returns:
    str: The industry ID if found, otherwise None.
    """
    query = f"""
    SELECT name
    FROM `tabIndustry`
    WHERE industry_name = '{given_industry_by_user}'
    """
    # Execute the query and fetch results
    results = fetch_query_results(query)

    # Extract industry ID if results exist; otherwise, set to None
    industry_id = results[0][0] if results else None

    return industry_id

def fetch_sub_sector_details(given_sub_sector_by_user: str) -> str:
    """
    Fetches the sub-sector ID from the database based on the given sub-sector name.

    Parameters:
    given_sub_sector_by_user (str): The sub-sector name provided by the user.

    Returns:
    str: The sub-sector ID if found, otherwise None.
    """
    if given_sub_sector_by_user is not None:
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

def fetch_area_details(given_area_by_user: str) -> str:
    """
    Fetches the area ID from the database based on the given area name.

    Parameters:
    given_area_by_user (str): The area name provided by the user.

    Returns:
    str: The area ID if found, otherwise None.
    """
    query = f"""
    SELECT DISTINCT name
    FROM `tabArea`
    WHERE area_name = '{given_area_by_user}'
    """

    # Execute the query and fetch results
    results = fetch_query_results(query)

    # Extract area ID if results exist; otherwise, set to None
    area_id = results[0][0] if results else None

    return area_id

def fetch_city_details(given_city_by_user: str) -> str:
    """
    Fetches the city ID from the database based on the given city name.

    Parameters:
    given_city_by_user (str): The city name provided by the user.

    Returns:
    str: The city ID if found, otherwise None.
    """
    query = f"""
    SELECT DISTINCT name
    FROM `tabCity`
    WHERE city_name = '{given_city_by_user}'
    """

    # Execute the query and fetch results
    results = fetch_query_results(query)

    # Extract city ID if results exist; otherwise, set to None
    city_id = results[0][0] if results else None

    return city_id

def fetch_state_details(given_state_by_user: str) -> str:
    """
    Fetches the state ID from the database based on the given state name.

    Parameters:
    given_state_by_user (str): The state name provided by the user.

    Returns:
    str: The state ID if found, otherwise None.
    """
    query = f"""
    SELECT DISTINCT name
    FROM `tabState`
    WHERE state_name  = '{given_state_by_user}'
    """

    # Execute the query and fetch results
    results = fetch_query_results(query)

    # Extract state ID if results exist; otherwise, set to None
    state_id = results[0][0] if results else None

    return state_id

def get_property_approval_data(sub_sector_id=None, industry_id=None, area_id=None, city_id=None, state_id=None):
    """
    Fetches property approval details based on industry, location, and sectoral filters.

    Parameters:
    sub_sector_id (str, optional): Sub-sector identifier.
    industry_id (str, optional): Industry identifier.
    area_id (str, optional): Area identifier.
    city_id (str, optional): City identifier.
    state_id (str, optional): State identifier.

    Returns:
    pd.DataFrame or None: DataFrame containing property approval details if records exist, otherwise None.
    """
    query = f"""
    SELECT a.name, a.license_approval, a.description, a.government_department, a.business_location_type as ABLT, a.land_type as ALT, a.vicinity_detail as AVD, a.cross_following_details as ACFD, a.road_cutting, a.tree_cutting, a.require_pole_shifting, a.delivery_schedule_in_working_days, a.mode_of_application, a.stage, a.is_dependent, a.depends_on, a.area, a.city, a.city_level, a.state, a.state_level, a.country_level, a.sub_sector, a.industry, a.pan_industries 
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
        property_approval_mapped_df = pd.DataFrame(results, columns=['approval_id', 'approval_name', 'description','Government Department','Business_location', 'Land_type', 'Vicinity_detail', 'Cross_following', 'Road Cutting', 'Tree Cutting', 'Pole Shifting', 'Time Taken', 'online_or_offline', 'stages', 'is_dependent', 'dependent_approval_ids', 'area_id', 'city_id', 'city_level', 'state', 'state_level', 'country_level', 'sub_sector', 'industry', 'pan_industries'])
        return property_approval_mapped_df
    else:
        return None
    
def normalize_series(series, highest_is_worst=False):
    """
    Normalizes a Pandas Series to a scale of 1 to 10 using Min-Max Scaling.

    Parameters:
    series (pd.Series): The input numerical series to normalize.
    highest_is_worst (bool, optional): If True, higher values will be considered worse (flipped scale).
                                        Defaults to False.

    Returns:
    pd.Series: Normalized series with values between 1 and 10.
    """

    # Calculate the minimum and maximum values of the series
    min_val, max_val = series.min(), series.max()

    # If all values in the series are the same, assign a default score of 5
    if min_val == max_val:
        return pd.Series([5] * len(series), index=series.index)

    # Determine the scaling factor: -1 (default) for normal scaling, 1 for reversed scaling
    scale = 1 if highest_is_worst else -1

    # Apply Min-Max Scaling and adjust the range to be between 1 and 10
    return ((series - min_val) / (max_val - min_val) * 9 + 1) * scale

def get_dependent_approval_time(testing_df1, dep_approval, approval_hierarchy, current_approval_main_stage, current_approval_id, effecient_time = None, infinity_loop_lst=None):
    """
    Recursively calculates the total time required for an approval, considering dependencies.
    Prevents infinite loops by tracking already visited approvals.
    
    Args:
        testing_df1 (pd.DataFrame): DataFrame containing approval data.
        dep_approval (str): The dependent approval ID.
        approval_hierarchy (list): List defining the approval stages hierarchy.
        current_approval_main_stage (str): The main stage of the current approval.
        current_approval_id (str): The ID of the current approval.
        effecient_time (dict, optional): Dictionary containing time taken per approval stage.
        infinity_loop_lst (list, optional): Tracks visited approvals to prevent infinite loops.
    
    Returns:
        list: List containing the total time required for the dependent approval.
    """
    if not infinity_loop_lst:
        infinity_loop_lst = []
        current_approval_id_independent = current_approval_id
        infinity_loop_lst.append(current_approval_id_independent)
    infinity_loop_lst.append(dep_approval)

    # Extract the dependent approval details from the DataFrame
    dep_approval_df = testing_df1[testing_df1["Approval ID"] == dep_approval]
    lst_dep_appr = []

    # Case 1: If the current approval stage is not "Others"
    if current_approval_main_stage != "Others":
        if not dep_approval_df.empty:   
            # Skip if the dependent approval's stage is different
            if dep_approval_df["Stages"].values[0] != current_approval_main_stage:
                pass
            else:
                # If the dependent approval is independent, return its time taken
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
                                temp_lst_for_max.append(0)# Avoid infinite recursion
                                continue
                            temp_placeholder = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_dep_lst, approval_hierarchy=approval_hierarchy, current_approval_main_stage=current_approval_main_stage, current_approval_id=current_approval_id, infinity_loop_lst=infinity_loop_lst)
                            temp_lst_for_max.append(sum(temp_placeholder))
                        lst_dep_appr.append(max(temp_lst_for_max))
        return lst_dep_appr

     # Case 2: If the current approval stage is "Others"
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
                                temp_lst_for_max.extend(0)# Prevent infinite recursion
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

    """
    Calculates the total approval time required for a given land, considering dependencies among approval stages.
    
    Parameters:
        all_approval_included_df (DataFrame): The input DataFrame containing approval details.
    
    Returns:
        tuple: A dictionary of efficient times for each stage, total approval time, and online approval percentage.
    """
    
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
    
    # Total effecient_time calculation for Approval (Stage-wise)

    online_percentages = {}

    # Total effecient_time calculation for Approval (Stage-wise)

    for current_approval_main_stage in approval_hierarchy:
        effecient_time_list = []
        temp_appr_rank_df = testing_df1[testing_df1["Stages"] == current_approval_main_stage]


        #### Stage-wise online percentage:
        # Count Online and Offline modes
        mode_counts = temp_appr_rank_df['Mode'].value_counts().to_dict()
        online_mode_count = mode_counts.get('Online', 0)
        offline_count = mode_counts.get('Offline', 0)
        total = online_mode_count + offline_count

        # Calculate percentage
        online_percentage = (online_mode_count / total * 100) if total > 0 else 0


        # Append to result dict
        online_percentages[current_approval_main_stage] = online_percentage


        if not temp_appr_rank_df.empty:
            for i,j in temp_appr_rank_df.iterrows():
                current_approval_id_ind = j["Approval ID"]
                if (j["Is Dependent"] == "Yes") and (j["Dependent Approval IDs"] is not None):
                    dependent_approval = [app_id.strip() for app_id in j["Dependent Approval IDs"].split(",")]
                    dependent_approval_time = []
                    for dep_approval in dependent_approval:
                        dep_final_time = get_dependent_approval_time(testing_df1=testing_df1,dep_approval=dep_approval, approval_hierarchy=approval_hierarchy,current_approval_main_stage=current_approval_main_stage, effecient_time=effecient_time, current_approval_id=current_approval_id_ind)
                        # print(dep_final_time)
                        print(dep_final_time) ###############################################################Change
                        dependent_approval_time.append(sum(dep_final_time))
                    if dependent_approval_time:
                        print("==>", dependent_approval_time)
                        eff_time = j["Time Taken"] + max(dependent_approval_time)
                        print(current_approval_id_ind,eff_time)
                        effecient_time_list.append(eff_time)
                else:
                    effecient_time_list.append(j["Time Taken"])
        else:
            effecient_time_list.append(0)
        effecient_time[current_approval_main_stage].extend(effecient_time_list)

    total_approval_time_for_given_land = max(max(effecient_time["Pre-Requisite"]) + max(effecient_time["Pre-Establishment"]) + max(effecient_time["Pre-Operation"]), max(effecient_time["Others"]))
    # print("*"*100)
    # print("total_approval_time_for_given_land:",total_approval_time_for_given_land)
    # print("total_approval_count:",len(effecient_time["Pre-Requisite"])+len(effecient_time["Pre-Establishment"])+len(effecient_time["Pre-Operation"])+len(effecient_time["Others"]))
    # print("*"*100)


    return effecient_time, total_approval_time_for_given_land, online_count, online_percentages

def calculate_efficiency(df, area_id=None, city_id=None, state_id=None, keyword_given_by_user = None, approval_keyword_df =None):
    """
    Calculates the effective time required for approvals based on location hierarchy (Area, City, State, Country)
    and filters approvals using user-provided keywords if applicable.
    
    Args:
        df (pd.DataFrame): DataFrame containing approval details.
        area_id (str, optional): Area identifier for filtering approvals.
        city_id (str, optional): City identifier for filtering approvals.
        state_id (str, optional): State identifier for filtering approvals.
        keyword_given_by_user (str, optional): Keywords provided by the user to filter approvals.
        approval_keyword_df (pd.DataFrame, optional): DataFrame containing keyword-based scores for approvals.

    Returns:
        dict: A dictionary containing the total effective time, online approval percentage,
              and JSON-serialized approval data.
    """

    # Compute the total approval time and online approval percentage    
    Stage_wise_eff_score, efficient_time, online_percentage_given, online_percentages = get_efficient_time_for_land(df)

    results = [] # Stores filtered approval data
    if area_id:
        # Area-level approvals
        area_df = df[df['area_id'] == area_id]
        if not area_df.empty:
            for _, row in area_df.iterrows():
                results.append({
                    'Approval ID': row['approval_id'],
                    'Approval Name': row['approval_name'],
                    'Business_location' : row['Business_location'],
                    'Land_type' : row['Land_type'],
                    'description': row['description'],
                    'Government Department': row['Government Department'],
                    'Mode of Application' : row['online_or_offline'],
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
                    'Business_location' : row['Business_location'],
                    'Land_type' : row['Land_type'],
                    'description': row['description'],
                    'Government Department': row['Government Department'],
                    'Mode of Application' : row['online_or_offline'],
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
                    'Business_location' : row['Business_location'],
                    'Land_type' : row['Land_type'],
                    'description': row['description'],
                    'Government Department': row['Government Department'],
                    'Mode of Application' : row['online_or_offline'],
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
                    'Business_location' : row['Business_location'],
                    'Land_type' : row['Land_type'],
                    'description': row['description'],
                    'Government Department': row['Government Department'],
                    'Mode of Application' : row['online_or_offline'],
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
                    'Business_location' : row['Business_location'],
                    'Land_type' : row['Land_type'],
                    'description': row['description'],
                    'Government Department': row['Government Department'],
                    'Mode of Application' : row['online_or_offline'],
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
                    'Business_location' : row['Business_location'],
                    'Land_type' : row['Land_type'],
                    'description': row['description'],
                    'Government Department': row['Government Department'],
                    'Mode of Application' : row['online_or_offline'],
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
                'Business_location' : row['Business_location'],
                'Land_type' : row['Land_type'],
                'description': row['description'],
                'Government Department': row['Government Department'],
                'Mode of Application' : row['online_or_offline'],
                'Level': 'Country',
                'Stages': row['stages']
            })
    
    result_df = pd.DataFrame(results)
    if not keyword_given_by_user:
        # Convert to DataFrame
        return {"Total Effective Time": efficient_time,
                "Online Percentage":online_percentage_given,
                "Approval Data":result_df.to_json(),
                "Pre-Requisite": max(Stage_wise_eff_score["Pre-Requisite"]),
                "Pre-Establishment": max(Stage_wise_eff_score["Pre-Establishment"]),
                "Pre-Operation": max(Stage_wise_eff_score["Pre-Operation"]),
                "Others": max(Stage_wise_eff_score["Others"]),
                "Mode_Pre-Requisite": (online_percentages["Pre-Requisite"]),
                "Mode_Pre-Establishment": (online_percentages["Pre-Establishment"]),
                "Mode_Pre-Operation": (online_percentages["Pre-Operation"]),
                "Mode_Others": (online_percentages["Others"]),
                }
    else:
        keyword_result = filter_df_by_keywords(keyword_given_by_user, approval_keyword_df)
        filtered_keyword_df, unfiltered_keyword_df = keyword_result[0], keyword_result[1]
        if len(filtered_keyword_df) != 0:
            filtered_result_df = pd.merge(result_df, filtered_keyword_df, left_on="Approval ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
            unfiltered_result_df = pd.merge(result_df, unfiltered_keyword_df, left_on="Approval ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
            Final_result_df = pd.concat([filtered_result_df,unfiltered_result_df], axis = 0, ignore_index= True ).sort_values(by= ['aggregated_score'])
            return {"Total Effective Time": efficient_time,
                    "Online Percentage":online_percentage_given,
                    "Approval Data":Final_result_df.to_json(),
                    "Pre-Requisite": max(Stage_wise_eff_score["Pre-Requisite"]),
                    "Pre-Establishment": max(Stage_wise_eff_score["Pre-Establishment"]),
                    "Pre-Operation": max(Stage_wise_eff_score["Pre-Operation"]),
                    "Others": max(Stage_wise_eff_score["Others"]),
                    "Mode_Pre-Requisite": (online_percentages["Pre-Requisite"]),
                    "Mode_Pre-Establishment": (online_percentages["Pre-Establishment"]),
                    "Mode_Pre-Operation": (online_percentages["Pre-Operation"]),
                    "Mode_Others": (online_percentages["Others"]),
                    }
        else:
            unfiltered_result_df = pd.merge(result_df, unfiltered_keyword_df, left_on="Approval ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
            return {"Total Effective Time": efficient_time,
                    "Online Percentage":online_percentage_given,
                    "Approval Data":unfiltered_result_df.to_json(),
                    "Pre-Requisite": max(Stage_wise_eff_score["Pre-Requisite"]),
                    "Pre-Establishment": max(Stage_wise_eff_score["Pre-Establishment"]),
                    "Pre-Operation": max(Stage_wise_eff_score["Pre-Operation"]),
                    "Others": max(Stage_wise_eff_score["Others"]),
                    "Mode_Pre-Requisite": (online_percentages["Pre-Requisite"]),
                    "Mode_Pre-Establishment": (online_percentages["Pre-Establishment"]),
                    "Mode_Pre-Operation": (online_percentages["Pre-Operation"]),
                    "Mode_Others": (online_percentages["Others"]),
                    }

def filter_df_by_keywords(
    extracted_keywords: List[str],
    df: pd.DataFrame,
    spacy_threshold: float = 0.65
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    1) Compute SpaCy similarity for EACH column separately.
    2) Store the similarity scores as new columns (e.g., "spacy_score_<column_name>").
    3) Compute an aggregated similarity score per row.
    4) Sort both DataFrames by the aggregated score.
    5) Return TWO DataFrames:
       - `filtered_df`: Rows where at least one column has similarity >= spacy_threshold.
       - `remaining_df`: Rows where no columns met the threshold.

    Parameters:
    -----------
    extracted_keywords : List[str]
        The list of keywords extracted from the user query (e.g., ["power", "incentive"]).

    df : pd.DataFrame
        The DataFrame containing textual columns to filter.
        Non-string columns will be converted to string before similarity computation.

    spacy_threshold : float
        The minimum SpaCy similarity (0.0-1.0) to consider a row a match.

    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame]:
        - `filtered_df`: Rows where at least one column met the threshold, sorted by relevance.
        - `remaining_df`: Rows where no columns met the threshold, sorted by relevance.
    """

    # 1) Concatenate the extracted keywords into a single user text string
    user_text = " ".join(kw.strip() for kw in extracted_keywords if kw.strip()).lower()

    # If no user_text is available, return empty DataFrames with the same structure
    if not user_text:
        return df.iloc[0:0], df.iloc[0:0]  # Return two empty DataFrames

    # Convert user text to a SpaCy Doc object
    user_doc = nlp(user_text)

    # Copy the DataFrame to avoid modifying the original
    df = df.copy()

    # Store similarity scores for each column
    similarity_columns = []
    # 2) Compute SpaCy similarity for each column separately
    for col in df.columns:
        if col == "ID":
            continue
        col_name = f"spacy_score_{col}"  # Create column name for similarity score
        similarity_columns.append(col_name)

        # Convert column to string and lowercase (handle NaN safely)
        df[col] = df[col].astype(str).str.lower()

        # Compute similarity for each row in the column
        df[col_name] = df[col].apply(lambda text: user_doc.similarity(nlp(text)) if text.strip() else 0)

    # 3) Compute an aggregated similarity score per row
    df["aggregated_score"] = (df[similarity_columns].max(axis=1) + df[similarity_columns].mean(axis=1)) / 2

    # 4) Filter rows where at least ONE column has similarity >= threshold
    mask = df[similarity_columns] >= spacy_threshold  # Check each column individually
    row_match = mask.any(axis=1)  # If at least one column meets threshold, keep the row

    # 5) Create the two DataFrames:
    filtered_df = df.loc[row_match].sort_values(by="aggregated_score", ascending=False)  # Sort by relevance
    remaining_df = df.loc[~row_match].sort_values(by="aggregated_score", ascending=False)  # Sort by relevance

    return filtered_df[["ID", "aggregated_score"]], remaining_df[["ID", "aggregated_score"]]
