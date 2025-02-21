import frappe
from datetime import datetime
import pandas as pd
import json
import sys
from numpy import average
import numpy as np
import traceback

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
    
def normalize_series(series, highest_is_worst=True):
    """
    Normalizes a Pandas Series to a range of 1 to 10 using Min-Max scaling.
    Handles edge cases where all values in the series are identical.
    """
    min_val = series.min()
    max_val = series.max()

    # Handle cases where all values are identical
    if min_val == max_val:
        return pd.Series([5] * len(series), index=series.index)  # Assign a neutral score (midpoint of 1-10)

    # Perform Min-Max scaling
    if highest_is_worst:
        return 1 + ((1 - ((series - min_val) / (max_val - min_val))) * 9)
    else:
        return 1 + (((series - min_val) / (max_val - min_val)) * 9)
    
def normalize_series(series, highest_is_worst=True):
    """
    Normalizes a Pandas Series to a range of 1 to 10 using Min-Max scaling.
    Handles edge cases where all values in the series are identical.
    """
    min_val = series.min()
    max_val = series.max()

    # Handle cases where all values are identical
    if min_val == max_val:
        return pd.Series([5] * len(series), index=series.index)  # Assign a neutral score (midpoint of 1-10)

    # Perform Min-Max scaling
    if highest_is_worst:
        return 1 + ((1 - ((series - min_val) / (max_val - min_val))) * 9)
    else:
        return 1 + (((series - min_val) / (max_val - min_val)) * 9)
    

def get_industry(industry):
    query = f"""
    SELECT name
    FROM `tabIndustry`
    WHERE industry_name = '{industry}'
    """

    # query = f"""
    # Show columns from `tabIndustry`

    # """

    # Call the function and assign results
    results = fetch_query_results(query)


    # Assign variables based on results
    if results:
        industry_id = results[0][0]  # Get the first row, first column
        return industry_id
    else:
        return None
    
def get_subsector(sub_Sector):
    if sub_Sector != None:
        query = f"""
            SELECT name, zone_id
            FROM `tabSub Sector`
            WHERE sub_sector_name = "{sub_Sector}"
            """
        results = fetch_query_results(query)
        if results:
            results = pd.DataFrame(results)
        else:
            return "Checked sub-sector but not found..."
                
        # Call the function and assign results
        results = fetch_query_results(query)
    else:
        return "Sub-sector not found..."

    # Assign variables based on results
    if results:
        sub_sector_id = results[0][0]  # Get the first row, first column
        zone_id = results[0][1]
        return sub_sector_id,zone_id
    else:
       return None

def get_segment(segment):
    query = f"""
    SELECT name
    FROM `tabSegment`
    WHERE segment = "{segment}"
    """

    results = fetch_query_results(query)

    if results:
        segment_id = results[0][0]  # Get the first row, first column
        return segment_id
    else:
       return None

# def get_land_requirements(industry_id,sub_sector_id,segment_id,required_capacity_by_user):
#     if industry_id != None and sub_sector_id != None and segment_id != None:
#         query = f"""
#         SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
#             `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
#         FROM `tabIndustry Capacity Rule`
#         WHERE (
#             ({required_capacity_by_user} BETWEEN `minimum_capacity_value` AND `maximum_capacity_value`) 
#             OR ((`minimum_capacity_value` < {required_capacity_by_user}) AND (`maximum_capacity_value` = 0))
#         )
#         AND (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment = '{segment_id}');
#     """

#     elif industry_id != None and sub_sector_id != None and segment_id == None:
#         query = f"""
#         SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
#             `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
#         FROM `tabIndustry Capacity Rule`
#         WHERE (
#             ({required_capacity_by_user} BETWEEN `minimum_capacity_value` AND `maximum_capacity_value`) 
#             OR ((`minimum_capacity_value` < {required_capacity_by_user}) AND (`maximum_capacity_value` = 0))
#         )
#         AND (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment IS NULL);
#         """

#     elif industry_id != None and sub_sector_id == None and segment_id == None:
#         # Show all `sub_sector_id` related to `industry_id`
#         query = f"""
#         SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
#             `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
#         FROM `tabIndustry Capacity Rule`
#         WHERE (
#             ({required_capacity_by_user} BETWEEN `minimum_capacity_value` AND `maximum_capacity_value`) 
#             OR ((`minimum_capacity_value` < {required_capacity_by_user}) AND (`maximum_capacity_value` = 0))
#         )
#         AND (industry = '{industry_id}');
#         """  

#     else:
#         query = None
#     # Ensure query execution happens only when query is not None
#     # log_to_file("query",query)
#     if query != None:
#         results = fetch_query_results(query)
#         # log_to_file("result",result)
#         # results = pd.DataFrame(result)
#     else:
#         results = None
#     # log_to_file("result",results)
#     # Assign variables based on results
#     if results != None:
#         for row in results:
#             minimum_land_requirement = row[3]  # 4th column
#             maximum_land_requirement = row[4]  # 5th column
#             return minimum_land_requirement,maximum_land_requirement
#     else:
#         return 'No Result Found For Land'


def fetch_capacity_data(required_capacity_by_user, industry_id, sub_sector_id=None, segment_id=None):
    """
    Function to fetch capacity-related data based on user inputs.
    """
    query = None
    if industry_id is not None and sub_sector_id is not None and segment_id is not None:
        query = f"""
        SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
            `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
        FROM `tabIndustry Capacity Rule`
        WHERE (
            ({required_capacity_by_user} BETWEEN `minimum_capacity_value` AND `maximum_capacity_value`) 
            OR ((`minimum_capacity_value` < {required_capacity_by_user}) AND (`maximum_capacity_value` = 0))
        )
        AND (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment = '{segment_id}');
        """
        results = fetch_query_results(query)
        if results:
            df = pd.DataFrame(results)
        else:
            return fetch_capacity_data(required_capacity_by_user, industry_id, sub_sector_id)


    elif industry_id is not None and sub_sector_id is not None and segment_id is None:
        query = f"""
        SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
            `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
        FROM `tabIndustry Capacity Rule`
        WHERE (
            ({required_capacity_by_user} BETWEEN `minimum_capacity_value` AND `maximum_capacity_value`) 
            OR ((`minimum_capacity_value` < {required_capacity_by_user}) AND (`maximum_capacity_value` = 0))
        )
        AND (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment IS NULL);
        """
        results = fetch_query_results(query)
        if results:
            df = pd.DataFrame(results)
        else:
            return fetch_capacity_data(required_capacity_by_user, industry_id)

    elif industry_id is not None and sub_sector_id is None and segment_id is None:
        query = f"""
        SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
            `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
        FROM `tabIndustry Capacity Rule`
        WHERE (
            ({required_capacity_by_user} BETWEEN `minimum_capacity_value` AND `maximum_capacity_value`) 
            OR ((`minimum_capacity_value` < {required_capacity_by_user}) AND (`maximum_capacity_value` = 0))
        )
        AND (industry = '{industry_id}');
        """
        results = fetch_query_results(query)
        if results:
            df = pd.DataFrame(results)
        else:
            results = None   

    else:
        results = None

    # If no results, append the nearest capacity range query to each case
    if not results:
        nearest_query = f"""
        SELECT `sub_sector`, `minimum_capacity_value`, `maximum_capacity_value`, 
            `minimum_land_requirement_in_acre`, `maximum_land_requirement_in_acre`, `capacity_unit`
        FROM `tabIndustry Capacity Rule`
        WHERE industry = '{industry_id}'
        """

        if sub_sector_id is not None:
            nearest_query += f" AND sub_sector = '{sub_sector_id}'"
        
        if segment_id is not None:
            nearest_query += f" AND segment = '{segment_id}'"

        nearest_query += f"""
        ORDER BY ABS(minimum_capacity_value - {required_capacity_by_user})
        LIMIT 1;
        """
        
        results = fetch_query_results(nearest_query)
        df = pd.DataFrame(results)


    if results:
        return float(results[0][1]), float(results[0][2]), float(results[0][3]), float(results[0][4])

    return None, None, None, None

