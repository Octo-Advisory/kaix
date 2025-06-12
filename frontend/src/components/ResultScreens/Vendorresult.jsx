import React, { useEffect, useState,useRef } from 'react';
import { FaLocationDot } from "react-icons/fa6";
import { useFrappeGetDocList } from 'frappe-react-sdk';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import Details from '../Details/Details';
import Backtochat from '../Backtochat/Backtochat';
import MapComponent from '../MapComponent/MapComponent';
import {
  FaBox,
  FaCheckCircle,
  FaList,
  FaAward,
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
import { data } from 'react-router-dom';
import GoogleMap from '../MapComponent/GoogleMap';
import LogoLoader from '../Responseloader/LogoLoader';


function Vendorresult({result,source}) {
  const defaultIcon = L.icon({
          iconUrl: markerIconPng,
          iconSize: [25, 41],
          iconAnchor: [12, 41]
      });
  const analytics_response = source==="SolutionScreen" ? result["Analytics_response"] : ''
  const user_lat_long = source==="SolutionScreen" ? result["latitude_longitude"] : ''
 
    const [viewMode, setViewMode] = useState('Suppliers')
    const [currentData, setCurrentData] = useState("All Suppliers");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedVendor, setSelectedVendor] = useState(null);
    const [supplierList, setSupplierList] = useState()
    const [groupedData, setGroupedData] = useState()
    const mapRef = useRef(null);  


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

  const bestSuppliers = source==="SolutionScreen" ? parseSuppliers(JSON.parse(analytics_response["Best Supplier"] || "{}")) : ''
  const betterSuppliers = source==="SolutionScreen" ? parseSuppliers(JSON.parse(analytics_response["Better Supplier"] || "{}")) : ''
  const allSuppliers = source==="SolutionScreen" ? parseSuppliers(JSON.parse(analytics_response["Unfiltered All Supplier"] || "{}")) : ''

  const vendorNames = source==="SolutionScreen" ? allSuppliers.map(f => f.vendor_id) : []
  const { data: vendorData, error, isLoading } = useFrappeGetDocList('Vendor', {
  filters: [['name', 'in', vendorNames]],
  fields: [
    'no_of_services',
    'no_of_past_clients',
    'portfolio',
    'category',
    'certifications',
    'state',
    'website_url',
    'email_id',
    'years_of_experience',
    'no_of_employees',
    'latitude_longitude',
    'vendor_name',
    'name'
  ]
});

const { data: supplies, isLoading:supplyLoading } = useFrappeGetDocList('Vendor', {
  filters: [['name', 'in', vendorNames]],
  fields: ['table_podq.supply', 'table_podq.maximum_supply_capacity', 'table_podq.uom', 'table_podq.parent'],
  limit: 100000,
}); 

function groupSuppliesWithVendors(vendors, supplies) {
  // Step 1: Group supplies by parent
  const grouped = supplies.reduce((acc, item) => {
    if (!acc[item.parent]) acc[item.parent] = [];
    acc[item.parent].push(item);
    return acc;
  }, {});

  // Step 2: Map vendors and attach grouped supplies
  return vendors.map(vendor => {
    return {
      ...vendor,
      supplies: grouped[vendor.vendor_name] || []
    };
  });
}

useEffect(()=>{
  if(source==='SolutionScreen') {
  console.log(vendorData,supplies, isLoading, supplyLoading)
  if(vendorData && supplies){
  let d = groupSuppliesWithVendors(vendorData, supplies)
  console.log(d, 'this is data grouped');
  setGroupedData(d)
  }
    console.log('this are vendor',vendorData, 'this are suplies ', supplies);
}
},[vendorData,supplies])

// Assuming the analytics response passes only the Ids ... and we have all data called from db in vendorData so match the names
const updateData = (datalist) => {
  return datalist.map(supplier => {
    const matchingVendor = groupedData?.find(
      v => v.vendor_name === supplier.vendor_id
    );
    return matchingVendor
      ? { ...supplier, ...matchingVendor }
      : supplier;
  });
}

const updatedAllSupplier = source==="SolutionScreen" ? updateData(allSuppliers) : ''
const updatedBetterSupplier = source==="SolutionScreen" ? updateData(betterSuppliers) : ''
const updatedBestSupplier = source==="SolutionScreen" ? updateData(bestSuppliers) : ''

useEffect(() => {
  if(source === "SolutionScreen") {
  const sourceList = currentData === 'All Suppliers' ? updatedAllSupplier : updatedBestSupplier;
  if (!groupedData || !sourceList || sourceList.length === 0) {
    setSupplierList([]);
    return;
  }

  const query = (searchQuery || "").toLowerCase();
  const filtered = query
    ? sourceList.filter(s => (s.name || "").toLowerCase().includes(query))
    : sourceList;

  setSupplierList(filtered);
  }
}, [currentData, groupedData, searchQuery]);


useEffect(() => {
  if(source==="SolutionScreen") {
    if (supplierList && supplierList.length > 0) {
      const newVendor = supplierList[0];
      setSelectedVendor(newVendor);
    } else {
      setSelectedVendor(null);
    }
  }
}, [supplierList]);


const map_bestSuppliers = source==="SolutionScreen" ? updatedBestSupplier?.map(supplier => {
    const latitudeLongitude = typeof supplier.latitude_longitude === 'string' && supplier.latitude_longitude.includes(',')
      ? supplier.latitude_longitude.split(",").map(Number)
      : [];  // Default to empty array if it's not in the correct format
    return { ...supplier, category: "Best", result_type: "Vendor", latitude_longitude: latitudeLongitude, user_lat_long: user_lat_long };
  }) : []
  
  // const map_betterSuppliers = updatedBetterSupplier.map(supplier => {
  //   const latitudeLongitude = typeof supplier.latitude_longitude === 'string' && supplier.latitude_longitude.includes(',')
  //     ? supplier.latitude_longitude.split(",").map(Number)
  //     : [];  // Default to empty array if it's not in the correct format
  //   return { ...supplier, category: "Better", result_type: "Vendor", latitude_longitude: latitudeLongitude, user_lat_long: user_lat_long };
  // });
  
  const map_allSuppliers = source==="SolutionScreen" ? updatedAllSupplier?.map(supplier => {
    const latitudeLongitude = typeof supplier.latitude_longitude === 'string' && supplier.latitude_longitude.includes(',')
      ? supplier.latitude_longitude.split(",").map(Number)
      : [];  // Default to empty array if it's not in the correct format
    return { ...supplier, category: "General", result_type: "Vendor", latitude_longitude: latitudeLongitude, user_lat_long: user_lat_long };
  }) : []

  const map_result = [
    ...map_bestSuppliers,
    ...map_allSuppliers
  ];

  const handleVendorClick = (vendor) => {
  setSelectedVendor((prev) => {
    if (prev?.name === vendor.name) return prev; // same vendor, avoid unnecessary state update
    return vendor;
  });
};

//   useEffect(() => {
 
//   const locationString = selectedVendor?.latitude_longitude; // e.g. "22.3039,70.8022"

//   let lat = null;
//   let lng = null;

//   if (locationString) {
//     const parts = locationString.split(",");
//     lat = parseFloat(parts[0]);
//     lng = parseFloat(parts[1]);
//   }

//   if (mapRef.current && lat && lng) {
//     mapRef.current.setView([lat, lng], 13); // ✅ FIX: pass array of numbers
//     // console.log("Set map view to:", lat, lng);
//   }
  
// }, [selectedVendor]);

const getLatLng = (latlngStr) => {
  if (!latlngStr) return [0, 0];
  const parts = latlngStr.split(",");
  const lat = parseFloat(parts[0]);
  const lng = parseFloat(parts[1]);
  if (isNaN(lat) || isNaN(lng)) return [0, 0];
  return [lat, lng];
};

const getLatLng2 = (latlngStr) => {
  if(!latlngStr) return [0,0];
  const lat = parseFloat(latlngStr[0])
  const lng = parseFloat(latlngStr[1])
  if (isNaN(lat) || isNaN(lng)) return [0, 0];
  return [lat, lng];
}

useEffect(()=>{
  if(source==='MapComponent') {
    setSelectedVendor(result)
  }
},[result])

const detailRef = useRef(null);
 useEffect(() => {
    if (detailRef.current) {
      detailRef.current.scrollTop = 0;
    }
  }, [selectedVendor]);

const vendorLatLng = source ==="SolutionScreen" ? getLatLng(selectedVendor?.latitude_longitude) : getLatLng2(selectedVendor?.latitude_longitude)
const shouldRender = source === "SolutionScreen" ? supplierList && selectedVendor : source === "MapComponent"? selectedVendor: false; // fallback if needed

   
// First of all i have to call the vendor data .....
// then after that i would have to call the suppliers data from Vendor Supply Capacity child table 
    
    return (
        // <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#f0f7ff] to-[#e6f0fa] overflow-hidden">
        <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655] overflow-hidden">
            <div className="w-[98%] h-[95%] mx-auto my-0 p-6 bg-white rounded-xl shadow-sm border border-white border-opacity-40 flex flex-col backdrop-blur-sm">
                {source==='SolutionScreen' && (<div className="flex items-center justify-between pb-4 mb-4 border-b border-[#B8D1F3]">
                    <div className="flex items-center">
                        <div className="p-3 mr-4 rounded-lg bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10">
                            <FaFileAlt className="text-xl text-[#7AA6DA]" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-semibold text-[#2C53A3]">Vendors List</h1>
                            <p className="text-[#5A7EC7]">Browse required supplies for your business</p>
                        </div>
                    </div>

                    <div className='flex relative flex-row items-center gap-4'>

                 
                      <div className="flex flex-row items-center bg-white border border-[#41b655] rounded-full overflow-hidden p-1 relative w-fit h-fit">
                        <div
                          onClick={() => setViewMode("Suppliers")}
                          className={`p-1 px-3 text-sm  flex flex-row items-center justify-center font-semibold cursor-pointer transition-all duration-300 ${
                            viewMode === "Suppliers"
                              ? "bg-[#0e2044] text-white"
                              : "text-[#0e2044] bg-white"
                          } rounded-l-full`}
                        >
                          Suppliers
                        </div>
                        <div
                          onClick={() => setViewMode("Map")}
                          className={`p-1 px-3 text-sm font-semibold flex flex-row items-center justify-center cursor-pointer transition-all duration-300 ${
                            viewMode === "Map"
                              ? "bg-[#0e2044] text-white"
                              : "text-[#0e2044] bg-white"
                          } rounded-r-full`}
                        >
                          Map
                        </div>
                      </div>
                    


                    <Backtochat />
                    </div>
                </div>)}
                
                {source==="SolutionScreen" && viewMode==='Suppliers' && (<div className="relative mb-4 flex flex-row gap-2">
                  <div className={`${currentData==='Best Suppliers' ? 'bg-green-500 text-white': ' border border-green-500 text-green-500 bg-green-100'} rounded-lg cursor-pointer relative flex items-center gap-2 flex-row whitespace-nowrap px-4`} onClick={()=> {setCurrentData('Best Suppliers')}}><FaAward size={20}/>Best Suppliers</div>
                  <div className={`${currentData==='All Suppliers' ? 'bg-orange-500 text-white' : 'border border-orange-500 text-orange-500 bg-orange-100'} relative flex items-center gap-2 flex-row whitespace-nowrap px-4 rounded-lg cursor-pointer`} onClick={()=> {setCurrentData('All Suppliers')}}><FaList size={20}/>All Suppliers</div>
                  <div className='relative flex w-full flex-row gap-4'>
                    <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5A7EC7]" />
                    <input type="text" placeholder="Search by Vendor name..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-12 pr-4 py-2 w-full border border-[#B8D1F3] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF80AB]/30 focus:border-[#7AA6DA] placeholder-[#5A7EC7]/70 text-[#2C53A3] bg-white bg-opacity-90"/>
                  </div>
                </div>)}
{/* Dark Blue: #0B2152
Medium Blue: #2C53A3
Light Blue: #70A1D9
White: #FFFFFF
Pink/Magenta: #E91E63 
Purple: #673AB7 
Green: #4CAF50 */}
                {viewMode==='Suppliers' && (<div className="flex flex-1 h-full w-full overflow-hidden bg-white rounded-lg border border-[#B8D1F3]">
                    {source==="SolutionScreen" && (<div className="w-1/3 border-r border-[#B8D1F3] flex flex-col">
                        <div className="overflow-y-auto flex-1 list-view bg-gradient-to-b from-[#E6F0FA]/10 to-transparent">
                            {supplierList && supplierList.length > 0 ? (
                                <div className="space-y-2 p-2">
                                    {supplierList.map((vendor,idx) => (
                                        <div
                                            key={idx}
                                            className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${selectedVendor?.name === vendor.name
                                                ? "bg-[#41b655] bg-opacity-20 border-l-4 border-[#41b655] "
                                                // ? "bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 border-l-4 border-[#0e2044]"
                                                : "bg-[#41b655] bg-opacity-10 border-none"
                                                }`}
                                            onClick={()=>{handleVendorClick(vendor)}}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h3 className={`font-medium ${selectedVendor?.name === vendor.name ? "text-black" : "text-[#3b69c5]"
                                                    }`}>
                                                    {vendor.name}
                                                </h3>
                                            </div>
                                            {/* <div className="flex items-center mt-2 text-sm text-[#5A7EC7]">
                                                <FaBuilding className="mr-2" />
                                                <span>{vendor.category}</span>
                                            </div> */}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                                    <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB]/20 to-[#9575CD]/20">
                                        <FaSearch className="text-2xl text-[#5A7EC7]" />
                                    </div>
                                    <h3 className="text-lg font-medium text-[#2C53A3]">No Vendors found</h3>
                                    <p className="text-[#5A7EC7]">Try a different search term or view mode</p>
                                </div>
                            )}
                        </div>
                    </div>)}

                    {selectedVendor && (
                        <div className={`${source==="MapComponent" ? 'w-full' : 'w-2/3'} flex flex-col`}>
                            <div ref={detailRef} className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6 full flex-1 overflow-y-auto scrollbar-hide">
          {selectedVendor ? (

            <div className='relative flex flex-col gap-8'>
              <div className='relative flex flex-row gap-2 justify-start items-center'>
                <div  className='relative flex flex-row gap-2'>
                  <span className='p-3 rounded-lg flex items-center justify-center relative bg-blue-100'><FaStoreAlt className='text-blue-800'/></span>
                  <div className='relative flex flex-col gap-0.5'>
                    <h2 className="text-xl font-bold text-blue-700 flex items-center">{selectedVendor.name}</h2>
                    <h3 className='relative text-md'>{selectedVendor.category}</h3>
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
                    <div className="text-3xl font-bold text-blue-700">500+</div>
                    <p className="text-gray-600 mt-1">Projects Completed</p>
                  </div>
                </div>
              </div>
                
              {selectedVendor && selectedVendor.portfolio && (<div className="relative flex flex-col gap-4">
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

              <div className="relative flex flex-col gap-4">
                <h2 className="text-xl font-bold text-gray-800 flex flex-row gap-3 items-center">
                  <MdPeopleAlt className="text-blue-700"/>
                  Past Clients
                </h2>
                      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="bg-blue-50 p-3 border-b border-gray-200">
                        {selectedVendor.no_of_past_clients}
                      </div>
                      </div>
              </div>

                
                {selectedVendor && selectedVendor.supplies && (<div className="relative flex flex-col gap-2">
                  <h2 className="text-xl font-bold text-gray-800 mb-4 flex flex-row gap-3 items-center">
                  <AiFillProduct className='text-blue-700'/>
                  Supplies & Capacities
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedVendor.supplies && selectedVendor.supplies.map((data, index) => (
                      <div key={index} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="bg-blue-50 p-3 border-b border-gray-200">
                          <div className="flex justify-between items-center">
                            <span className="font-medium text-gray-800">{data.supply}</span>
                            <span className="bg-[#0e2044] text-white text-xs px-2 py-0.5 rounded-full flex flex-row gap-1 items-center">{data.maximum_supply_capacity} {data.uom}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>)}
                
                {selectedVendor && selectedVendor.certifications && (<div className='relative flex flex-col gap-4'>
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
                </div>)}
                
                
               

                <div className="relative flex flex-col gap-2">
                  <h4 className="text-xl font-semibold text-gray-800 flex flex-row gap-2 items-center">
                    <FaLocationDot className='text-blue-700' size={20}/>
                    Location
                  </h4>
                  <div className="relative h-[250px] w-full p-4">
                    <GoogleMap lat={vendorLatLng[0]} lng={vendorLatLng[1]} tooltipText={selectedVendor?.name} />
                    {/* <MapContainer
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
                    </MapContainer> */}
                  </div>
                  <div className="relative flex justify-between flex-row text-sm items-center">
                    <span className="text-sm text-gray-600 flex flex-row gap-1 items-center">
                      <FaLocationArrow className="text-blue-600"/>
                      Distance from the Project site: <strong>{selectedVendor.distance || '12'}Kms</strong>
                    </span>
                    <button className="text-sm text-blue-600 hover:text-blue-800 flex flex-row gap-1 items-center" onClick={()=>{setViewMode('Map')}}>
                      <FaDirections />
                      Get Directions
                    </button>
                  </div>
                </div>
              </div>
          ) : (
            <div>
              <h1>Please Select a Vendor</h1>
            </div>
          )
        }
        </div>
      </div>
    )}
                </div>)} 
                
                {viewMode==='Map' && (
                  <div className='relative h-full w-full flex items-center justify-center overflow-hidden'>
                    <MapComponent solutions={map_result} />
                  </div>
                )}
        </div>
            
  </div>
    );
}

export default Vendorresult;
