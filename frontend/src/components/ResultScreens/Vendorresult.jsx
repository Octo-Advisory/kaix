import React, { useState, useEffect } from 'react';
import { FaList, FaAward, FaMapMarkedAlt, FaSearch } from "react-icons/fa";
import Details from '../Details/Details';
import Backtochat from '../Backtochat/Backtochat';
import MapComponent from '../MapComponent/MapComponent';

function Vendorresult({ result }) {
  console.log("result in vendors", result);
  const analytics_response = result["Analytics_response"]
  const user_lat_long = result["latitude_longitude"]
  console.log("analytics_response", analytics_response);

  const [activeTab, setActiveTab] = useState("map");
  const [viewMode, setViewMode] = useState("best");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSupplier, setSelectedSupplier] = useState(null);

  const parseSuppliers = (supplierData) => {
    if (!supplierData.vendor_id) return [];
    return Object.keys(supplierData.vendor_id).map(key => {
      const supplierInfo = {};
      Object.keys(supplierData).forEach(innerKey => {
        supplierInfo[innerKey] = supplierData[innerKey][key];
      });
      return supplierInfo;
    });
  };

  const bestSuppliers = parseSuppliers(JSON.parse(analytics_response["Best Supplier"] || "{}"));
  const betterSuppliers = parseSuppliers(JSON.parse(analytics_response["Better Supplier"] || "{}"));
  const allSuppliers = parseSuppliers(JSON.parse(analytics_response["Unfiltered All Supplier"] || "{}"));

  const map_bestSuppliers = bestSuppliers.map(supplier => {
    const latitudeLongitude = typeof supplier.latitude_longitude === 'string' && supplier.latitude_longitude.includes(',')
      ? supplier.latitude_longitude.split(",").map(Number)
      : [];  // Default to empty array if it's not in the correct format
    return { ...supplier, category: "Best", result_type: "Vendor", latitude_longitude: latitudeLongitude, user_lat_long: user_lat_long };
  });
  
  const map_betterSuppliers = betterSuppliers.map(supplier => {
    const latitudeLongitude = typeof supplier.latitude_longitude === 'string' && supplier.latitude_longitude.includes(',')
      ? supplier.latitude_longitude.split(",").map(Number)
      : [];  // Default to empty array if it's not in the correct format
    return { ...supplier, category: "Better", result_type: "Vendor", latitude_longitude: latitudeLongitude, user_lat_long: user_lat_long };
  });
  
  const map_allSuppliers = allSuppliers.map(supplier => {
    const latitudeLongitude = typeof supplier.latitude_longitude === 'string' && supplier.latitude_longitude.includes(',')
      ? supplier.latitude_longitude.split(",").map(Number)
      : [];  // Default to empty array if it's not in the correct format
    return { ...supplier, category: "General", result_type: "Vendor", latitude_longitude: latitudeLongitude, user_lat_long: user_lat_long };
  });
  
  // Combine all categorized suppliers into a single array
  const map_result = [
    ...map_bestSuppliers,
    ...map_betterSuppliers,
    ...map_allSuppliers
  ];

  const getFilteredSuppliers = () => {
    let suppliers = [];
    if (viewMode === "best") suppliers = bestSuppliers;
    else if (viewMode === "better") suppliers = betterSuppliers;
    else if (viewMode === "all") suppliers = allSuppliers;
    return suppliers.filter(s => s.vendor_id.toLowerCase().includes(searchQuery.toLowerCase()));
  };

  const filteredSuppliers = getFilteredSuppliers();

  useEffect(() => {
    setSelectedSupplier(filteredSuppliers.length > 0 ? filteredSuppliers[0] : null);
  }, [viewMode, searchQuery]);

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
      <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200 flex justify-between pb-2">
          <ul className="flex text-sm font-medium text-gray-500">
            <li>
              <button onClick={() => setActiveTab("suppliers")} className={`p-4 border-b-2 ${activeTab === "suppliers" ? "text-blue-600 border-blue-600" : "border-transparent"}`}>
                <FaList className="w-5 h-5 inline-block mr-2" /> Suppliers
              </button>
            </li>
            <li>
              <button onClick={() => setActiveTab("map")} className={`p-4 border-b-2 ${activeTab === "map" ? "text-blue-600 border-blue-600" : "border-transparent"}`}>
                <FaMapMarkedAlt className="w-5 h-5 inline-block mr-2" /> Map
              </button>
            </li>
          </ul>
          <Backtochat />
        </div>

        <div className="py-4 h-[94%] overflow-auto">
          {activeTab === "map" ? (
            <MapComponent solutions={map_result} />
          ) : (
            <div className='w-full h-full'>
              <div className="flex gap-2 mb-4 items-center">
                <button className="bg-red-500 text-white px-4 py-2 rounded flex items-center gap-2" onClick={() => setViewMode("best")}> <FaAward /> Best Suppliers </button>
                {betterSuppliers.length > 0 && (
                  <button className="bg-yellow-500 text-white px-4 py-2 rounded flex items-center gap-2" onClick={() => setViewMode("better")}> Better Suppliers </button>
                )}
                <button className="bg-green-500 text-white px-4 py-2 rounded flex items-center gap-2" onClick={() => setViewMode("all")}> <FaList /> All Suppliers </button>
                <div className="relative flex-1">
                  <FaSearch className="absolute left-3 top-3 text-gray-500" />
                  <input type="text" placeholder="Search Suppliers..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="px-3 py-2 border rounded-lg pl-10 w-full" />
                </div>
              </div>

              <div className="flex h-[90%] overflow-y-auto bg-white shadow">
                <div className="w-2/3">
                  {filteredSuppliers.length > 0 ? (
                    filteredSuppliers.map((supplier, index) => (
                      <div key={index} className={`p-4 border cursor-pointer shadow-sm ${selectedSupplier?.vendor_id === supplier.vendor_id ? "bg-[#242f6a] text-white border-none" : "bg-white"}`} onClick={() => setSelectedSupplier(supplier)}>
                        <span className="font-semibold">{supplier.vendor_id}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-gray-500">No suppliers found.</p>
                  )}
                </div>
                {selectedSupplier && (
                  <div className="w-1/3 bg-[#242f6a] shadow p-4 text-white">
                    <h2 className="text-xl font-bold">{selectedSupplier.vendor_id}</h2>
                    <p><strong>Supply:</strong> {selectedSupplier.supply_id}</p>
                    <p><strong>Capacity:</strong> {selectedSupplier.vendor_supply_capacity}</p>
                    <p><strong>Experience:</strong> {selectedSupplier.years_of_experience} years</p>
                    <p><strong>Services:</strong> {selectedSupplier.no_of_servieces}</p>
                    <p><strong>Employees:</strong> {selectedSupplier.no_of_employees}</p>
                    <p><strong>Distance:</strong> {selectedSupplier.Dist ? Number(selectedSupplier.Dist).toFixed(2) : "N/A"} km</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      <Details />
    </div>
  );
}

export default Vendorresult;