def calculate_land_requirements(user_cap, max_cap, min_cap, max_land, min_land, margin_percentage=30):
    """
    Function to calculate land requirements for a given user capacity.
    
    Args:
        user_cap (float): The user's capacity.
        max_cap (float): The maximum capacity.
        min_cap (float): The minimum capacity.
        max_land (float): The maximum land area available.
        min_land (float): The minimum land area available.
        margin_percentage (float, optional): Percentage margin for adjustments. Default is {margin_percentage}.
    
    Returns:
        tuple: Land size for user capacity, adjusted lower capacity, and adjusted higher capacity.
    """
    epsilon = sys.float_info.epsilon
    
    # Adjust capacity and land calculations based on given constraints
    if user_cap > max_cap and user_cap > min_cap:
        if max_land == 0 and max_cap == 0:
            max_cap = user_cap
            max_land = min_land + (min_land * ((user_cap - min_cap) / min_cap))
        elif max_cap != 0 and max_land == 0:
            max_land = min_land + (min_land * ((max_cap - min_cap) / min_cap))
            min_cap = min_cap + (min_cap * ((user_cap - max_cap) / max_cap))
            min_land = min_land + (min_land * ((user_cap - max_cap) / max_cap))
            max_land = max_land + (max_land * ((user_cap - max_cap) / max_cap))
            max_cap = user_cap
        elif max_cap == 0 and max_land != 0:
            max_cap = min_cap + (min_cap * ((max_land - min_land) / min_land))
            min_cap = min_cap + (min_cap * ((user_cap - max_cap) / max_cap))
            min_land = min_land + (min_land * ((user_cap - max_cap) / max_cap))
            max_land = max_land + (max_land * ((user_cap - max_cap) / max_cap))
            max_cap = user_cap
        else:
            min_cap = min_cap + (min_cap * ((user_cap - max_cap) / max_cap))
            min_land = min_land + (min_land * ((user_cap - max_cap) / max_cap))
            max_land = max_land + (max_land * ((user_cap - max_cap) / max_cap))
            max_cap = user_cap

    if user_cap < min_cap:
        if max_land == 0 and max_cap == 0:
            max_land = min_land
            max_cap = min_cap
            min_land = min_land - (min_land * ((min_cap - user_cap) / min_cap))
            min_cap = user_cap
        elif max_land == 0 and max_cap != 0:
            max_land = min_land + (min_land * ((max_cap - min_cap) / min_cap))
            max_cap = max_cap - (max_cap * ((min_cap - user_cap) / min_cap))
            max_land = max_land - (max_land * ((min_cap - user_cap) / min_cap))
            min_land = min_land - (min_land * ((min_cap - user_cap) / min_cap))
            min_cap = user_cap
        elif max_land != 0 and max_cap == 0:
            max_cap = min_cap + (min_cap * ((max_land - min_land) / min_land))
            max_cap = max_cap - (max_cap * ((min_cap - user_cap) / min_cap))
            max_land = max_land - (max_land * ((min_cap - user_cap) / min_cap))
            min_land = min_land - (min_land * ((min_cap - user_cap) / min_cap))
            min_cap = user_cap
        else:
            max_cap = max_cap - (max_cap * ((min_cap - user_cap) / min_cap))
            max_land = max_land - (max_land * ((min_cap - user_cap) / min_cap))
            min_land = min_land - (min_land * ((min_cap - user_cap) / min_cap))
            min_cap = user_cap

    # Calculate margin for adjusted capacities
    margin_factor = margin_percentage / 100
    adj_user_cap_max = user_cap + (max_cap - min_cap) * margin_factor
    adj_user_cap_min = user_cap - (max_cap - min_cap) * margin_factor
    
    def recursive_land_calculation(capacity):
        """
        Helper function to calculate the land size based on the given capacity.
        
        Args:
            capacity (float): The capacity value to compute land size for.
        
        Returns:
            float: The computed land size.
        """
        return (((capacity - min_cap) / (abs(max_cap - min_cap) + epsilon)) * abs(max_land - min_land)) + min_land
    
    # Compute land sizes for user capacity and adjusted capacities
    return {
        "Land_size": recursive_land_calculation(user_cap),
        "Lower_limit_land_size": recursive_land_calculation(adj_user_cap_min),
        "Upper_limit_land_size": recursive_land_calculation(adj_user_cap_max)
    }

def integrate_land_calculation(required_capacity_by_user, industry_id, sub_sector_id=None, segment_id=None):
    """
    Function to fetch capacity data and compute land requirements.
    """
    min_cap, max_cap, min_land, max_land = fetch_capacity_data(required_capacity_by_user, industry_id, sub_sector_id, segment_id)
    
    if None in (min_cap, max_cap, min_land, max_land):
        return None
    
    return calculate_land_requirements(required_capacity_by_user, max_cap, min_cap, max_land, min_land)

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

def get_list_of_area_id(zone_id):
    query = f"""
    SELECT DISTINCT area
    FROM `tabArea Zone Mapping`
    WHERE zone = '{zone_id}'
    """

    # Call the function and assign results
    results = fetch_query_results(query)
    # Assign variables based on results
    if results:
        area_id_list = [row[0] for row in results]
        return area_id_list
    else:
        return None

def get_list_of_city_list(area_id_list):
    # Convert the list into a string format that can be used in SQL
    area_id_str = ', '.join(f"'{area_id}'" for area_id in area_id_list)

    sql_query = f"""
    SELECT DISTINCT city_id
    FROM `tabArea`
    WHERE name IN ({area_id_str});
    """
    
    # Call the fetch_query_results function to execute the query
    results = fetch_query_results(sql_query)

    # Process the results and extract the unique city_ids
    if results:
        city_id_list = [row[0] for row in results]  # Extracting the city_id from each row
        return city_id_list
    else:
        return None
    
