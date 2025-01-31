import frappe
import requests



def createUrl(source,destinations):
    profile = "mapbox/driving"
    coordinates=f"{source};{destinations} -122.42,37.78;-122.45,37.91;-122.48,37.73"
    access_token="pk.eyJ1IjoidmlzaGFsY2hhdWhhbjUyNSIsImEiOiJjbHo1M2J5cmszdXF3MmtzaHFyaW9qazMxIn0.7vJesIZKhldn0HKYoAfgpw"
    
    dest=""
    for item in source:
        dest+= source
    url = f"https://api.mapbox.com/directions-matrix/v1/{profile}/{source};{dest}?access_token={access_token}"




@frappe.whitelist()
def CalculateDistance(data):
    url = createUrl(data.Property,data.Vendor)
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        print(response.json())  # Convert the response to JSON
    else:
        frappe.log_error(response.status_code)