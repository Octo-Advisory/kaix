import pandas as pd
from datetime import datetime
import frappe
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
        industry_id = results[0][0]  # Get the first row, first column
    else:
        industry_id = None
    return industry_id

def fetch_sub_sector_details(given_sub_sector_by_user):
    if given_sub_sector_by_user != None:
        query = f"""
        SELECT name, zone_id
        FROM `tabSub Sector`
        WHERE sub_sector_name = "{given_sub_sector_by_user}"
        """
        results = fetch_query_results(query)
                
        # Call the function and assign results
        results = fetch_query_results(query)

        # Assign variables based on results
        if results:
            sub_sector_id = results[0][0]  # Get the first row, first column
            zone_id = results[0][1]
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
        # [row[0] for row in results]
        # print(f"Fetched list of all area id: \n{area_id}")
    else:
        area_id = None
    return area_id

def fetch_city_details(given_city_by_user):
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

def get_incentive_data(sub_sector_id=None, industry_id=None, area_id=None, city_id=None, state_id=None, today_date=None):
    with open("log2.txt", "a") as file:
            file.write(f"\nstate is {sub_sector_id, industry_id, area_id, city_id, state_id, today_date}")
    # Initialize the query string with the common parts
    sql_query = """
    SELECT i.name, i.incentive_name, i.incentive_type, i.quantum_of_assistance, i.incentive_operation_start_date, i.incentive_operation_end_date, iim.sub_sector, iim.industry, iim.area, iim.city, iim.state, 
           i.incentive_rank, iim.city_level, iim.state_level, iim.country_level, iim.pan_industries
    FROM `tabIncentive Industry Mapping` iim
    JOIN `tabIncentive` i ON i.name = iim.incentive
    WHERE 
    """

    # Define condition list
    conditions = []
    
    if sub_sector_id and industry_id and area_id and city_id and state_id:
        # print("I'm in Condition 1")
        conditions.append(f"""
        (iim.sub_sector = '{sub_sector_id}' OR (iim.sub_sector IS NULL AND iim.industry = '{industry_id}') OR (iim.pan_industries = 1))
        AND (
            iim.area IN ('{area_id}')  
            OR (iim.area IS NULL AND (iim.city IN ('{city_id}') AND iim.city_level = 1))
            OR (iim.area IS NULL AND iim.city IS NULL AND (iim.state IN ('{state_id}') AND iim.state_level = 1))
            OR (iim.country_level = 1)
        )
        """)

    elif not sub_sector_id and industry_id and area_id and city_id and state_id:
        # print("I'm in Condition 2")
        conditions.append(f"""
        (iim.sub_sector IS NULL AND iim.industry = '{industry_id}' OR iim.pan_industries = 1)
        AND (
            iim.area IN ('{area_id}')
            OR (iim.area IS NULL AND (iim.city IN ('{city_id}') AND iim.city_level = 1))
            OR (iim.area IS NULL AND iim.city IS NULL AND (iim.state IN ('{state_id}') AND iim.state_level = 1))
            OR (iim.country_level = 1)
        )
        """)

    elif sub_sector_id and industry_id and not area_id and city_id and state_id:
        # print("I'm in Condition 3")
        conditions.append(f"""
        (iim.sub_sector = '{sub_sector_id}' OR (iim.sub_sector IS NULL AND iim.industry = '{industry_id}') OR iim.pan_industries = 1)
        AND (
            iim.city IN ('{city_id}') AND iim.city_level = 1
            OR (iim.area IS NULL AND iim.city IS NULL AND (iim.state IN ('{state_id}') AND iim.state_level = 1))
            OR (iim.country_level = 1)
        )
        """)

    elif sub_sector_id and industry_id and not area_id and not city_id and state_id:
        # print("I'm in Condition 4")
        conditions.append(f"""
        (iim.sub_sector = '{sub_sector_id}' OR (iim.sub_sector IS NULL AND iim.industry = '{industry_id}') OR iim.pan_industries = 1)
        AND (
            iim.state IN ('{state_id}') AND iim.state_level = 1
            OR iim.country_level = 1
        )
        """)

    elif not sub_sector_id and industry_id and not area_id and city_id and state_id:
        # print("I'm in Condition 5")
        conditions.append(f"""
        (iim.sub_sector IS NULL AND iim.industry = '{industry_id}' OR iim.pan_industries = 1)
        AND (
            iim.city IN ('{city_id}') AND iim.city_level = 1
            OR (iim.area IS NULL AND iim.city IS NULL AND (iim.state IN ('{state_id}') AND iim.state_level = 1))
            OR (iim.country_level = 1)
        )
        """)

    elif not sub_sector_id and not area_id and not city_id and industry_id and state_id:
        # print("I'm in Condition 6")
        conditions.append(f"""
        (iim.sub_sector IS NULL AND iim.industry = '{industry_id}' OR iim.pan_industries = 1)
        AND (
            iim.state IN ('{state_id}') AND iim.state_level = 1
            OR iim.country_level = 1
        )
        """)

    # Combine conditions into SQL query
    if conditions:
        sql_query += " OR ".join(conditions)

    # Add the incentive operation date check if a valid date is provided
    if today_date:
        sql_query += f" AND '{today_date}' BETWEEN i.incentive_operation_start_date AND i.incentive_operation_end_date"

    # Close SQL statement
    sql_query += ";"
    
    # Execute the query
    results = fetch_query_results(sql_query)  # Ensure fetch_query_results() is correctly implemented
    
    # Process results
    if results:
        Incentive_only_df = pd.DataFrame(results, columns=[
            'incentive_id', 'Incentive_name', 'Incentive Type', 'Incentive Details', 'Incentive Start Date', 'Incentive End Date', 'sub_sector_id', 'industry_id', 
            'area_id', 'city_id', 'state_id', 'incentive_rank', "city_level", "state_level", 
            "country_level", "pan_industries"
        ])
        Incentive_only_df['incentive_rank'] = pd.to_numeric(Incentive_only_df['incentive_rank'], errors='coerce').astype('Int64')
        return (Incentive_only_df)
    else:
        return None

