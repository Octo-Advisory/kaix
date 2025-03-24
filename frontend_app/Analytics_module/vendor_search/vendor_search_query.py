import frappe
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import traceback
import json
import spacy
from typing import List, Tuple
nlp = spacy.load("en_core_web_lg")

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

def fetch_supply_data(given_industry_by_user, given_sub_sector_by_user, given_segment_by_user,given_supplies_by_user):

    if given_industry_by_user is None and given_sub_sector_by_user is None and given_segment_by_user is None:
        # print("No industry, sub-sector, or segment provided. Returning supply_id_str.")
        supply_id = given_supplies_by_user
        return supply_id  # Returns None since it was initialized

    else:
        industry_id = None
        sub_sector_id = None 
        segment_id = None
        # Fetching Industry_id
        if given_industry_by_user is not None:
            query = f"""
            SELECT name
            FROM `tabIndustry`
            WHERE industry_name = '{given_industry_by_user}'
            """
            results = fetch_query_results(query)
            industry_id = results[0][0] if results else None
            # print(f"Fetched industry_id: {industry_id}" if industry_id else "No industry found.")

        # Fetching Subsector_id
        if given_sub_sector_by_user is not None:
            query = f"""
            SELECT name
            FROM `tabSub Sector`
            WHERE sub_sector_name = '{given_sub_sector_by_user}'
            """
            results = fetch_query_results(query)
            sub_sector_id = results[0][0] if results else None
            # print(f"Fetched subsector_id: {sub_sector_id}" if sub_sector_id else "No sub-sector found.")

        # Fetching Segment_id
        if given_segment_by_user is not None:
            query = f"""
            SELECT name
            FROM `tabSegment`
            WHERE segment = '{given_segment_by_user}'
            """
            results = fetch_query_results(query)
            segment_id = results[0][0] if results else None
            # print(f"Fetched segment_id: {segment_id}" if segment_id else "No segment found.")

        # Fetching Supplies
        supply_rules_query = None
        if industry_id and sub_sector_id and segment_id:
            supply_rules_query = f"""
            SELECT supply
            FROM `tabSupply Rules`
            WHERE industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment = '{segment_id}'
            """
            results = fetch_query_results(supply_rules_query)

            if not results:
                return fetch_supply_data(industry_id, sub_sector_id)
            
        elif industry_id and sub_sector_id and segment_id is None:
            supply_rules_query = f"""
            SELECT supply
            FROM `tabSupply Rules`
            WHERE industry = '{industry_id}' AND sub_sector = '{sub_sector_id}'
            """

            if not results:
                return fetch_supply_data(industry_id)


        elif industry_id and sub_sector_id is None and segment_id is None:
            supply_rules_query = f"""
            SELECT supply
            FROM `tabSupply Rules`
            WHERE industry = '{industry_id}'
            """
            results = fetch_query_results(supply_rules_query)
            if not results:
                return []

        if supply_rules_query:
            results = fetch_query_results(supply_rules_query)
            if not results:
                return None  # Return None when no results are found
            return results
        else:
            return None

def vendor_df(supply_id_str):
    vendor_fetching_query = f""" 
    select VSC.parent, VSC.parent, VSC.supply, VSC.maximum_supply_capacity, 
        V.years_of_experience, V.no_of_location, V.no_of_past_clients, 
        V.no_of_services, V.no_of_employees, V.latitude_longitude, V.certifications, VSC.supply_description_by_vendor
    From `tabVendor` AS V
    Join `tabVendor Supply Capacity` as VSC
    ON V.name = VSC.parent
    WHERE supply IN ({supply_id_str})
    """

    # Execute the query using the fetch_query_results function
    results = fetch_query_results(vendor_fetching_query)

    # Convert the query results to a pandas DataFrame
    if results:
        # Define the column names corresponding to the SELECT statement
        vendor_df = pd.DataFrame(results, columns=['vendor_id', 'vendor_name', 'supply_id', 'vendor_supply_capacity', 
                                        'years_of_experience', 'no_of_locations', 'no_of_past_clients', 
                                        'no_of_servieces', 'no_of_employees', 'latitude_longitude', 'Certifications', 'Description'])
    else:
        vendor_df = pd.DataFrame()
    return vendor_df

# Function to transform data
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

def calculate_distance(loc1: str, loc2: str) -> float:
    """
    Calculate the distance between two locations given as strings
    with latitude and longitude in degrees.

    Parameters:
    loc1 (str): Latitude and longitude of the first location as "lat, long".
    loc2 (str): Latitude and longitude of the second location as "lat, long".

    Returns:
    float: Distance between the two locations in kilometers.
    """
    # Parse the string inputs into floats
    lat1, lon1 = map(float, loc1.split(","))
    lat2, lon2 = map(float, loc2.split(","))
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_earth_km = 6371  # Earth's radius in kilometers
    
    # Calculate the distance
    distance = radius_earth_km * c
    return distance

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
        return False  # In case conversion to float fails

