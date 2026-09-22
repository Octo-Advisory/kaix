#region Imports
import requests
import copy
import frappe
import json
from datetime import datetime
# from frontend_app.frontend_app.Management_Class.helpers.utility import checkApiThreshold
from kaix.Management_Class.helpers.utility import checkApiThreshold
from geopy.point import Point
from geopy.distance import geodesic
from shapely.geometry import Polygon, mapping, Point
#endregion

#region Global Varialble Declaration
profile = "mapbox/driving"
access_token="pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ"  

#endregion

#region Helper Functions
def is_valid_lat_long_geopy(lat, lon):
    try:
        Point(lat, lon)
        return True
    except ValueError:
        return False

#create batch of a list
def createBatch(destinations):

    # Getting the Vendor array
    vendor_data = destinations

    # Batch size of 24
    batch_size = 24

    # Create batches
    batches = [vendor_data[i:i + batch_size] for i in range(0, len(vendor_data), batch_size)]
    return batches

#endregion 

#calculate distance between two points
@frappe.whitelist()
def calculateDistance(source,destination):
    profile = "mapbox/driving"
    access_token="pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ"    

    url = f"https://api.mapbox.com/directions-matrix/v1/{profile}/{source};{destination}?sources=0&access_token={access_token}&annotations=distance"
    
    response = requests.get(url)
    responseJson = (response.json())  # Convert the response to JSON
    # Check if the request was successful
    if response.status_code == 200:   
        return round(responseJson["distances"][0][1] / 1000, 2)        
    else:
        return responseJson['message']

@frappe.whitelist()
def CalculateMergedPropSubstationDistance():
    try:
        # Fetch survey numbers from 'Property Proximity'
        proximity_data = frappe.db.get_list('Property Proximity', fields=['connected_property_id'], as_list=True)

        #Fetch substation data
        substation_list = frappe.db.get_list('Substation', fields=['name','title','coordinates','type'])
        
        # Extract survey numbers from tuples into a simple list
        simple_list = [item[0] for item in proximity_data if item[0] not in [None]]

        # Fetch records from 'Survey No' doctype where 'Survey no' is not present in 'Property Proximity' doctype
        connected_propert_list = frappe.db.get_list('Connected Property', filters=[['name', 'not in', simple_list]],fields=['name','map'])
        for item in substation_list:
            lat, lon = item['coordinates'].split(', ')
            new_atitude_longitude = f"{lon.strip()},{lat.strip()}"
            item['coordinates'] = new_atitude_longitude
        # print(connected_propert_list)
        for item in connected_propert_list:
            mapDetail = json.loads(item.map)
            print(len(mapDetail['features']))

        pass
    except:
        pass

@frappe.whitelist()
def CalculatePropSubstationDistance():
    try:

        # Fetch survey numbers from 'Property Proximity'
        proximity_data = frappe.db.get_list('Property Proximity', fields=['survey_no'], as_list=True)
        
        #Fetch substation data
        substation_list = frappe.db.get_list('Substation', fields=['name','title','coordinates','type'])
        
        # Extract survey numbers from tuples into a simple list
        simple_list = [item[0] for item in proximity_data]

        # Fetch records from 'Survey No' doctype where 'Survey no' is not present in 'Property Proximity' doctype
        surveyno_list = frappe.db.get_list('Survey No', filters=[['name', 'not in', simple_list]],fields=['name','latitude_longitude'])
        
        for item in substation_list:
            lat, lon = item['coordinates'].split(', ')
            new_atitude_longitude = f"{lon.strip()},{lat.strip()}"
            item['coordinates'] = new_atitude_longitude
        tempArray = []
        for index,item in enumerate(surveyno_list) :
            if item.get('latitude_longitude') not in (None, '0.000000000'):
                lat, lon = item['latitude_longitude'].split(',')
                new_atitude_longitude = f"{lon.strip()},{lat.strip()}"
                item['latitude_longitude'] = new_atitude_longitude
                tempArray.append(item)
        


        surveyno_list = copy.deepcopy(tempArray)
        destination_list = createBatch(substation_list)

        for sourceitem in surveyno_list:
            distanceArray = []
            addRecord = True
            for batch in destination_list:            
                destinationCount = ";".join(str(i + 1) for i in range(len(batch)))
                dest = ";".join(item["coordinates"] for item in batch)
                if len(substation_list)>1:
                    url = f"https://api.mapbox.com/directions-matrix/v1/{profile}/{sourceitem['latitude_longitude']};{dest}?sources=0&destinations={destinationCount}&access_token={access_token}&annotations=distance"
                else:
                    url = f"https://api.mapbox.com/directions-matrix/v1/{profile}/{sourceitem['latlong']};{dest}?sources=0&access_token={access_token}&annotations=distance"
                print(url)
                response = requests.get(url)
                if response.status_code == 200:     
                    responseJson = (response.json())  # Convert the response to JSON
                    if responseJson["distances"]:
                        distanceArray.extend(responseJson["distances"][0])
                    else:
                        addRecord = False
                else:
                    frappe.log_error(responseJson)
                    addRecord = False
            if addRecord:
                minIndex, minDistance = min(enumerate(distanceArray), key=lambda x: x[1])
                nearestSubstation = substation_list[minIndex]
                doc = frappe.get_doc({
                        'doctype': 'Property Proximity',            
                        "survey_no": sourceitem["name"],
                        "nearest_substation": nearestSubstation["name"],
                        "distance": round(minDistance / 1000, 2)
                    })
                
                doc.insert()
                frappe.db.commit()
    except KeyError:
        frappe.log_error("Error: 'distances' key not found in responseJson.")
        print("Error: 'distances' key not found in responseJson.")
    except ValueError as ve:
        frappe.log_error(f"Error: {ve}")
        print(f"Error: {ve}")
    except Exception as e:
        frappe.log_error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

