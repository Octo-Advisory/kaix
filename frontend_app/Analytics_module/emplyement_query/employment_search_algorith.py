import frappe
import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt
# from pandas.api.types import CategoricalDtype
import warnings
from frontend_app.Management_Class.helpers.progress import insert_process,update_process
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


def employment_search_algo(intention, input_data,chatId):
    """
    Employment search algorithm based on user intention.
    """
    try:
        with open("log.txt", "a") as file:
            file.write(f"\nentering in the function")
        frappe.log_error(f"use intension is{intention}")
        frappe.log_error(f"chatid is now {chatId}")
        insert_process(chatId,"Analyzing Your Query","Analyzing Your query","Pending")
        insert_process(chatId,"Fetching Data","Fetching Data Based On Your Query","Pending")
        insert_process(chatId,"Analyzing Data","Analyzing Gathered Data","Pending")   
        insert_process(chatId,"Preparing Result","Preparing Result","Pending")
        time.sleep(1)   
        update_process(chatId,"Analyzing Your Query","Processing")
        time.sleep(3)
        update_process(chatId,"Analyzing Your Query","Complete")
        #get Employement status
        update_process(chatId,"Fetching Data","Processing")
        Employment_Status = get_employment_status()
        time.sleep(3)
        update_process(chatId,"Fetching Data","Complete")
        update_process(chatId,"Analyzing Data","Processing")
        time.sleep(3)
        if intention == "Individual employment status":
            state = input_data.get("state")
            city = input_data.get("city_name")
            
            if not state and not city:
                #print("Invalid Choice")
                update_process(chatId,"Analyzing Data","Fail")
                response = {
                    "Analytics_response": "Invalid Choice",
                    "Is_Error" : True
                }
                return response
            
            elif state and not city:
                # State-wise Employment Status
                state_data = Employment_Status[Employment_Status['state'] == state]
                if state_data.empty:
                    #print(f"No data available for state: {state}")
                    update_process(chatId,"Analyzing Data","Fail")
                    response = {
                        "Analytics_response": "No data available for state",
                        "Is_Error" : True
                    }
                    return response
                
                # Calculate aggregated employment type data
                state_data["employment_type"] = state_data["employment_type"]
                state_summary = state_data.groupby("employment_type")["availability"].sum()
                img_base64 = plot_pie_chart(state_summary, f"State-wise Employment Status: {state}")
                #print(f"There are {state_data['city_name'].nunique()} cities in {state}.")
                response = {
                    "Analytics_response": state_summary,
                    "Is_Error" : False,
                    "chart_base64": img_base64
                }
                update_process(chatId,"Analyzing Data","Complete")
                update_process(chatId,"Preparing Result","Processing")
                time.sleep(3)
                update_process(chatId,"Preparing Result","Complete")
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
                        "Is_Error" : True
                    }
                    update_process(chatId,"Analyzing Data","Fail")
                    return response
                
                city_data["employment_type"] = city_data["employment_type"]
                city_summary = city_data.groupby("employment_type")["availability"].sum()
                img_base64 = plot_pie_chart(city_summary, f"City-wise Employment Status: {city}, {state}")
                response = {
                    "Analytics_response": city_summary,
                    "Is_Error" : False,
                    "chart_base64": img_base64
                }
                update_process(chatId,"Analyzing Data","Complete")
                update_process(chatId,"Preparing Result","Processing")
                time.sleep(5)
                update_process(chatId,"Preparing Result","Complete")
                return response
            
        elif intention == "Comparison between cities, states, or areas":
            cities = input_data.get("cities")
            if not cities or len(cities) < 2:
                #print("Comparison requires at least two cities.")
                response = {
                        "Analytics_response": "Comparison requires at least two cities",
                        "Is_Error" : True
                    }
                update_process(chatId,"Analyzing Data","Fail")
                return response
            
            # Check if cities are in the same state
            city_data = Employment_Status[Employment_Status['city_name'].isin(cities)]
            states = city_data['state'].unique()
            
            if len(states) != 1:
                #print("Cities must belong to the same state for comparison.")
                response = {
                        "Analytics_response": "Cities must belong to the same state for comparison.",
                        "Is_Error" : True
                    }
                update_process(chatId,"Analyzing Data","Fail")
                return response
            
            # Comparison of cities
            city_data["employment_type"] = city_data["employment_type"]
            comparison_data = city_data.groupby(['city_name', 'employment_type'])["availability"].sum().unstack()
            # comparison_data = comparison_data.reindex(columns=employment_order.categories)  # Reorder columns
            comparison_data_percentage = comparison_data.div(comparison_data.sum(axis=1), axis=0) * 100
            img_base64 = plot_bar_chart(comparison_data_percentage, f"Comparison Between Cities: {', '.join(cities)}")
            response = {
                    "Analytics_response": comparison_data_percentage,
                    "Is_Error" : False,
                    "chart_base64": img_base64
                }
            update_process(chatId,"Analyzing Data","Complete")
            update_process(chatId,"Preparing Result","Processing")
            time.sleep(5)
            update_process(chatId,"Preparing Result","Complete")
            return response
        
        else:
            #print("Invalid intention provided.")
            response = {
                        "Analytics_response": "Invalid intention provided.",
                        "Is_Error" : True
                    }
            update_process(chatId,"Analyzing Data","Fail")
            return response
    except Exception as e:
        return e

# def plot_pie_chart(data, title):
    """
    Plots a pie chart for employment data.
    """
    data.plot.pie(autopct='%1.1f%%', startangle=90, legend=False)
    plt.title(title)
    plt.ylabel("")  # Remove default ylabel
    plt.show()

# def plot_bar_chart(data, title):
    """
    Plots a bar chart for comparison between cities, grouped by employment type.
    """
    # Transpose the data so that cities are grouped under each employment type
    data = data.T
    
    data.plot(kind='bar', stacked=False)
    plt.title(title)
    plt.ylabel("Percentage (%)")
    plt.xlabel("Employment Type")
    plt.legend(title="City", loc='upper left', bbox_to_anchor=(1, 1))  # Place legend outside the chart
    plt.tight_layout()  # Adjust layout to fit everything
    plt.show()

def plot_pie_chart(data, title):
    """
    Plots a pie chart for employment data and returns it as a base64 string.
    """
    fig, ax = plt.subplots()
    data.plot.pie(autopct='%1.1f%%', startangle=90, legend=False, ax=ax)
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
    """
    fig, ax = plt.subplots()
    data.plot(kind='bar', stacked=False, ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Percentage (%)")
    ax.set_xlabel("Employment Type")
    
    # Convert plot to PNG and then to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close(fig)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    return img_base64