def calculate_distance(loc1: str, loc2: str) -> float:
    # Check if both loc1 and loc2 are valid lat/lon strings
    if not (is_valid_latlong(loc1) and is_valid_latlong(loc2)):
        return 0.0  # Return 0 if any of the coordinates are invalid
    
    lat1, lon1 = map(float, loc1.split(","))
    lat2, lon2 = map(float, loc2.split(","))
    
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return 6371 * c  # Earth's radius in kilometers


def calculate_vendor_property_distances(input_data: dict) -> dict:
    """
    Computes distances between vendors and properties.
    Uses `calculate_distance()` for distance calculation.
    
    Parameters:
    input_data (dict): Dictionary containing "Vendor" and "Property" lists.

    Returns:
    dict: A nested dictionary where vendors map to properties with distances.
    """
    output = {}

    for vendor in input_data.get("Vendor", []):
        vendor_id = vendor["id"]
        vendor_latlong = vendor["latlong"]

        # Skip invalid vendor coordinates
        if not is_valid_latlong(vendor_latlong):
            continue

        vendor_distances = {}
        for property in input_data.get("Property", []):
            property_id = property["id"]
            property_latlong = property["latlong"]

            # Skip invalid property coordinates
            if not is_valid_latlong(property_latlong):
                continue

            # Calculate distance
            distance = calculate_distance(vendor_latlong, property_latlong)
            vendor_distances[property_id] = distance

        # Only add vendor if it has valid distances
        if vendor_distances:
            output[vendor_id] = vendor_distances

    return output


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

