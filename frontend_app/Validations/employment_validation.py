import frappe

def employment_query_validation(Area,City,State):
    allLogs = []
    
    def parameter_check():
        if not State:
            return (False,'Got the State Value Empty')
        elif not Area and not City and State:
            query = f"""SELECT state_name from `tabState` where state_name ='{State}'"""
            res = frappe.db.sql(query,as_dict=True)
            location_check = []
            for a in res:
                if a['state_name'] == State:
                    location_check.append(a)
            if location_check:
                return check_for_state(State)
            else:
                return (False,'State was available in the database')

        elif not Area and City and State:
            query = f"""SELECT city.city_name, city.state from `tabCity` as city where state='{State}'"""
            res = frappe.db.sql(query,as_dict=True)
            location_check = []
            for a in res:
                if a['city_name'] == City:
                    location_check.append(a)
            if location_check:
                return check_a_city(City)
            else:
                return (False,'City was not available in the database')

        elif Area and City and State:
            query = f"""SELECT area.area_name, city.city_name, city.state FROM `tabArea` as area INNER JOIN `tabCity` as city ON area.city_display_name = city.city_name WHERE city_display_name='{City}' AND city.state='{State}';"""
            res = frappe.db.sql(query,as_dict=True)
            location_check = []
            for a in res:
                if a['area_name'] == Area:
                    location_check.append(a)
            if location_check:
                return check_a_city(City)
            else:
                return (False,'Area was not available in the database')
        
        elif not Area and not City and not State:
            return (False, 'Didnt got anything for the location')       

    def check_a_city(city_id):
        
        query1 = f"""select name from `tabCity` where city_name='{city_id}'"""
        result1 = frappe.db.sql(query1,as_dict=True)
        city = result1[0]['name'] if result1 else None
        
        if not city:
            # allLogs.append({"error": f"No matching city found for city_name '{city_id}'"})
            return (False,f'{city_id} not found in the database')
        
        query2 = f"""SELECT name from `tabArea` Where city_id='{city}'"""
        result2 = frappe.db.sql(query2,as_dict=True)
        if not result2:
            # allLogs.append({"no_areas_found": f"No areas found for city '{city_id}'"})
            return (False, f'No areas found for {city_id}')
        
        Area_id_list = [row['name'] for row in result2]
        query = f""" SELECT 
            ecm.area, a.city_id, ecm.employment_type, ecm.availability
            FROM `tabArea` AS a
            INNER JOIN `tabEmployment City Mapping` AS ecm
                ON a.name = ecm.area
            WHERE a.city_id = '{city}'
            """
        result = frappe.db.sql(query)
        
        if result:
            common_area=[row[0] for row in result]
            leftout_area = set(Area_id_list)-set(common_area)
            
            negative_availability_areas = [(area, city_id , employment_type) for area, city_id, employment_type, availability in result if availability < 0]
            
            city_employment_mapping={}
            for area, city_id, employment_type, availability in result:
                
                if city_id not in city_employment_mapping:
                    city_employment_mapping[city_id] = {}
                if area not in city_employment_mapping[city_id]:
                    city_employment_mapping[city_id][area] = {}
                if employment_type not in city_employment_mapping[city_id][area]:
                    city_employment_mapping[city_id][area][employment_type] = []
                city_employment_mapping[city_id][area][employment_type].append(availability)
                       
            missing_area_data = []
            perfect_cities = []
            not_equal_data_cities=[]
            for city, areas in city_employment_mapping.items():
               
                available_data = []
                for area, data in areas.items():
                    
                    if len(data)==3:  # If employment data is present
                        available_data.append(data)
                       
                    else:  # If data is missing
                        missing_area_data.append({"city":city_id,"area":area})
                 
                if available_data:           
                    if all(available_data[0] == data for data in available_data):  # Compare available data
                        perfect_cities.append(city_id)

                    else:
                        not_equal_data_cities.append(city_id)
               
            if perfect_cities:
                allLogs.append({"cities_having_inequal_values_between_areas":not_equal_data_cities, "incomplete_area_data":missing_area_data, "negative_availability_areas":negative_availability_areas, "Area_having_zero_employment_records":leftout_area})
                return (True, allLogs)
            else:
                allLogs.append({"cities_having_inequal_values_between_areas":not_equal_data_cities, "incomplete_area_data":missing_area_data, "negative_availability_areas":negative_availability_areas, "Area_having_zero_employment_records":leftout_area})
                return (False, allLogs)
        else:
            allLogs.append({"no Areas for city":city_id})
            return (False,allLogs)        
       
    def check_for_state(state):
        query = f"""
        select distinct name
        from `tabCity`
        where state = "{state}"
        """
        result = frappe.db.sql(query)
        
        if result:

            city_id_list = [row[0] for row in result]
            city_id_str = ", ".join(f"'{row}'" for row in city_id_list)

            query = f"""
            select distinct name, city_id
            from `tabArea`
            where city_id in ({city_id_str})
            """
            result = frappe.db.sql(query)
            common_city=[row[1] for row in result]
            leftout_city = set(city_id_list)-set(common_city)
            
            if result:
        
                Area_id_list = [row[0] for row in result]
                Area_id_str = ", ".join(f"'{row}'" for row in Area_id_list)
    
                query = f"""
                select ecm.area, a.city_id, a.state, ecm.employment_type, ecm.availability 
                from `tabEmployment City Mapping` as ecm
                join `tabArea` as a
                on ecm.area = a.name
                where area in ({Area_id_str})
                """
                result = frappe.db.sql(query)
                
                if result:
                    common_area=[row[0] for row in result]
                    leftout_area = set(Area_id_list)-set(common_area)
                    # Validation 1: Find areas with negative availability
                    negative_availability_areas = [(area, city_id) for area, city_id, state, employment_type, availability in result if availability < 0]
                   
                    # Validation 2: Check for employment type consistency within each city
                    city_employment_mapping = {}
                    
                    for area, city_id, state, employment_type, availability in result:
                        if city_id not in city_employment_mapping:
                            city_employment_mapping[city_id] = {}
                        if area not in city_employment_mapping[city_id]:
                            city_employment_mapping[city_id][area] = {}
                        if employment_type not in city_employment_mapping[city_id][area]:
                            city_employment_mapping[city_id][area][employment_type] = []
                        city_employment_mapping[city_id][area][employment_type].append(availability)
                    
                    missing_area_data = []
                    perfect_cities = []
                    not_equal_data_cities=[]
                    for city, areas in city_employment_mapping.items():
                        available_data = []
                        
                        for area, data in areas.items():
                            if len(data)==3:  # If employment data is present
                                available_data.append(data)
                            else:  # If data is missing
                                missing_area_data.append({"city":city,"area":area})
                        if available_data:
                            if all(available_data[0] == data for data in available_data):  # Compare available data
                                perfect_cities.append(city)
                            else:
                                not_equal_data_cities.append(city)

                    if perfect_cities:
                        allLogs.append({"cities_having_inequal_values_between_areas":not_equal_data_cities, "incomplete_area_data":missing_area_data, "cities_having_zero_areas":list(leftout_city), "negative_availability_areas":negative_availability_areas, "Area_having_zero_employment_records":list(leftout_area)})
                        return (True,allLogs)
                    else:
                        allLogs.append({"cities_having_inequal_values_between_areas":not_equal_data_cities, "incomplete_area_data":missing_area_data, "cities_having_zero_areas":list(leftout_city), "negative_availability_areas":negative_availability_areas, "Area_having_zero_employment_records":list(leftout_area)})
                        return (False,allLogs)
                else:
                    allLogs.append({ "Area_data_missing":list(leftout_area)})
                    return (False,allLogs)
            else:
                allLogs.append({"We didnt find any areas for the given cities":city_id_str})
                return (False,allLogs)
            
        else:
            allLogs.append({"We Didnt Find any cities for state":state})
            return (False,allLogs)
            
    return parameter_check()
    
# employment_query_validation('','','Gujarat')
result = employment_query_validation('','Dummy City 98765','Gujarat')