@frappe.whitelist()
def CalculatePropVenDistance(data):
    try:
        source, destinations = data["Property"], data["Vendor"]
        profile = "mapbox/driving"
        invalidProperty = []
        invalidVendor = []

        for index,sourceitem in enumerate(source):     
            if(len(sourceitem['latlong'].split(',')))>2:                  
                invalidProperty.append(sourceitem)  
            else:
                lat, lon, *_ = sourceitem['latlong'].split(',')
                isvalid = is_valid_lat_long_geopy(lat,lon)
                if not isvalid:                
                    invalidProperty.append(sourceitem)

        for index,vendoritem in enumerate(destinations):  
            if(len(vendoritem['latlong'].split(',')))>2: 
                invalidVendor.append(vendoritem)
            else:
                lat, lon, *_ = vendoritem['latlong'].split(',')
                isvalid = is_valid_lat_long_geopy(lat,lon)
                if not isvalid:                
                    invalidVendor.append(vendoritem)



        # Convert lists to sets for easy comparison
        orignal_set = {json.dumps(prop, sort_keys=True) for prop in source}
        invalidItem_set = {json.dumps(prop, sort_keys=True) for prop in invalidProperty}
        # Find properties that are in 'Property' but not in 'Property1'
        missing_items = [json.loads(prop) for prop in orignal_set - invalidItem_set]
        source = copy.deepcopy(missing_items)

        # Convert lists to sets for easy comparison
        orignal_set = {json.dumps(prop, sort_keys=True) for prop in destinations}
        invalidItem_set = {json.dumps(prop, sort_keys=True) for prop in invalidVendor}
        # Find properties that are in 'Property' but not in 'Property1'
        missing_items = [json.loads(prop) for prop in orignal_set - invalidItem_set]
        destinations = copy.deepcopy(missing_items)
        
        for item in destinations:
            lat, lon, *_ = item['latlong'].split(',')
            item['latlong'] = f"{lon.strip()},{lat.strip()}"

        #removes the variable reference, allowing Python to reclaim memory.
        del orignal_set
        del invalidItem_set
        del missing_items


        customDestinationArray = []
        access_token="pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ"   
        
        dest=""
        batches = createBatch(destinations)
        for sourceitem in source:
            lat, lon, *_ = sourceitem['latlong'].split(',')
            sourceitem['latlong'] = f"{lon.strip()},{lat.strip()}"
            destinationUpdateCount = 0
            tempCustomDestinationArray = []
            for batch in batches:
                destinationCount = ";".join(str(i + 1) for i in range(len(batch)))
                dest = ";".join(item["latlong"] for item in batch)
                if len(destinations)>1:
                    url = f"https://api.mapbox.com/directions-matrix/v1/{profile}/{sourceitem['latlong']};{dest}?sources=0&destinations={destinationCount}&access_token={access_token}&annotations=distance"
                else:
                    url = f"https://api.mapbox.com/directions-matrix/v1/{profile}/{sourceitem['latlong']};{dest}?sources=0&access_token={access_token}&annotations=distance"
                response = requests.get(url)
                responseJson = (response.json())  # Convert the response to JSON
                # Check if the request was successful
                if response.status_code == 200:           
                    if len(destinations)>1:
                        for index,item in enumerate(responseJson["destinations"]):
                        # for item in (responseJson["destinations"]):
                            orignalDest = destinations[destinationUpdateCount]
                            orignalDest["distance"] = round(responseJson["distances"][0][index] / 1000, 2)
                            orignalDest["isError"] = False
                            orignalDest["propertyId"] = sourceitem["id"]
                            tempCustomDestinationArray.append(orignalDest)
                            destinationUpdateCount+=1
                    else:                    
                        orignalDest = destinations[0]
                        orignalDest["distance"] = round(responseJson["distances"][0][1] / 1000, 2)
                        orignalDest["isError"] = False
                        orignalDest["propertyId"] = sourceitem["id"]
                        tempCustomDestinationArray.append(orignalDest)
                        destinationUpdateCount+=1
                else:
                    for item in (responseJson["destinations"]):
                        orignalDest = destinations[destinationUpdateCount]
                        orignalDest["isError"] = True
                        tempCustomDestinationArray.append(orignalDest)
                        destinationUpdateCount+=1
            tempArray = copy.deepcopy(tempCustomDestinationArray)
            customDestinationArray.extend(tempArray)
        result = {}
        # Loop through the data and build the dictionary
        for item in customDestinationArray:
            id_value = item["id"]
            property_id = item["propertyId"]
            distance = item["distance"]
            
            # If the id is not already in the result dictionary, add it
            if id_value not in result:
                result[id_value] = {}
            
            # Add the propertyId and corresponding distance to the nested dictionary
            result[id_value][property_id] = distance
        with open("log3.txt", "a") as file: 
                file.write(f"\nresult {result}")
        return {"IsError":False,"result":result,"InvalidProperty":invalidProperty,"InvalidVendor":invalidVendor}
    except Exception as e:
        with open("log3.txt", "a") as file:
                file.write(f"\nException from here {e}")
        return {"IsError":True,"result":{},"InvalidProperty":invalidProperty,"InvalidVendor":invalidVendor,"error_message":str(e)}
