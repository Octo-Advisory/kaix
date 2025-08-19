import frappe
import json
from shapely.geometry import shape, Polygon
from pyproj import Proj,transform
import copy
from shapely.ops import unary_union
from datetime import datetime

def convertTo3857(coord):
    # Define projections
    proj_3857 = Proj(init='epsg:3857')  # Web Mercator (meters)

    polygon_3857 = []
    for ring in coord:
        new_ring = []
        for lon, lat in ring:
            # Validate the latitude and longitude range
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                x, y = proj_3857(lon, lat)
                if not (float('inf') in [x, y]):  # Avoid invalid projections
                    new_ring.append([x, y])
                else:
                    print(f"Invalid projection result for ({lon}, {lat})")
            else:
                print(f"Invalid coordinate: ({lon}, {lat})")
        polygon_3857.append(new_ring)
    return polygon_3857

def convertTo4326(coord):
    # Define projections
    proj_4326 = Proj(init='epsg:4326')  # WGS84 (lat, lon)
    proj_3857 = Proj(init='epsg:3857')  # Web Mercator (meters)
    
    polygon_4326 = []
    for ring in coord:
        x, y = ring  # Unpack the tuple to x, y
         # Convert from EPSG:3857 to EPSG:4326
        lon, lat = transform(proj_3857, proj_4326, x, y)
        # Validate the latitude and longitude range
        if -180 <= lon <= 180 and -90 <= lat <= 90:
            polygon_4326.append([lon, lat])
        else:
            print(f"Invalid coordinate after conversion: ({lon}, {lat})")

    return polygon_4326

def createPolygon(element,coordinate):
    return {"geometry": {"type": "Polygon", "coordinates": coordinate ,
                               "properties": {
                                "name": element["name"],
                                "area": element["area"],
                                "city": element["city"],
                                "taluka": element["taluka"],
                                "district": element["district"],
                                "zone": element["zone"],
                                "area_acre": element["area_acre"]
                            }
                            }}