def get_state_list(city_id_list):
    city_id_str = ', '.join(f"'{city_id}'" for city_id in city_id_list)
    sql_query = f"""
    SELECT DISTINCT state
    FROM `tabCity`
    WHERE name IN ({city_id_str});
    """

    # Call the fetch_query_results function to execute the query
    results = fetch_query_results(sql_query)

    # Process the results and extract the unique city_ids
    if results:
        state_id_list = [row[0] for row in results]  # Extracting the city_id from each row
        return state_id_list
    else:
        return None
    
def get_property_and_employement(zone_id,area_id_list,required_LowerMargin_land_for_user,required_UpperMargin_land_for_user,found_property,found_employment):
    # convert list to string to use in query
    area_id_str = ', '.join(f"'{area_id}'" for area_id in area_id_list)

    sql_query_for_property_and_employment = f"""
    SELECT p.name, p.area, p.city, p.state, p.distance_from_nearest_railway_station, p.distance_from_nearest_seaport, p.distance_from_power_source, p.latitude_longitude, p.business_location_type, p.land_type, p.require_shifting_of_any_electricity_line_or_pole, p.vicinity_of, p.tree_cutting_involved, p.road_cutting_involved, p.will_your_industry_cross_the_following, p.road_connectivity, p.distance_from_nearest_airport, e.area, e.employment_type, e.availability
    FROM `tabSurvey No` p
    JOIN `tabEmployment City Mapping` e ON p.area = e.area
    WHERE (p.zone = '{zone_id}') 
    AND (p.area IN ({area_id_str}))
    AND (p.area_acre BETWEEN {required_LowerMargin_land_for_user} AND {required_UpperMargin_land_for_user});
    """

    # Call the function and assign results
    results = fetch_query_results(sql_query_for_property_and_employment)

    if results:
        # Convert the fetched results into a pandas DataFrame
        property_employment_df = pd.DataFrame(results, columns=['property_id', 'area', 'city', 'state', 'distance_from_nearest_railway_station', 'distance_from_nearest_seaport', 'distance_from_power_source', 'latitude_longitude',"business_location_type", "land_type","pole_shifting", "vicinity_of", "tree_cutting_involved", "road_cutting_involved", "Cross_the_following_?", "road_connectivity", "distance_from_nearest_airport" ,'employment_area_id', 'employmenttype_id', 'availability'])
        # log_to_file("propert_emp",property_employment_df)
        # log_to_file("propert_emp unique",property_employment_df.property_id.unique())
        return property_employment_df,property_employment_df.property_id.unique()
    else:
        found_property = False
        found_employment = False
        return None,None
    
def get_property_incentive_mapped(industry_id,sub_sector_id,area_id_list,city_id_list,state_id_list,property_id_list,found_incentive):
    area_id_str = ', '.join(f"'{area_id}'" for area_id in area_id_list)
    city_id_str = ', '.join(f"'{area_id}'" for area_id in city_id_list)
    state_id_str = ', '.join(f"'{state_id}'" for state_id in state_id_list)
    property_id_list_str = ', '.join(f"'{property_id}'" for property_id in property_id_list)
    today_date = datetime.now().strftime('%Y-%m-%d 00:00:00')
    sql_query = f"""
    SELECT i.name, i.incentive_name, i.incentive_type, i.incentive_operation_start_date, i.incentive_operation_end_date, i.quantum_of_assistance, iim.sub_sector, iim.area, iim.city, iim.state, i.incentive_rank,
       p.name, p.area AS property_area_id
FROM `tabIncentive Industry Mapping` iim
JOIN `tabIncentive` i
    ON i.name = iim.incentive
JOIN `tabSurvey No` p
    ON (iim.area = p.area)  -- Join on area_id
    OR (iim.area IS NULL AND iim.city = p.city OR iim.city_level = 1)
    OR (iim.area IS NULL AND iim.city IS NULL AND iim.state = p.state OR iim.state_level = 1)
    OR (iim.country_level = 1)
WHERE
    (iim.sub_sector = '{sub_sector_id}')
    OR (iim.sub_sector IS NULL AND iim.industry = '{industry_id}')
    OR (iim.pan_industries = 1)
  AND (
      (iim.area IN ({area_id_str}))  
      OR (iim.area IS NULL AND iim.city IN ({city_id_str}) OR iim.city_level = 1)
      OR (iim.area IS NULL AND iim.city IS NULL AND iim.state IN ({state_id_str}) OR iim.state_level = 1)
      OR (iim.country_level = 1)
  )
  AND (p.name IN ({property_id_list_str}))
  AND '{today_date}' BETWEEN i.incentive_operation_start_date AND i.incentive_operation_end_date;
    """

    # Execute the query using the provided fetch_query_results function
    results = fetch_query_results(sql_query)

    if results:
        property_incentive_mapped_df = pd.DataFrame(results, columns=['incentive_id', "incentive_name", "incentive_type", "incentive_operation_start_date", 'incentive_operation_end_date', "quantum_of_assistance", 'sub_sector_id', 'area_id', 
                                        'city_id', 'state_id', 'incentive_rank',
                                        'property_id', 'property_area_id'])
        found_incentive = True
        return property_incentive_mapped_df,found_incentive
    else:
        found_incentive = False
        return None,found_incentive

def transform_dataframes(df):
    
    # First DataFrame: Select unique property_id with distances
    df1 = df.groupby("property_id")[
        ["distance_from_nearest_railway_station", "distance_from_nearest_seaport", "distance_from_power_source","distance_from_nearest_airport","road_connectivity"]
    ].first().reset_index()

    # Second DataFrame: Pivot for employmenttype_id as columns and level_of_availability as values
    df2 = df.pivot(index="property_id", columns="employmenttype_id", values="availability").reset_index()

    # Rename the index column
    df2.columns.name = ""  # Remove the name of the index
    return df1, df2

def calculate_property_suitability(df, preference_power_plant=5, preference_road=5, preference_railway=4, preference_seaport=3, preference_airport=2):
    # Ensure the distance columns are numeric
    distance_columns = ['distance_from_nearest_railway_station', 'distance_from_nearest_seaport', 'distance_from_power_source',"distance_from_nearest_airport","road_connectivity"]
    for col in distance_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to numeric, coercing errors to NaN
    df.fillna(0, inplace=True)
    total_preference_score = (preference_power_plant + preference_road + preference_railway + preference_seaport + preference_airport)

    # Define weightages
    weight_railway = preference_railway/total_preference_score
    weight_seaport = preference_seaport/total_preference_score
    weight_power_plant = preference_power_plant/total_preference_score
    weight_airport = preference_airport/total_preference_score
    weight_road = preference_road/total_preference_score

    # Compute normalized scores for each mode
    df['railway_score'] = normalize_series(df['distance_from_nearest_railway_station'],highest_is_worst=True)
    df['seaport_score'] = normalize_series(df['distance_from_nearest_seaport'],highest_is_worst=True)
    df['airport_score'] = normalize_series(df['distance_from_nearest_airport'],highest_is_worst=True)
    df['road_score'] = normalize_series(df['road_connectivity'],highest_is_worst=True)
    df['power_plant_score'] = normalize_series(df['distance_from_power_source'],highest_is_worst=True)

    # Compute property suitability score
    df['property_suitability_score'] = (
        (weight_railway * df['railway_score']) +
        (weight_seaport * df['seaport_score']) +
        (weight_airport * df['airport_score']) +
        (weight_road * df['road_score']) +
        (weight_power_plant * df['power_plant_score'])
    )

    return df

