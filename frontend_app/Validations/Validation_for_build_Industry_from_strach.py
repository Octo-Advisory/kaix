import frappe

def fetch_capacity_data(required_capacity_by_user, industry_id, sub_sector_id=None, segment_id=None):
    # """
    # Function to fetch capacity-related data based on user inputs.
    # """
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
        AND (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment = '{segment_id}')
        AND extremity_record = 0;
        """
        results = frappe.db.sql(query)
        if results:
            df = results
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
        AND (industry = '{industry_id}' AND sub_sector = '{sub_sector_id}' AND segment IS NULL)
        AND extremity_record = 0;
        """
        results = frappe.db.sql(query)
        if results:
            df = results
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
        AND (industry = '{industry_id}')
        AND extremity_record = 0;
        """
        results = frappe.db.sql(query)
        if results:
            df = results
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
        AND extremity_record = 0
        """

        if sub_sector_id is not None:
            nearest_query += f" AND sub_sector = '{sub_sector_id}'"
        
        if segment_id is not None:
            nearest_query += f" AND segment = '{segment_id}'"

        nearest_query += f"""
        ORDER BY ABS(minimum_capacity_value - {required_capacity_by_user})
        LIMIT 1;
        """
        
        results = frappe.db.sql(nearest_query)
        df = results


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
    epsilon = 0.0000000000000001 # When it goes to the python file, user sys.float_info.epsilon but first import the sys library
    
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
    result = fetch_capacity_data(required_capacity_by_user, industry_id, sub_sector_id, segment_id)
    min_cap = result[0]
    max_cap = result[1]
    min_land = result[2]
    max_land = result[3]
    
    if None in (min_cap, max_cap, min_land, max_land):
        return None
    
    return calculate_land_requirements(required_capacity_by_user, max_cap, min_cap, max_land, min_land)


def search_all_supply(INDUSTRY_NAME, SUB_SECTOR, SEGMENT):

    if INDUSTRY_NAME is not None and SUB_SECTOR is not None and SEGMENT is not None:
        query = """
        SELECT DISTINCT sr.supply
        FROM `tabSupply Rules` AS sr
        WHERE sr.industry = %s
        AND sr.sub_sector = %s
        AND sr.segment = %s
        """
        
        results = frappe.db.sql(query, (INDUSTRY_NAME,SUB_SECTOR, SEGMENT), as_dict=True)

        if results:
            unique_supply_list = [row.supply for row in results]            
            # Convert the list into a string format that can be used in SQL
            supply_id_str = ', '.join(f"'{supply_id}'" for supply_id in unique_supply_list)
            
            query = f"""
            SELECT DISTINCT supply
            FROM `tabVendor Supply Capacity`
            WHERE supply IN ({supply_id_str})
            """
            results = frappe.db.sql(query)
            unique_supply_from_vendor = [row[0] for row in results]

            if len(unique_supply_from_vendor) == len(unique_supply_list):
                return {
                    "Supply_validation_status": True,
                    "supply_not_across_table": None
                }
            else:
                supply_not_across_table = list(set(unique_supply_from_vendor) ^ set(unique_supply_list))
                return {
                    "Supply_validation_status": False,
                    "supply_not_across_table": supply_not_across_table
                }
        else:
            return search_all_supply(INDUSTRY_NAME, SUB_SECTOR, None)
    
    elif INDUSTRY_NAME is not None and SUB_SECTOR is not None and SEGMENT is None:
        query = """
        SELECT DISTINCT sr.supply
        FROM `tabSupply Rules` AS sr
        WHERE sr.industry = %s
        AND sr.sub_sector = %s
        """

        results = frappe.db.sql(query, (INDUSTRY_NAME,SUB_SECTOR), as_dict=True)

        if results:
            unique_supply_list = [row.supply for row in results]
            # Convert the list into a string format that can be used in SQL
            supply_id_str = ', '.join(f"'{supply_id}'" for supply_id in unique_supply_list)
            
            query = f"""
            SELECT DISTINCT vs.supply
            FROM `tabVendor Supply Capacity` AS vs
            WHERE supply IN ({supply_id_str})
            """
            results = frappe.db.sql(query)
            unique_supply_from_vendor = [row[0] for row in results]
            
            if len(unique_supply_from_vendor) == len(unique_supply_list):
                return {
                    "Supply_validation_status": True,
                    "supply_not_across_table": None
                }
            else:
                supply_not_across_table = list(set(unique_supply_from_vendor) ^ set(unique_supply_list))
                return {
                    "Supply_validation_status": False,
                    "supply_not_across_table": supply_not_across_table
                }
        else:
            return search_all_supply(INDUSTRY_NAME, None, None)
    
    elif INDUSTRY_NAME is not None and SUB_SECTOR is None and SEGMENT is None:
        query = """
        SELECT DISTINCT sr.supply
        FROM `tabSupply Rules` AS sr
        WHERE sr.industry = %s
        """

        results = frappe.db.sql(query, (INDUSTRY_NAME), as_dict=True)

        if results:
            unique_supply_list = [row.supply for row in results]
            # Convert the list into a string format that can be used in SQL
            supply_id_str = ', '.join(f"'{supply_id}'" for supply_id in unique_supply_list)
            
            query = f"""
            SELECT DISTINCT supply
            FROM `tabVendor Supply Capacity`
            WHERE supply IN ({supply_id_str})
            """
            
            results = frappe.db.sql(query)
            unique_supply_from_vendor = [row[0] for row in results]
            
            if len(unique_supply_from_vendor) == len(unique_supply_list):
                return {
                    "Supply_validation_status": True,
                    "supply_not_across_table": None
                }
            else:
                supply_not_across_table = list(set(unique_supply_from_vendor) ^ set(unique_supply_list))
                return {
                    "Supply_validation_status": False,
                    "supply_not_across_table": supply_not_across_table
                }
        else:
            return {
                    "Supply_validation_status": False,
                    "supply_not_across_table": None
                }

