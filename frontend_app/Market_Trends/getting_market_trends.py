from frontend_app.Market_Trends.market_trends import get_market_trends
import requests
import json
import frappe

    
def retreiving_sql_database_or_llm_market_trends(sql_query,llm_query,main_industry,sub_sector,segment,state,city):
    # Try to fetch from database
    sql_or_llm_results = frappe.db.sql(sql_query) #Changed by Jenith on 24-06
    # print(sql_or_llm_results)
    # CHECK sql_or_llm_results

    # Initialize fallback flag
    check = "sql"

    # Check if SQL query failed or returned invalid/empty value
    if (sql_or_llm_results == "Error" or
    not sql_or_llm_results or
    sql_or_llm_results[0][-3] in [None, '', 'null', "'',", '"",', '"" ,']):


        # print("🛑 Invalid or empty result from SQL. Falling back to LLM...")
        check = "llm"
        websearch_agent_result = get_market_trends(
            llm_query,
            main_industry,
            sub_sector,
            segment,
            state,
            city,
        )

        market_trends_0 = websearch_agent_result
        local_laws = None if not sql_or_llm_results else sql_or_llm_results[0][-2]
        taxes =  None if not sql_or_llm_results else sql_or_llm_results[0][-1]
        return market_trends_0, local_laws, taxes, check
    
    # SQL result is valid
    market_trends_0 = sql_or_llm_results[0][-3] ## market trends
    local_laws = sql_or_llm_results[0][-2]
    taxes = sql_or_llm_results[0][-1]

    return market_trends_0, local_laws, taxes, check


def updating_database_with_llm_market_trends(update_check, final_results, segment=None, sub_sector=None, main_industry=None, state=None, city=None, pan_industry=0, pan_state=0, pan_sub_sector=0):
    if update_check != "llm":
        return  # Do nothing if not falling back to LLM

    # check_url = "https://marsinfraix.marsbazaar.com/api/resource/Regulatory insights"
    # headers = {
    #     "Authorization": "token d3de1e0e4e25846:51fd8e403a19045",
    #     "Content-Type": "application/json",
    #     "Expect": ""  # prevent 417 error
    # }

    # Step 1: Collect all possible parameters
    field_map = {
        "industry": main_industry,             # str or None
        "sub_sector": sub_sector,              # str or None
        "segment": segment,                    # str or None
        "state": state,                        # str or None
        "city": city,                          # str or None
        "pan_industry": pan_industry,          # int (1) or None
        "pan_state": pan_state,                # int (1) or None
        "pan_sub_sector": pan_sub_sector       # int (1) or None
    }


    # # Step 2: Dynamically build filters list (for GET request)
    # filters_list = []
    # for key, value in field_map.items():
    #     if isinstance(value, str):
    #         if value.strip().lower() != "null":
    #             filters_list.append(["Regulatory insights", key, "=", value]) 
    #     elif isinstance(value, int):
    #         filters_list.append(["Regulatory insights", key, "=", value])
    #     # else ignore None

    # filters = {
    #     "filters": json.dumps(filters_list)
    # }

    try:
        # ______Added By Jenith on 26-06_________________________________________________________________________
        exists = frappe.db.get_value("Regulatory insights", field_map, 'name')

        if exists:
            docname = exists
            frappe.db.set_value("Regulatory insights", docname, "market_trends", final_results)
            frappe.db.commit()
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 Updated Doctype Name : {docname} , fields Updated: {final_results}")
        # _______________________________________________________________________________
        
        # Step 3: Try to fetch existing record
        # check_response = requests.get(check_url, headers=headers, params=filters)
        # check_response.raise_for_status()
        # existing_data = check_response.json()

        # if existing_data.get("data"):
            # Step 4: Update existing record
            # existing_docname = existing_data["data"][0]["name"]
            # update_url = f"{check_url}/{existing_docname}"
            # update_payload = {
            #     "market_trends": final_results
            # }

            # update_response = requests.put(update_url, headers=headers, json=update_payload)
            # update_response.raise_for_status()
            # updated existing record
            # CHECK existing_docname

        else:
            # Step 5: Create a new record dynamically
            create_payload = {}
            for key, value in field_map.items():
                if isinstance(value, str):
                    if value.strip().lower() != "null":
                        create_payload[key] = value
                elif isinstance(value, int):
                    create_payload[key] = value
                # else ignore None

            # __________Added by jenith 26-06_________________________________________________________________
            create_payload["market_trends"] = final_results
            create_payload['doctype'] = 'Regulatory insights'

            new_doc = frappe.get_doc(create_payload)
            new_doc.insert(ignore_permissions=True)
            update_doc_name = new_doc.name
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 New Record inserted : {update_doc_name} , fields Updated: {new_doc}")
            # ___________________________________________________________________________


            # create_payload["market_trends"] = final_results

            
            # create_response = requests.post(check_url, headers=headers, json=create_payload)
            # create_response.raise_for_status()
            # new_docname = create_response.json()["data"]["name"]
            # new_docname
            # created new record
            # CHECK new_docname

    except requests.exceptions.RequestException as e:
        return f"❌ Error communicating with Frappe API:, {e}"


            