# Function to calculate new lat/lon given a start point and distance
def move_point(lat, lon, dx_km, dy_km):
    new_lat = geodesic(kilometers=dy_km).destination((lat, lon), 0).latitude   # Move North
    new_lon = geodesic(kilometers=dx_km).destination((lat, lon), 90).longitude # Move East
    return new_lat, new_lon
@frappe.whitelist()
def getBBoxData(center_lat, center_lon):
        # Create 100 km x 100 km square polygon
    half_side = 2.5  # 50 km in each direction
    bottom_left = move_point(center_lat, center_lon, -half_side, -half_side)
    bottom_right = move_point(center_lat, center_lon, half_side, -half_side)
    top_right = move_point(center_lat, center_lon, half_side, half_side)
    top_left = move_point(center_lat, center_lon, -half_side, half_side)

    big_square = Polygon([bottom_left, bottom_right, top_right, top_left, bottom_left])

    # Create 100 smaller squares (1 km x 1 km each)
    small_squares = []
    grid_size = 1  # Each small square is 1 km x 1 km

    for i in range(5):  # 100 rows
        for j in range(5):  # 100 columns
            start_lat, start_lon = move_point(bottom_left[0], bottom_left[1], j * grid_size, i * grid_size)
            end_lat, end_lon = move_point(start_lat, start_lon, grid_size, grid_size)

            square = Polygon([
                (start_lon, start_lat),
                (end_lon, start_lat),
                (end_lon, end_lat),
                (start_lon, end_lat),
                (start_lon, start_lat)  # Close the loop
            ])
            small_squares.append(square)

    return {}

# def get_geocode(address):
#     isProcessFurther = checkApiThreshold("Goolge Geocoding Api")
#     if(isProcessFurther):
#         if address  != None and address != "" and address != " ":
#                     try:
#                         actualAddress = copy.deepcopy(address)
#                         address = str(address).upper()
#                         updatedAddress = address+",Gujarat"
#                         #API request
#                         url = f"https://maps.googleapis.com/maps/api/geocode/json?address={updatedAddress}&key=AIzaSyCgESPN3REByWpiQYiRKGpDWwBZLwQEnVA"
#                         response = requests.get(url)
#                         data = response.json()  #parse the JSON data
                        
#                         if data['status'] == 'OK' and len(data['results']) > 0:
#                             for item in data['results']:
#                                 formatted_address = item['formatted_address']
#                                 formatted_address = formatted_address.upper()
#                                 frappe.log_error(formatted_address)
#                                 isAddressPresent = address in formatted_address
#                                 frappe.log_error(isAddressPresent)
#                                 if isAddressPresent:
                                    
#                                     location = item['geometry']['location']
#                                     latitude_longitude = f"{location['lat']},{location['lng']}"
#                                     # location_name = item['address_components'][0]['long_name']
#                                     isAddressPresent = address in formatted_address
#                                     from_gujarat = "Gujarat" in formatted_address
#                                     from_india = "India" in formatted_address
#                                     return {
#                                         'location_info': {
#                                             'location_name': actualAddress,
#                                             'latitude_longitude': latitude_longitude,
#                                             'from_gujarat': from_gujarat,
#                                             'from_india': from_india,
#                                         },
#                                         'isError': False
#                                     }
#                             # formatted_address = data['results'][0]['formatted_address']
#                             # location = data['results'][0]['geometry']['location']
#                             # latitude_longitude = f"{location['lat']},{location['lng']}"
#                             # location_name = data['results'][0]['address_components'][0]['long_name']
                            
