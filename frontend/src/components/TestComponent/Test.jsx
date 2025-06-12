import React, { useContext, useEffect, useState,useRef } from 'react';
import map from '../../assets/map.png'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import { RiGovernmentLine ,RiRoadMapLine} from 'react-icons/ri';
import { useFrappeGetDocList,FrappeContext,useFrappeGetDoc} from 'frappe-react-sdk'
import { FaLocationDot } from "react-icons/fa6";
import {
  FaBox,
  FaCheckCircle,
  FaStar,
  FaInfoCircle,
  FaChartBar,
  FaCogs,
  FaBoxes,
  FaBolt,
  FaShieldAlt,
  FaMoneyBillWave,
  FaCreditCard,
  FaComments,
  FaBookmark,
  FaStoreAlt,
  FaShare,
  FaFileAlt,
  FaClock,
  FaCheck,
  FaBuilding,
  FaMapMarkerAlt,
  FaCertificate,
  FaLocationArrow,
  FaDirections,
  FaSearch, FaTag, FaLayerGroup, FaSync
} from 'react-icons/fa';
  import { AiFillProduct } from "react-icons/ai";
  import { MdPeopleAlt } from "react-icons/md";

function Test() {
  const defaultIcon = L.icon({
          iconUrl: markerIconPng,
          iconSize: [25, 41],
          iconAnchor: [12, 41]
      });
      

    const {call} = useContext(FrappeContext)
    const [viewMode, setViewMode] = useState("Trader");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedVendor, setSelectedVendor] = useState(null);
    const [approvalsData, setApprovalsDataData] = useState([]);
    const [filteredVendors, setFilteredVendors] = useState([])
    const [supplyData, setSupplyData] = useState([])
    const mapRef = useRef(null);
   
    const { data: vendorData, isLoading: vendorLoading } = useFrappeGetDocList("Vendor", {
      fields: ["*"],
      // filters: ['name', 'in', ['Dummy 1', 'Dummy 2']],
      limit: 10,
    });
    useEffect(() => {
      if (vendorData) {
        setFilteredVendors(vendorData);
        console.log(vendorData, "this is the called data");
      }
    }, [vendorData])

    const { data:supply, isLoading:supplyLoading } = useFrappeGetDocList("Vendor", {
        fields: ["table_podq.supply", "table_podq.maximum_supply_capacity", 'table_podq.uom'],
        filters: [["name", "=", selectedVendor?.name]],
      });
    useEffect(()=>{
      if(supply) {
        setSupplyData(supply)
        console.log(supply, 'this is the supply')
      }
    },[supply])  

  useEffect(() => {
  const locationString = selectedVendor?.latitude_longitude; // e.g. "22.3039,70.8022"

  let lat = null;
  let lng = null;

  if (locationString) {
    const parts = locationString.split(",");
    lat = parseFloat(parts[0]);
    lng = parseFloat(parts[1]);
  }

  if (mapRef.current && lat && lng) {
    mapRef.current.setView([lat, lng], 13); // ✅ FIX: pass array of numbers
    console.log("Set map view to:", lat, lng);
  }
}, [selectedVendor]);

const getLatLng = (latlngStr) => {
  if (!latlngStr) return [0, 0];
  const parts = latlngStr.split(",");
  const lat = parseFloat(parts[0]);
  const lng = parseFloat(parts[1]);
  if (isNaN(lat) || isNaN(lng)) return [0, 0];
  return [lat, lng];
};