def retrieving_market_trends(
    main_industry: str,
    sub_sector: str,
    segment: str,
    state: str,
    city: str,
    deepdown_industry_info: str,
    deepdown_location_info: str
    ) -> str:
    
    
    try:
        all_params = locals()
        selected_keys = ["main_industry", "sub_sector", "segment", "state", "city"]
        selected_params = {k: all_params[k] for k in selected_keys}
        final_results = "Required Data not found. 🤡"

        if (deepdown_industry_info.lower() == "segment" and
            deepdown_location_info.lower() == "city" and  ##✔️
            all(x != None for x in [main_industry, sub_sector, segment, city, state])):

            actual_names_based_on_id = f"""SELECT 
                                            (SELECT `sub_sector_name` FROM `tabSub Sector` WHERE name = '{sub_sector}') AS sub_sector,
                                            (SELECT `segment` FROM `tabSegment` WHERE name = '{segment}') AS segment,
                                            (SELECT `city_name` FROM `tabCity` WHERE name = '{city}') AS city"""
            
            id_names = frappe.db.sql(actual_names_based_on_id) #Changed by Jenith on 24-06
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 Id_names  : {id_names} ")
            # CHECK id_names
            

            llm_query = f"market trends for {id_names[0][1]} segment in {id_names[0][0]} sub_sector within the {main_industry} industry in {id_names[0][2]}, {state} for 2024-2025"
            sql_query = f"""
                        SELECT state, city ,industry, sub_sector, segment, market_trends, local_laws, taxes
                        FROM `tabRegulatory insights` where segment='{segment}' and sub_sector='{sub_sector}' and  industry='{main_industry}' and state='{state}' and city='{city}'
                        """

            final_results, local_laws, taxes,  update_check = retreiving_sql_database_or_llm_market_trends(sql_query = sql_query,
                                                    llm_query = llm_query,
                                                    main_industry = main_industry,
                                                    sub_sector = sub_sector,
                                                    segment = segment,
                                                    state = state,
                                                    city = city,
                                                    )
            # CHECK final_results, local_laws, taxes
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 final results  : {final_results} local Laws {local_laws} taxes {taxes} ")

            if update_check == "llm":
                updating_database_with_llm_market_trends(update_check=update_check,
                                                        main_industry = main_industry,
                                                        sub_sector = sub_sector,
                                                        segment = segment,
                                                        state = state,
                                                        city = city,
                                                        final_results=final_results,
                                                        )    

        elif (deepdown_industry_info.lower() in ("industry","pan_industry") and 
            deepdown_location_info.lower() in ("state","pan_state") and  ##✔️
            all(x != None for x in [main_industry, state])):    
            llm_query = f"market trends for {main_industry} industry in {state} for 2024-2025" ## asd 1
            sql_query = f"""
                        SELECT state, industry, pan_industry, pan_state, market_trends, local_laws, taxes
                        FROM `tabRegulatory insights` where state='{state}' and industry='{main_industry}' and pan_industry=1 and pan_state=1
                        """

            final_results, local_laws, taxes,update_check = retreiving_sql_database_or_llm_market_trends(sql_query = sql_query,
                                                    llm_query = llm_query,
                                                    main_industry = main_industry,
                                                    sub_sector = sub_sector,
                                                    segment = segment,
                                                    state = state,
                                                    city = city,
                                                    )
            # CHECK final_results, local_laws, taxes
            if update_check == "llm":
                updating_database_with_llm_market_trends(update_check=update_check,
                                                        main_industry = main_industry,
                                                        state = state,
                                                        final_results=final_results,
                                                        pan_industry=1,
                                                        pan_state=1)     

        elif (deepdown_industry_info.lower() in ("industry","pan_industry") and
            deepdown_location_info.lower() == "city" and ##✔️
            all(x != None for x in [main_industry, city, state])):

            actual_names_based_on_id = f"""SELECT 
                                            (SELECT `city_name` FROM `tabCity` WHERE name = '{city}') AS city"""
            
            id_names = frappe.db.sql(actual_names_based_on_id) #Changed by Jenith on 24-06
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 Id_names  : {id_names} ")
            # CHECK id_names
            

            llm_query = f"market trends for {main_industry} industry in {id_names[0][0]} city, {state} for 2024-2025" ## asd3
            sql_query = f"""
                        SELECT state, city ,industry, pan_industry, pan_state, market_trends, local_laws, taxes
                        FROM `tabRegulatory insights` where state='{state}' and city='{city}' and industry='{main_industry}' and pan_industry=1
                        """

            final_results, local_laws, taxes,update_check = retreiving_sql_database_or_llm_market_trends(sql_query = sql_query,
                                                    llm_query = llm_query,
                                                    main_industry = main_industry,
                                                    sub_sector = sub_sector,
                                                    segment = segment,
                                                    state = state,
                                                    city = city,
                                                    )
            # CHECK CHECK final_results, local_laws, taxes
            if update_check == "llm":
                updating_database_with_llm_market_trends(update_check=update_check,
                                                        main_industry = main_industry,
                                                        state = state,
                                                        city = city,
                                                        final_results=final_results,
                                                        pan_industry=1)     

        elif (deepdown_industry_info.lower() in ("sub_sector","pan_sub_sector") and 
            deepdown_location_info.lower() == "city" and  ##✔️
            all(x != None for x in [main_industry, sub_sector, city, state])):

            actual_names_based_on_id = f"""SELECT 
                                            (SELECT `sub_sector_name` FROM `tabSub Sector` WHERE name = '{sub_sector}') AS sub_sector,
                                            (SELECT `city_name` FROM `tabCity` WHERE name = '{city}') AS city"""
            
            id_names = frappe.db.sql(actual_names_based_on_id) #Changed by Jenith on 24-06
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 Id_names  : {id_names} ")
            # CHECK id_names
           

            llm_query = f"market trends for {id_names[0][0]} sub sector within {main_industry} industry in {id_names[0][1]} city, {state} for 2024-2025"  ##asd 4
            sql_query = f"""
                        SELECT state, city ,industry, sub_sector, pan_sub_sector, pan_state, market_trends, local_laws, taxes
                        FROM `tabRegulatory insights` where state='{state}' and city='{city}' and industry='{main_industry}' and sub_sector='{sub_sector}' and pan_sub_sector=1
                        """

            final_results, local_laws, taxes,update_check = retreiving_sql_database_or_llm_market_trends(sql_query = sql_query,
                                                    llm_query = llm_query,
                                                    main_industry = main_industry,
                                                    sub_sector = sub_sector,
                                                    segment = segment,
                                                    state = state,
                                                    city = city,
                                                    )
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 final results  : {final_results} local Laws {local_laws} taxes {taxes} ")

            # CHECK CHECK final_results, local_laws, taxes
            if update_check == "llm":
                updating_database_with_llm_market_trends(update_check=update_check,
                                                        main_industry = main_industry,
                                                        sub_sector = sub_sector,
                                                        state = state,
                                                        city = city,
                                                        final_results=final_results,
                                                        pan_sub_sector = 1)     

        elif (deepdown_industry_info.lower() in ("sub-sector","pan_sub_sector") and 
            deepdown_location_info.lower() in ("state","pan_state") and ##✔️
            all(x != None for x in [main_industry, sub_sector, state])):

            actual_names_based_on_id = f"""SELECT 
                                            (SELECT `sub_sector_name` FROM `tabSub Sector` WHERE name = '{sub_sector}') AS sub_sector,"""
            
            id_names = frappe.db.sql(actual_names_based_on_id) #Changed by Jenith on 24-06
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 Id_names  : {id_names} ")
            # CHECK id_names
            

            llm_query = f"market trends for {id_names[0][0]} sub sector within {main_industry} industry  in {state} for 2024-2025" ## asd 5
            sql_query = f"""
                        SELECT state, industry, sub_sector, pan_sub_sector, pan_state, market_trends, local_laws, taxes
                        FROM `tabRegulatory insights` where state='{state}' and industry='{main_industry}' and sub_sector='{sub_sector}' and pan_sub_sector=1 and pan_state=1
                        """

            final_results, local_laws, taxes,update_check = retreiving_sql_database_or_llm_market_trends(sql_query = sql_query,
                                                    llm_query = llm_query,
                                                    main_industry = main_industry,
                                                    sub_sector = sub_sector,
                                                    segment = segment,
                                                    state = state,
                                                    city = city,
                                                    )
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 final results  : {final_results} local Laws {local_laws} taxes {taxes} ")
            # CHECK final_results, local_laws, taxes
          
            if update_check == "llm":
                updating_database_with_llm_market_trends(update_check=update_check,
                                                        main_industry = main_industry,
                                                        state = state,
                                                        sub_sector = sub_sector,
                                                        final_results=final_results,
                                                        pan_sub_sector=1,
                                                        pan_state=1) 

        elif (deepdown_industry_info.lower() == "segment" and 
            deepdown_location_info.lower() in ("state","pan_state") and 
            all(x != None for x in [main_industry, sub_sector, segment, state])):

            actual_names_based_on_id = f"""SELECT 
                                            (SELECT `sub_sector_name` FROM `tabSub Sector` WHERE name = '{sub_sector}') AS sub_sector,
                                            (SELECT `segment` FROM `tabSegment` WHERE name = '{segment}') AS segment,"""
            
            id_names = frappe.db.sql(actual_names_based_on_id) #Changed by Jenith on 24-06
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 Id_names  : {id_names} ")
            # CHECK id_names
            

            llm_query = f"market trends for {id_names[0][1]} segment in {id_names[0][0]} sub sector within the {main_industry} industry in {state} for 2024-2025" ## asd 2  
            sql_query = f"""
                        SELECT state, industry, sub_sector, segment, market_trends, local_laws, taxes
                        FROM `tabRegulatory insights` where state='{state}' and industry='{main_industry}' and sub_sector='{sub_sector}' and segment='{segment}' and pan_state=1
                        """  

            final_results, local_laws, taxes,update_check = retreiving_sql_database_or_llm_market_trends(sql_query = sql_query,
                                                    llm_query = llm_query,
                                                    main_industry = main_industry,
                                                    sub_sector = sub_sector,
                                                    segment = segment,
                                                    state = state,
                                                    city = city,
                                                    )    
            # CHECK final_results, local_laws, taxes
            with open("market_trends_logs.txt", "a") as file:
                file.write(f"\n📨 final results  : {final_results} local Laws {local_laws} taxes {taxes} ")

            if update_check == "llm":
                updating_database_with_llm_market_trends(update_check=update_check,
                                                        main_industry = main_industry,
                                                        state = state,
                                                        sub_sector = sub_sector,
                                                        segment = segment,
                                                        final_results=final_results,
                                                        pan_state=1)     
                
        selected_params["market_trends"] = final_results
        selected_params["local_laws"] = local_laws
        selected_params["taxes"] = taxes

        return final_results, selected_params
        
    except Exception as e:
        return f"Error fetching market trends ❌, {e}"

    
    