#                             # from_gujarat = "Gujarat" in formatted_address
#                             # from_india = "India" in formatted_address
                            
#                             return {
#                                 'location_info': {
#                                     'location_name': None,
#                                     'latitude_longitude': None,
#                                     'from_gujarat': None,
#                                     'from_india': None,
#                                 },
#                                 'isError': False
#                             }
#                         else:
#                             #no valid result found, return False
#                             return {
#                                 'location_info': {
#                                     'location_name': None,
#                                     'latitude_longitude': None,
#                                     'from_gujarat': None,
#                                     'from_india': None,
#                                 },
#                                 'isError': True,
#                                 'error_message':data['status']
#                             }

#                     except Exception as e:
#                         # If any error occurs,
#                         return {
#                             'location_info': {
#                                 'location_name': None,
#                                 'latitude_longitude': None,
#                                 'from_gujarat': None,
#                                 'from_india': None,
#                             },
#                             'isError': True,
#                             'error_message': str(e)  
#                         }
#         else:
#             return {
#                     'location_info': {
#                         'location_name': None,
#                         'latitude_longitude': None,
#                         'from_gujarat': None,
#                         'from_india': None,
#                     },
#                     'isError': True,
#                     'error_message': "Invalid Address" 
#             }
#     else:
#         return {
#             'location_info': {
#                 'location_name': None,
#                 'latitude_longitude': None,
#                 'from_gujarat': None,
#                 'from_india': None,
#             },
#             'isError': True,
#             'error_message': "Api Limit Exceed"  
#         }
@frappe.whitelist()
def get_geocode(address):
    def callApi(url):
        response = requests.get(url)
        data = response.json()  #parse the JSON data
        return data
    def returnResult(location_name=None,latitude_longitude=None,from_gujarat=None,from_india=None,isError=False,error_message=None):
        return {
            'location_info': {
                'location_name': location_name,
                'latitude_longitude': latitude_longitude,
                'from_gujarat': from_gujarat,
                'from_india': from_india,
            },
            'isError': isError,
            'error_message':error_message
        }
    isProcessFurther = checkApiThreshold("Goolge Geocoding Api")
    if(isProcessFurther):
        if address  != None and address != "" and address != " ":
                    try:
                        actualAddress = copy.deepcopy(address)
                        address = str(address).upper()
                        #API request
                        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key=AIzaSyBw2Zjd854U9LZ7StEZ6Ocl1ByZq7QXg7s"
                        data = callApi(url)
                        
                        if data['status'] == 'OK' and len(data['results']) > 0:
                                formatted_address = data['results'][0]['formatted_address']
                                formatted_address = formatted_address.upper()
                                location = data['results'][0]['geometry']['location']
                                latitude_longitude = f"{location['lat']},{location['lng']}"
                                from_gujarat = "GUJARAT" in formatted_address
                                from_india = "INDIA" in formatted_address
                                return returnResult(actualAddress,latitude_longitude,from_gujarat,from_india,False,None)

                        elif data['status'] == 'ZERO_RESULTS' or len(data['results']) <= 0:
                            updatedAddress = address+",Gujarat"
                            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={updatedAddress}&key=AIzaSyCgESPN3REByWpiQYiRKGpDWwBZLwQEnVA"
                            data = callApi(url)
                            if data['status'] == 'OK' and len(data['results']) > 0:
                                for item in data['results']:
                                    formatted_address = item['formatted_address']
                                    formatted_address = formatted_address.upper()                                    
                                    isAddressPresent = address in formatted_address
                                
                                    if isAddressPresent:                                    
                                        location = item['geometry']['location']
                                        latitude_longitude = f"{location['lat']},{location['lng']}"                                    
                                        
                                        from_gujarat = "GUJARAT" in formatted_address
                                        from_india = "INDIA" in formatted_address
                                        return returnResult(actualAddress,latitude_longitude,from_gujarat,from_india,False,None)

                                return returnResult(None,None,None,None,False,None)
                        else:
                            #no valid result found, return False
                            return returnResult(None,None,None,None,False,None)

                    except Exception as e:
                        # If any error occurs,
                        return returnResult(None,None,None,None,True,str(e))                        
 
        else:
            return returnResult(None,None,None,None,True, "Invalid Address")
    else:
        return returnResult(None,None,None,None,True, "Api Limit Exceed")