def calculate_employment_availability_score(df, sub_sector_id):
    """
    Calculate Employment Availability Score based on different skill types.

    Parameters:
    df: DataFrame containing the properties and employment type availability data.
    high_skill: The column that represents the "High" required skill type.
    mod_skill: The column that represents the "Moderate" required skill type.
    low_skill: The column that represents the "Low" required skill type.

    Returns:
    A DataFrame with Employment Availability Score.
    """

    query = f"""
        SELECT majorly_required_skill_type, moderately_required_skill_type, least_required_skill_type
        FROM `tabIndustry Specific Info`
        WHERE sub_sector = "{sub_sector_id}"
    """

    result = fetch_query_results (query)

    required_skill_type = {"high_skill": result[0][0], "mod_skill": result[0][1], "low_skill": result[0][2] }

    high_skill = required_skill_type["high_skill"] 
    mod_skill = required_skill_type["mod_skill"]
    low_skill = required_skill_type["low_skill"]

    df.fillna(0, inplace=True)

    # Define the weightages (you can customize these weights if needed)
    weights = {
        high_skill: 60 / 100,  # High required skill type
        mod_skill: 30 / 100,   # Moderate required skill type
        low_skill: 10 / 100    # Low required skill type
    }

    df["Skill_Type"] = [high_skill,]*len(df)
 
    # Map the availability scores to the DataFrame for each skill type
    df[f"{high_skill}_score"] = normalize_series(df[high_skill],highest_is_worst=False)
    df[f"{mod_skill}_score"] = normalize_series(df[mod_skill],highest_is_worst=False)
    df[f"{low_skill}_score"] = normalize_series(df[low_skill],highest_is_worst=False)

    # Calculate Employment Availability Score
    df["employment_availability_score"] = (
        df[f"{high_skill}_score"] * weights[high_skill] +
        df[f"{mod_skill}_score"] * weights[mod_skill] +
        df[f"{low_skill}_score"] * weights[low_skill]
    )
    
    return df

def calculate_incentive_weighted_score(scores):
    # Rank the scores in descending order
    ranked_scores = sorted(scores, reverse=True)
    # Define the weights using 1 / 2^(i-1)
    weights = [1 / (2 ** (i - 1)) for i in range(1, len(ranked_scores) + 1)]
    # Calculate weighted scores
    weighted_scores = [ranked_scores[i] * weights[i] for i in range(len(ranked_scores))]
    # Calculate the final weighted score as the sum of weighted scores
    final_weighted_score = sum(weighted_scores)
    final_average_score = average(scores)
    final_effective_score = (0.7 * final_weighted_score) + (0.3 * final_average_score)
    
    # Return the detailed results as a dictionary
    return {
        "Ranked Scores": ranked_scores,
        "Weights": weights,
        "Weighted Scores": weighted_scores,
        "Final Weighted Score": final_weighted_score,
        "Average Score": final_average_score,
        "Final_Score": final_effective_score
    }

# Define the function to calculate the final incentive scores for each property from the DataFrame
def calculate_property_wise_incentive_scores(df):
    # Convert the 'incentive_rank' to numeric (in case it's stored as strings like '1', '2', etc.)
    df["incentive_rank"] = pd.to_numeric(df["incentive_rank"], errors='coerce')
    df.fillna(0, inplace=True)
    # Group by property_id and get the list of incentive ranks for each property
    property_incentives = df.groupby("property_id")["incentive_rank"].apply(list).reset_index()

    # List to store results for each property
    results = []

    # Iterate over each property and calculate scores
    for index, row in property_incentives.iterrows():
        property_id = row["property_id"]
        incentive_scores = row["incentive_rank"]
        
        # Check if incentive_scores is not empty before calculating
        if incentive_scores:
            score_data = calculate_incentive_weighted_score(incentive_scores)
        
            # Append the results for each property
            results.append({
                "Property ID": property_id,
                "Ranked Scores": score_data["Ranked Scores"],
                "Mean Score": score_data["Average Score"],
                "Weights": score_data["Weights"],
                "Weighted Scores": score_data["Weighted Scores"],
                "Final Weighted Score": score_data["Final Weighted Score"],
                "Final Score": score_data["Final_Score"]
            })

    # Convert the results into a DataFrame for better visualization
    final_results_df = pd.DataFrame(results)

    # Sort the DataFrame by Final Score in descending order
    final_results_sorted = final_results_df.sort_values(by="Final Score", ascending=False).reset_index(drop=True)

    # Min-Max Scaling to 1 to 10
    final_results_sorted["Scaled Final Score"] = normalize_series(final_results_sorted["Final Score"], highest_is_worst=False)

    return final_results_sorted

def get_property_wise_incentive_score(property_incentive_mapped_df,property_employment_df,found_incentive):
    if found_incentive:
        df_with_property_wise_incentive_score = calculate_property_wise_incentive_scores(property_incentive_mapped_df)

        return df_with_property_wise_incentive_score
    else:
        df_with_property_wise_incentive_score = pd.DataFrame({
            "Property ID": list(property_employment_df["property_id"].unique()),
            "Scaled Final Score": [5,]*len(list(property_employment_df["property_id"].unique()))
        })
        return df_with_property_wise_incentive_score
    