def ApplyMerge(properties,currentProerty):
    rawArray = properties
    newArray = []
    for item in rawArray:
        locationDetail = json.loads(item['location_pin'])
        if len(locationDetail["features"]) > 1:
            coord = locationDetail["features"][1]['geometry']['coordinates']
            obj = {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": coord,
                            "properties": {
                                "name": item['name'],
                                "area": item['area'],
                                "city": item['city'],
                                "taluka": item['taluka'],
                                "district": item['district'],
                                "zone": item['zone'],
                                "area_acre": item['area_acre']
                            }
                        },   
                        "name": item['name'],
                         "area": item['area'],
                         "city": item['city'],
                         "taluka": item['taluka'],
                         "district": item['district'],
                         "zone": item['zone'],
                         "area_acre": item['area_acre']
                    }
            newArray.append(obj)

    # Buffer distance in meters
    buffer_distance = 10  # Adjust as needed
    uniqueProperty = []
    
    # Iterate through each element
    currentLocationDetail = json.loads(currentProerty["location_pin"])
    if len(currentLocationDetail["features"]) > 1:
        convertCoord = convertTo3857(currentLocationDetail["features"][1]["geometry"]["coordinates"])
        currentLocationDetail["features"][1]["geometry"]["coordinates"] = convertCoord   
        element_polygon = shape(currentLocationDetail["features"][1]["geometry"])  # Convert to Shapely Polygon
        element_name = currentProerty["name"]

        # Extend boundary by buffering
        buffered = element_polygon.buffer(buffer_distance)
        
        # Example logic: Compare overlaps with other polygons
        for  index1,element1 in enumerate(newArray):        
            convertCoord1 = convertTo3857(element1["geometry"]["coordinates"])#convert to epsg:3857           
            currentElement1 = copy.deepcopy(element1)
            currentElement1["geometry"]["coordinates"] = convertCoord1
            element1_polygon = shape(currentElement1["geometry"])  # Convert to Shapely Polygon
            element1_name = currentElement1["geometry"]["properties"]["name"]
            # Check if the boundaries overlap
            if buffered.intersects(element1_polygon):
                property = {
                    'from':element_name,                   
                    'fromCoordinates': buffered.__geo_interface__["coordinates"],
                    'to':element1_name,
                    'toCoordinates':convertCoord1,
                }
                #adding current/recently added property
                isFrom_present = any(
                                    propertyItem["geometry"]["properties"]["name"] == element_name
                                    for propertyItem in uniqueProperty
                                )
                if not isFrom_present:
                    uniqueProperty.append(createPolygon(currentProerty,buffered.__geo_interface__["coordinates"]))
                
                #adding other property which are connected to current property
                isTo_present = any(
                                    propertyItem["geometry"]["properties"]["name"] == element1_name
                                    for propertyItem in uniqueProperty
                                )
                
                if not isTo_present:
                    uniqueProperty.append(createPolygon(currentElement1,convertCoord1))
                            
        
        tempPropertiesToDelete = list(filter(lambda item: item["geometry"]["properties"]["name"] != currentProerty["name"], uniqueProperty))
        nameArrayToDelete = ",".join(item["geometry"]["properties"]["name"] for item in tempPropertiesToDelete)
        frappe.log_error(f"current Property len {len(uniqueProperty)}")
        if len(uniqueProperty)>1:
            
            # Create Shapely Polygon objects
            polygons = [Polygon(item['geometry']['coordinates'][0]) for item in uniqueProperty]
            # Validate geometries before merging
            valid_geometries = [geom for geom in polygons if geom.is_valid]
            # Merge all buffered polygons into one
            merged_polygon = unary_union(valid_geometries)
            # Access the boundary coordinates (the exterior)
        
            # Get the centroid of the polygon
            centroid = merged_polygon.centroid
            centerPoint = [centroid.x, centroid.y]
            centerPoint = (convertTo4326([centerPoint]))[0]

            #region get boundry coordinates
            if merged_polygon.geom_type == 'Polygon':
                boundary_coords = list(merged_polygon.exterior.coords)
                convertValues = convertTo4326(boundary_coords)
            #end region
            
            #region If merged_polygon is a MultiPolygon, you can loop over each polygon in the collection
            elif merged_polygon.geom_type == 'MultiPolygon':
                featureArray=[]
                featureArray.append()
                for polygon in merged_polygon.geoms:  # Use the 'geoms' attribute to iterate
                    boundary_coords = list(polygon.exterior.coords)
                    print(boundary_coords)
                    convertValues = convertTo4326(boundary_coords) 
            #endregion
    

            #region Calculate Total Area
            totalArea = 0
            for item in uniqueProperty:
                area = item["geometry"]["properties"]["area_acre"]
                isFaultvalue = area in {None, "NoneType", ""} 
                area = 0.0 if isFaultvalue else area
                totalArea+= area
            #endregion


            #region create map object
            mapCoor = {'type': 'FeatureCollection', 'features': [
                        {'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Point', 'coordinates': centerPoint
                            }
                        },
                        {'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [convertValues]
                            }
                        }
                    ]
                }
            mapCoor = json.dumps(mapCoor) 
            #endregion
            

            
            nameArrayToInsert = ",".join(item["geometry"]["properties"]["name"] for item in uniqueProperty)

            # check if mergeed property is alerady exists
            data = frappe.get_all('Connected Property', filters=[
                    ['survey_no_array', '=', str(nameArrayToInsert)]
                    ],
                    fields=["*"])
            
            frappe.log_error("Data Length "+str(len(data)))
            if len(data) <= 0:
                # Delete records
                data = frappe.get_all('Connected Property', filters=[
                        ['survey_no_array', '=', nameArrayToDelete]],
                        fields=["*"])
                
                for itemToDelete in data:           
                    frappe.delete_doc('Connected Property', itemToDelete.name)
                    frappe.db.commit()

                frappe.log_error("nameArrayToInsert "+nameArrayToInsert)
                doc = frappe.get_doc({
                    'doctype': 'Connected Property',            
                    "area": uniqueProperty[0]["geometry"]["properties"]['area'],
                    "city": uniqueProperty[0]["geometry"]["properties"]['city'],
                    "taluka": uniqueProperty[0]["geometry"]["properties"]['taluka'],
                    "district": uniqueProperty[0]["geometry"]["properties"]['district'],
                    "zone": uniqueProperty[0]["geometry"]["properties"]['zone'],
                    "total_area_in_acre": totalArea,
                    'map':mapCoor,
                    'survey_no_array':nameArrayToInsert
                })
            
                doc.insert()
                frappe.db.commit()

                for item in uniqueProperty:
                    childDoc = frappe.get_doc({
                    'parent': doc.name,
                    "parentfield": "section_break_m9bt",
                    "parenttype": "Connected Property",
                    "doctype": "Connected Properties",
                    "survey_no": item["geometry"]["properties"]['name']
                    })

                    childDoc.insert( ignore_permissions=True)
                    frappe.db.commit()

            resObject ={
                'connected_properties':uniqueProperty,
                'boundry':convertValues,
                'totalArea':totalArea
            } 
            return (uniqueProperty)
        else:
            return []
    else:
        return []

@frappe.whitelist()
def CreateMergedProperty(properties,currentProerty):
    prop = {
                "name": currentProerty.name,
                "area": currentProerty.area,
                "city": currentProerty.city,
                "taluka": currentProerty.taluka,
                "district": currentProerty,
                "zone": currentProerty.zone ,
                "area_acre": currentProerty.area_acre,
                "location_pin":currentProerty.location_pin
            }

    res = ApplyMerge(properties,prop)
    return res