const vendorLatLng = getLatLng(selectedVendor?.latitude_longitude);
    
    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#f0f7ff] to-[#e6f0fa] overflow-hidden">
            <div className="w-[95%] h-[95%] mx-auto my-0 p-6 bg-white bg-opacity-95 rounded-xl shadow-sm border border-white border-opacity-40 flex flex-col backdrop-blur-sm">
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#B8D1F3]">
                    <div className="flex items-center">
                        <div className="p-3 mr-4 rounded-lg bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10">
                            <FaFileAlt className="text-xl text-[#7AA6DA]" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-semibold text-[#2C53A3]">Vendors List</h1>
                            <p className="text-[#5A7EC7]">Browse required supplies for your business</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center justify-between mb-4">
                    <div className="flex gap-2">
                        {["Trader", "Service Provider", "Manufacturer"].map(mode => (
                            <button
                                key={mode}
                                className={`px-4 py-2 rounded-md text-sm font-medium ${viewMode === mode
                                    ? "bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 text-[#2C53A3] border border-[#B8D1F3]"
                                    : "bg-white text-[#5A7EC7] hover:bg-[#E6F0FA] border border-[#B8D1F3]/50"
                                    }`}
                                onClick={() => setViewMode(mode)}
                            >
                                {mode}
                            </button>
                        ))}
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 px-4 py-2.5 rounded-lg border border-[#B8D1F3]">
                            <div className="p-2 bg-[#B8D1F3]/30 rounded-full">
                                <FaClock className="text-[#2C53A3] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">TOTAL TIME</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-bold text-[#2C53A3]">10</span>
                                    <span className="text-xs text-[#5A7EC7]/70">days</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#81C784]/20 to-[#4CAF50]/20 px-4 py-2.5 rounded-lg border border-[#81C784]">
                            <div className="p-2 bg-[#81C784]/30 rounded-full">
                                <FaCheckCircle className="text-[#2E7D32] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">ONLINE</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-bold text-[#2E7D32]">15</span>
                                    <span className="text-xs text-[#5A7EC7]/70">%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="relative mb-4">
                    <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5A7EC7]" />
                    <input
                        type="text"
                        placeholder="Search by Vendor name..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-12 pr-4 py-3 w-full border border-[#B8D1F3] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF80AB]/30 focus:border-[#7AA6DA] placeholder-[#5A7EC7]/70 text-[#2C53A3] bg-white bg-opacity-90"
                    />
                </div>

                <div className="flex flex-1 min-h-0 overflow-hidden bg-white rounded-lg border border-[#B8D1F3]">
                    <div className="w-1/3 border-r border-[#B8D1F3] flex flex-col">
                        <div className="overflow-y-auto flex-1 list-view bg-gradient-to-b from-[#E6F0FA]/10 to-transparent">
                            {filteredVendors.length > 0 ? (
                                <div className="space-y-2 p-2">
                                    {filteredVendors.map((vendor,idx) => (
                                        <div
                                            key={idx}
                                            className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${selectedVendor?.name === vendor.name
                                                ? "bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 border-l-4 border-[#FF80AB]"
                                                : "hover:bg-[#E6F0FA]/30 border-l-4 border-transparent"
                                                }`}
                                            onClick={() => setSelectedVendor(vendor)}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h3 className={`font-medium ${selectedVendor?.name === vendor.name ? "text-[#FF80AB]" : "text-[#2C53A3]"
                                                    }`}>
                                                    {vendor.name}
                                                </h3>
                                            </div>
                                            <div className="flex items-center mt-2 text-sm text-[#5A7EC7]">
                                                <FaBuilding className="mr-2" />
                                                <span>{vendor.category}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                                    <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB]/20 to-[#9575CD]/20">
                                        <FaSearch className="text-2xl text-[#5A7EC7]" />
                                    </div>
                                    <h3 className="text-lg font-medium text-[#2C53A3]">No approvals found</h3>
                                    <p className="text-[#5A7EC7]">Try a different search term or view mode</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {selectedVendor && (
                        <div className="w-2/3 flex flex-col">
                            <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6 full flex-1 overflow-y-auto scrollbar-hide">
          {selectedVendor && (

            <div className='relative flex flex-col gap-8'>
              <div className='relative flex flex-row gap-2 justify-between items-center'>
                <div  className='relative flex flex-row gap-2'>
                  <span className='py-2 px-4 rounded-sm flex items-center relative bg-blue-100'><FaStoreAlt className='text-blue-800' size={24}/></span>
                  <div className='relative flex flex-col gap-0.5'>
                    <h2 className="text-xl text-blue-700 flex items-center font-semibold">{selectedVendor.name}</h2>
                    <h3 className='relative text-md'>Steel Material Supplier</h3>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 px-4 py-1 rounded-lg border border-[#B8D1F3]">
                            <div className="p-2 bg-[#B8D1F3]/30 rounded-full">
                                <FaClock className="text-[#2C53A3] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">TOTAL TIME</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-bold text-[#2C53A3]">10</span>
                                    <span className="text-xs text-[#5A7EC7]/70">days</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#81C784]/20 to-[#4CAF50]/20 px-4 py-1 rounded-lg border border-[#81C784]">
                            <div className="p-2 bg-[#81C784]/30 rounded-full">
                                <FaCheckCircle className="text-[#2E7D32] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">ONLINE</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-bold text-[#2E7D32]">15</span>
                                    <span className="text-xs text-[#5A7EC7]/70">%</span>
                                </div>
                            </div>
                        </div>
                    </div>
              </div>

              <div className="flex flex-col flex-1 gap-4">
                <h2 className="text-xl font-bold text-gray-800 flex gap-3 flex-row items-center">
                  <FaChartBar className="text-blue-700"/>
                  Company Statistics
                </h2>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                    <div className="text-3xl font-bold text-blue-700">{selectedVendor.years_of_experience}+</div>
                    <p className="text-gray-600 mt-1">Years Experience</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                    <div className="text-3xl font-bold text-blue-700">{selectedVendor.no_of_services}</div>
                    <p className="text-gray-600 mt-1">Services Offered</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                    <div className="text-3xl font-bold text-blue-700">{selectedVendor.no_of_employees}+</div>
                    <p className="text-gray-600 mt-1">Employees</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                    <div className="text-3xl font-bold text-blue-700">{selectedVendor.no_of_past_clients}+</div>
                    <p className="text-gray-600 mt-1">Projects Completed</p>
                  </div>
                </div>
              </div>
                
              {selectedVendor?.portfolio && (<div className="relative flex flex-col gap-4">
                <h2 className="text-xl font-bold text-gray-800 flex flex-row gap-3 items-center">
                  <FaInfoCircle className="text-blue-700"/>
                  Overview
                </h2>
                <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <p className="text-gray-700 leading-relaxed">
                    {selectedVendor.portfolio}
                  </p>
                </div>
              </div>)}

              {selectedVendor?.no_of_past_clients &&(<div className="relative flex flex-col gap-4">
                <h2 className="text-xl font-bold text-gray-800 flex flex-row gap-3 items-center">
                  <MdPeopleAlt className="text-blue-700"/>
                  Past Clients
                </h2>
                <div className="relative grid grid-cols-2 w-full gap-4">
                  {selectedVendor.no_of_past_clients.split(',').map((client, id) => (
                    <div className='relative border border-gray-200 p-2 items-center flex flex-row justify-start'>
                      <p className='text-md font-semibold text-gray-700'>{client}</p>
                    </div>
                  ))}
                </div>
              </div>)}

                
                <div className="relative flex flex-col gap-2">
                  <h2 className="text-xl font-bold text-gray-800 mb-4 flex flex-row gap-3 items-center">
                  <AiFillProduct className='text-blue-700'/>
                  Supplies & Capacities
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {supplyData.map((supplies, id) => (
                      <div key={id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="bg-blue-50 p-3 border-b border-gray-200">
                          <div className="flex justify-between items-center">
                            <span className="font-medium text-gray-800">{supplies.supply}</span>
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">{supplies.maximum_supply_capacity} {supplies.uom}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className='relative flex flex-col gap-4'>
                  <h2 className="text-xl font-bold text-gray-800 flex items-center flex-row gap-3">
                    <FaShieldAlt className="text-blue-700"/>
                    Certifications
                  </h2>
                  <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm flex flex-col">
                    <div className="relative grid grid-cols-2 gap-2">
                       {selectedVendor.certifications.split(',').map((opt, i) => (
                      <div key={i} className="flex flex-row gap-1 items-center col-span-1">
                        <div className="bg-green-100 p-1 rounded-full">
                          <FaCheckCircle className="text-green-700"/>
                        </div>
                        <span className="text-gray-700 font-semibold">{opt}</span>
                      </div>))}
                    </div>
                  </div>
                </div>

                <div className="relative flex flex-col gap-2">
                  <h4 className="text-xl font-semibold text-gray-800 flex flex-row gap-2 items-center">
                    <FaLocationDot className='text-blue-700' size={20}/>
                    Location
                  </h4>
                  <div className="relative h-[250px] w-full p-4">
                    <MapContainer
                        key={selectedVendor?.address}
                        center={vendorLatLng}
                        zoom={13}
                        style={{ height: '100%', width: '100%' }}
                        className="rounded-b-lg"
                        attributionControl={false}
                        zoomControl={false}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                        />
                        <Marker position={vendorLatLng} icon={defaultIcon}>
                            <Popup className="font-medium">{selectedVendor?.name}</Popup>
                        </Marker>
                    </MapContainer>
                  </div>
                  <div className="relative flex justify-between flex-row text-sm items-center">
                    <span className="text-sm text-gray-600 flex flex-row gap-1 items-center">
                      <FaLocationArrow className="text-blue-600"/>
                      Distance from the Project site: <strong>{selectedVendor.distance || '12'}Kms</strong>
                    </span>
                    <button className="text-sm text-blue-600 hover:text-blue-800 flex flex-row gap-1 items-center">
                      <FaDirections />
                      Get Directions
                    </button>
                  </div>
                </div>
              </div>
          )}
        </div>
                        </div>
                    )}
                </div>
            </div>
            
        </div>
    );
}

export default Test;