def get_property_approval_mapped(industry_id,sub_sector_id,area_id_list,city_id_list,state_id_list,property_id_list,found_approval):
    area_id_str = ', '.join(f"'{area_id}'" for area_id in area_id_list)
    city_id_str = ', '.join(f"'{area_id}'" for area_id in city_id_list)
    state_id_str = ', '.join(f"'{state_id}'" for state_id in state_id_list)
    property_id_list_str = ', '.join(f"'{property_id}'" for property_id in property_id_list)
    query = f"""
    SELECT a.name, a.license_approval, a.government_department, a.business_location_type as ABLT, a.land_type as ALT, a.vicinity_detail as AVD, a.cross_following_details as ACFD,a.road_cutting, a.delivery_schedule_in_working_days, a.mode_of_application, a.stage, a.is_dependent, a.depends_on, a.area, p.name,  p.business_location_type, p.land_type, p.require_shifting_of_any_electricity_line_or_pole, p.vicinity_of, p.tree_cutting_involved, p.road_cutting_involved, p.will_your_industry_cross_the_following
FROM `tabLicenses and Approvals Type` a
JOIN `tabSurvey No` p
    ON (a.area = p.area)  -- Join on area_id
    OR (a.area IS NULL AND a.city = p.city OR a.city_level = 1)
    OR (a.area IS NULL AND a.city IS NULL AND a.state = p.state OR a.state_level = 1)
    OR (a.country_level = 1)
WHERE
    (a.sub_sector = '{sub_sector_id}')
    OR (a.sub_sector IS NULL AND a.industry = '{industry_id}')
    OR (a.pan_industries = "Yes")
  AND (
      (a.area IN ({area_id_str}))  
      OR (a.area IS NULL AND a.city IN ({city_id_str}) OR a.city_level = 1)
      OR (a.area IS NULL AND a.city IS NULL AND a.state IN ({state_id_str}) OR a.state_level = 1)
      OR (a.country_level = 1)
  )
  AND (
      ((a.cross_following_details =  'None of the above')
      AND (a.vicinity_detail = 'None of the above')
      AND (a.road_cutting = "No")
      AND (a.tree_cutting = "No")
      AND (a.business_location_type IS NULL)
      AND (a.land_type IS NULL)
      AND (a.require_pole_shifting = "No")
      )
      OR (a.cross_following_details = p.will_your_industry_cross_the_following)
      OR (a.vicinity_detail = p.vicinity_of)
      OR (a.road_cutting = "Yes" and p.road_cutting_involved = "Yes")
      OR (a.tree_cutting = "Yes" AND p.tree_cutting_involved = "Yes")
      OR (a.business_location_type = p.business_location_type AND a.land_type = p.land_type)
      OR ((a.business_location_type = p.business_location_type) AND (a.land_type IS NULL))
      OR (a.require_pole_shifting = "Yes" AND p.require_shifting_of_any_electricity_line_or_pole = "Yes")
  )
  AND (p.name IN ({property_id_list_str}))
    """
    # Call the fetch_query_results function to get the results from the query
    results = fetch_query_results(query)
    # Check if there are results
    if results:
        property_approval_mapped_df = pd.DataFrame(results, columns=['approval_id', "approval_name", "government_department", 'Approval_business_location', 'Approval_land_type', 'Approval_vicinity_detail', 'Approval_cross_following', 'Approval_Road_cutiing', 'time_taken', 'online_or_offline', 
                                        'stages', 'is_dependent', 'dependent_approval_ids', 
                                        'area_id', 'property_id',"business_location_type", "land_type","pole_shifting", 
                                        "vicinity_of", "tree_cutting_involved", "road_cutting_involved", "Cross_the_following_?"])
        return property_approval_mapped_df,found_approval
    else:
       found_approval = False
       return None,found_approval
    

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
    name_change_mapping_for_approval = {
        "approval_id": "Approval ID",
        "stages":"Stages",
        "is_dependent": "Is Dependent",
        "time_taken": "Time Taken",
        "dependent_approval_ids": "Dependent Approval IDs",
        "online_or_offline":"Mode", 
    }
    testing_df1 = all_approval_included_df
    testing_df1 = testing_df1.rename(columns= name_change_mapping_for_approval)
    # Convert "Time Taken" to numeric, coercing errors to NaN (in case of invalid strings)
    testing_df1["Time Taken"] = pd.to_numeric(testing_df1["Time Taken"], errors='coerce')
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

# Function to calculate property efficiency and rankings
def calculate_property_efficiency(df):
    property_results = []

    # Loop through each unique property_id
    for property_id in df['property_id'].unique():
        property_df = df[df['property_id'] == property_id]
        
        # Calculate efficient time and online percentage for this property
        efficient_time, total_approval_time, online_percentage = get_efficient_time_for_land(property_df)
        
        # Append the result for this property
        property_results.append({
            'Property ID': property_id,
            'Efficient Approval Time': total_approval_time,
            'Online Percentage': online_percentage
        })

    # Convert the results to a DataFrame for easy visualization
    result_df = pd.DataFrame(property_results)



    result_df['Approval Time Rank'] = normalize_series(result_df['Efficient Approval Time'],highest_is_worst=True)


    # Rank properties based on Online Percentage
    result_df['Online Percentage Rank'] = normalize_series(result_df['Online Percentage'], highest_is_worst=False)

    # Calculate Final Ranking using weighted formula
    result_df['Final Score'] = (
        0.7 * result_df['Approval Time Rank'] +
        0.3 * result_df['Online Percentage Rank']
    )

    return result_df

def get_property_wise_approval_score(found_approval,property_approval_mapped_df,property_employment_df):
    if found_approval:
        df_with_property_wise_approval_score = calculate_property_efficiency(property_approval_mapped_df)
        df_with_property_wise_approval_score.sort_values(by=["Final Score"], ascending=False)
        return df_with_property_wise_approval_score
    else:
        df_with_property_wise_approval_score = pd.DataFrame({
        "Property ID": list(property_employment_df["property_id"].unique()),
        "Final Score": [5,]*len(list(property_employment_df["property_id"].unique()))
        })
        return df_with_property_wise_approval_score

def fetch_supply_data(industry_id, sub_sector_id=None, segment_id=None):

    if industry_id is not None and sub_sector_id is not None and segment_id is not None:

        supply_rules_query = f"""
        SELECT supply, minimum_supply_requirement, essential_items
        FROM `tabSupply Rules`
        WHERE (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment = '{segment_id}')
        """
        results = fetch_query_results(supply_rules_query)

        if not results:
            return fetch_supply_data(industry_id, sub_sector_id)

    elif industry_id is not None and sub_sector_id is not None and segment_id is None:
        
        supply_rules_query = f"""
        SELECT supply, minimum_supply_requirement, essential_items
        FROM `tabSupply Rules`
        WHERE (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment IS NULL)
        """
        results = fetch_query_results(supply_rules_query)

        if not results:
            return fetch_supply_data(industry_id)
        
    elif industry_id is not None and sub_sector_id is None and segment_id is None:

        supply_rules_query = f"""
        SELECT supply, minimum_supply_requirement, essential_items
        FROM `tabSupply Rules`
        WHERE (industry = '{industry_id}')
        """
        results = fetch_query_results(supply_rules_query)
        if not results:
            return None

    else:
        return None

    if results:
        return results
    
def get_supply_rule(industry_id, sub_sector_id, segment_id,required_capacity_by_user):
    results = fetch_supply_data(industry_id, sub_sector_id, segment_id)

    # Check if there are results and convert to DataFrame
    if results:
        # Define the column names corresponding to the SELECT statement
        supply_rules_df = pd.DataFrame(results, columns=['supply_id', 'minimum_supply_requirement', 'essentials_items'])
        supply_rules_df.drop_duplicates(subset=["supply_id"], inplace=True)
        supply_rules_df["minimum_supply_requirement"] = (required_capacity_by_user*supply_rules_df["minimum_supply_requirement"])
        supply_rules_df["minimum_supply_requirement"] = pd.to_numeric(supply_rules_df["minimum_supply_requirement"])
        supply_rules_df.fillna(0, inplace=True)
        return supply_rules_df
    else:
        return None
    
