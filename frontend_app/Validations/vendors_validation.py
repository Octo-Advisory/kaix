import frappe
import requests
import traceback

@frappe.whitelist()
def vendor_validation(param):
    try:
        allLogs=[]
        # Extract location details
        location_info = param.get("Location_info", {})
        location = location_info.get("Location")
        location_category = location_info.get("Location Category")
        from_india = location_info.get("From_India")

        # Extract industry details
        industry_info = param.get("Industry_info", {})
        main_industry = industry_info.get("Main-Industry")
        sub_sector = industry_info.get("Sub-Sector")
        segment = industry_info.get("Segment")
        product = industry_info.get("Product")
        
        # Extract supply details
        supply_info = param.get("Supply_info", {})
        supplies = supply_info.get("Supplies")

        # Below is the checkpoints that should be fulfilled in this validation
        # 1. First check what have we got ... Location info , Industry info , supply info..  List the conditions to handle all its scenarios 
        # 2. If we get location info empty .. return False, If we get location info but no industry and no supply then return False
        # 3. When the above condition returns True .. then execute the industry or supply function whatever we've got ...
        # 4. Go to location check function only when industry or supply what we've got returns True else no need to execute location check function
        # 5. If we get industry info : then First check their arguments like if we get all three of them .. then first get supply for that segment and for that supply check the vendor table that whether any vendor exists or not for that supply
        # 6. Atleast one vendor must be their in the db for any one of the supply ... if no vendors are found for any of the supply return False.
        # 7. If we dont get supply for that segment from supply table ... then check supply for the sub sector .. if not sub sector also then check for main industry .. else return False....
        # 8. If the supply or industry returns True execute location check ... In that first check whether fromIndia is checked or not .. if not return False.. if yes go ahead
        # 9. For the location check if the location exists anywhere in the area, city or state table ... if exists then check for coordinates.. if not coordinates run Mapping Function .. get coordinates and pass true along with the Mapping function info and update those coordinates in the record where it was missing

        def verify_location():
            if location and location_category and from_india == "Yes":
                return True
            elif location and location_category and from_india == "No":
                return 'For now we have no data available for outside India'
            elif location and not location_category and from_india == "Yes":
                return True
            elif location and not location_category and from_india == "No":
                return 'For now we have no data available for outside India'
            elif not location and not location_category and from_india == "Yes":
                return 'No location mentioned in the query'
            elif not location and location_category and from_india == "Yes":
                return 'No location mentioned in the query'
            elif not location and location_category and from_india == "No":
                return 'No location mentioned in the query'
        
        def verify_industry():
            if not main_industry:
                return 'No industry mentioned in the query'
            
            elif main_industry and sub_sector and not segment:
                subsectorname=  sub_sector+'-'+main_industry
                query = f"""SELECT name from `tabSub Sector` WHERE industry_id = '{main_industry}'"""
                verify_industry_subsector = frappe.db.sql(query,as_dict=True)
                subsector_verify = []
                if verify_industry_subsector:
                    for a in verify_industry_subsector:
                        if a['name'] == subsectorname:
                            subsector_verify.append(a['name'])
                    if not subsector_verify:
                        return f'Subsector {sub_sector} didnt match with industry {main_industry}'
                    else:
                        return True
                else:
                    query2 = f"""select name from `tabIndustry` WHERE industry_name = '{main_industry}'"""
                    verify_industry_in_db = frappe.db.sql(query2, as_dict=True)
                    if verify_industry_in_db:
                        return True
                    else:
                        return f'Main industry {main_industry} is not available in the database'

            elif main_industry and not sub_sector and not segment:
                query = f"""select name from `tabIndustry` where industry_name='{main_industry}'"""
                industry_check = frappe.db.sql(query,as_dict=True)
                if industry_check:
                    return True
                else:
                    return f'Main industry {main_industry} is not available in the database'
            
            elif main_industry and sub_sector and segment:
                return True
            
            elif not main_industry and not sub_sector and not segment:
                return f'Nothing provided in Industry Info'
            
        def verify_supply():
            supplies_length = len(supplies)
            check_supplies = [a for a in supplies if str(a) != "Not Available in list" and a != '']
            if len(check_supplies) <= 0:
                return 'Didnt got anything for supplies'
            else:
                return True
            
        def parameter_check():
            location_check = verify_location()
            industry_check = verify_industry()
            supply_check = verify_supply()

            if location_check != True:
                return  {'pass_to_analytics_module': False, 'log': location_check, 'latitude_longitude': 'None',"location_name":'None', 'from_gujarat': 'None'}
            elif location_check == True and industry_check != True and supply_check != True:
                return  {'pass_to_analytics_module': False, 'log': industry_check, 'latitude_longitude': 'None',"location_name":'None', 'from_gujarat': 'None'}
            elif location_check == True and industry_check == True and supply_check != True:
                return location_and_industry()
            elif location_check == True and industry_check != True and supply_check == True:
                return location_and_supply()
            elif location_check == True and industry_check == True and supply_check == True:
                return location_and_supply()

        def location_and_industry():
            # checking for industry first 
            industry_check = industry_info_check()
            pass_to_analytics = industry_check.get('pass_to_analytics_module')
            if pass_to_analytics:
                location_check =  location_info_check()
                return {"location_check":location_check,"industry_check": industry_check}
            else:
                return {"location_check":'Didnt executed the location check as industry check returned False', "industry_check": industry_check}

        def location_and_supply():
            supply_check = supply_info_check()
            pass_to_analytics = supply_check.get('pass_to_analytics_module')
            if pass_to_analytics:
                location_check = location_info_check()
                return {'location_check':location_check, 'supply_check':supply_check}
            else:
                return {'location_check':'Didnt executed the location check as supply check returned False', 'supply_check':supply_check}
        def geocode_check():
            geocode = get_geocode(location)
            latitude_longitude = geocode['location_info']['latitude_longitude']
            from_gujarat = geocode['location_info']['from_gujarat']
            from_india = geocode['location_info']['from_india']
            location_name = geocode['location_info']['location_name']

            if latitude_longitude:
                if from_india == False:
                    return [False,'Location was outside of India', 'didnt got from_gujarat']
                else:
                    return [True, latitude_longitude, from_gujarat,location_name]
            else:
                return [False,'Location function didnt returned any data', 'didnt got from_gujarat']
            
        def location_info_check():
            if location_category == 'State':
                query = f"""select name,state_name, latitude_longitude from  `tabState` where state_name = '{location}'"""
                state_check = frappe.db.sql(query, as_dict = True)
                if state_check:
                    latitude_longitude = state_check[0]['latitude_longitude']
                    state_name = state_check[0]['state_name']
                    if state_name == 'Gujarat':
                        from_gujarat = True
                    else:
                        from_gujarat = False
                    if (latitude_longitude is not None) and (latitude_longitude != ''):
                        return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude for the state', 'latitude_longitude': latitude_longitude, "location_name":location, 'from_gujarat': from_gujarat}
                    else:
                        geocode = geocode_check()
                        if geocode[0] == False:
                            log = geocode[1]
                            return {'pass_to_analytics_module': False, 'log': log, latitude_longitude: 'didnt got any latitude longitude',"location_name":'Didnt got any location',  'from_gujarat': False}
                        else:
                            if len(state_check) == 1:
                                lat_long = geocode[1]
                                from_gujarat = geocode[2]
                                location_name = geocode[3]
                                updatequery = f"""UPDATE `tabState` SET latitude_longitude = '{lat_long}' where state_name = '{location}'"""
                                frappe.db.sql(updatequery)
                                #the above query needs to be executed
                                frappe.db.commit() 
                                return {"pass_to_analytics_module": True, 'log':f'State Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name, "from_gujarat": from_gujarat}
                            else:
                                return {"pass_to_analytics_module": True, 'log':f'State Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}

                else:
                    query1 = f"""select state,city_name,name,latitude_longitude from `tabCity` where city_name = '{location}'"""
                    city_check = frappe.db.sql(query1, as_dict= True)
                    if city_check:
                        latitude_longitude = city_check[0]['latitude_longitude']
                        city_name  = city_check[0]['city_name']
                        state_name= city_check[0]['state']
                        if state_name == 'Gujarat':
                            from_gujarat = True
                        else:
                            from_gujarat = False
                        if (latitude_longitude is not None) and (latitude_longitude != ''):
                            return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude in City table instead of State', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                        else:
                            geocode = geocode_check()
                            if geocode[0] == False:
                                log = geocode[1]
                                return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                            else:
                                if len(city_check) == 1:
                                    lat_long = geocode[1]
                                    from_gujarat = geocode[2]
                                    location_name = geocode[3]
                                    updatequery = f"""UPDATE `tabCity` SET latitude_longitude = '{lat_long}' where city_name = '{location}'"""
                                    frappe.db.sql(updatequery)
                                    #the above query needs to be executed
                                    frappe.db.commit() 
                                    return {"pass_to_analytics_module": True, 'log':f'City Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                                else:
                                    return {"pass_to_analytics_module": True, 'log':f'City Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                    else:
                        query2 = f"""select state,name,latitude_longitude from `tabArea` where area_name = '{location}'"""
                        area_check = frappe.db.sql(query2, as_dict=True)
                        if area_check:
                            latitude_longitude = area_check[0]['latitude_longitude']
                            state_name= area_check[0]['state']
                            if state_name == 'Gujarat':
                                from_gujarat = True
                            else:
                                from_gujarat = False
                            if (latitude_longitude is not None) and (latitude_longitude != ''):
                                return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude in Area table instead of State', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                            else:
                                geocode = geocode_check()
                                if geocode[0] == False:
                                    log = geocode[1]
                                    return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                                else:
                                    if len(area_check) == 1:
                                        lat_long = geocode[1]
                                        from_gujarat = geocode[2]
                                        location_name = geocode[3]
                                        updatequery = f"""UPDATE `tabArea` SET latitude_longitude = '{lat_long}' where area_name = '{location}'"""
                                        frappe.db.sql(updatequery)
                                        #the above query needs to be executed
                                        frappe.db.commit() 
                                        return {"pass_to_analytics_module": True, 'log':f'Area Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                                    else:
                                        return {"pass_to_analytics_module": True, 'log':f'Area Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                        else: 
                             geocode = geocode_check()
                        if geocode[0] == False:
                            log = geocode[1]
                            return {"pass_to_analytics_module":False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude', "location_name":'Didnt got any location', 'from_gujarat': False}
                        else:
                            lat_long = geocode[1]
                            from_gujarat = geocode[2]
                            location_name = geocode[3]
                            return {"pass_to_analytics_module": True, 'log':f'Didnt found the location in the database.. getting coordinates directly from map function', 'latitude_longitude': lat_long, "location_name":location_name,"from_gujarat": from_gujarat}
                            
            elif location_category == 'City':
                query1 = f"""select state,name,latitude_longitude from `tabCity` where city_name = '{location}'"""
                city_check = frappe.db.sql(query1, as_dict= True)
                if city_check:
                    latitude_longitude = city_check[0]['latitude_longitude']
                    state_name= city_check[0]['state']
                    if state_name == 'Gujarat':
                        from_gujarat = True
                    else:
                        from_gujarat = False
                    if (latitude_longitude is not None) and (latitude_longitude != ''):
                        return {'pass_to_analytics_module': True, 'log': 'got the location in City table', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                    else:
                        geocode = geocode_check()
                        if geocode[0] == False:
                            log = geocode[1]
                            return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                        else:
                            if len(city_check) == 1:
                                lat_long = geocode[1]
                                from_gujarat = geocode[2]
                                location_name = geocode[3]
                                updatequery = f"""UPDATE `tabCity` SET latitude_longitude = '{lat_long}' where city_name = '{location}'"""
                                frappe.db.sql(updatequery)
                                #the above query needs to be executed
                                frappe.db.commit() 
                                return {"pass_to_analytics_module": True, 'log':f'City Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                            else:
                                return {"pass_to_analytics_module": True, 'log':f'City Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}

                else:
                    query2 = f"""select state,name,latitude_longitude from `tabArea` where area_name = '{location}'"""
                    area_check = frappe.db.sql(query2, as_dict=True)
                    if area_check:
                        latitude_longitude = area_check[0]['latitude_longitude']
                        state_name= area_check[0]['state']
                        if state_name == 'Gujarat':
                            from_gujarat = True
                        else:
                            from_gujarat = False
                        if (latitude_longitude is not None) and (latitude_longitude != ''):
                            return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude in Area table instead of City', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                        else:
                            geocode = geocode_check()
                            if geocode[0] == False:
                                log = geocode[1]
                                return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                            else:
                                if len(area_check) == 1:
                                    lat_long = geocode[1]
                                    from_gujarat = geocode[2]
                                    location_name = geocode[3]
                                    updatequery = f"""UPDATE `tabArea` SET latitude_longitude = '{lat_long}' where area_name = '{location}'"""
                                    frappe.db.sql(updatequery)
                                    #the above query needs to be executed
                                    frappe.db.commit() 
                                    return {"pass_to_analytics_module": True, 'log':f'Area Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                                else:
                                    return {"pass_to_analytics_module": True, 'log':f'Area Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}

                    else: 
                        query3 = f"""select state_name,name, latitude_longitude from  `tabState` where state_name = '{location}'"""
                        state_check = frappe.db.sql(query3, as_dict = True)
                        if state_check:
                            latitude_longitude = state_check[0]['latitude_longitude']
                            state_name= area_check[0]['state_name']
                            if state_name == 'Gujarat':
                                from_gujarat = True
                            else:
                                from_gujarat = False
                            if (latitude_longitude is not None) and (latitude_longitude != ''):
                                return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude for the state instead of City', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                            else:
                                geocode = geocode_check()
                                if geocode[0] == False:
                                    log = geocode[1]
                                    return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                                else:
                                    if len(state_check) == 1:
                                        lat_long = geocode[1]
                                        from_gujarat = geocode[2]
                                        location_name = geocode[3]
                                        updatequery = f"""UPDATE `tabState` SET latitude_longitude = '{lat_long}' where state_name = '{location}'"""
                                        frappe.db.sql(updatequery)
                                        #the above query needs to be executed
                                        frappe.db.commit() 
                                        return {"pass_to_analytics_module": True, 'log':f'State Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                                    else:
                                        return {"pass_to_analytics_module": True, 'log':f'State Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                        else:
                             geocode = geocode_check()
                        if geocode[0] == False:
                            log = geocode[1]
                            return {"pass_to_analytics_module":False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude', "location_name":'Didnt got any location', 'from_gujarat': False}
                        else:
                            lat_long = geocode[1]
                            from_gujarat = geocode[2]
                            location_name = geocode[3]
                            return {"pass_to_analytics_module": True, 'log':f'Didnt found the location in the database.. getting coordinates directly from map function', 'latitude_longitude': lat_long, "location_name":location_name,"from_gujarat": from_gujarat}
            elif location_category == 'Area':
                query = f"""select state,name,latitude_longitude from `tabArea` where area_name = '{location}'"""
                area_check = frappe.db.sql(query, as_dict=True)
                if area_check:
                    latitude_longitude = area_check[0]['latitude_longitude']
                    state_name= area_check[0]['state']
                    if state_name == 'Gujarat':
                        from_gujarat = True
                    else:
                        from_gujarat = False
                    if (latitude_longitude is not None) and (latitude_longitude != ''):
                        return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude for Area', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                    else:
                        geocode = geocode_check()
                        if geocode[0] == False:
                            log = geocode[1]
                            return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                        else:
                            if len(area_check) == 1:
                                lat_long = geocode[1]
                                from_gujarat = geocode[2]
                                location_name = geocode[3]
                                updatequery = f"""UPDATE `tabArea` SET latitude_longitude = '{lat_long}' where area_name = '{location}'"""
                                frappe.db.sql(updatequery)
                                #the above query needs to be executed
                                frappe.db.commit() 
                                return {"pass_to_analytics_module": True, 'log':f'Area Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                            else:
                                return {"pass_to_analytics_module": True, 'log':f'Area Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}

                else:
                    query1 = f"""select state,name,latitude_longitude from `tabCity` where city_name = '{location}'"""
                    city_check = frappe.db.sql(query1, as_dict= True)
                    if city_check:
                        latitude_longitude = city_check[0]['latitude_longitude']
                        state_name= city_check[0]['state']
                        if state_name == 'Gujarat':
                            from_gujarat = True
                        else:
                            from_gujarat = False
                        if (latitude_longitude is not None) and (latitude_longitude != ''):
                            return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude for City instead of Area', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                        else:
                            geocode = geocode_check()
                            if geocode[0] == False:
                                log = geocode[1]
                                return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                            else:
                                if len(city_check) == 1:
                                    lat_long = geocode[1]
                                    from_gujarat = geocode[2]
                                    updatequery = f"""UPDATE `tabCity` SET latitude_longitude = '{lat_long}' where city_name = '{location}'"""
                                    frappe.db.sql(updatequery)
                                    #the above query needs to be executed
                                    frappe.db.commit() 
                                    return {"pass_to_analytics_module": True, 'log':f'City Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                                else:
                                    return {"pass_to_analytics_module": True, 'log':f'City Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}

                    else:
                        query2 = f"""select state_name,name,latitude_longitude from `tabState` where state_name = '{location}'"""
                        state_check = frappe.db.sql(query2, as_dict= True)
                        if state_check:
                            latitude_longitude = state_check[0]['latitude_longitude']
                            state_name= city_check[0]['state_name']
                            if state_name == 'Gujarat':
                                from_gujarat = True
                            else:
                                from_gujarat = False
                            if (latitude_longitude is not None) and (latitude_longitude != ''):
                                return {'pass_to_analytics_module': True, 'log': 'got the latitude and longitude for State instead of Area', 'latitude_longitude': latitude_longitude,"location_name":location, 'from_gujarat': from_gujarat}
                            else:
                                geocode = geocode_check()
                                if geocode[0] == False:
                                    log = geocode[1]
                                    return {'pass_to_analytics_module': False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude',"location_name":'Didnt got any location', 'from_gujarat': False}
                                else:
                                    if len(state_check) == 1:
                                        lat_long = geocode[1]
                                        updatequery = f"""UPDATE `tabState` SET latitude_longitude = '{lat_long}' where state_name = '{location}'"""
                                        frappe.db.sql(updatequery)
                                        #the above query needs to be executed
                                        frappe.db.commit() 
                                        return {"pass_to_analytics_module": True, 'log':f'State Table updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}
                                    else:
                                        return {"pass_to_analytics_module": True, 'log':f'State Table not updated for {location}', 'latitude_longitude': lat_long,"location_name":location_name,"from_gujarat": from_gujarat}

                        else:
                            geocode = geocode_check()
                        if geocode[0] == False:
                            log = geocode[1]
                            return {"pass_to_analytics_module":False, 'log': log, 'latitude_longitude': 'didnt got any latitude longitude', "location_name":'Didnt got any location', 'from_gujarat': False}
                        else:
                            lat_long = geocode[1]
                            from_gujarat = geocode[2]
                            location_name = geocode[3]
                            return {"pass_to_analytics_module": True, 'log':f'Didnt found the location in the database.. getting coordinates directly from map function', 'latitude_longitude': lat_long, "location_name":location_name,"from_gujarat": from_gujarat}
                            
            else:
                return 'Invalid Location Category'

        def industry_info_check():

            if main_industry and sub_sector and segment:
                subsectorname=  sub_sector+'-'+main_industry
                segmentname = segment+'-'+subsectorname
                query1 = f"""SELECT supply FROM `tabSupply Rules` WHERE segment='{segmentname}'"""
                segmentcheck = frappe.db.sql(query1, as_dict=True)
                if segmentcheck:
                    Supply_id_list = [row['supply'] for row in segmentcheck] 
                    Supply_id_str = ", ".join(f"'{row}'" for row in Supply_id_list)  

                    subquery1 = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE vm.supply IN ({Supply_id_str})"""
                    vendorcheck = frappe.db.sql(subquery1, as_dict=True)
                    if vendorcheck:

                        vendor_supply_mapping = {}
                        for a in vendorcheck:
                            if a['vendor_name'] not in vendor_supply_mapping:
                                vendor_supply_mapping[a['vendor_name']] = set()
                            vendor_supply_mapping[a['vendor_name']].add(a['supply'])

                        all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                        supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                        
                        return {'pass_to_analytics_module': True, 'log': 'Got the vendors for the given industry, subsector and segment', 'supplies_with_no_vendors':supplies_with_no_vendors }
                        
                    else:
                        return {'pass_to_analytics_module': False, 'log': 'There Wasnt even a single vendor for any of the supplies at segment level 😠', 'supplies_with_no_vendors': 'not a single vendor found'}
                        
                else:
                    # now checking for subsector
                    subsectorname=  sub_sector+'-'+main_industry 
                    query2 = f"""SELECT supply FROM `tabSupply Rules` WHERE sub_sector='{subsectorname}'"""
                    subsectorcheck = frappe.db.sql(query2, as_dict=True)
                    if subsectorcheck:

                        Supply_id_list = [row['supply'] for row in subsectorcheck] 
                        Supply_id_str = ", ".join(f"'{row}'" for row in Supply_id_list) 

                        subquery1 = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN  `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE  vm.supply IN ({Supply_id_str})"""
                        vendorcheck = frappe.db.sql(subquery1, as_dict=True)
                        if vendorcheck:

                            vendor_supply_mapping = {}
                            for a in vendorcheck:
                                if a['vendor_name'] not in vendor_supply_mapping:
                                    vendor_supply_mapping[a['vendor_name']] = set()
                                vendor_supply_mapping[a['vendor_name']].add(a['supply'])
                            
                            all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                            supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                            return {'pass_to_analytics_module': True, 'log': 'Instead of segment level got vendors for sub sector level', 'supplies_with_no_vendors':supplies_with_no_vendors }
                        else:
                            return {'pass_to_analytics_module': False, 'log': 'Got supplies at subsector level instead of segment level but there wasnt even a single vendor for any of the supplies at sub sector level', 'supplies_with_no_vendors': 'not a single vendor found'}

                    else:
                        #now checking for main industry
                        query3 = f"""SELECT supply FROM `tabSupply Rules` WHERE industry='{main_industry}'"""
                        industrycheck = frappe.db.sql(query3, as_dict=True)
                        if industrycheck:
                            Supply_id_list = [row['supply'] for row in industrycheck] 
                            Supply_id_str = ", ".join(f"'{row}'" for row in Supply_id_list)  

                            subquery1 = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE vm.supply IN ({Supply_id_str})"""
                            vendorcheck = frappe.db.sql(subquery1, as_dict=True)
                            if vendorcheck:

                                vendor_supply_mapping = {}
                                for a in vendorcheck:
                                    if a['vendor_name'] not in vendor_supply_mapping:
                                        vendor_supply_mapping[a['vendor_name']] = set()
                                    vendor_supply_mapping[a['vendor_name']].add(a['supply'])

                                    # Find which supplies have no vendors
                                all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                                # Find which supplies have no vendors
                                supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                                
                                return {'pass_to_analytics_module': True, 'log': 'Instead of segment and sub sector level got vendors for industry level', 'supplies_with_no_vendors':supplies_with_no_vendors }
                            else:
                                return {'pass_to_analytics_module': False, 'log': 'Got supplies at industry level instead of segment and subsector level but there wasnt even a single vendor for any of the supplies at the industry level', 'supplies_with_no_vendors': 'not a single vendor found'}
                        else:
                            return {'pass_to_analytics_module': False, 'log': 'Didnt Got any supplies for segment, subsector and even the main industry', 'supplies_with_no_vendors': 'not a single vendor found'}
            
            elif main_industry and sub_sector and not segment:
                # now checking for subsector 
                subsectorname=  sub_sector+'-'+main_industry
                query2 = f"""SELECT supply FROM `tabSupply Rules` WHERE sub_sector='{subsectorname}'"""
                subsectorcheck = frappe.db.sql(query2, as_dict=True)
                if subsectorcheck:

                    Supply_id_list = [row['supply'] for row in subsectorcheck] 
                    Supply_id_str = ", ".join(f"'{row}'" for row in Supply_id_list)  

                    subquery1 = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN  `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE  vm.supply IN ({Supply_id_str})"""
                    vendorcheck = frappe.db.sql(subquery1, as_dict=True)
                    if vendorcheck:

                        vendor_supply_mapping = {}
                        for a in vendorcheck:
                            if a['vendor_name'] not in vendor_supply_mapping:
                                vendor_supply_mapping[a['vendor_name']] = set()
                            vendor_supply_mapping[a['vendor_name']].add(a['supply'])
                            
                        all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                        supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                        return {'pass_to_analytics_module': True, 'log': 'Got the vendors for the given industry and subsector', 'supplies_with_no_vendors':supplies_with_no_vendors }
                    else:
                        return {'pass_to_analytics_module': False, 'log': 'There wasnt even a single vendor for any of the supplies at sub sector level', 'supplies_with_no_vendors': 'not a single vendor found'}

                else:
                        #now checking for main industry
                    query3 = f"""SELECT supply FROM `tabSupply Rules` WHERE industry='{main_industry}'"""
                    industrycheck = frappe.db.sql(query3, as_dict=True)
                    if industrycheck:
                        Supply_id_list = [row['supply'] for row in industrycheck]
                        Supply_id_str = ", ".join(f"'{row}'" for row in Supply_id_list)

                        subquery1 = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE vm.supply IN ({Supply_id_str})"""
                        vendorcheck = frappe.db.sql(subquery1, as_dict=True)
                        if vendorcheck:

                            vendor_supply_mapping = {}
                            for a in vendorcheck:
                                if a['vendor_name'] not in vendor_supply_mapping:
                                    vendor_supply_mapping[a['vendor_name']] = set()
                                vendor_supply_mapping[a['vendor_name']].add(a['supply'])

                            all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                            supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                                
                            return {'pass_to_analytics_module': True, 'log': 'Instead sub sector level got vendors for industry level', 'supplies_with_no_vendors':supplies_with_no_vendors }
                        else:
                            return {'pass_to_analytics_module': False, 'log': 'Got supplies at industry level instead subsector level but there wasnt even a single vendor for any of the supplies at the industry level', 'supplies_with_no_vendors': 'not a single vendor found'}
                    else:
                        return {'pass_to_analytics_module': False, 'log': 'Didnt Got any supplies for subsector and even the main industry', 'supplies_with_no_vendors': 'not a single vendor found'}

            elif main_industry and not sub_sector and not segment:
                query3 = f"""SELECT supply FROM `tabSupply Rules` WHERE industry='{main_industry}'"""
                industrycheck = frappe.db.sql(query3, as_dict=True)
                if industrycheck:
                    Supply_id_list = [row['supply'] for row in industrycheck]
                    Supply_id_str = ", ".join(f"'{row}'" for row in Supply_id_list)  

                    subquery1 = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE vm.supply IN ({Supply_id_str})"""
                    vendorcheck = frappe.db.sql(subquery1, as_dict=True)
                    if vendorcheck:

                        vendor_supply_mapping = {}
                        for a in vendorcheck:
                            if a['vendor_name'] not in vendor_supply_mapping:
                                vendor_supply_mapping[a['vendor_name']] = set()
                            vendor_supply_mapping[a['vendor_name']].add(a['supply'])

                        all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                        supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                                
                        return {'pass_to_analytics_module': True, 'log': 'Got the vendors for given industry', 'supplies_with_no_vendors':supplies_with_no_vendors }
                    else:
                        return {'pass_to_analytics_module': False, 'log': 'There wasnt even a single vendor for any of the supplies at the industry level', 'supplies_with_no_vendors': 'not a single vendor found'}
                else:
                    return {'pass_to_analytics_module': False, 'log': 'Didnt Got any supplies for the main industry', 'supplies_with_no_vendors': 'not a single vendor found'}

        def supply_info_check():
            supply_list = []
            for a in supplies:
                if a != 'Not Available in list' and a != '':
                    supply_list.append(a)

            Supply_id_list = [row for row in supply_list]
            Supply_id_str = ", ".join(f"'{row}'" for row in supply_list) 
            query = f"""SELECT v.vendor_name, vm.supply FROM `tabVendor` AS v JOIN `tabVendor Supply Capacity` AS vm ON v.name = vm.parent WHERE vm.supply IN ({Supply_id_str})"""
            vendorcheck = frappe.db.sql(query,as_dict=True)
            if vendorcheck:

                vendor_supply_mapping = {}
                for a in vendorcheck:
                    if a['vendor_name'] not in vendor_supply_mapping:
                        vendor_supply_mapping[a['vendor_name']] = set()
                    vendor_supply_mapping[a['vendor_name']].add(a['supply'])

                all_vendor_supplies = [supply for supplies in vendor_supply_mapping.values() for supply in supplies]
                supplies_with_no_vendors = set(Supply_id_list) - set(all_vendor_supplies)
                return {'pass_to_analytics_module':True, 'log': 'Found the vendors for the given supplies', 'supplies_with_no_vendors': supplies_with_no_vendors}
            else: 
                return {'pass_to_analytics_module':False, 'log': 'There wasnt even a single vendor for any of the supplies in the database', 'supplies_with_no_vendors': 'Not a single vendor found'}
                
        def get_geocode(address):
            if address  != None and address != "" and address != " ":
                try:
                    address = str(address)
                    #API request
                    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key=AIzaSyCgESPN3REByWpiQYiRKGpDWwBZLwQEnVA"
                    response = requests.get(url)
                    data = response.json()  #parse the JSON data
                
                    if data['status'] == 'OK' and len(data['results']) > 0:
                        formatted_address = data['results'][0]['formatted_address']
                        location = data['results'][0]['geometry']['location']
                        latitude_longitude = f"{location['lat']},{location['lng']}"
                        location_name = data['results'][0]['address_components'][0]['long_name']
                    
                        from_gujarat = "Gujarat" in formatted_address
                        from_india = "India" in formatted_address
                    
                        return {
                            'location_info': {
                                'location_name': location_name,
                                'latitude_longitude': latitude_longitude,
                                'from_gujarat': from_gujarat,
                                'from_india': from_india,
                            },
                            'isError': False
                        }
                    else:
                        #no valid result found, return False
                        return {
                            'location_info': {
                                'location_name': None,
                                'latitude_longitude': None,
                                'from_gujarat': None,
                                'from_india': None,
                            },
                            'isError': False
                        }
        
                except Exception as e:
                    # If any error occurs,
                    return {
                        'location_info': {
                            'location_name': None,
                            'latitude_longitude': None,
                            'from_gujarat': None,
                            'from_india': None,
                        },
                        'isError': True,
                        'error_message': str(e)  
                    }
            else:
                return {
                        'location_info': {
                            'location_name': None,
                            'latitude_longitude': None,
                            'from_gujarat': None,
                            'from_india': None,
                        },
                        'isError': False
                }
            
        return parameter_check()
    except Exception as e:
        error_message = traceback.format_exc()
        with open("log.txt", "a") as file:
                file.write(f"\nException from vendor validation {error_message}")
        return e