def get_supply_scores(property_latlong_df, supply_rules_df, vendor_df, prefered_range, tolerable_range,keyword_given_by_user,vendor_keyword_df):
    try:
        supply_rules_df.fillna(0, inplace=True)
        vendor_df.fillna(0, inplace=True)
        input_data_for_map = transform_data_for_map_call(vendor_df[["vendor_id", "latitude_longitude"]], property_latlong_df)
        vendor_property_distance = calculate_vendor_property_distances(input_data_for_map)
        missing_vendor_from_distance_dict = list(set(list(vendor_df["vendor_id"].unique())) ^ set(vendor_property_distance.keys()))
        if len(missing_vendor_from_distance_dict) > 0:
            vendor_df = vendor_df[~vendor_df["vendor_id"].isin(missing_vendor_from_distance_dict)]
        final_results = []  # Store results for all property-supply combinations
        better_results = []
        all_vendors_df = pd.DataFrame()
        # Loop through all properties
        for _, property_row in property_latlong_df.iterrows():
            property_id = property_row['property_id']
            if all(property_id in vendor_property_distance[ven_id].keys() for ven_id in list(vendor_property_distance.keys())):
                # Loop through all supplies
                for _, supply_row in supply_rules_df.iterrows():
                    supply_id = supply_row['supply_id']
                    minimum_supply_requirement = 0
                    # print("minimum_supply_requirement:",minimum_supply_requirement)
                    # essential = (supply_row['essentials_items']).lower() == "yes"
                    
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
                        
                        # print("vendors_for_supply are:",vendors_for_supply)
                        # Find the best vendor based on the logic provided
                        req_cap = minimum_supply_requirement
                        pref_r = prefered_range
                        final_result_for_vendors_df = vendors_for_supply[["supply_id", "Final_Score_With_Features", "vendor_id", "vendor_supply_capacity", 'years_of_experience', 'no_of_locations', 'no_of_past_clients', 'no_of_servieces', 'no_of_employees', 'latitude_longitude', "Dist"]].sort_values(by =["Final_Score_With_Features"], ascending = False)
                        all_vendors_df = pd.concat([all_vendors_df, final_result_for_vendors_df], axis=0)
                        best_ranked_row = vendors_for_supply.loc[
                            vendors_for_supply["Final_Score_With_Features"].idxmax()
                        ] 
                        
                        if best_ranked_row["vendor_supply_capacity"] >= req_cap:
                            # print("The Best Solution: \n", best_ranked_row[[
                            #     "vendor_id","supply_id", "vendor_supply_capacity", "Dist", "Final Ranking", "Fea_rank", "Final_Score_With_Features"
                            # ]])
                            final_results.append({
                                # "property_id": property_id,
                                "supply_id": supply_id,
                                # "minimum_supply_requirement": minimum_supply_requirement,
                                "Final_Score_With_Features": best_ranked_row["Final_Score_With_Features"],
                                "vendor_id": best_ranked_row["vendor_id"],
                                "vendor_supply_capacity": best_ranked_row["vendor_supply_capacity"],
                                "years_of_experience": best_ranked_row["years_of_experience"],
                                "no_of_locations": best_ranked_row["no_of_locations"],
                                "no_of_past_clients": best_ranked_row["no_of_past_clients"],
                                "no_of_servieces": best_ranked_row["no_of_servieces"],
                                "no_of_employees": best_ranked_row["no_of_employees"],
                                "latitude_longitude": best_ranked_row["latitude_longitude"],
                                "Dist": best_ranked_row["Dist"],
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
                                        # "property_id": property_id,
                                        "supply_id": supply_id,
                                        # "essential": essential,
                                        # "minimum_supply_requirement": minimum_supply_requirement,
                                        "Final_Score_With_Features": best_ranked_row["Final_Score_With_Features"],
                                        "vendor_id": best_ranked_row["vendor_id"],
                                        "vendor_supply_capacity": best_ranked_row["vendor_supply_capacity"],
                                        "years_of_experience": best_ranked_row["years_of_experience"],
                                        "no_of_locations": best_ranked_row["no_of_locations"],
                                        "no_of_past_clients": best_ranked_row["no_of_past_clients"],
                                        "no_of_servieces": best_ranked_row["no_of_servieces"],
                                        "no_of_employees": best_ranked_row["no_of_employees"],
                                        "latitude_longitude": best_ranked_row["latitude_longitude"],
                                        "Dist": best_ranked_row["Dist"],
                                        "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                                        
                                    }
                                )
                                final_results.append({
                                    # "property_id": property_id,
                                    "supply_id": supply_id,
                                    # "essential": essential,
                                    # "minimum_supply_requirement": minimum_supply_requirement,
                                    "Final_Score_With_Features": best_g_cap_row["Final_Score_With_Features"],
                                    "vendor_id": best_g_cap_row["vendor_id"],
                                    "vendor_supply_capacity": best_g_cap_row["vendor_supply_capacity"],
                                    "years_of_experience": best_g_cap_row["years_of_experience"],
                                    "no_of_locations": best_g_cap_row["no_of_locations"],
                                    "no_of_past_clients": best_g_cap_row["no_of_past_clients"],
                                    "no_of_servieces": best_g_cap_row["no_of_servieces"],
                                    "no_of_employees": best_g_cap_row["no_of_employees"],
                                    "latitude_longitude": best_g_cap_row["latitude_longitude"],
                                    "Dist": best_g_cap_row["Dist"],
                                    "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                                    
                                    })
                            else:
                                # print("The Best Solution: \n", best_ranked_row[[
                                #     "vendor_id","supply_id", "vendor_supply_capacity", "Dist", "Final Ranking", "Fea_rank", "Final_Score_With_Features"
                                # ]], "\nOptions: Combinations")
                                final_results.append({
                                    # "property_id": property_id,
                                    "supply_id": supply_id,
                                    # "essential": essential,
                                    # "minimum_supply_requirement": minimum_supply_requirement,
                                    "Final_Score_With_Features": best_ranked_row["Final_Score_With_Features"],
                                    "vendor_id": best_ranked_row["vendor_id"],
                                    "vendor_supply_capacity": best_ranked_row["vendor_supply_capacity"],
                                    "years_of_experience": best_ranked_row["years_of_experience"],
                                    "no_of_locations": best_ranked_row["no_of_locations"],
                                    "no_of_past_clients": best_ranked_row["no_of_past_clients"],
                                    "no_of_servieces": best_ranked_row["no_of_servieces"],
                                    "no_of_employees": best_ranked_row["no_of_employees"],
                                    "latitude_longitude": best_ranked_row["latitude_longitude"],
                                    "Dist": best_ranked_row["Dist"],
                                    "No_of_vendors_found": len(vendors_for_supply["vendor_id"].unique())
                                    
                                })
        final_df = pd.DataFrame(final_results)
        better_df = pd.DataFrame(better_results)
        # return final_df.to_json, better_df.to_json, all_vendors_df.to_json
        if not keyword_given_by_user :
            return {"Best Supplier": final_df.to_json(),
                    "Better Supplier": better_df.to_json(),
                    "Filtered All Supplier" : None,
                    "Unfiltered All Supplier" : all_vendors_df.to_json()}
        else:
            keyword_result = filter_df_by_keywords(keyword_given_by_user, vendor_keyword_df)
            filtered_keyword_df, unfiltered_keyword_df = keyword_result[0], keyword_result[1]
            if len(filtered_keyword_df) != 0:
                filtered_result_df = pd.merge(all_vendors_df, filtered_keyword_df, left_on="vendor_id", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                unfiltered_result_df = pd.merge(all_vendors_df, unfiltered_keyword_df, left_on="vendor_id", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                unfiltered_result_df = pd.concat([filtered_result_df, unfiltered_result_df], axis= 0, ignore_index= True).sort_values(by = 'aggregated_score')
                return {
                        "Best Supplier": final_df.to_json(),
                        "Better Supplier": better_df.to_json(),
                        "Filtered All Supplier": filtered_result_df.to_json(),
                        "Unfiltered All Supplier":unfiltered_result_df.to_json()
                        }
            else:
                unfiltered_result_df = pd.merge(all_vendors_df, unfiltered_keyword_df, left_on="vendor_id", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score"], ascending=False)
                return {
                        "Best Supplier": final_df.to_json(),
                        "Better Supplier": better_df.to_json(),
                        "Filtered All Supplier": None,
                        "Unfiltered All Supplier":unfiltered_result_df.to_json()
                        }
    except Exception as e:
        error_message = traceback.format_exc()
        with open("log.txt", "a") as file:
            file.write(f"\nerror_message from analtics {error_message}")
        return e
    
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
