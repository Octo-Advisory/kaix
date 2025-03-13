import React, { useEffect, useState } from 'react'
import 'leaflet/dist/leaflet.css';
// import { result } from './data'
import './Industryresult.css'

import { FaMapMarkedAlt, FaBuilding } from "react-icons/fa";
import Properties from '../Property/Properties';
import MapComponent from '../MapComponent/MapComponent';
import Backtochat from '../Backtochat/Backtochat';
import Details from '../Details/Details';

function Industryresult({ result }) {
// function Industryresult() {

    const [activeTab, setActiveTab] = useState("property");
    console.log("result in indeustry solution screen", result);
    const analytics_response = result["Analytics_response"]
    console.log("Analytics_response", analytics_response);

    const [solutions, setSolutions] = useState([])

    const fetchData = async (property) => {
        console.log("proprtis here", property);
        try {
            const response = await fetch(`api/resource/Survey No?fields=["*"]&filters=[["name","=","${property}"]]&order_by=modified asc`, {
                method: 'GET',
                headers: {
                    'Authorization': 'token d3de1e0e4e25846:3d3be60aaa3b67c',
                    'Content-Type': 'application/json'
                }
            });
            // Check if the response is OK
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("data is", data.data);
            return data.data
        } catch (error) {
            console.error('Error fetching data:', error); // Handles errors
        }
    }

    const fetchPropertyData = async (analytics_response) => {
        let preaparedSolutions = [];
        const final_scoring_df = JSON.parse(analytics_response['final_scoring_df'])
        console.log("final_scoring_df", final_scoring_df);
        const property_id = final_scoring_df["Property_ID"]
        console.log("pid", property_id);

        // for supply and vendors
        const Essential_supply_vendor_lookup_df = JSON.parse(analytics_response['Essential_supply_vendor_lookup_df'])
        console.log("Essential_supply_vendor_lookup_df", Essential_supply_vendor_lookup_df);

        const nonEssential_supply_vendor_lookup_df = JSON.parse(analytics_response['Non_essential_supply_vendor_lookup_df'])
        console.log("nonEssential_supply_vendor_lookup_df", nonEssential_supply_vendor_lookup_df);

        // for employemnt 
        const Employment_lookup_df = JSON.parse(analytics_response['Employment_lookup_df'])
        console.log("Employment_lookup_df", Employment_lookup_df);


        // for incenetive
        const Solution_lookup_df = JSON.parse(analytics_response['Solution_lookup_df'])
        console.log("Solution_lookup_df", Solution_lookup_df);

        //for approvals
        const Approval_lookup_df = JSON.parse(analytics_response['Approval_lookup_df'])
        console.log("Approval_lookup_df", Approval_lookup_df);

        const promises = Object.entries(property_id).map(async ([key, value]) => {
            console.log(`key ${key} value ${value}`);
            try {
                const get_data = await fetchData(value)
                const data = get_data[0]
                console.log("actual result data", data);

                if (data) {
                    const boundary_coordinates = data.boundary_coordinates // Add by ushan 
                    const latLong = data.latitude_longitude
                    const latLongArray = latLong ? latLong.split(', ').map(coord => parseFloat(coord)) : []    
                    const area = data.area
                    const city = data.city
                    const district = data.district
                    const availability_of_local_transportation = data.availability_of_local_transportation
                    const road_connectivity = data.road_connectivity
                    const area_acre = data.area_acre
                    const state = data.state
                    const property_type = data.property_type
                    const business_location_type = data.business_location_type
                    const distance_from_power_source = data.distance_from_power_source
                    const distance_from_nearest_railway_station = data.distance_from_nearest_railway_station
                    const distance_from_nearest_airport = data.distance_from_nearest_airport
                    const distance_from_nearest_seaport = data.distance_from_nearest_seaport

                    const essential_supply_and_vendor = []
                    const nonessential_supply_and_vendor = []

                    if (Essential_supply_vendor_lookup_df["No_of_vendors_found"][key] > 0) {
                        const ess_supply_id = Essential_supply_vendor_lookup_df["supply_id"][key]
                        const ess_No_of_vendors_found = Essential_supply_vendor_lookup_df["No_of_vendors_found"][key]
                        const ess_Distance = Essential_supply_vendor_lookup_df["Distance"][key]

                        ess_supply_id.forEach((supply, index) => {
                            const supply_vendor = { supply: supply, total_vendor: ess_No_of_vendors_found[index], nearest_venodor_distance: ess_Distance[index], status: get_status_for_distance(ess_Distance[index]) }
                            essential_supply_and_vendor.push(supply_vendor)
                        })
                    }

                    if (nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key] > 0) {
                        const noness_supply_id = nonEssential_supply_vendor_lookup_df["supply_id"][key]
                        const noness_No_of_vendors_found = nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key]
                        const noness_Distance = nonEssential_supply_vendor_lookup_df["Distance"][key]

                        noness_supply_id.forEach((supply, index) => {
                            const supply_vendor = { supply: supply, total_vendor: noness_No_of_vendors_found[index], nearest_venodor_distance: noness_Distance[index], status: get_status_for_distance(noness_Distance[index]) }
                            nonessential_supply_and_vendor.push(supply_vendor)
                        })
                    }


                    console.log("essential_supply_and_vendor", essential_supply_and_vendor);


                    const emp_skill_type = Employment_lookup_df['Skill_Type'][key]
                    const count = Employment_lookup_df[`${emp_skill_type}`][key]

                    // for incentive make array
                    const incenetives = []
                    const incentive_name = Solution_lookup_df['incentive_name'][key]
                    const incentive_type = Solution_lookup_df['incentive_type'][key]
                    const incentive_rank = Solution_lookup_df['incentive_rank'][key]
                    incentive_name.forEach((incentive, index) => {
                        const inc = { incentive_name: incentive, incentive_rank: incentive_rank[index], incentive_type: incentive_type[index] }
                        incenetives.push(inc)
                    })

                    // for approvals make array
                    const approval_name = Approval_lookup_df["approval_name"][key]
                    const government_department = Approval_lookup_df["government_department"][key]
                    const online_or_offline = Approval_lookup_df["online_or_offline"][key]
                    const stages = Approval_lookup_df["stages"][key]
                    const time_taken = Approval_lookup_df["time_taken"][key]
                    const approvals = []

                    approval_name.forEach((approval, index) => {
                        const appr = { approval_name: approval_name[index], government_department: government_department[index], online_or_offline: online_or_offline[index], stages: stages[index], time_taken: time_taken[index] }
                        approvals.push(appr)
                    })

                    const road_transport = availability_of_local_transportation == 'Yes' ? 'good' : 'bad'

                    const solution = {
                        address: `${area || city}, ${district}, ${state}`,
                        property_type: property_type,
                        total_area: area_acre,
                        lat_long: latLongArray,
                        business_location_type: business_location_type || 'GIDC',
                        availability_of_local_transportation: road_transport,
                        seaport: { distance: distance_from_nearest_seaport, status: get_status_for_distance(distance_from_nearest_seaport) },
                        airport: { distance: distance_from_nearest_airport, status: get_status_for_distance(distance_from_nearest_airport) },
                        power: { distance: distance_from_power_source, status: get_status_for_distance(distance_from_power_source) },
                        railway: { distance: distance_from_nearest_railway_station, status: get_status_for_distance(distance_from_nearest_railway_station) },
                        essential_vendors: essential_supply_and_vendor,
                        nonessential_vendors: nonessential_supply_and_vendor,
                        employement: { type: emp_skill_type, count: count },
                        incentives: incenetives,
                        approvals: approvals,
                        road_connectivity: { distance: road_connectivity, status: get_status_for_distance(road_connectivity) },
                        boundary_coordinates: boundary_coordinates, // Add by ushan 
                        result_type:"Industry_Result" // Add by ushan 
                    }
                    console.log("solution json", solution);
                    preaparedSolutions.push(solution)
                    console.log("final array is", preaparedSolutions);
                }
            } catch (error) {
                console.log("error is ", error);
            }

        });

        await Promise.all(promises);
        setSolutions(preaparedSolutions);
    };

    useEffect(() => {
        fetchPropertyData(analytics_response);
    }, []);

    const get_status_for_distance = (distance) => {
        if (distance < 100) {
            return "good";
        } else if (distance >= 100 && distance < 200) {
            return "warning";
        } else if (distance >= 200 && distance < 300) {
            return "danger";
        } else {
            return "bad";
        }
    }

    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
        <div className="w-[98%] h-[98%] mx-auto p-4 bg-white rounded-lg shadow-md">
          <div className="border-b border-gray-200 dark:border-gray-700 flex justify-between">
            <ul className="flex flex-wrap -mb-px text-sm font-medium text-center text-gray-500 dark:text-gray-400">
              <li className="me-2">
                <button
                  onClick={() => setActiveTab("property")}
                  className={`inline-flex items-center justify-center p-4 border-b-2 rounded-t-lg group transition-all ${
                    activeTab === "property"
                      ? "text-blue-600 border-blue-600 dark:text-blue-500 dark:border-blue-500"
                      : "border-transparent hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300"
                  }`}
                >
                  <FaBuilding
                    className={`w-5 h-5 me-2 ${
                      activeTab === "property" ? "text-blue-600 dark:text-blue-500" : "text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-300"
                    }`}
                  />
                  Property
                </button>
              </li>
              <li className="me-2">
                <button
                  onClick={() => setActiveTab("map")}
                  className={`inline-flex items-center justify-center p-4 border-b-2 rounded-t-lg group transition-all ${
                    activeTab === "map"
                      ? "text-blue-600 border-blue-600 dark:text-blue-500 dark:border-blue-500"
                      : "border-transparent hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300"
                  }`}
                >
                  <FaMapMarkedAlt
                    className={`w-5 h-5 me-2 ${
                      activeTab === "map" ? "text-blue-600 dark:text-blue-500" : "text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-300"
                    }`}
                  />
                  Map
                </button>
              </li>
            </ul>
            <Backtochat/>
          </div>
          <div className="mt-1 w-full h-full">{activeTab === "property" ? <Properties solutions = {solutions}/> : <MapComponent solutions= {solutions}/>}</div>
        </div>
        <Details/>
      </div>
    )
}

export default Industryresult