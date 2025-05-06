import frappe
import json

@frappe.whitelist()
def approval_validation(param):
    '''The flow of the method goes as :
    1. Area, City, State,Industry, Sub Sector will be extracted from the parameters
    2. Then parameter_check() will be executed which will verify that whether the extracted details as per the necessity are there in the db or not
    3. Then further area_check(), city_check(), state_check() functions are there which will verify the availability of approvals based on industry and sub sector as per the location given'''
    
    allLogs=[]
    frappe.log_error("validation error!")
    # Extract location details
    location_info = param.get("location_info", {})
    area = location_info.get("Area")
    city = location_info.get("City")
    state = location_info.get("State")

    # Extract industry details
    industry_info = param.get("Industry_info", {})
    industry_name = industry_info.get("Main-Industry")
    sub_sector = industry_info.get("Sub-Sector")
    product = industry_info.get("Product")

    def parameter_check():
        '''This function will check as per parameters extracted, it will check and execute further as per the parameters extracted'''
        if area and city and state:
            query = f"""SELECT area.area_name, city.city_name, city.state FROM `tabArea` as area INNER JOIN `tabCity` as city ON area.city_display_name = city.city_name WHERE city_display_name='{city}' AND city.state='{state}';"""
            res = frappe.db.sql(query,as_dict=True)
            location_check = []
            for a in res:
                if a['area_name'] == area:
                    location_check.append(a)
            if location_check:
                return check_for_area()
            else:
                return {'pass_to_analytics': False, 'log':f'Area {area} was not available in the database','detailed_info':None}
            
        elif not area and city and state:
            query = f"""SELECT city.city_name, city.state from `tabCity` as city where state='{state}'"""
            res = frappe.db.sql(query,as_dict=True)
            location_check = []
            for a in res:
                if a['city_name'] == city:
                    location_check.append(a)
            if location_check:
                return check_for_city()
            else:
                return {'pass_to_analytics': False, 'log':f'City {city} was not available in the database','detailed_info':None}
            
        elif not area and not city and state:
            query = f"""SELECT state_name from `tabState` where state_name ='{state}'"""
            res = frappe.db.sql(query,as_dict=True)
            location_check = []
            for a in res:
                if a['state_name'] == state:
                    location_check.append(a)
            if location_check:
                return check_for_state()
            else:
                return {'pass_to_analytics': False, 'log':f'State {state} was not available in the database','detailed_info':None}
            
        elif not area and not city and not state:
            return {'pass_to_analytics': False, 'log':f'Didnt got anything for the location','detailed_info':None}
    
    def check_for_area():
        '''This function checks first for approvals of industry and sub sector for the area,if not available then for city,if not available then for city,if not available then looks for country level PAN industries'''
        if not industry_name and not sub_sector:
            return {'pass_to_analytics': False, 'log':f'Industry and subsector not provided','detailed_info':None}
            
        if not industry_name and sub_sector:
            return {'pass_to_analytics': False, 'log':f'Industry not provided','detailed_info':None}
        
        if industry_name:
            subsector_check = f"""SELECT name from `tabSub Sector` WHERE industry_id='{industry_name}'"""
            subsector_res = frappe.db.sql(subsector_check,as_dict=True)
            if subsector_res:
                pass
            else:
                industry_check = f"""SELECT name from `tabIndustry` WHERE name = '{industry_name}'"""
                industry_res = frappe.db.sql(industry_check,as_dict=True)
                if industry_res:
                    pass
                else:
                    return {'pass_to_analytics': False, 'log':f'Didnt found the industry {industry_name} in the database','detailed_info':None}
        
        #comparing area zone with the sub sector zone
        if industry_name and sub_sector:
            subsector =  sub_sector+'-'+industry_name
            #verifying the the given sub sector is of that industry or not 
            first_check = verify_subsector(industry_name,sub_sector)
            if first_check == False:
                return {'pass_to_analytics': False, 'log':f'Industry {industry_name} didnt match with subsector {sub_sector}','detailed_info':None}
            zone_check = f"""SELECT zone_id from `tabSub Sector` WHERE name='{subsector}'"""
            res = frappe.db.sql(zone_check,as_dict=True)
            subsector_zone = res[0]['zone_id']
            query1 = f"""SELECT area.area_name from `tabArea Zone Mapping` as azm INNER JOIN `tabArea` as area ON azm.area = area.name WHERE azm.zone='{subsector_zone}' AND azm.area=area.name"""
            result1 = frappe.db.sql(query1,as_dict=True)
            zone = [row['area_name'] for row in result1]
            if area in zone:
                pass
            else:
                return {'pass_to_analytics': False, 'log':'Area zone didnt match with sub sector zone ', 'detailed_info': None}
                
        elif industry_name and not sub_sector:
            query = f"""SELECT zone_id FROM `tabSub Sector` WHERE industry_id ='{industry_name}'"""
            result = frappe.db.sql(query,as_dict=True)
            zone = set()
            for i in result:
                zone.add(i['zone_id'])
            query1 = f"""SELECT azm.zone from `tabArea Zone Mapping` as azm INNER JOIN `tabArea` as area ON azm.area=area.name WHERE area.area_name = '{area}'"""
            result1 = frappe.db.sql(query1,as_dict=True)
            # area_zone = [row['zone'] for row in result1]
            area_zone = result1[0]['zone']
            if area_zone in zone:
                pass
            else:
                return {'pass_to_analytics': False, 'log':f'Area zone didnt match with any zone of the industrys sub sectors','detailed_info':None}
                
        
        #getting area name from area table by the area name given
        query1 = f"""SELECT name from `tabArea` where area_name='{area}'"""
        res = frappe.db.sql(query1,as_dict=True)
        areaname = res[0]['name']
    
        query2 = f"""SELECT name,area,city,city_level,state,country_level,state_level,industry,sub_sector,pan_industries from `tabLicenses and Approvals Type` as lat where lat.area='{areaname}' UNION SELECT name,area,city,city_level, state, country_level,state_level,industry,sub_sector,pan_industries from `tabLicenses and Approvals Type` where (city_level=1 and city='{city}') OR  (state_level=1 and state='{state}') OR country_level=1"""
        result2 = frappe.db.sql(query2,as_dict=True)
        subsector =  (sub_sector or '')+'-'+industry_name
        area_level_approvals= []
        city_level_approvals = []
        state_level_approvals=[]
        country_level_approvals=[]
        
        for a in result2:
            if a['area'] == areaname:
                if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                    area_level_approvals.append({'cityName': a['area'],'Approval': a['name'],'for industry': a['industry'],'for sub_sector': a['sub_sector']})
                    
                elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector']=='')):
                    allLogs.append('Got the area level approval but it was for the industry not the subsector')
                    area_level_approvals.append({'cityName': a['city'],'Approval': a['name'],'for industry': a['industry']})
                    
                elif (a['pan_industries']==1):
                    allLogs.append('Got the area level approval but it was for PAN industries, didnt found industry and subsector')
                    area_level_approvals.append({'cityName': a['city'],'Approval': a['name'], 'for pan industries': a['pan_industries']})

                
        
        if area_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Found the Approvals for the given area {area}', 'detailed_info': logs}
        for a in result2:
                
            if (a['city'] == city and a['city_level'] == 1):
                if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                    city_level_approvals.append({'cityName': a['city'],'Approval': a['name'],'for industry': a['industry'],'for sub_sector': a['sub_sector'], 'city_level': a['city_level']})
                    
                elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector']=='')):
                    allLogs.append('Got the city level approval but it was for the industry not the subsector')
                    city_level_approvals.append({'cityName': a['city'],'Approval': a['name'],'for industry': a['industry']})
                    
                elif (a['pan_industries']==1):
                    allLogs.append('Got the city level approval but it was for PAN industries, didnt found industry and subsector')
                    city_level_approvals.append({'cityName': a['city'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
                    
                    # else:
                        # allLogs.append('Didnt got the city level approval, Trying for the State Level Approval')
                
        if city_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Instead of area level got the approvals for city level', 'detailed_info': logs}
        else:
            for a in result2:
                    
                if a['state'] == state and a['state_level'] == 1:
                    if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                        state_level_approvals.append({'stateName': a['state'], 'Approval': a['name'], 'for industry': a['industry'], 'for sub_sector':a['sub_sector'], 'state_level':a['state_level']})
                
                    elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector']== '')):
                        allLogs.append('Got the state level approval but it was for the industry not the subsector')
                        state_level_approvals.append({'stateName': a['state'],'Approval': a['name'],'for industry': a['industry'], 'state_level':a['state_level']})
                    
                    elif (a['pan_industries'] == 1):
                        allLogs.append('Got the state level approval but it was for PAN industries, didnt found industry and subsector')
                        state_level_approvals.append({'stateName': a['state'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
                        
                        # else:
                            # allLogs.append('Didnt got the state level approval, Trying for the Country Level Approval')

        if state_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Instead of area level we got approvals for state level', 'detailed_info': logs}
        else:
            for a in result2:
                    
                if a['country_level'] == 1:
                    if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                        country_level_approvals.append({'stateName': a['state'], 'Approval': a['name'], 'for industry': a['industry'], 'for sub_sector':a['sub_sector'], 'state_level':a['state_level']})
                    
                    elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector']== '')):
                        allLogs.append('Got the country approval but it was for the industry not the subsector')
                        country_level_approvals.append({'stateName': a['state'],'Approval': a['name'],'for industry': a['industry'], 'state_level':a['state_level']})
                        
                    elif (a['pan_industries'] == 1):
                        allLogs.append('Got the countrty level approval but it was for PAN industries, didnt found industry and subsector')
                        country_level_approvals.append({'stateName': a['state'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
            
        if country_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Instead of area, city level and state level we got for country level', 'detailed_info': logs}
        else:
           return {'pass_to_analytics': False, 'log':f'we didnt found approvals for city level or state level or country level and even pan industries', 'detailed_info': None}
        
    def check_for_city():
        '''This function checks approvals for city level for the industry and that sub sector, if not available then for State, if not available then looks for country level PAN industries'''
        if not industry_name and not sub_sector:
            return {'pass_to_analytics': False, 'log':f'Industry and subsector not provided', 'detailed_info': None}
            
        if not industry_name and sub_sector:
            return {'pass_to_analytics': False, 'log':f'Industry name not provided', 'detailed_info': None}
        
        if industry_name:
            subsector_check = f"""SELECT name from `tabSub Sector` WHERE industry_id='{industry_name}'"""
            subsector_res = frappe.db.sql(subsector_check,as_dict=True)
            if subsector_res:
                pass
            else:
                industry_check = f"""SELECT name from `tabIndustry` WHERE name = '{industry_name}'"""
                industry_res = frappe.db.sql(industry_check,as_dict=True)
                if industry_res:
                    pass
                else:
                    return {'pass_to_analytics': False, 'log':f'Didnt found the industry {industry_name} in the database', 'detailed_info': None}
            

        if industry_name and sub_sector:
            subsector =  sub_sector+'-'+industry_name
            #verifying the the given sub sector is of that industry or not 
            first_check = verify_subsector(industry_name,sub_sector)
            if first_check == False:
                return {'pass_to_analytics': False, 'log':f'Industry {industry_name} didnt match with subsector {sub_sector}', 'detailed_info': None}
            zone_check = f"""SELECT zone_id from `tabSub Sector` WHERE name='{subsector}'"""
            res = frappe.db.sql(zone_check,as_dict=True)
            subsector_zone = res[0]['zone_id']
            query1 = f"""SELECT distinct azm.zone from `tabArea Zone Mapping` as azm INNER JOIN `tabArea` as area ON azm.area = area.name WHERE area.city_display_name='{city}'"""
            result1 = frappe.db.sql(query1,as_dict=True)
            zone = [row['zone'] for row in result1]
                
            # Zone Check verification whether city have atleast one zone = subSector Zone 
            if subsector_zone in zone:
                pass
            else:
                return {'pass_to_analytics': False, 'log':f'No zone found in the city ${city} which is same as sub sector zone', 'detailed_info': None}
        elif industry_name and not sub_sector:
            query = f"""SELECT zone_id FROM `tabSub Sector` WHERE industry_id ='{industry_name}'"""
            result = frappe.db.sql(query,as_dict=True)
            zone = set()
            for i in result:
                zone.add(i['zone_id'])

            query1 = f"""SELECT distinct azm.zone from `tabArea Zone Mapping` as azm INNER JOIN `tabArea` as area ON azm.area = area.name WHERE area.city_display_name='{city}'"""
            result1 = frappe.db.sql(query1,as_dict=True)
            area_zone = [row['zone'] for row in result1]
            zone_checklist= set()
            for a in area_zone:
                 if a in zone:
                    zone_checklist.add(a)
                        
            if not zone_checklist:
                return {'pass_to_analytics': False, 'log':f'The area zone didnt matched with industry zones', 'detailed_info':None}

        query2 = f"""SELECT name,city,city_level,state,country_level,state_level,industry,sub_sector,pan_industries from `tabLicenses and Approvals Type` as lat where lat.city='{city}' UNION SELECT name,city,city_level, state, country_level,state_level,industry,sub_sector,pan_industries from `tabLicenses and Approvals Type` where (state_level=1 and state='{state}') OR country_level=1"""
        result2 = frappe.db.sql(query2,as_dict=True)
        subsector =  (sub_sector or '')+'-'+industry_name
        city_level_approvals = []
        state_level_approvals=[]
        country_level_approvals=[]
        
        for a in result2:
                
            if (a['city'] == city and a['city_level'] == 1):
                if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                    city_level_approvals.append({'cityName': a['city'],'Approval': a['name'],'for industry': a['industry'],'for sub_sector': a['sub_sector'], 'city_level': a['city_level']})
                    
                elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector'] is '')):
                    allLogs.append('Got the city level approval but it was for the industry not the subsector')
                    city_level_approvals.append({'cityName': a['city'],'Approval': a['name'],'for industry': a['industry']})
                    
                elif (a['pan_industries'] == 1):
                    allLogs.append('Got the city level approval but it was for PAN industries, didnt found industry and subsector')
                    city_level_approvals.append({'cityName': a['city'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
                    
                    # else:
                        # allLogs.append('Didnt got the city level approval, Trying for the State Level Approval')
                
        if city_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Found the approvals for the given city {city}', 'detailed_info':logs}
        else:
            for a in result2:
                    
                if a['state'] == state and a['state_level'] == 1:
                    if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                        state_level_approvals.append({'stateName': a['state'], 'Approval': a['name'], 'for industry': a['industry'], 'for sub_sector':a['sub_sector'], 'state_level':a['state_level']})
                
                    elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector'] is '')):
                        allLogs.append('Got the state level approval but it was for the industry not the subsector')
                        state_level_approvals.append({'stateName': a['state'],'Approval': a['name'],'for industry': a['industry'], 'state_level':a['state_level']})
                    
                    elif (a['pan_industries'] == 1):
                        allLogs.append('Got the state level approval but it was for PAN industries, didnt found industry and subsector')
                        state_level_approvals.append({'stateName': a['state'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
                        
                        # else:
                            # allLogs.append('Didnt got the state level approval, Trying for the Country Level Approval')

        if state_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Instead of city level we got approvals for state level', 'detailed_info':logs}
        else:
            for a in result2:
                    
                if a['country_level'] == 1:
                    if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                        country_level_approvals.append({'stateName': a['state'], 'Approval': a['name'], 'for industry': a['industry'], 'for sub_sector':a['sub_sector'], 'state_level':a['state_level']})
                    
                    elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector'] is '')):
                        allLogs.append('Got the country level approval but it was for the industry not the subsector')
                        country_level_approvals.append({'stateName': a['state'],'Approval': a['name'],'for industry': a['industry'], 'state_level':a['state_level']})
                        
                    elif (a['pan_industries'] == 1):
                        allLogs.append('Got the conutry level approval but it was for PAN industries, didnt found industry and subsector')
                        country_level_approvals.append({'stateName': a['state'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
            
        if country_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Instead of city level and state level we got for country level', 'detailed_info':logs}
        else:
            return {'pass_to_analytics': False, 'log':f'we didnt found Incentive for city level or state level or country level and even pan industries ', 'detailed_info':None}
                
    def check_for_state():
        '''This function checks approvals for State level for the provided industry and sub sector, if not available then check for country level PAN industries'''
        if not industry_name and not sub_sector:
            return {'pass_to_analytics': False, 'log':f'Industry and subsector not provided', 'detailed_info': None}
            
        if not industry_name and sub_sector:
            return {'pass_to_analytics': False, 'log':f'Industry name not provided', 'detailed_info': None}
            
        if industry_name:
            subsector_check = f"""SELECT name from `tabSub Sector` WHERE industry_id='{industry_name}'"""
            subsector_res = frappe.db.sql(subsector_check,as_dict=True)
            if subsector_res:
                pass
            else:
                industry_check = f"""SELECT name from `tabIndustry` WHERE name = '{industry_name}'"""
                industry_res = frappe.db.sql(industry_check,as_dict=True)
                if industry_res:
                    pass
                else:
                    return {'pass_to_analytics': False, 'log':f'Industry name {industry_name} not in the database', 'detailed_info':None}
        
        if industry_name and sub_sector:
            subsector =  sub_sector+'-'+industry_name
            #verifying the the given sub sector is of that industry or not 
            first_check = verify_subsector(industry_name,sub_sector)
            if first_check == False:
                return {'pass_to_analytics': False, 'log':f'Industry {industry_name} didnt match with subsector {sub_sector}', 'detailed_info':None}
            zone_check = f"""SELECT zone_id from `tabSub Sector` WHERE name='{subsector}'"""
            res = frappe.db.sql(zone_check,as_dict=True)
            subsector_zone = res[0]['zone_id']
            #checking the zone that atleast one city of this state should have that zone
            # query = f"""SELECT azm.zone, area.city_display_name from `tabArea Zone Mapping` as azm INNER JOIN `tabArea` as area ON area.name = azm.area WHERE area.state={state} GROUP BY area.city_display_name"""
            query = f"""SELECT distinct area.city_display_name, GROUP_CONCAT(DISTINCT azm.zone ORDER BY azm.zone SEPARATOR ', ') AS zones FROM `tabArea Zone Mapping` AS azm INNER JOIN `tabArea` AS area ON area.name = azm.area WHERE area.state = '{state}' GROUP BY area.city_display_name"""
            res = frappe.db.sql(query,as_dict=True)
            city_having_zones = []
            for a in res:
                if subsector_zone in a['zones']:
                    city_having_zones.append(a['zones'])
            if not city_having_zones:
                return {'pass_to_analytics': False, 'log':f'Didnt found a single city having zone same as sub sector ', 'detailed_info':None}
                
        elif industry_name and not sub_sector:
            query = f"""SELECT zone_id FROM `tabSub Sector` WHERE industry_id ='{industry_name}'"""
            result = frappe.db.sql(query,as_dict=True)
            zone = set()
            for i in result:
                zone.add(i['zone_id'])

            query = f"""SELECT distinct area.city_display_name, GROUP_CONCAT(DISTINCT azm.zone ORDER BY azm.zone ) AS zones FROM `tabArea Zone Mapping` AS azm INNER JOIN `tabArea` AS area ON area.name = azm.area WHERE area.state = '{state}' GROUP BY area.city_display_name"""
            res = frappe.db.sql(query,as_dict=True)
            zones_array = []
            for a in res:
                zones_array.append(a['zones'].split(',') if a['zones'] else [])
            
            flattened_list = [zone for sublist in zones_array for zone in sublist]
            # Convert to set to remove duplicates
            unique_zones = set(flattened_list)
            if unique_zones.intersection(zone):
                pass
            else:
                return {'pass_to_analytics': False, 'log':f'Industry Zones was not present anywhere in the stat', 'detailed_info':None}
            
            
        query2 = f"""SELECT name,state,state_level,country_level,industry,sub_sector,pan_industries from `tabLicenses and Approvals Type` as lat where (lat.state_level=1 and lat.state='{state}') OR country_level=1"""
        result2 = frappe.db.sql(query2,as_dict=True)
        subsector =  (sub_sector or '')+'-'+industry_name
        city_level_approvals = []
        state_level_approvals=[]
        country_level_approvals=[]
        for a in result2:    
            if a['state'] == state and a['state_level'] == 1:
                if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                    state_level_approvals.append({'stateName': a['state'], 'Approval': a['name'], 'for industry': a['industry'], 'for sub_sector':a['sub_sector'], 'state_level':a['state_level']})
                
                elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector'] is '')):
                    allLogs.append('Got the state level approval but it was for the industry not the subsector')
                    state_level_approvals.append({'stateName': a['state'],'Approval': a['name'],'for industry': a['industry'], 'state_level':a['state_level']})
                    
                elif (a['pan_industries'] == 1):
                    allLogs.append('Got the state level approval but it was for PAN industries, didnt found industry and subsector')
                    state_level_approvals.append({'stateName': a['state'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
                        
                        # else:
                            # allLogs.append('Didnt got the state level approval, Trying for the Country Level Approval')

        if state_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Found the approvals for the state {state} ', 'detailed_info':logs}
        else:
            for a in result2:
                if a['country_level'] == 1:
                    if (a['industry'] == industry_name and a['sub_sector'] == subsector):
                        country_level_approvals.append({'stateName': a['state'], 'Approval': a['name'], 'for industry': a['industry'], 'for sub_sector':a['sub_sector'], 'state_level':a['state_level']})
                    
                    elif (a['industry'] == industry_name and (a['sub_sector'] is None or a['sub_sector'] is '')):
                        allLogs.append('Got the country level approval but it was for the industry not the subsector')
                        country_level_approvals.append({'stateName': a['state'],'Approval': a['name'],'for industry': a['industry'], 'state_level':a['state_level']})
                        
                    elif (a['pan_industries'] == 1):
                        allLogs.append('Got the country level approval but it was for PAN industries, didnt found industry and subsector')
                        country_level_approvals.append({'stateName': a['state'],'Approval': a['name'], 'for pan industries': a['pan_industries']})
            
        if country_level_approvals:
            logs = set(allLogs)
            return {'pass_to_analytics': True, 'log':f'Instead of state level we got approvals for country level', 'detailed_info':logs}
            # return [True,'Instead of state level we got approvals for country level',logs]
        else:
            return {'pass_to_analytics': False, 'log':f'we didnt found Incentive for city level or state level or country level and even pan industries ', 'detailed_info':None}

    def verify_subsector(industry_name,sub_sector):
        '''This function verifies that whether the subsector name is of that industry or not in the database'''
        query = f"""SELECT i.name,s.zone_id FROM `tabIndustry` as i Inner join `tabSub Sector` as s on i.name = s.industry_id WHERE s.name='{sub_sector}-{industry_name}'"""
        result = frappe.db.sql(query,as_dict=True)
          
        industryname = result[0]['name'] if result else None
        zone = result[0]['zone_id'] if result else None
        if not industryname:
            return [False, f'Industry {industry_name} was not found in the database']
        else:
            return [True, 'verified industry and sub sector']

    return parameter_check()