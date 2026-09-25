import frappe
import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt
# from pandas.api.types import CategoricalDtype
import warnings
from kaix.Management_Class.helpers.progress import insert_process,update_process
import time
import io
import base64

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

def get_employment_status():
    """
    Fetches employment availability data by joining employment types with location details.

    Returns:
        pd.DataFrame: Processed employment data containing employment type, city, state, and availability.
    """

    query = """
    SELECT
        area_employment_joined_table.employment_type,
        area_city_mapped.area_name,
        area_employment_joined_table.availability,
        area_city_mapped.city_name,
        area_city_mapped.state
    from (
        select te.employment_type, ecm.area, ecm.availability
        FROM `tabEmployment City Mapping` ecm
        JOIN `tabType of Employment` te
        ON ecm.employment_type = te.name) as area_employment_joined_table
    JOIN (
        select  a.name,a.area_name, a.city_id, c.city_name, c.state
        from `tabArea` as a
        join `tabCity` as c
        on a.city_id = c.name) as area_city_mapped
    on area_employment_joined_table.area = area_city_mapped.name
    """

    Employement_result = fetch_query_results (query)

    Employment_Status = pd.DataFrame(Employement_result, columns= ["employment_type","area_name","availability","city_name","state"])

    new_df= Employment_Status.drop(columns=["area_name"], axis=1)

    new_df.drop_duplicates(keep="first", inplace=True)

    new_df["availability"] = new_df["availability"].abs()

    return new_df

# Suppress all warnings
warnings.filterwarnings("ignore")


