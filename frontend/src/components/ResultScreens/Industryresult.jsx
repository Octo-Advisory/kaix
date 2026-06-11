import React, { useEffect, useState } from 'react'
import 'leaflet/dist/leaflet.css';
import './Industryresult.css'
import { FaMapMarkedAlt, FaBuilding, FaChartLine } from "react-icons/fa";
import Properties from '../Property/Properties';
import MapComponent from '../MapComponent/MapComponent';
import Backtochat from '../Backtochat/Backtochat';
import Model from '../ResultScreens/Model';
// import { result } from './data';
import Details from '../Details/Details';

function Industryresult({ result }) {
  console.log("insdutry",result);
  
// function Industryresult() {
  const [activeTab, setActiveTab] = useState("property");
  const [isLoading, setIsLoading] = useState(true);
  const analytics_response = result["Analytics_response"]
  console.log("analytics respon",analytics_response);
  
  const [solutions, setSolutions] = useState([])

  const fetchData = async (property) => {
    try {
      const response = await fetch(`/api/resource/Survey No?fields=["*"]&filters=[["name","=","${property}"]]&order_by=modified asc`, {
        method: 'GET',
        headers: {
          'Authorization': 'token d3de1e0e4e25846:a17a89fc01bd744',
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`Error: ${response.statusText}`);
      const data = await response.json();
      return data.data
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  }

  const fetchPropertyData = async (analytics_response) => {
    let preaparedSolutions = [];
    const final_scoring_df = JSON.parse(analytics_response['final_scoring_df'])
    const property_id = final_scoring_df["Property_ID"]

    const Essential_supply_vendor_lookup_df = JSON.parse(analytics_response['Essential_supply_vendor_lookup_df'])
    const nonEssential_supply_vendor_lookup_df = JSON.parse(analytics_response['Non_essential_supply_vendor_lookup_df'])
    const Employment_lookup_df = JSON.parse(analytics_response['Employment_lookup_df'])
    const Solution_lookup_df = JSON.parse(analytics_response['Solution_lookup_df'])
    const Approval_lookup_df = JSON.parse(analytics_response['Approval_lookup_df'])
    console.log("essen", Essential_supply_vendor_lookup_df);


    const promises = Object.entries(property_id).map(async ([key, value]) => {
      try {
        const get_data = await fetchData(value)
        const data = get_data[0]

        if (data) {
          const boundary_coordinates = data.boundary_coordinates
          const latLong = data.latitude_longitude
          const latLongArray = latLong ? latLong.split(',').map(coord => parseFloat(coord)) : []
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

          if (Essential_supply_vendor_lookup_df["No_of_vendors_found"][key] && Array.isArray(Essential_supply_vendor_lookup_df["No_of_vendors_found"][key]) && Essential_supply_vendor_lookup_df["No_of_vendors_found"][key].length > 0) {
            const ess_supply_id = Essential_supply_vendor_lookup_df["supply_id"][key] || [];
            const ess_No_of_vendors_found = Essential_supply_vendor_lookup_df["No_of_vendors_found"][key] || [];
            const ess_Distance = Essential_supply_vendor_lookup_df["Distance"][key] || [];

            ess_supply_id.forEach((supply, index) => {
              if (ess_No_of_vendors_found[index] !== undefined && ess_Distance[index] !== undefined) {
                const supply_vendor = {
                  supply: supply,
                  total_vendor: ess_No_of_vendors_found[index],
                  nearest_vendor_distance: ess_Distance[index],
                  status: get_status_for_distance(ess_Distance[index])
                };
                essential_supply_and_vendor.push(supply_vendor);
              }
            });
          }

          if (nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key] && Array.isArray(nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key]) && nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key].length > 0) {
            const noness_supply_id = nonEssential_supply_vendor_lookup_df["supply_id"][key] || [];
            const noness_No_of_vendors_found = nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key] || [];
            const noness_Distance = nonEssential_supply_vendor_lookup_df["Distance"][key] || [];

            noness_supply_id.forEach((supply, index) => {
              if (noness_No_of_vendors_found[index] !== undefined && noness_Distance[index] !== undefined) {
                const supply_vendor = {
                  supply: supply,
                  total_vendor: noness_No_of_vendors_found[index],
                  nearest_vendor_distance: noness_Distance[index],
                  status: get_status_for_distance(noness_Distance[index])
                };
                nonessential_supply_and_vendor.push(supply_vendor);
              }
            });
          }

          const emp_skill_type = Employment_lookup_df['Skill_Type'][key]
          const count = Employment_lookup_df[`${emp_skill_type}`][key]

          const incenetives = []
          const incentive_name = Solution_lookup_df['incentive_name'][key]
          const incentive_type = Solution_lookup_df['incentive_type'][key]
          const incentive_rank = Solution_lookup_df['incentive_rank'][key]
          incentive_name.forEach((incentive, index) => {
            const inc = { incentive_name: incentive, incentive_rank: incentive_rank[index], incentive_type: incentive_type[index] }
            incenetives.push(inc)
          })

          const approval_name = Approval_lookup_df["approval_name"][key]
          const government_department = Approval_lookup_df["government_department"][key]
          const online_or_offline = Approval_lookup_df["online_or_offline"][key]
          const stages = Approval_lookup_df["stages"][key]
          const time_taken = Approval_lookup_df["time_taken"][key]
          const approvals = []

          approval_name.forEach((approval, index) => {
            const appr = {
              approval_name: approval_name[index],
              government_department: government_department[index],
              online_or_offline: online_or_offline[index],
              stages: stages[index],
              time_taken: time_taken[index]
            }
            approvals.push(appr)
          })

          const road_transport = availability_of_local_transportation == 'Yes' ? 'good' : 'bad'

          const solution = {
            address: `${area || city}, ${district}, ${state}`,
            property_type: property_type,
            total_area: area_acre,
            latitude_longitude: latLongArray,
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
            boundary_coordinates: boundary_coordinates,
            result_type: "Industry_Result"
          }
          preaparedSolutions.push(solution)
        }
      } catch (error) {
        console.log("error is ", error);
      }
    });

    await Promise.all(promises);
    setSolutions(preaparedSolutions);
  };

  useEffect(() => {
    const loadPropertyData = async () => {
      await fetchPropertyData(analytics_response);
      setIsLoading(false);
    };
    loadPropertyData();
  }, []);

  const get_status_for_distance = (distance) => {
    if (distance < 100) return "good";
    else if (distance >= 100 && distance < 200) return "warning";
    else if (distance >= 200 && distance < 300) return "danger";
    else return "bad";
  }

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalData, setModalData] = useState([]);
  const [modalTitle, setModalTitle] = useState('');

  const toggleModal = (data, title) => {
    setModalData(data);
    setModalTitle(title);
    setIsModalOpen(!isModalOpen);
  };

  return (
    <div className="bg-gray-50 font-sans text-gray-800 w-full h-screen flex justify-center items-center">
      <div className="container max-w-full p-6 lg:p-8 bg-[#f0f0f0] w-[98%] h-[98%] rounded-lg">
        <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-blue-900 mb-2">Industrial Property Solutions</h1>
          </div>
          <Backtochat />
        </header>

        <nav className="flex space-x-6 border-b-2 border-gray-200 mb-2">
          <button
            onClick={() => setActiveTab("property")}
            className={`pb-2 flex items-center ${activeTab === "property" ? "text-blue-900 border-b-4 border-orange-500 font-semibold" : "text-gray-600 hover:text-blue-900"}`}
          >
            <FaBuilding className="mr-2" /> Property Details
          </button>
          <button
            onClick={() => setActiveTab("map")}
            className={`pb-2 flex items-center ${activeTab === "map" ? "text-blue-900 border-b-4 border-orange-500 font-semibold" : "text-gray-600 hover:text-blue-900"}`}
          >
            <FaMapMarkedAlt className="mr-2" /> Map View
          </button>
          <button
            onClick={() => setActiveTab("analytics")}
            className={`pb-2 flex items-center ${activeTab === "analytics" ? "text-blue-900 border-b-4 border-orange-500 font-semibold" : "text-gray-600 hover:text-blue-900"}`}
          >
            <FaChartLine className="mr-2" /> Analytics
          </button>
        </nav>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <p>Loading...</p>
          </div>
        ) : (
          <div className={`w-full ${activeTab === "property"
              ? "h-[88%]"
              : activeTab === "map"
                ? "h-[95%]"
                : "h-auto"
            }`}>
            {activeTab === "property" ? (
              <Properties solutions={solutions} toggleModal={toggleModal} />
            ) : activeTab === "map" ? (
              <MapComponent solutions={solutions} toggleModal={toggleModal} />
            ) : (
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h2 className="text-2xl font-semibold text-blue-900 mb-6">Analytics Dashboard</h2>
                <p>Analytics view coming soon</p>
              </div>
            )}
          </div>
        )}
      </div>
      <Model isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={modalTitle} data={modalData} />
    </div>
  )
}

export default Industryresult