@frappe.whitelist()
def search_industry(INDUSTRY_NAME, SUB_SECTOR, SEGMENT, user_cap):
    # Check the Industry Name is exits in the "industry table "
    query = """
    SELECT name FROM `tabIndustry` AS i WHERE i.industry_name = %s
    """
    industry = frappe.db.sql(query, (INDUSTRY_NAME,), as_dict=True)

    if industry:
        industry_name = industry[0]['name']
        
        # Check the Sub Sector name is exits in the "sub-sector table"
        query = """
        SELECT name FROM `tabSub Sector` AS sb WHERE sb.sub_sector_name = %s AND sb.industry_id = %s
        """
        sub_sector = frappe.db.sql(query, (SUB_SECTOR, industry_name), as_dict=True)
        if sub_sector:
            sub_sector_name = sub_sector[0]['name']
        else:
            sub_sector_name = None
            
        # Check the Segment name exits in the "Segment Table"
        query = """
        SELECT name FROM `tabSegment` AS s WHERE s.segment = %s AND s.sub_sector = %s AND s.industry = %s
        """
        segment = frappe.db.sql(query, (SEGMENT,sub_sector_name,industry_name), as_dict=True)
    
        if segment:
            segment_name = segment[0]['name']
        else:
            segment_name = None  
        

        # Query 2: Check if INDUSTRY_NAME in Industry Capacity Rule and tabSupply Rules table
        query2 = """
            SELECT 
            %s AS industry_name,
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM `tabIndustry Capacity Rule` 
                    WHERE industry = %s
                ) 
                AND EXISTS (
                    SELECT 1 
                    FROM `tabSupply Rules`
                    WHERE industry = %s
                )
                THEN 'true'
                ELSE 'false'
            END AS result;
        """
        supply_rules = frappe.db.sql(query2, (industry_name, industry_name, industry_name), as_dict=True)
    
        # Combine all results
        Industry_validation = True if  supply_rules[0].result == 'true' else False
        
        # Additional logic for True results
        if Industry_validation == True:
            if sub_sector_name is not None:
                # Query 4: Check if sub_sector_name exists and retrieve Survey no.           ----->
                query4 = """
                    SELECT a.name
                    FROM `tabArea Zone Mapping` AS azm
                    JOIN `tabSub Sector` AS s
                        ON azm.zone = s.zone_id
                    LEFT JOIN `tabArea` AS a
                        ON a.name = azm.area  
                    LEFT JOIN `tabSurvey No` AS sn
                        ON sn.area = a.name 
                    WHERE TRIM(s.name) = %s 
                    AND sn.zone = azm.zone
                    AND sn.area_acre BETWEEN %s AND %s;
                """
                valide_survey_no = integrate_land_calculation (user_cap, industry_name, sub_sector_name, segment_name)
                required_LowerMargin_land_for_user = valide_survey_no["Lower_limit_land_size"] 
                required_UpperMargin_land_for_user = valide_survey_no["Upper_limit_land_size"]

                validate_property = frappe.db.sql(query4, (sub_sector_name,required_LowerMargin_land_for_user, required_UpperMargin_land_for_user), as_dict=True)
                Property_check = True if validate_property else False

            else:
                query4 = """
                    SELECT a.name
                    FROM `tabArea Zone Mapping` AS azm
                    JOIN `tabSub Sector` AS s
                        ON azm.zone = s.zone_id
                    LEFT JOIN `tabArea` AS a
                        ON a.name = azm.area  
                    LEFT JOIN `tabSurvey No` AS sn
                        ON sn.area = a.name 
                    WHERE TRIM(s.industry_id) = %s
                    AND sn.zone = azm.zone
                    AND sn.area_acre BETWEEN %s AND %s;
                """
                
                valide_survey_no = integrate_land_calculation (user_cap, industry_name, sub_sector_name, segment_name)
                required_LowerMargin_land_for_user = valide_survey_no["Lower_limit_land_size"]
                required_UpperMargin_land_for_user = valide_survey_no["Upper_limit_land_size"]
                # print(required_LowerMargin_land_for_user, required_UpperMargin_land_for_user)
                # print("Land Requirement Calculation:", result)
    
                validate_property = frappe.db.sql(query4, (industry_name,required_LowerMargin_land_for_user, required_UpperMargin_land_for_user), as_dict=True)
                Property_check = True if validate_property else False

                
            
            if Property_check == True :
                area_id_list = [row.name for row in validate_property] 
            else:
                if sub_sector_name is not None:
                    # Query 4: Check if sub_sector_name exists and retrieve cp.area, cp.name            ----->
                    query4 = """
                        SELECT a.name
                        FROM `tabArea Zone Mapping` AS azm
                        JOIN `tabSub Sector` AS s
                            ON azm.zone = s.zone_id
                        LEFT JOIN `tabArea` AS a
                            ON a.name = azm.area  
                        LEFT JOIN `tabConnected Property` AS cp
                            ON cp.area = a.name 
                        WHERE TRIM(s.name) = %s
                        AND cp.zone = azm.zone
                        AND cp.total_area_in_acre >= %s;
                    """
                    validate_property = frappe.db.sql(query4, (sub_sector_name,required_LowerMargin_land_for_user), as_dict=True)
                    area_id_list = [row.name for row in validate_property] 
                else:
                    # Query 4: Check if industry exists and retrieve cp.total_area_in_acre, cp.name            ----->
                    query4 = """
                        SELECT a.name
                        FROM `tabArea Zone Mapping` AS azm
                        JOIN `tabSub Sector` AS s
                            ON azm.zone = s.zone_id
                        LEFT JOIN `tabArea` AS a
                            ON a.name = azm.area  
                        LEFT JOIN `tabConnected Property` AS cp
                            ON cp.area = a.name 
                        WHERE TRIM(s.industry_id) = %s
                        AND cp.zone = azm.zone
                        AND cp.total_area_in_acre >= %s;
                    """
                    validate_property = frappe.db.sql(query4, (industry_name,required_LowerMargin_land_for_user), as_dict=True)
                    area_id_list = [row.name for row in validate_property]
                   
            
            if area_id_list:
                # Convert the list into a string format that can be used in SQL
                area_id_str = ', '.join(f"'{area_id}'" for area_id in area_id_list)
    
                query = f"""
                SELECT area
                FROM `tabEmployment City Mapping`
                WHERE area IN ({area_id_str});
                """
                validate_employe = frappe.db.sql(query)
                if validate_employe:
                    employment_city_mapping_area_list = [row[0] for row in validate_employe]
                    employment_city_mapping_area_set = set([row[0] for row in validate_employe])
                        
                    if len(area_id_list) == len(employment_city_mapping_area_set) and len(employment_city_mapping_area_list) == len(area_id_list)*3:
                        pass
                    elif len(employment_city_mapping_area_list) < 3:
                        return (False,"Couldn't Find Proper Employement Data For Even One Land." )
                    else:
                        query = f"""
                        SELECT area
                        FROM `tabEmployment City Mapping`
                        WHERE area IN ({area_id_str})
                        AND employment_type IN ('Skilled', 'Semi-skilled', 'Unskilled')
                        GROUP BY
                            area
                        HAVING
                            COUNT(DISTINCT employment_type) IN (1, 2);
                        """
                    
                        employement_check = frappe.db.sql(query)
                        if employement_check:
                            # Put this print in log
                            # print("="*100,"\n", "atleast 1 employment type is missing for this areas:\n",employement_check, "\n")
                            pass
                            
                        area_not_accross_table = set(area_id_list) ^ set(employment_city_mapping_area_list)
                        if len(area_not_accross_table) != 0:
                            # Put this print in log
                            # print("Area that are not accross the Area & Employment City Mapping:\n", area_not_accross_table)
                            pass
                                    
                    get_supply = search_all_supply(industry_name, sub_sector_name, segment_name)
                    supply_validation_status = get_supply["Supply_validation_status"]
                    supply_not_across_table_list = get_supply["supply_not_across_table"]
                    
                    
                    if supply_validation_status:
                        return (True,f"Got Perfect Property, Employement & Supply Data For Given {INDUSTRY_NAME} Industry")
                    else:
                        # Put this print in log
                        # print(f"List of supplyes which are there in supply rules but not in vendor table..:- {supply_not_across_table_list}")
                        return (False,f"Didn't get Proprer Supply Data For Given {INDUSTRY_NAME} Industry.")
                else:
                    return (False,"Couldn't Find Proper Employement Data For Even One Land." )
            
            else:
                return (False,"Couldn't Find Any Property Which Satisfy User Requirements.")  
        else:
            return (False,f"Couldn't Find Given {INDUSTRY_NAME} Industry In Either Capacity Rules or Supply Rulles.")  
    else:
        return (False,f"Couldn't Find Given {INDUSTRY_NAME} Industry In Industry Master.")  
    