def employment_search_algo(intention, input_data,chatId,keyword_given_by_user):
    """
    Employment search algorithm to analyze and retrieve employment data based on user queries.
    
    Parameters:
    - intention (str): Type of analysis (e.g., 'Individual employment status', 'Comparison between cities, states, or areas').
    - input_data (dict): Contains user input like state, city, or a list of cities for comparison.
    - chatId (str): Unique identifier for tracking query progress.
    - keyword_given_by_user (list or None): Employment types to filter (e.g., 'Skilled', 'Unskilled').
    
    Returns:
    - dict: Response containing employment statistics, error flag, and visualization (if applicable).
    """
    try:
        
        with open("log.txt", "a") as file:
            file.write(f"\n I am here at this scenario UP: -> city and state: uushvjuicfgtvjvcv  IF {intention} Check {intention == 'Individual employment status'}")
        insert_process(chatId,"Analyzing Your Query","Analyzing Your query","Pending")
        insert_process(chatId,"Fetching Data","Fetching Data Based On Your Query","Pending")
        insert_process(chatId,"Analyzing Data","Analyzing Gathered Data","Pending")   
        insert_process(chatId,"Preparing Result","Preparing Result","Pending")
        time.sleep(1)   
        update_process(chatId,"Analyzing Your Query","Processing",0)
        time.sleep(2)
        update_process(chatId,"Analyzing Your Query","Complete",1)
        #get Employement status
        update_process(chatId,"Fetching Data","Processing",0)
        Employment_Status = get_employment_status()
        time.sleep(2)
        update_process(chatId,"Fetching Data","Complete",1)
        update_process(chatId,"Analyzing Data","Processing",0)
        time.sleep(2)
        with open("log.txt", "a") as file:
            file.write(f"\n I am here at this scenario DOWN: -> city and state: uushvjuicfgtvjvcv  IF {intention} Check {intention == 'Individual employment status'}")
        if intention == "Individual employment status":
            state = input_data.get("state")
            city = input_data.get("city_name")
            
            if not state and not city:
                #print("Invalid Choice")
                update_process(chatId,"Analyzing Data","Fail",0)
                response = {
                    "Analytics_response": "Invalid Choice",
                    "Is_Error" : True,
                    "intention" : intention
                }
                with open("log2.txt", "a") as file:
                    file.write(f"\n {intention} No city and state found in ~ {response} ::")
                return response
            
            # elif state and not city:
                # State-wise Employment Status
                state_data = Employment_Status[Employment_Status['state'] == state]
                if state_data.empty:
                    #print(f"No data available for state: {state}")
                    update_process(chatId,"Analyzing Data","Fail",0)
                    response = {
                        "Analytics_response": "No data available for state",
                        "Is_Error" : True,
                        "intention" : intention
                    }
                    with open("log2.txt", "a") as file:
                        file.write(f"\n state data empty {intention} ~ {response} ::")
                    return response
                
                # Calculate aggregated employment type data
                total_state_summary = state_data.groupby("employment_type")["availability"].sum()
                with open("log.txt", "a") as file:
                    file.write(f"\ntotal_state_summary {total_state_summary}")
                img_base64 = plot_pie_chart(total_state_summary, f"State-wise Employment Status: {state}")

                if not keyword_given_by_user:
                    response = {
                        "Analytics_response": {"total_state_summary" : total_state_summary.to_json() if not total_state_summary.empty else None},
                        "Is_Error" : False,
                        "chart_base64": img_base64,
                        "intention" : intention
                    }

                else:
                    # Separate selected employment types from others
                    selected_data = state_data[state_data["employment_type"].isin(keyword_given_by_user)]
                    other_data = state_data[~state_data["employment_type"].isin(keyword_given_by_user)]

                    selected_summary = selected_data.groupby("employment_type")["availability"].sum()
                    other_summary = other_data.groupby("employment_type")["availability"].sum()

                    response = {
                            "Analytics_response": {
                                "selected_data": selected_summary.to_json() if not selected_summary.empty else None,
                                "other_summary": other_summary.to_json() if not other_summary.empty else None
                            },
                            "Is_Error" : False,
                            "chart_base64": img_base64,
                            "intention" : intention
                        }
                
                update_process(chatId,"Analyzing Data","Complete",1)
                update_process(chatId,"Preparing Result","Processing",0)
                time.sleep(3)
                update_process(chatId,"Preparing Result","Complete",1)
                return response
            
            elif state and city:
                # City-wise Employment Status
                city_data = Employment_Status[
                    (Employment_Status['state'] == state) & 
                    (Employment_Status['city_name'] == city)
                ]
                if city_data.empty:
                    #print(f"No data available for city: {city} in state: {state}")
                    response = {
                        "Analytics_response": f"No data available for city: {city} in state: {state}",
                        "Is_Error" : True,
                        "intention" : intention
                    }
                    with open("log2.txt", "a") as file:
                        file.write(f"\n {intention} :~ {response} ::")
                    update_process(chatId,"Analyzing Data","Fail",0)
                    return response
                
                 # Always generate the pie chart with all employment types
                city_summary = city_data.groupby("employment_type")["availability"].sum()
                with open("log.txt", "a") as file:
                    file.write(f"\ncity_summary {city_summary}")
                img_base64 = plot_pie_chart(city_summary, f"City-wise Employment Status: {city}, {state}")
                if not keyword_given_by_user:
                    # If no keyword is provided, return the full summary as usual
                    city_summary_json = city_summary.to_json() if not city_summary.empty else None
                    response = {
                        "Analytics_response": {"city_summary":str(city_summary_json)},
                        "Is_Error" : False,
                        "chart_base64": img_base64,
                        "intention" : intention
                    }
                else:
                    # If keyword(s) is provided, split into selected and remaining employment types
                    selected_data = city_data[city_data["employment_type"].isin(keyword_given_by_user)]
                    remaining_data = city_data[~city_data["employment_type"].isin(keyword_given_by_user)]
                    
                    selected_summary = selected_data.groupby("employment_type")["availability"].sum()
                    remaining_summary = remaining_data.groupby("employment_type")["availability"].sum()

                    response = {
                        "Analytics_response": {
                            "selected_data": selected_summary.to_json() if not selected_summary.empty else None,
                            "remaining_summary": remaining_summary.to_json() if not remaining_summary.empty else None
                        },
                        "Is_Error" : False,
                        "chart_base64": img_base64,
                        "intention" : intention
                    }
                update_process(chatId,"Analyzing Data","Complete",1)
                update_process(chatId,"Preparing Result","Processing",0)
                time.sleep(3)
                update_process(chatId,"Preparing Result","Complete",1)
                return response
            
        elif intention == "Comparison between cities, states, or areas":
            cities = input_data.get("cities")
            if not cities or len(cities) < 2:
                #print("Comparison requires at least two cities.")
                response = {
                        "Analytics_response": "Comparison requires at least two cities",
                        "Is_Error" : True,
                        "intention" : intention
                    }
                with open("log2.txt", "a") as file:
                    file.write(f"\n Comparison reqquired at least 2 cities {intention} :~ {response} ::")
                update_process(chatId,"Analyzing Data","Fail",0)
                return response
            
            # Check if cities are in the same state
            city_data = Employment_Status[Employment_Status['city_name'].isin(cities)]
            states = city_data['state'].unique()
            
            if len(states) != 1:
                #print("Cities must belong to the same state for comparison.")
                response = {
                        "Analytics_response": "Cities must belong to the same state for comparison.",
                        "Is_Error" : True,
                        "intention" : intention
                    }
                with open("log2.txt", "a") as file:
                    file.write(f"\n Comparison Citieis must belon to same state {intention} ~ {response} ::")
                update_process(chatId,"Analyzing Data","Fail",0)
                return response
            
            if not keyword_given_by_user:
                city_data["employment_type"] = city_data["employment_type"]
                comparison_data = city_data.groupby(['city_name', 'employment_type'])["availability"].sum().unstack()
                # comparison_data = comparison_data.reindex(columns=employment_order.categories)  # Reorder columns
                comparison_data_percentage = comparison_data.div(comparison_data.sum(axis=1), axis=0) * 100
                img_base64 = plot_bar_chart(comparison_data_percentage, f"Comparison Between Cities: {', '.join(cities)}")
                response = {
                         "Analytics_response": {
                            "comparison_data": comparison_data.to_json() if not comparison_data.empty else None,
                            "comparison_data_percentage": comparison_data_percentage.to_json() if not comparison_data_percentage.empty else None
                        },
                        "Is_Error" : False,
                        "chart_base64": img_base64,
                        "intention" : intention
                    }
            else:
                # Split employment types into selected and others
                selected_data = city_data[city_data["employment_type"].isin(keyword_given_by_user)]
                other_data = city_data[~city_data["employment_type"].isin(keyword_given_by_user)]

                # Compute grouped data
                selected_comparison = selected_data.groupby(['city_name', 'employment_type'])["availability"].sum().unstack()
                other_comparison = other_data.groupby(['city_name', 'employment_type'])["availability"].sum().unstack()
                with open("log2.txt", "a") as file:
                    file.write(f"\n Comparison Selected and Other ~ {selected_comparison} ::::: {other_comparison}")
                # Convert "other" employment types into a single column
                # other_comparison = other_comparison.to_frame(name="Other Employment Types")

                # Compute percentages
                # selected_comparison_percentage = selected_comparison.div(selected_comparison.sum(axis=1), axis=0) * 100
                # other_comparison_percentage = other_comparison.div(other_comparison.sum(axis=1), axis=0) * 100

                # Plot the full bar chart for all employment types (Skilled, Semi-Skilled, Unskilled)
                full_comparison = city_data.groupby(['city_name', 'employment_type'])["availability"].sum().unstack()
                full_comparison_percentage = full_comparison.div(full_comparison.sum(axis=1), axis=0) * 100
                img_base64 = plot_bar_chart(full_comparison_percentage, f"Comparison Between Cities: {', '.join(cities)}")
                response = {
                    "Analytics_response": {
                        "selected_comparison": selected_comparison.to_json() if not selected_comparison.empty else None,
                        "other_comparison": other_comparison.to_json() if not other_comparison.empty else None
                    },
                    "Is_Error" : False,
                    "chart_base64": img_base64,
                    "intention" : intention
                }
                with open("log2.txt", "a") as file:
                    file.write(f"\n Comparison Selected full comparison ~ {response} ::")
                # return response
            update_process(chatId,"Analyzing Data","Complete",1)
            update_process(chatId,"Preparing Result","Processing",0)
            time.sleep(3)
            update_process(chatId,"Preparing Result","Complete",1)
            return response
        
        else:
            #print("Invalid intention provided.")
            response = {
                        "Analytics_response": "Invalid intention provided.",
                        "Is_Error" : True,
                        "intention" : intention
                    }
            with open("log2.txt", "a") as file:
                file.write(f"\n Comparison Selected and Other else PArt~ {response} ::")
            update_process(chatId,"Analyzing Data","Fail",0)
            return response
    except Exception as e:
        with open("log2.txt", "a") as file:
            file.write(f"\n Comparison Selected and Other Exception~ {e} ::")
        return e