# market_trends, params_dict = retrieving_market_trends(main_industry="Agricultural",
#                                          sub_sector="Agricultural Trade and Marketing-Agricultural",
#                                          segment="Agri-Exports-Agricultural Trade and Marketing-Agricultural",
#                                          state="Gujarat",
#                                          city="Shehera-Shehera-PanchMahal",
#                                          deepdown_industry_info="segment",
#                                          deepdown_location_info="city")

# market_trends, params_dict = retrieving_market_trends(main_industry="Foods and Beverages",
#                                         state="Gujarat",
#                                         sub_sector="Paint, Coatings & Inks-Chemical",
#                                         segment=None,
#                                         city=None,
#                                         deepdown_industry_info="pan_industry",
#                                         deepdown_location_info="pan_state")

# market_trends, params_dict = retrieving_market_trends(main_industry="Mining",
#                                         state="Gujarat",
#                                         sub_sector="Paint, Coatings & Inks-Chemical",
#                                         segment=None,
#                                         city=None,
#                                         deepdown_industry_info="pan_industry",
#                                         deepdown_location_info="pan_state")


# CHECK market_trends, params_dict
# with open("market_trends_logs.txt", "a") as file:
#     file.write(f"\n📨 market Trends : {market_trends}  Params Dict {params_dict} ")










