import frappe
def all_conditions(Area, City, State):
    
    # checking if state name is not NONE
    def condition1():
        if not State:
            reason_of_failing("Got the State value = None")
        elif not Area and not City and State:
            return condition2()
        elif not Area and City and State:
            return condition3()
        elif Area and City and State:
            return condition3() #by default it will check for the city only 
     
    # checking the cities of a state           
    def condition2():
        city_names = []
        query = f"SELECT name FROM `tabCity` AS s WHERE s.state='{State}' ;"
        result = frappe.db.sql(query, as_dict=True)
        for row in result:
            city_names.append(row['name'])
        
        return got_names(city_names)
    
    #checking for a single city
    def condition3():
        que = f"SELECT name FROM `tabCity` WHERE city_name='{City}'"
        result = frappe.db.sql(que,as_dict=True)
        for d in result:
            city= [d['name']]
            
        forLogs(city)
        return checks(city)
        
    def got_names(city_names):
        forLogs(city_names)
        return checks(city_names)
        
    def checks(city_names):
        incomplete_count = []
        complete_city = []
        incomplete_city = []
        all_areas = []
        
        for cityy in city_names:
            query = f" SELECT name FROM `tabArea` WHERE city_id='{cityy}'"
            result = frappe.db.sql(query, as_dict=True)
         
            complete_count = []
            
            for areaname in result:
                areaa = areaname['name']
                all_areas.append(areaa)
                query2 = f"SELECT name,availability FROM `tabEmployment City Mapping` as i WHERE i.name IN ('Semi-skilled-{areaa}','Skilled-{areaa}','Unskilled-{areaa}')"
                result2 = frappe.db.sql(query2, as_dict=True)
               
                if len(result2) < 3:
                    # incomplete_count.append(f'The city {cityy} has one area {areaa} that have incomplete record so we stopped ❌')
                    incomplete_count.append(areaa)
                elif len(result2) ==3:
                    # complete_count.append(f'The city {cityy} has area {areaa} that have complete records')
                    complete_count.append(areaa)
            if len(complete_count) == len(result):
                complete_city.append({"cityname": cityy, "areas": result})
            else:
                incomplete_city.append({'cityname':cityy, "areas":result})
      
        if len(complete_city) >0:
            return complete_citys(complete_city)
        else:
            reason_of_failing(f'we Didnt got the areas that had all the three types in data : {incomplete_city}')
            return False
        
    def complete_citys(cities):
        checked_cities = []
        incomplete_cities = []
        
        for cityy in cities:
            city_name = cityy["cityname"]
            areas = cityy["areas"]
            area_data_list = []
            count = 0
            skilled=0
            unskilled=0
            semiskilled=0
            loopcount =0
            for areaname in areas:
                
                areaa= areaname['name']
                query = f"SELECT availability,name FROM `tabEmployment City Mapping` AS i WHERE i.name IN ('Skilled-{areaa}','Semi-skilled-{areaa}','Unskilled-{areaa}')"
                result = frappe.db.sql(query, as_dict=True)
                first = result[0]['availability']
                second = result[1]['availability']
                third = result[2]['availability']
                if count==0:
                    skilled= first
                    unskilled= second
                    semiskilled= third
                
                if skilled == first and unskilled == second and semiskilled == third:
                    loopcount = loopcount+1
                else:
                    break
            if loopcount == len(areas):
              
                checked_cities.append(city_name)
            else:
                incomplete_cities.append(city_name)
                

        if checked_cities:
            return True
        else: 
            reason_of_failing(f'here we didnt even got a single city that have perfect records , and this much cities had incomplete data {incomplete_cities}')
            return False
            
    def forLogs(city_names):
        complete_data = []
        incomplete_data = []
        for cityy in city_names:
            query = f"SELECT name FROM `tabArea` WHERE city_id='{cityy}'"
            result = frappe.db.sql(query, as_dict=True)
            for areaname in result:
                areaa = areaname['name']
                query2 = f"SELECT name,availability FROM `tabEmployment City Mapping` AS i WHERE i.name IN ('Semi-skilled-{areaa}','Skilled-{areaa}','Unskilled-{areaa}')"
                result2 = frappe.db.sql(query2, as_dict=True)
                if len(result2) < 3:
                    for ecm in result2:
                        valid = ecm['availability']
                        if valid < 0:
                            incomplete_data.append(f'In {cityy} we found negative values in {ecm} of area {areaa}')
                    incomplete_data.append(f'In city {cityy} and area {areaa} we found only {result2} which is incomplete')
                elif len(result2) == 3:
                    for ecm in result2: 
                        valid = ecm['availability']
                        if valid < 0:
                            incomplete_data.append(f'In {cityy} we found negative values in {ecm} of area {areaa}')
                    complete_data.append(f'In {cityy} and area {areaa} we found complete data that is {result2} ')
        all_logs(incomplete_data) 
    
    return condition1()   
    
def reason_of_failing(reason):
    print(reason)
        
def all_logs(data):
    print('all logs ',data)

all_conditions('','','Gujarat') #from here you can test by passing diff arguments like (Area, City, State)
result = all_conditions('','','Gujarat')
print('this ',result)