def plot_pie_chart(data, title):
    """
    Plots a pie chart for employment data with actual counts and percentages.
    Returns the chart as a base64 string.
    """
    fig, ax = plt.subplots()

    # Define autopct function to show count and percentage
    def autopct_format(pct):
        total = sum(data)
        count = int(round(pct * total / 100))  # Convert percentage to count
        return f"{count} ({pct:.1f}%)"  # Format as count (percentage)

    # Plot pie chart
    wedges, texts, autotexts = ax.pie(
        data, 
        labels=data.index, 
        autopct=autopct_format,  # Show count and percentage
        startangle=90, 
        wedgeprops={'edgecolor': 'black'}
    )

    # Adjust font size for better readability
    for text in texts + autotexts:
        text.set_fontsize(10)

    ax.set_title(title)
    ax.set_ylabel("")  # Remove default ylabel
    
    # Convert plot to PNG and then to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close(fig)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    return img_base64

def plot_bar_chart(data, title):
    """
    Plots a bar chart and returns it as a base64 string.
    Adds percentage labels on top of the bars for clarity.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Transpose if needed to group by employment type
    data = data.T  
    data.plot(kind='bar', stacked=False, ax=ax)

    ax.set_title(title)
    ax.set_ylabel("Percentage (%)")
    ax.set_xlabel("Employment Type")

    # Improve legend placement
    ax.legend(title="City", loc='upper left', bbox_to_anchor=(1, 1))

    # Add percentage labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', label_type='edge', fontsize=10, padding=3)

    # Adjust layout
    plt.xticks(rotation=45, ha="right")  
    plt.tight_layout()

    # Convert to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight')
    plt.close(fig)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')

    return img_base64