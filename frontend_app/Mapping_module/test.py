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
                                "name": element["geometry"]["properties"]["name"],
                                "area": element["geometry"]["properties"]['area'],
                                "city": element["geometry"]["properties"]['city'],
                                "taluka": element["geometry"]["properties"]['taluka'],
                                "district": element["geometry"]["properties"]['district'],
                                "zone": element["geometry"]["properties"]['zone'],
                                "area_acre": element["geometry"]["properties"]['area_acre']
                            }}}

def mergeProperty(properties,currentPropertyId):
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
                        }
                    }
            newArray.append(obj)

    # Example polygons with properties
    array = [
        {"geometry": {"type": "Polygon", "coordinates": [[[73.01469090699968, 21.605449474000014], [73.01465682899969, 21.605020530999994], [73.0144992989997, 21.605157724999984], [73.01340623299973, 21.60661957499999], [73.01343959199964, 21.606676436000022], [73.01378319099973, 21.606647489000025], [73.01469090699968, 21.605449474000014]]] , "properties": {"name": "Blank_5"}}},
        {"geometry": {"type": "Polygon", "coordinates": [[[73.01450531699967, 21.606215062999993], [73.01447275999969, 21.605873015999993], [73.01419706699969, 21.606230968], [73.01450531699967, 21.606215062999993]]], "properties": {"name": "Plot_20"}}},
        {"geometry": {"type": "Polygon", "coordinates": [[[73.0133444699997, 21.606887289999996], [73.01333439399971, 21.606783967000027], [73.0131385769997, 21.606480536999996], [73.0127976359997, 21.606928009000036], [73.0133444699997, 21.606887289999996]]], "properties": {"name": "RP_14"}}},
        {"geometry": {"type": "Polygon", "coordinates": [[[73.01453671499974, 21.60658831799999], [73.01451399899963, 21.606311925000014], [73.01412765399967, 21.606329078000016], [73.0139149469997, 21.606614621000016], [73.01392254399974, 21.606629754999997], [73.01393448199974, 21.60663379099999], [73.01453671499974, 21.60658831799999]]] , "properties": {"name": "Plot_15"}}},
        {"geometry": {"type": "Polygon", "coordinates": [[[73.01479307699967, 21.606777629000035], [73.01478401799972, 21.606652463999993], [73.01349185499967, 21.606755008], [73.01349992899966, 21.60687618400002], [73.01479307699967, 21.606777629000035]]], "properties": {"name": "Blank_3"}}},
        {"geometry": {"type": "Polygon", "coordinates": [[[73.01459948399966, 21.60495659700004], [73.0144154299997, 21.604826055000025], [73.0143150579997, 21.604929104000025], [73.01323798999968, 21.606356953], [73.01335953099968, 21.606543071000004], [73.01441145299965, 21.60512877700003], [73.01459948399966, 21.60495659700004]]], "properties": {"name": "Blank_4"}}},
        {"geometry": {"type": "Polygon", "coordinates": [[[73.01477826199968, 21.606572933000024], [73.01470018899968, 21.605566311000047], [73.01455378499965, 21.605762523000028], [73.01462272699972, 21.606584425000005], [73.01477826199968, 21.606572933000024]]], "properties": {"name": "20P_2"}}},
    ]

    # Buffer distance in meters
    buffer_distance = 10  # Adjust as needed
    uniqueProperty = []
    frappe.log_error("newArray"+ str(len(newArray)) )
    # Iterate through each element
    for index, element in enumerate(newArray):
        convertCoord = convertTo3857(element["geometry"]["coordinates"])
        currentElement = copy.deepcopy(element)
        currentElement["geometry"]["coordinates"] = convertCoord
        element_polygon = shape(currentElement["geometry"])  # Convert to Shapely Polygon
        element_name = currentElement["geometry"]["properties"]["name"]

        # Extend boundary by buffering
        buffered = element_polygon.buffer(buffer_distance)
        
        # Example logic: Compare overlaps with other polygons
        for index1, element1 in enumerate(newArray):
            
            if index != index1:  # Ensure different polygons are compared
                coordinates_copy1 = copy.deepcopy(element1["geometry"]["coordinates"])
                convertCoord1 = convertTo3857(coordinates_copy1)#convert to epsg:3857           

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
                    isFrom_present = any(
                                        propertyItem["geometry"]["properties"]["name"] == property["from"]
                                        for propertyItem in uniqueProperty
                                    )
                    if not isFrom_present:
                        uniqueProperty.append(createPolygon(currentElement,buffered.__geo_interface__["coordinates"]))

                    isTo_present = any(
                                        propertyItem["geometry"]["properties"]["name"] == property["to"]
                                        for propertyItem in uniqueProperty
                                    )
                    if not isTo_present:
                        uniqueProperty.append(createPolygon(currentElement1,convertCoord1))
                        
    frappe.log_error(len(uniqueProperty))
    tempPropertiesToDelete = list(filter(lambda item: item["geometry"]["properties"]["name"] != currentPropertyId, uniqueProperty))
    nameArrayToDelete = ",".join(item["geometry"]["properties"]["name"] for item in uniqueProperty)
    if len(uniqueProperty)>0:
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
       
        if merged_polygon.geom_type == 'Polygon':
            boundary_coords = list(merged_polygon.exterior.coords)
        # If merged_polygon is a MultiPolygon, you can loop over each polygon in the collection
        elif merged_polygon.geom_type == 'MultiPolygon':
            for polygon in merged_polygon.geoms:  # Use the 'geoms' attribute to iterate
                boundary_coords = list(polygon.exterior.coords)
                print(boundary_coords)
            # for polygon in merged_polygon:
            #     boundary_coords = list(polygon.exterior.coords)
        convertValues = convertTo4326(boundary_coords)
        totalArea = 0
        for item in uniqueProperty:
            totalArea+= float(item["geometry"]["properties"]["area_acre"]) 
        
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
        # Delete records

        data = frappe.get_all('Connected Property', filters=[
                ['survey_no_array', '=', nameArrayToDelete],

                ],
                fields=["*"])
        
        for itemToDelete in data:           
            frappe.delete_doc('Connected Property', itemToDelete.name)
            frappe.db.commit()
            
        nameArrayToInsert = ",".join(item["geometry"]["properties"]["name"] for item in uniqueProperty)

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
        return (resObject)
    else:
        return []


@frappe.whitelist()
def JustForTestin(properties,currentPropertyId):
    res = mergeProperty(properties,currentPropertyId)
    #locationDetail = json.loads(data.location_pin)
    #if len(locationDetail["features"])>0:



    return res