def get_vendor_df(supply_rules_df):
    all_supply_id_list = list(supply_rules_df["supply_id"].values)
    supply_id_str = ', '.join(f"'{supply_id}'" for supply_id in all_supply_id_list)
    vendor_fetching_query = f""" 
    select VSC.parent, VSC.supply, VSC.maximum_supply_capacity, 
        V.years_of_experience, V.no_of_location, V.no_of_past_clients, 
        V.no_of_services, V.no_of_employees, V.latitude_longitude
    From `tabVendor` AS V
    Join `tabVendor Supply Capacity` as VSC
    ON V.name = VSC.parent
    WHERE supply IN ({supply_id_str})
    """
    log_to_file("vendor_fetching_query",vendor_fetching_query)
    log_to_file("supply_id_str",supply_id_str)
    # Execute the query using the fetch_query_results function
    results = fetch_query_results(vendor_fetching_query)
    log_to_file("result",results)
    # Convert the query results to a pandas DataFrame
    if results:
        # Define the column names corresponding to the SELECT statement
        vendor_df = pd.DataFrame(results, columns=['vendor_id', 'supply_id', 'vendor_supply_capacity', 
                                            'years_of_experience', 'no_of_locations', 'no_of_past_clients', 
                                            'no_of_servieces', 'no_of_employees', 'latitude_longitude'])
        columns_to_convert = ["vendor_supply_capacity", "years_of_experience", "no_of_past_clients", "no_of_locations", "no_of_servieces", "no_of_employees"]
        vendor_df[columns_to_convert] = vendor_df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

        return vendor_df
    else:
        vendor_df = pd.DataFrame(results, columns=['vendor_id', 'supply_id', 'vendor_supply_capacity', 
                                            'years_of_experience', 'no_of_locations', 'no_of_past_clients', 
                                            'no_of_servieces', 'no_of_employees', 'latitude_longitude'])
        # columns_to_convert = ["vendor_supply_capacity", "years_of_experience", "no_of_past_clients", "no_of_locations", "no_of_servieces", "no_of_employees"]
        # vendor_df[columns_to_convert] = vendor_df[columns_to_convert].apply(pd.to_numeric, errors='coerce')
        return vendor_df
    
def transform_data_for_map_call(vendor_latlong_df, property_latlong_df):
    input_data = {
        "Vendor": [
            {"id": row["vendor_id"], "latlong": row["latitude_longitude"]}
            for i, row in vendor_latlong_df.iterrows()
        ],
        "Property": [
            {"id": row["property_id"], "latlong": row["latitude_longitude"]}
            for i, row in property_latlong_df.iterrows()
        ]
    }
    return input_data

def is_valid_latlong(latlong: str) -> bool:
    try:
        # Split the input string into lat and lon
        lat, lon = map(float, latlong.split(","))
        
        # Check if lat and lon are within valid ranges
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return True
        else:
            return False
    except ValueError:
        return False

def calculate_distance(data):
    """
    Function to calculate the distance between vendors and properties.
    It sends data to a Frappe API call and processes the response.

    Parameters:
        data (dict): A dictionary containing vendor and property details with lat-long.

    Returns:
        dict: A dictionary with vendor IDs as keys and property distances as values.
    """
    try:
        # Call the Frappe function
        
        resp = frappe.call("frontend_app.Mapping_module.distance.CalculatePropVenDistance", data=data)
        # log_to_file("response is",str(resp))
        response = resp['result']
        log_to_file("response is",str(response))
        # Validate response
        if not response or not isinstance(response, dict): 
            raise ValueError("Invalid response received from Frappe API")

        # Process response and return formatted output
        output = {}
        for vendor_id, properties in response.items():
            output[vendor_id] = {prop_id: round(distance, 2) for prop_id, distance in properties.items()}

        return output

    except Exception as e:
        return e

def calculate_vendor_property_distances(input_data: dict) -> dict:
    """
    Computes distances between vendors and properties.
    Uses `calculate_distance()` for distance calculation.
    
    Parameters:
    input_data (dict): Dictionary containing "Vendor" and "Property" lists.

    Returns:
    dict: A nested dictionary where vendors map to properties with distances.
    """

    distance = calculate_distance(input_data)
    log_to_file("distance ",str(distance))

    return distance


def calculate_adjustment_factor(series, threshold):
    base_value = 0.00001
    range_value = 0.00002 - 0.00001
    filtered_series = series[series >= threshold]
    min_val = filtered_series.min()
    max_val = filtered_series.max()

    def adjustment_factor(value):
        if threshold - value > 0:
            return 0
        normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0
        return base_value + (range_value * normalized)

    return series.apply(adjustment_factor)

