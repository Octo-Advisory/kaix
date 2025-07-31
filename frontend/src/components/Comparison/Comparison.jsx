import { useEffect, useState } from 'react'
import {
 FaRegQuestionCircle, FaRoad, FaTrain, FaPlane, FaArrowLeft, FaBus,
} from 'react-icons/fa';
import { RiShipFill } from "react-icons/ri";
import { BsBarChartFill, BsPatchCheckFill } from "react-icons/bs";
import { MdOfflineBolt } from "react-icons/md";
import { FaCircleXmark, FaTriangleExclamation } from 'react-icons/fa6';
import { IoWifi } from 'react-icons/io5';
import Spider from '../Spider/Spider';
import { Doughnut } from 'react-chartjs-2';
import { useFrappeGetDoc } from 'frappe-react-sdk';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import MapBoxMap from '../MapComponent/MapBoxMap';


const Comparison = ({ solutions }) => {
    const { data: uiData } = useFrappeGetDoc("UI Configuration", "Build From Scratch")
      
      const configurations = uiData?.configurations || [];
      const uiConfig = configurations.reduce((acc, curr) => {
        acc[curr.key] = curr.value;
        return acc;
      }, {});

    ChartJS.register(ArcElement, Tooltip, Legend);
     

   const [visibleTooltips, setVisibleTooltips] = useState({});
     const [showEssentialMaterials, setShowEssentialMaterials] = useState(true);
      
        const handleMouseEnter = (index, type) => {
  setVisibleTooltips(prev => ({
    ...prev,
    [index]: {
      ...(prev[index] || {}),
      [type]: true
    }
  }));
};

const handleMouseLeave = (index, type) => {
  setVisibleTooltips(prev => ({
    ...prev,
    [index]: {
      ...(prev[index] || {}),
      [type]: false
    }
  }));
};

        
    const data = solutions
    const [selectionTab, setSelectionTab] = useState(true)

    // State for selected checkboxes
    const [selectedProperties, setSelectedProperties] = useState([]);
    // State for filtered data
    const [filteredData, setFilteredData] = useState([]);
    // State to track if filters are applied
    const [filtersApplied, setFiltersApplied] = useState(false);

    // Handle checkbox change
    const handleCheckboxChange = (propertyId) => {
        if (selectedProperties.includes(propertyId)) {
            // If already selected, remove it
            setSelectedProperties(selectedProperties.filter(id => id !== propertyId));
        } else {
            // If not selected and we have less than 3 selected, add it
            if (selectedProperties.length < 3) {
                setSelectedProperties([...selectedProperties, propertyId]);
            }
        }
    };

    // Apply filters
    const applyFilters = () => {
        // Filter the data based on selected properties
        const filtered = data.filter(property =>
            selectedProperties.includes(property.property_id)
        );
        setFilteredData(filtered);
        setFiltersApplied(true);
        setSelectionTab(false)
    };


    useEffect(() => {
        console.log(filteredData, 'this is the data ');
    }, [filteredData])


    const isApplyDisabled = selectedProperties.length < 2;
    const selectedOnes = data.filter((item) => selectedProperties.includes(item.property_id));

    return (
        <div className='h-full max-h-full w-full relative flex flex-col items-center gap-6 '>
            {selectionTab && (
                <div className='relative flex flex-col justify-between h-[85%] w-full '>
                    <div className='w-full h-15 relative flex flex-col py-2 px-4 bg-gradient-to-br from-[#0e2044] to-[#41b655]'>
                        <h1 className='text-white font-semibold text-md'>{uiConfig?.['comparison_screen_main_title'] || "Property Analysis Dashboard"}</h1>
                        <h2 className='text-white font-light text-xs'>Choose upto 3 properties to compare</h2>
                    </div>
                    <div className='flex relative py-4 z-[11] items-center border-gray-200 border-b justify-between px-8 w-full h-fit'>
                        <div className='relative flex flex-row gap-4 items-center'>
                            <div className={`shadow-xl border cursor-default border-gray-100 rounded-full py-2 px-4  flex flex-row justify-center transition-all duration-300  gap-4 items-center select-none bg-gray-100 text-black`}>
                                <span className='h-5 w-5 rounded-full flex items-center justify-center bg-[#41b655] text-white text-xs'>{selectedOnes.length}</span>
                             {uiConfig?.['property_selection_label'] || 'Properties Selected'}
                            </div>
                            <p className={`text-xs text-gray-600 ${selectedOnes.length<2 ? 'block' : 'hidden'}` }>Select properties to Compare.</p>
                        </div>
                        <button disabled={isApplyDisabled} className={`px-4 py-1 rounded-md flex flex-row gap-2 items-center bg-[#0e2044] text-white ${isApplyDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`} onClick={() => !isApplyDisabled && applyFilters()}> <BsBarChartFill /> {uiConfig?.['compare_properties_button'] || 'Compare Properties'} </button>
                    </div>
                    <div className='h-full w-full relative py-8 overflow-y-auto flex flex-col gap-8 items-center justify-start'>
                        <div className={`relative w-fit h-fit z-[10] grid gap-6 ${data?.length > 6 ? 'grid-cols-4 ' : 'grid-cols-3'}`}>
                            {data.sort((a, b) => b.score - a.score).map((property, index) => (
                                
                                <div key={index} className={`relative cursor-pointer min-h-28 h-28 min-w-[270px] w-[270px] border border-gray-400 flex flex-col rounded-md hover:cursor-pointer overflow-hidden transform transition duration-300  shadow-lg ${selectedProperties.length >= 3 && !selectedProperties.includes(property.property_id) ? 'opacity-70' : 'opacity-100'}`} onClick={() => handleCheckboxChange(property.property_id)}>
                                    <div className='relative min-h-8 h-8 max-h-8 bg-gradient-to-r from-[#0e2044] to-[#41b655] w-full opacity-80'></div>
                                    <div className='relative min-h-20 h-20 max-h-24 bg-white-500 w-full flex flex-col gap-1 pt-4 pb-2 px-2'>
                                        <span className='absolute rounded-full h-6 w-6 bg-white flex items-center -top-3.5 left-2 justify-center text-sm shadow-md'>{index + 1}</span>
                                        <h1 className='relative font-semibold text-sm'>{property.area}</h1>
                                        <h2 className='relative text-gray-600 text-xs'>{property.address}</h2>
                                        <input className='absolute right-5 top-5 accent-blue-600 h-4 w-4' type='checkbox' checked={selectedProperties.includes(property.property_id)} onChange={() => handleCheckboxChange(property.property_id)} disabled={selectedProperties.length >= 3 && !selectedProperties.includes(property.property_id)} />
                                    </div>
                                    <p>{property.area}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    
                </div>

            )}

            {!selectionTab && (
                <div className='flex flex-col relative h-full w-full'>
                    <div className='w-full h-8 relative flex flex-row justify-between items-center  p-4 bg-gradient-to-br from-[#0e2044] to-[#41b655]'>
                        <h1 className='text-white font-bold text-md relative '> {uiConfig?.['compare_properties_label'] || 'Compare Properties'}</h1>
                        <h2 className='text-white font-semibold text-xs cursor-pointer relative flex flex-row items-center gap-2' onClick={() => { setSelectionTab(true) }}><FaArrowLeft />Back to Selection</h2>
                    </div>
                    <div className='h-full relative overflow-y-auto w-full flex flex-col items-center '>
                        <div className={`relative  grid grid-rows-1 gap-6 px-4 py-8 ${selectedOnes.length === 2 ? 'grid-cols-2 w-[70%]' : 'grid-cols-3 w-full'}`}>
                            
                            {/* Property Headers Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={`header-${index}`} className='sticky top-0 p-4 flex rounded-md shadow-md bg-white z-[11] items-center justify-center'>
                                        <h1>Property in <span>{property.area}</span></h1>
                                    </div>
                                ))}
                            </div>

                            {/* Spider Maps Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={index} className=" flex flex-col p-4 bg-white rounded shadow-md">
                                        <div className="flex flex-row justify-start self-start items-center w-full">
                                            <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">{uiConfig?.['spider_map_card_title'] ||"Decision Support Radar"} <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={()=>{handleMouseEnter(index, 'spider')}} onMouseLeave={() => {handleMouseLeave(index, 'spider')}}/><div className={`${visibleTooltips[index]?.spider ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>{uiConfig?.['spider_map_card_tooltip'] || "Summarizes core property suitability factors."}</div></div></h2>
                                        </div>
                                    <div key={`spider-${index}`} className="h-[400px] p-4 bg-white rounded-md">
                                        <Spider label={property.property_id} scores={property.scores} />
                                    </div>
                                    </div>
                                ))}
                            </div>

                            {/* Location Maps Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={`location-${index}`} className="card p-4 bg-white rounded-md shadow-md gap-4 flex flex-col items-start">
                                        <div className="flex justify-start items-center flex-row w-full">
                                            <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">
                                                Location Map 
                                                <div className="relative inline-block">
                                                    <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter(index, 'map')} onMouseLeave={() => handleMouseLeave(index, 'map')} />
                                                    <div className={`${visibleTooltips[index]?.map ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>
                                                        Shows the exact location of the property/project on the map
                                                    </div>
                                                </div>
                                            </h2>
                                        </div>
                                        <div className="bg-gray-100 h-48 w-full rounded relative overflow-hidden">
                                             <MapBoxMap lat={property?.latitude_longitude[0]} lng={property?.latitude_longitude[1]} source='FromProperty' />
                                        </div>
                                        <div className="text-xs text-gray-600 flex justify-start relative w-full flex-row">
                                            <span>{property.address}</span>
                                        </div>
                                        <div className='flex flex-col gap-3 relative w-full'>
                                            <div className="flex justify-between items-center border-b border-gray-100">
                                                <span className="text-sm text-gray-600">{uiConfig?.['property_card_detail_1'] || "Property Type"}</span>
                                                <span className="text-sm font-medium">{property.property_type}</span>
                                            </div>
                                            <div className="flex justify-between items-center border-b border-gray-100">
                                                <span className="text-sm text-gray-600">{uiConfig?.['property_card_detail_2'] || "Total Area"}</span>
                                                <span className="text-sm font-medium">{property.total_area} Acres</span>
                                            </div>
                                            <div className="flex justify-between items-center border-b border-gray-100">
                                                <span className="text-sm text-gray-600">{uiConfig?.['property_card_detail_3'] || "Business Location Type"}</span>
                                                <span className="text-sm font-medium">{property.business_location_type}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Geo Snapshots Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={`geo-${index}`} className="card p-4 bg-white min-h-[320px] rounded-md shadow-md gap-6 flex flex-col items-start">
                                        <div className="flex justify-between items-center">
                                            <h2 className="text-base font-semibold text-primary flex flex-row items-center gap-2">
                                                {uiConfig?.['location_summary_card_title'] || "Location Intelligence Summary"}
                                                <div className='relative inline-block'>
                                                    <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter(index, 'geo')} onMouseLeave={() => handleMouseLeave(index, 'geo')}/>
                                                    <div className={`${visibleTooltips[index]?.geo ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>
                                                        {uiConfig?.['location_summary_card_tooltip'] || "Nearby Transport & Connectivity Distances"}
                                                    </div>
                                                </div>
                                                <span title='Property-Wise Suitability Score' className='py-1 cursor-default px-4 relative flex items-center justify-center rounded-full text-xs text-white font-semibold  bg-gradient-to-r from-[#673AB7] to-[#5f2abb]'>{property?.scores[0].toFixed(2)}&nbsp;/&nbsp;10</span>
                                            </h2>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 w-full">
                                            <div className="flex items-center col-span-1 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <FaRoad className="text-indigo-600" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_highway_title'] || "Highway"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.road_connectivity.distance} km 
                                                        {property.road_connectivity.status === 'good' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500' />
                                                        ) : property.road_connectivity.status === 'warning' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500' />
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500' />
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center col-span-1 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <FaTrain className="text-indigo-600" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_railway_title'] || "Railway"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.railway.distance} km 
                                                        {property.railway.status === 'good' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500' />
                                                        ) : property.railway.status === 'warning' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500' />
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500' />
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center col-span-1 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <RiShipFill className="text-indigo-600" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_seaport_title'] || "Seaport"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.seaport.distance} km 
                                                        {property.seaport.status === 'good' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500' />
                                                        ) : property.seaport.status === 'warning' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500' />
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500' />
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center col-span-1 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <FaPlane className="text-indigo-600" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_airport_title'] || "Airport"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.airport.distance} km 
                                                        {property.airport.status === 'good' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500' />
                                                        ) : property.airport.status === 'warning' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500' />
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500' />
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center col-span-2 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <MdOfflineBolt className="text-indigo-600 text-md" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_power_source_title'] || "Power Source"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.power.distance} km 
                                                        {property.power.status === 'good' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500' />
                                                        ) : property.power.status === 'warning' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500' />
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500' />
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center col-span-2 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <FaBus className="text-indigo-600 text-md" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_transportation_title'] || "Availability of Local Transportation"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.availability_of_local_transportation} 
                                                        {property.availability_of_local_transportation === 'good' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500' />
                                                        ) : property.power.status === 'warning' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500' />
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500' />
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center col-span-2 flex-row gap-2">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                                                    <IoWifi className="text-indigo-600 text-md" />
                                                </div>
                                                <div className='flex flex-col gap-1'>
                                                    <p className="text-sm font-medium">{uiConfig?.['location_summary_network_title'] || "Network Availability"}</p>
                                                    <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">
                                                        {property.network_availability} 
                                                        {property.network_availability === '4G & 5G' ? (
                                                            <BsPatchCheckFill size={12} className='text-green-500'/>
                                                        ) : property.network_availability === '4G' ? (
                                                            <FaTriangleExclamation size={12} className='text-yellow-500'/>
                                                        ) : (
                                                            <FaCircleXmark size={12} className='text-red-500'/>
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Vendor Proximity Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={`vendor-${index}`} className="card p-4 bg-white rounded-md shadow-md gap-6 relative flex flex-col items-start">
                                        <div className='relative flex flex-row items-center justify-between'>
                                            <div className="flex gap-2 items-center relative flex-row">
                                                <h2 className="text-base font-semibold text-primary relative">{uiConfig?.['vendor_card_title'] || "Supply Chain Accessibility"}</h2>
                                                <div className="tooltip relative inline-block">
                                                    <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter(index, 'vendor')} onMouseLeave={() => handleMouseLeave(index, 'vendor')}/>
                                                    <div className={`${visibleTooltips[index]?.vendor ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>
                                                        {uiConfig?.['vendor_card_tooltip'] ||"Nearby vendors sorted by distance and relevance to the selected property"}
                                                    </div>
                                                </div>
                                                 <span title='Property-Wise Vendor Score' className='py-1 cursor-default px-4 relative flex items-center  justify-center rounded-full text-white font-semibold text-xs bg-gradient-to-r from-[#70A1D9] to-[#5b96d8]'>{property?.scores[4].toFixed(2)} &nbsp;/&nbsp;10</span>
                                            </div>
                                            <div className='relative p-2 text-sm text'></div>
                                        </div>
                                        <div className="flex space-x-2 justify-between items-center relative w-full">
                                            <div className='relative flex flex-row gap-2'>
                                                <div className='relative flex flex-col gap-1 items-center'>
                                                    <button 
                                                        onClick={()=> {setShowEssentialMaterials(true)}}
                                                        className={`px-3 py-1 text-xs cursor-pointer text-black font-semibold transition-all`}
                                                    >
                                                        {uiConfig?.['essential_supplies_title'] || "Essential Supplies"}
                                                    </button>
                                                    <div className={`${showEssentialMaterials ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                                                </div>
                                                <div className='relative flex flex-col gap-1 items-center'>
                                                    <button 
                                                        onClick={()=> {setShowEssentialMaterials(false)}}
                                                        className={`px-3 py-1 text-xs font-medium rounded-full cursor-pointer`}
                                                    >
                                                         {uiConfig?.['non_essential_supplies_title'] || "Non-Essential Supplies"}
                                                    </button>
                                                    <div className={`${!showEssentialMaterials ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                                                </div>
                                            </div>
                                        </div>
                                        {showEssentialMaterials ? (
                                            <div className="gap-3 w-full relative grid grid-cols-2">
                                                {property.essential_vendors.length === 0 ? (
                                                    <p className="text-sm text-gray-500 italic col-span-2 h-28 justify-self-center self-center">
                                                        No vendors available
                                                    </p>
                                                ) : (
                                                    property.essential_vendors.slice(0, 5).map((essentials, idx) => (
                                                        <div key={idx} className="grid grid-cols-2 gap-2 col-span-2">
                                                            <div className="flex flex-row gap-2 items-start">
                                                                <div className="w-2 h-2 rounded-full bg-[#70A1D9] mt-2"></div>
                                                                <div className='flex flex-col'>
                                                                    <span className="text-sm font-medium">{essentials.supply}</span>
                                                                    <span className='text-xs font-light text-gray-600'>{uiConfig?.['no_of_vendors'] || 'No of Vendors:'} {essentials.total_vendor}</span>
                                                                </div>
                                                            </div>
                                                            <div className='flex flex-row gap-2 justify-self-end'>
                                                                <span className="text-xs text-gray-600 ">
                                                                    {uiConfig?.['nearest_vendor'] || 'Nearest Vendor:'} <span className='font-semibold text-gray-700'>{essentials.nearest_vendor_distance.toFixed(2)} km</span>
                                                                </span>
                                                                {essentials.status === 'good' ? (
                                                                    <BsPatchCheckFill className="text-green-500" />
                                                                ) : essentials.status === 'warning' ? (
                                                                    <FaTriangleExclamation className="text-yellow-500" />
                                                                ) : (
                                                                    <FaCircleXmark className="text-red-500" />
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))
                                                )}
                                            </div>
                                        ) : (
                                            <div className="gap-3 w-full relative grid grid-cols-2">
                                                {property.nonessential_vendors.length === 0 ? (
                                                    <p className="text-sm text-gray-500 italic col-span-2 h-28 justify-self-center self-center">
                                                        No vendors available
                                                    </p>
                                                ) : (
                                                    property.nonessential_vendors.slice(0, 5).map((essential, idx) => (
                                                        <div key={idx} className="grid grid-cols-2 gap-2 col-span-2">
                                                            <div className="flex flex-row gap-2 items-start">
                                                                <div className="w-2 h-2 rounded-full bg-[#70A1D9] mt-2"></div>
                                                                <div className='flex flex-col'>
                                                                    <span className="text-sm font-medium">{essential.supply}</span>
                                                                    <span className='text-xs font-light text-gray-600'>{uiConfig?.['no_of_vendors'] || 'No of Vendors:'} {essential.total_vendor}</span>
                                                                </div>
                                                            </div>
                                                            <div className='flex flex-row gap-2 justify-self-end'>
                                                                <span className="text-xs text-gray-600 ">
                                                                     {uiConfig?.['nearest_vendor'] || 'Nearest Vendor:'} <span className='font-semibold text-gray-700'>{essential.nearest_vendor_distance.toFixed(2)} km</span>
                                                                </span>
                                                                {essential.status === 'good' ? (
                                                                    <BsPatchCheckFill className="text-green-500" />
                                                                ) : essential.status === 'warning' ? (
                                                                    <FaTriangleExclamation className="text-yellow-500" />
                                                                ) : (
                                                                    <FaCircleXmark className="text-red-500" />
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Approvals List Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={`approvals-${index}`} className="card p-4 bg-white rounded-md shadow-md relative flex flex-col items-start gap-6">
                                        <div className='flex relative flex-row items-center justify-between w-full'>
                                            <div className='relative gap-2 flex flex-row items-center'>
                                                <h2 className="text-base relative font-semibold text-primary">{uiConfig?.['approval_card_title'] ||"Compliance & Regulatory Checklist"}</h2>
                                                <div className="tooltip relative inline-block">
                                                    <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter(index, 'approval')} onMouseLeave={() => handleMouseLeave(index, 'approval')}/>
                                                    <div className={`${visibleTooltips[index]?.approval ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>
                                                        {uiConfig?.['approval_card_tooltip'] || "Govt. clearances required for the project"}
                                                    </div>
                                                </div>
                                                <span title='Property-Wise Approval Score' className='py-1 cursor-default px-4 relative flex items-center justify-center rounded-full text-xs tex-white text-white font-semibold bg-gradient-to-r from-[#E91E63] to-[#ec135c]'>{property?.scores[3].toFixed(2)} &nbsp;/&nbsp;10</span>
                                            </div>
                                            <div className='relative rounded-full bg-orange-100 py-1 px-2 text-orange-800 text-xs font-semibold'>
                                                {property.approvals.length} Needed
                                            </div>
                                        </div>
                                        
                                        <div className="relative w-full grid grid-cols-4 gap-3">
                                            {property.approvals.slice(0,5).map((approval, idx) => 
                                                <>
                                                    <div key={idx} className="relative flex flex-row items-start w-full gap-2 col-span-3">
                                                        <div className="w-2 h-2 rounded-full flex-shrink-0 bg-[#E91E63] mt-2"></div>
                                                        <div className='relative flex flex-col'>
                                                            <span className="text-sm font-medium">{approval.approval_name}</span>
                                                            <span className='text-xs text-gray-500'>{approval.government_department}</span>
                                                        </div>
                                                    </div>
                                                    <div key={idx} className="relative flex flex-row items-center gap-2 whitespace-nowrap col-span-1 justify-self-end">
                                                        <div className='relative flex flex-col'>
                                                            <p className='relative text-gray-600 text-xs'>{uiConfig?.['approval_duration'] || 'Est. Duration'}</p>
                                                            <span className="text-sm text-black">{approval.time_taken} days</span>
                                                        </div>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Government Incentives Row */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div key={`incentives-${index}`} className="card p-4 bg-white rounded-md shadow-md gap-6 relative flex flex-col items-start">
                                        <div className="flex flex-row justify-between items-center w-full">
                                            <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">
                                                {uiConfig?.['incentives_card_title'] ||"Subsidy & Support Matrix"}
                                                <div className='relative inline-block'>
                                                    <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter(index, 'incentive')} onMouseLeave={() => handleMouseLeave(index, 'incentive')}/>
                                                    <div className={`${visibleTooltips[index]?.incentive ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>
                                                        {uiConfig?.['incentives_card_tooltip'] || "Applicable Government Incentives & Schemes"}
                                                    </div>
                                                </div>
                                                 <span title='Property-Wise Incentive Score' className='py-1 px-4 relative cursor-default flex items-center justify-center rounded-full text-xs  text-white font-semibold bg-gradient-to-r from-[#4CAF50] to-[#3cb340]'>{property?.scores[2].toFixed(2)} &nbsp;/&nbsp;10</span>
                                            </h2>
                                            <div className='relative py-1 px-2 rounded-full text-xs text-orange-800 bg-orange-100 font-semibold'>
                                                {property.incentives.length} Found
                                            </div>
                                        </div>
                                        <div className="flex flex-col gap-3 relative w-full h-full">
                                            {property.incentives.sort((a,b)=>a.incentive_rank - b.incentive_rank).slice(0,5).map((incentive,idx) =>
                                                <div key={idx} className="flex items-start relative flex-row gap-2">
                                                    <div className="w-2 h-2 rounded-full bg-[#4CAF50] mt-2"></div>
                                                    <div className='relative flex flex-col items-start'>
                                                        <h3 className="text-sm font-medium">{incentive.type}</h3>
                                                        <p className="text-xs text-gray-600">{incentive.name}</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Employment Overview  */}
                            <div className='contents'>
                                {filteredData.map((property, index) => (
                                    <div 
                                    key={`workforce-${index}`} 
                                    className="card p-4 bg-white h-fit min-h-[400px] flex flex-col gap-2 rounded shadow-md"
                                    >
                                    <div className="flex justify-between h-fit items-center mb-3">
                                        <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">
                                        {uiConfig?.['employement_card_title'] ||"Workforce Availability Insights"}
                                        <div className='relative inline-block'>
                                            <FaRegQuestionCircle 
                                            size={15} 
                                            className="text-gray-400" 
                                            onMouseEnter={() => handleMouseEnter(index, 'employment')} 
                                            onMouseLeave={() => handleMouseLeave(index, 'employment')} 
                                            />
                                            <div className={`${visibleTooltips[index]?.employment ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>
                                            {uiConfig?.['employement_card_tooltip'] || "Local Workforce Skill Levels Overview"}
                                            </div>
                                        </div>
                                        <span title='Property-Wise Employment Score' className='py-1 px-4 relative cursor-default flex items-center justify-center rounded-full text-xs  text-white font-semibold  bg-gradient-to-r from-[#2C53A3] to-[#234ea4]'>{property?.scores[1].toFixed(2)} &nbsp;/&nbsp;10</span>
                                        </h2>
                                    </div>
                                    
                                    <div className="flex-1 relative w-full">
                                        <Doughnut 
                                        data={{
                                            labels: ['Skilled', 'Semi-Skilled', 'Unskilled'],
                                            datasets: [{
                                            data: [property.skilled_no, property.semiskilled_no, property.unskilled_no],
                                            backgroundColor: ['#2563EB', '#16A34A', '#D97706'],
                                            borderWidth: 1,
                                            }]
                                        }} 
                                        options={{
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            cutout: '60%',
                                            plugins: {
                                            legend: {
                                                display: false
                                            },
                                            },
                                        }}
                                        className="w-full h-full"
                                        />
                                    </div>
                                    
                                    <div className="mt-2 mb-2 h-fit grid grid-cols-3 gap-2">
                                        <div className="text-center flex flex-col gap-2">
                                        <div className="text-xs font-medium">Skilled</div>
                                        <div className="text-sm text-blue-600 font-semibold">{property.skilled_no} workers</div>
                                        </div>
                                        <div className="text-center flex flex-col gap-2">
                                        <div className="text-xs font-medium">Semi-skilled</div>
                                        <div className="text-sm text-green-600 font-semibold">{property.semiskilled_no} workers</div>
                                        </div>
                                        <div className="text-center flex flex-col gap-2">
                                        <div className="text-xs font-medium">Unskilled</div>
                                        <div className="text-sm text-amber-600 font-semibold">{property.unskilled_no} workers</div>
                                        </div>
                                    </div>    
                                    </div>
                                ))}
                            </div>

                            <div className='contents'>
                                {filteredData.map((property, index)=> (
                                    <div key={index} className='relative h-[52px] p-8 min-h-[52px] w-full'>
                                        <span className='text-white'>, </span>
                                    </div>  
                                ))}
                            </div>

                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Comparison