def incentive_details(df, area_id=None, city_id=None, state_id=None, keyword_given_by_user= None, incentive_keyword_df = None):
    results = []
    if area_id:
        # Area-level approvals
        area_df = df[df['area_id'] == area_id]
        if not area_df.empty:
            for _, row in area_df.iterrows():
                results.append({
                    'Incentive ID': row['incentive_id'],
                    'Incentive Name': row['Incentive_name'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Rank': row['incentive_rank'],
                    'Incentive Details': row['Incentive Details'],
                    'Incentive Start Date': row['Incentive Start Date'],
                    'Incentive End Date': row['Incentive End Date'],
                    'Level': 'Area'
                })
        
        # City-level approvals
        city_df = df[(df['city_level'] == 1) & (df['area_id'].isna())]
        if not city_df.empty:
            for _, row in city_df.iterrows():
                results.append({
                    'Incentive ID': row['incentive_id'],
                    'Incentive Name': row['Incentive_name'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Rank': row['incentive_rank'],
                    'Incentive Details': row['Incentive Details'],
                    'Incentive Start Date': row['Incentive Start Date'],
                    'Incentive End Date': row['Incentive End Date'],
                    'Level': 'City'
                })
        
        # State-level approvals
        state_df = df[(df['state_level'] == 1) & (df['city_id'].isna()) & (df['area_id'].isna())]
        if not state_df.empty:
            for _, row in state_df.iterrows():
                results.append({
                    'Incentive ID': row['incentive_id'],
                    'Incentive Name': row['Incentive_name'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Rank': row['incentive_rank'],
                    'Incentive Details': row['Incentive Details'],
                    'Incentive Start Date': row['Incentive Start Date'],
                    'Incentive End Date': row['Incentive End Date'],
                    'Level': 'State'
                })
    
    elif city_id:
        # City-level approvals
        city_df = df[(df['city_id'] == city_id) & (df['city_level'] == 1)]
        if not city_df.empty:
            for _, row in city_df.iterrows():
                results.append({
                    'Incentive ID': row['incentive_id'],
                    'Incentive Name': row['Incentive_name'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Rank': row['incentive_rank'],
                    'Incentive Details': row['Incentive Details'],
                    'Incentive Start Date': row['Incentive Start Date'],
                    'Incentive End Date': row['Incentive End Date'],
                    'Level': 'City'
                })
        
        # State-level approvals
        state_df = df[(df['state_level'] == 1) & (df['city_id'].isna()) & (df['area_id'].isna())]
        if not state_df.empty:
            for _, row in state_df.iterrows():
                results.append({
                    'Incentive ID': row['incentive_id'],
                    'Incentive Name': row['Incentive_name'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Rank': row['incentive_rank'],
                    'Incentive Details': row['Incentive Details'],
                    'Incentive Start Date': row['Incentive Start Date'],
                    'Incentive End Date': row['Incentive End Date'],
                    'Level': 'State'
                })
    elif state_id:
        # State-level approvals
        state_df = df[(df['state_level'] == 1) & (df['city_id'].isna()) & (df['area_id'].isna())]
        if not state_df.empty:
            for _, row in state_df.iterrows():
                results.append({
                    'Incentive ID': row['incentive_id'],
                    'Incentive Name': row['Incentive_name'],
                    'Incentive Type': row['Incentive Type'],
                    'Incentive Rank': row['incentive_rank'],
                    'Incentive Details': row['Incentive Details'],
                    'Incentive Start Date': row['Incentive Start Date'],
                    'Incentive End Date': row['Incentive End Date'],
                    'Level': 'State'
                })
    # Country-level approvals
    country_df = df[(df['country_level'] == 1) & (df['state_id'].isna()) & (df['city_id'].isna()) & (df['area_id'].isna())]
    if not country_df.empty:
        for _, row in country_df.iterrows():
            results.append({
                'Incentive ID': row['incentive_id'],
                'Incentive Name': row['Incentive_name'],
                'Incentive Type': row['Incentive Type'],
                'Incentive Rank': row['incentive_rank'],
                'Incentive Details': row['Incentive Details'],
                'Incentive Start Date': row['Incentive Start Date'],
                'Incentive End Date': row['Incentive End Date'],
                'Level': 'Country'
            })
    
    # Convert to DataFrame
    result_df = pd.DataFrame(results).sort_values(by='Incentive Rank',ascending=False)
    if not keyword_given_by_user:
        return {
            "Filtered Incentive Data":None,
            "Unfiltered Incentive Data":result_df.to_json(),
            }
    
    else:
        keyword_result = filter_df_by_keywords(keyword_given_by_user, incentive_keyword_df)
        filtered_keyword_df, unfiltered_keyword_df = keyword_result[0], keyword_result[1]

        if len(filtered_keyword_df) != 0:
            filtered_result_df = pd.merge(result_df, filtered_keyword_df, left_on="Incentive ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score", "Incentive Rank"], ascending=[False, False])
            unfiltered_result_df = pd.merge(result_df, unfiltered_keyword_df, left_on="Incentive ID", right_on="ID").drop("ID", axis=1).sort_values(by=["Incentive Rank", "aggregated_score"], ascending=[False, False])
            return {            
                "Filtered Incentive Data":filtered_result_df.to_json(),
                "Unfiltered Incentive Data":unfiltered_result_df.to_json(),
                }
        else:
            unfiltered_result_df = pd.merge(result_df, unfiltered_keyword_df, left_on="Approval ID", right_on="ID").drop("ID", axis=1).sort_values(by=["aggregated_score", "Incentive Rank"], ascending=[False, False])
            return {
                "Filtered Incentive Data":None,
                "Unfiltered Incentive Data":unfiltered_result_df.to_json()
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