def get_supply_scores(property_latlong_df, supply_rules_df, vendor_df, prefered_range, tolerable_range):
    try:
        final_results = []  # Store results for all property-supply combinations
        better_results = []
        ### Checking if vendor df is empty
        if not vendor_df.empty:
            vendor_latlong_df = vendor_df[["vendor_id", "latitude_longitude"]].drop_duplicates()
            supply_rules_df.fillna(0, inplace=True)
            vendor_df.fillna(0, inplace=True)
            input_data_for_map = transform_data_for_map_call(vendor_latlong_df, property_latlong_df)
            vendor_property_distance = calculate_vendor_property_distances(input_data_for_map)
            missing_vendor_from_distance_dict = list(set(list(vendor_df["vendor_id"].unique())) ^ set(vendor_property_distance.keys()))
            if len(missing_vendor_from_distance_dict) > 0:
                vendor_df = vendor_df[~vendor_df["vendor_id"].isin(missing_vendor_from_distance_dict)]
            # Loop through all properties
            for _, property_row in property_latlong_df.iterrows():
                property_id = property_row['property_id']
                if all(property_id in vendor_property_distance[ven_id].keys() for ven_id in list(vendor_property_distance.keys())):
                    # Loop through all supplies
                    for _, supply_row in supply_rules_df.iterrows():
                        supply_id = supply_row['supply_id']
                        minimum_supply_requirement = supply_row['minimum_supply_requirement']
                        essential = (supply_row['essentials_items']).lower() == "yes"
                        
                        # Filter vendors for the current supply
                        vendors_for_supply = vendor_df[vendor_df['supply_id'] == supply_id].copy()
                        # Calculate distances between property and vendors
                        if not vendors_for_supply.empty:
                            vendors_for_supply['Dist'] = vendors_for_supply['vendor_id'].apply(
                                lambda vendor_unique_id: vendor_property_distance[vendor_unique_id][property_id]
                            )                
                            
                            # Add normalized columns and calculate scores
                            vendors_for_supply['Diff_cap'] = vendors_for_supply['vendor_supply_capacity'].apply(
                                lambda x: max(0, minimum_supply_requirement - x)
                            )
                            vendors_for_supply["R_C"] = normalize_series(vendors_for_supply["Diff_cap"])
                            vendors_for_supply["R_d"] = normalize_series(vendors_for_supply["Dist"])
                            vendors_for_supply["Ranking"] = (0.7 * vendors_for_supply["R_C"]) + (0.3 * vendors_for_supply["R_d"])
                            vendors_for_supply["Adjustment Factor"] = calculate_adjustment_factor(
                                vendors_for_supply["vendor_supply_capacity"], threshold=minimum_supply_requirement
                            )
                            vendors_for_supply["Final Ranking"] = vendors_for_supply["Ranking"] + vendors_for_supply["Adjustment Factor"]
                            vendors_for_supply["rank_exp"] = normalize_series(vendors_for_supply["years_of_experience"], highest_is_worst=False)
                            vendors_for_supply["rank_loc"] = normalize_series(vendors_for_supply["no_of_locations"], highest_is_worst=False)
                            vendors_for_supply["rank_pc"] = normalize_series(vendors_for_supply["no_of_past_clients"], highest_is_worst=False)
                            vendors_for_supply["rank_n_ser"] = normalize_series(vendors_for_supply["no_of_servieces"], highest_is_worst=False)
                            vendors_for_supply["Fea_rank"] = (
                                0.4 * vendors_for_supply["rank_exp"] +
                                0.3 * vendors_for_supply["rank_loc"] +
                                0.2 * vendors_for_supply["rank_n_ser"] +
                                0.1 * vendors_for_supply["rank_pc"]
                            )
                            vendors_for_supply["Final_Score_With_Features"] = (
                                0.7 * vendors_for_supply["Final Ranking"] +
                                0.3 * vendors_for_supply["Fea_rank"]
                            )
                            
                            # Find the best vendor based on the logic provided
                            req_cap = minimum_supply_requirement
                            pref_r = prefered_range
                            best_ranked_row = vendors_for_supply.loc[
                                vendors_for_supply["Final_Score_With_Features"].idxmax()
                            ]
                            
                            if best_ranked_row["vendor_supply_capacity"] >= req_cap:
                                final_results.append({
                                "property_id": property_id,
                                "supply_id": supply_id,
                                "essential": essential,
                                "minimum_supply_requirement": minimum_supply_requirement,
                                "supply_score": best_ranked_row["Final_Score_With_Features"],
                                "vendor_id": best_ranked_row["vendor_id"],
                                "vendor_supply_capacity": best_ranked_row["vendor_supply_capacity"],
                                "years_of_experience": best_ranked_row["years_of_experience"],
                                "no_of_locations": best_ranked_row["no_of_locations"],
                                "no_of_past_clients": best_ranked_row["no_of_past_clients"],
                                "no_of_servieces": best_ranked_row["no_of_servieces"],
                                "no_of_employees": best_ranked_row["no_of_employees"],
                                "latitude_longitude": best_ranked_row["latitude_longitude"],
                                "Distance": best_ranked_row["Dist"],
                                "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                            })
                            else:
                                g_cap = vendors_for_supply[
                                    (vendors_for_supply["vendor_supply_capacity"] >= req_cap) &
                                    (vendors_for_supply["Dist"] <= pref_r[1])
                                ]
                                if not g_cap.empty:
                                    best_g_cap_row = g_cap.loc[g_cap["Final_Score_With_Features"].idxmax()]
                                    better_results.append(
                                        {
                                            "property_id": property_id,
                                            "supply_id": supply_id,
                                            "essential": essential,
                                            "minimum_supply_requirement": minimum_supply_requirement,
                                            "supply_score": best_ranked_row["Final_Score_With_Features"],
                                            "vendor_id": best_ranked_row["vendor_id"],
                                            "vendor_supply_capacity": best_ranked_row["vendor_supply_capacity"],
                                            "years_of_experience": best_ranked_row["years_of_experience"],
                                            "no_of_locations": best_ranked_row["no_of_locations"],
                                            "no_of_past_clients": best_ranked_row["no_of_past_clients"],
                                            "no_of_servieces": best_ranked_row["no_of_servieces"],
                                            "no_of_employees": best_ranked_row["no_of_employees"],
                                            "latitude_longitude": best_ranked_row["latitude_longitude"],
                                            "Distance": best_ranked_row["Dist"],
                                            "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                                        }
                                    )
                                    final_results.append({
                                        "property_id": property_id,
                                        "supply_id": supply_id,
                                        "essential": essential,
                                        "minimum_supply_requirement": minimum_supply_requirement,
                                        "supply_score": best_g_cap_row["Final_Score_With_Features"],
                                        "vendor_id": best_g_cap_row["vendor_id"],
                                        "vendor_supply_capacity": best_g_cap_row["vendor_supply_capacity"],
                                        "years_of_experience": best_g_cap_row["years_of_experience"],
                                        "no_of_locations": best_g_cap_row["no_of_locations"],
                                        "no_of_past_clients": best_g_cap_row["no_of_past_clients"],
                                        "no_of_servieces": best_g_cap_row["no_of_servieces"],
                                        "no_of_employees": best_g_cap_row["no_of_employees"],
                                        "latitude_longitude": best_g_cap_row["latitude_longitude"],
                                        "Distance": best_g_cap_row["Dist"],
                                        "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                                        })
                                else:
                                    final_results.append({
                                    "property_id": property_id,
                                    "supply_id": supply_id,
                                    "essential": essential,
                                    "minimum_supply_requirement": minimum_supply_requirement,
                                    "supply_score": best_ranked_row["Final_Score_With_Features"],
                                    "vendor_id": best_ranked_row["vendor_id"],
                                    "vendor_supply_capacity": best_ranked_row["vendor_supply_capacity"],
                                    "years_of_experience": best_ranked_row["years_of_experience"],
                                    "no_of_locations": best_ranked_row["no_of_locations"],
                                    "no_of_past_clients": best_ranked_row["no_of_past_clients"],
                                    "no_of_servieces": best_ranked_row["no_of_servieces"],
                                    "no_of_employees": best_ranked_row["no_of_employees"],
                                    "latitude_longitude": best_ranked_row["latitude_longitude"],
                                    "Distance": best_ranked_row["Dist"],
                                    "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                                })

        # Convert results to DataFrame
        final_df = pd.DataFrame(final_results)
        if len(better_results) == 0:
            return final_df
        better_df = pd.DataFrame(better_results)
        return final_df, better_df
    except Exception as e:
        error_details = traceback.format_exc()
        log_to_file("Execprion form anaytics",str(error_details))
        return None,None

def calculate_final_supply_mapped_property_scores_with_condition(property_mapped_supply_individual_score, property_latlong_df_for_no_supply, weight_distance=0.7, weight_capacity=0.3):
    """
    Function to calculate the final aggregated vendor scores for each property ID based on weighted distance and capacity scores,
    with conditional weights based on the 'essential' column.

    Parameters:
    - property_mapped_supply_individual_score (pd.DataFrame): The input DataFrame containing supply and property data.
    - normalize_series (function): Function to normalize a pandas series.
    - weight_distance (float): Default weight for the distance score (0.7).
    - weight_capacity (float): Default weight for the capacity score (0.3).

    Returns:
    - pd.DataFrame: A DataFrame with property_id and final aggregated scores.
    """
    if not property_mapped_supply_individual_score.empty:
        # Initialize an empty DataFrame to store the results
        final_supply_score_df = pd.DataFrame()

        # Get all unique supply_id values
        unique_supply_ids = property_mapped_supply_individual_score["supply_id"].unique()

        # Iterate over each supply_id
        for supply_id in unique_supply_ids:
            # Filter the DataFrame for the current supply_id
            temp_supply_all_property_df = property_mapped_supply_individual_score[
                property_mapped_supply_individual_score["supply_id"] == supply_id
            ].copy()

            # Normalize and assign scores
            temp_supply_all_property_df["Distance_score"] = normalize_series(temp_supply_all_property_df["Distance"])
            temp_supply_all_property_df["Capacity_score"] = normalize_series(
                temp_supply_all_property_df["vendor_supply_capacity"], highest_is_worst=False
            )
            
            # Weighted scores based on 'essential' column
            temp_supply_all_property_df['weighted_distance_score'] = np.where(
                temp_supply_all_property_df['essential'], 
                0.8 * temp_supply_all_property_df["Distance_score"], 
                (1 - 0.8) * temp_supply_all_property_df["Distance_score"]
            )
            temp_supply_all_property_df['weighted_capacity_score'] = np.where(
                temp_supply_all_property_df['essential'], 
                0.8 * temp_supply_all_property_df["Capacity_score"], 
                (1 - 0.8) * temp_supply_all_property_df["Capacity_score"]
            )

            # Append the processed DataFrame to the final DataFrame
            final_supply_score_df = pd.concat([final_supply_score_df, temp_supply_all_property_df], ignore_index=True)

        # Aggregate scores for each property_id
        dict_supply_dist_agg_score = {}
        dict_supply_agg_cap_score = {}
        for property_id in final_supply_score_df["property_id"].unique():
            dict_supply_dist_agg_score[property_id] = final_supply_score_df[
                final_supply_score_df["property_id"] == property_id
            ]["weighted_distance_score"].sum()
            dict_supply_agg_cap_score[property_id] = final_supply_score_df[
                final_supply_score_df["property_id"] == property_id
            ]["weighted_capacity_score"].sum()

        # Combine scores to calculate the final aggregated score
        final_scores = []
        for property_id in dict_supply_dist_agg_score.keys():
            final_aggregated_score = (
                weight_distance * dict_supply_dist_agg_score[property_id]
                + weight_capacity * dict_supply_agg_cap_score[property_id]
            )
            final_scores.append({"property_id": property_id, "final_score": final_aggregated_score})
        
        final_scores_df = pd.DataFrame(final_scores)

        final_scores_df["final_score"] = normalize_series(final_scores_df["final_score"], highest_is_worst=False)

        # Convert to a DataFrame for output
        return final_scores_df
    else:
        unique_property_list = list(property_latlong_df_for_no_supply["property_id"].unique())
        final_scores_df = pd.DataFrame({
            "property_id": unique_property_list,
            "final_score": [5]*(len(unique_property_list))
        })
        return final_scores_df

def process_incentive_df_to_send_solution_screen(df):
    grouped_df = (
        df.sort_values(by=['property_id', 'incentive_rank'], ascending=[True, False])
        .groupby('property_id')
        .agg({
            'incentive_id': lambda x: list(x),  # List of incentives
            'incentive_name': lambda x: list(x),
            'incentive_name': lambda x: list(x),
            'incentive_type': lambda x: list(x),
            'incentive_operation_start_date': lambda x: list(x),
            'incentive_operation_end_date': lambda x: list(x),
            'quantum_of_assistance': lambda x: list(x),
            'incentive_rank': lambda x: list(x),  # Corresponding scores
        })
        .reset_index()
    )
    return grouped_df

def process_approval_df_to_send_solution_screen(df):
    # Define custom stage order
    stage_order = {'Pre-Requisite': 1, 'Pre-Establishment': 2, 'Pre-Operation': 3, 'Others': 4}

    df['stage_order'] = df['stages'].map(stage_order)

    grouped_df = (
        df.sort_values(by=['property_id', 'stage_order', "time_taken"], ascending=[True, True, True])
        .groupby('property_id')
        .agg({
            'approval_id': lambda x: list(x),  # List of incentives
            'approval_name': lambda x: list(x),
            'government_department': lambda x: list(x),
            'time_taken': lambda x: list(x),
            'online_or_offline': lambda x: list(x),
            'stages': lambda x: list(x),
        })
        .reset_index()
    )
    return grouped_df

def process_supply_vendor_df_to_send_solution_screen(df):
    log_to_file("df is",str(df))
    if not df.empty:
        essential_supply_df = df[df["essential"]]
        non_essential_supply_df = df[~df["essential"]]
        grouped_essential_df = (
            essential_supply_df.sort_values(by=['property_id', 'No_of_vendors_found'], ascending=[True, False])
            .groupby('property_id')
            .agg({
                'supply_id': lambda x: list(x),  # List of incentives
                'vendor_id': lambda x: list(x),  # List of incentives
                'minimum_supply_requirement': lambda x: list(x),
                'vendor_supply_capacity': lambda x: list(x),
                'years_of_experience': lambda x: list(x),
                'no_of_locations': lambda x: list(x),
                'no_of_past_clients': lambda x: list(x),
                'no_of_servieces': lambda x: list(x),
                'no_of_employees': lambda x: list(x),
                'latitude_longitude': lambda x: list(x),
                'Distance': lambda x: list(x),
                'No_of_vendors_found': lambda x: list(x),
            })
            .reset_index()
        )
        grouped_non_essential_df = (
            non_essential_supply_df.sort_values(by=['property_id', 'No_of_vendors_found'], ascending=[True, False])
            .groupby('property_id')
            .agg({
                'supply_id': lambda x: list(x),  # List of incentives
                'vendor_id': lambda x: list(x),  # List of incentives
                'minimum_supply_requirement': lambda x: list(x),
                'vendor_supply_capacity': lambda x: list(x),
                'years_of_experience': lambda x: list(x),
                'no_of_locations': lambda x: list(x),
                'no_of_past_clients': lambda x: list(x),
                'no_of_servieces': lambda x: list(x),
                'no_of_employees': lambda x: list(x),
                'latitude_longitude': lambda x: list(x),
                'Distance': lambda x: list(x),
                'No_of_vendors_found': lambda x: list(x),
            })
            .reset_index()
        )
        return grouped_essential_df, grouped_non_essential_df
    else:
        return pd.DataFrame(), pd.DataFrame()

def sort_by_scores(df, scores_df):
    df_sorted = df.set_index('property_id').reindex(scores_df['Property_ID']).reset_index()
    return df_sorted