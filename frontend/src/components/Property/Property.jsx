import React, { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import { FaCheckCircle, FaTimesCircle, FaMapMarkerAlt, FaIndustry, FaRuler, FaShip, FaTrain, FaCity, FaBus, FaRoad, FaUsers, FaBoxes, FaTag, FaShieldAlt, FaCheck, FaExclamationTriangle, FaChevronRight, FaRegCheckCircle, FaRegDotCircle } from 'react-icons/fa';
import { GiFactory, GiCommercialAirplane, GiPowerGenerator } from 'react-icons/gi';
import { PiPolygonBold } from "react-icons/pi";
import { MdApartment, MdLocalShipping, MdConstruction, MdApproval } from 'react-icons/md';
import { RiGovernmentLine ,RiRoadMapLine} from 'react-icons/ri';
import { GoAlertFill } from "react-icons/go";
import Model from '../ResultScreens/Model';

function Property({ solution, toggleModal }) {
    console.log("pt",solution);
    
    const defaultIcon = L.icon({
        iconUrl: markerIconPng,
        iconSize: [25, 41],
        iconAnchor: [12, 41]
    });
    

    const statusIcon = {
        good: <FaCheckCircle size={18} className="text-green-500 mt-1" />,
        bad: <FaTimesCircle size={18} className="text-red-500 mt-1" />,
        warning: <GoAlertFill size={18} className="text-yellow-500 mt-1" />,
        danger: <GoAlertFill size={18} className="text-red-500 mt-1" />,
    }

    const mapRef = useRef(null);

    useEffect(() => {
        if (mapRef.current && solution.latitude_longitude) {
            mapRef.current.setView(solution.latitude_longitude, 13);
        }
    }, [solution]);

    return (
        <div className="p-6 bg-[#f8f9fa]">
            {/* Header Section */}
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8">
                <div>
                    <h1 className="text-2xl lg:text-4xl font-bold text-gray-900 mt-1">{solution.property_type}</h1>
                    <p className="text-gray-500 mt-2 flex items-center">
                        <FaMapMarkerAlt className="w-4 h-4 mr-2 text-blue-500" />
                        {solution.address}
                    </p>
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Map Section */}
                <div className="lg:col-span-1 h-full bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
                    <div className="p-3 bg-gradient-to-r from-blue-50 to-blue-100 border-b flex items-center">
                        <RiRoadMapLine className="w-5 h-5 mr-2 text-blue-600" />
                        <span className="text-sm font-medium text-gray-700">Location Overview</span>
                    </div>
                    <MapContainer
                        key={solution.address}
                        center={solution.latitude_longitude || [0, 0]}
                        zoom={13}
                        style={{ height: 'calc(100% - 40px)', width: '100%' }}
                        className='rounded-b-lg'
                        attributionControl={false}
                        zoomControl={false}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                        />
                        <Marker position={solution.latitude_longitude || [0, 0]} icon={defaultIcon}>
                            <Popup className="font-medium">{solution.property_type}</Popup>
                        </Marker>
                    </MapContainer>
                </div>

                {/* Specifications Section */}
                <div className="lg:col-span-1 bg-white rounded-xl shadow-md p-5 border border-gray-100">
                    <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
                        <div className="bg-blue-100 p-2 rounded-lg mr-3">
                            <FaIndustry className="w-5 h-5 text-blue-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800">Specifications</h3>
                    </div>
                    <ul className="space-y-3">
                        {[
                            {
                                icon: <PiPolygonBold className="text-gray-600" />,
                                title: solution.property_type,
                                subtitle: 'Industrial property type',
                                status: 'good'
                            },
                            {
                                icon: <FaRuler className="text-gray-600" />,
                                title: `${solution.total_area} Acres`,
                                subtitle: 'Total land area',
                                status: 'good'
                            },
                            {
                                icon: <FaShip className="text-gray-600" />,
                                title: `${solution.seaport.distance} km from Seaport`,
                                subtitle: 'Nearest port facility',
                                status: solution.seaport.status
                            },
                            {
                                icon: <FaTrain className="text-gray-600" />,
                                title: `${solution.railway.distance} km from Railway`,
                                subtitle: 'Nearest railway station',
                                status: solution.railway.status
                            }
                        ].map((item, index) => (
                            <li key={index} className="flex items-start">
                                <div className="bg-gray-100 p-2 rounded-lg mr-3 text-gray-600">
                                    {item.icon}
                                </div>
                                <div className="flex-1">
                                    <p className="font-medium text-gray-800">{item.title}</p>
                                    <p className="text-xs text-gray-500">{item.subtitle}</p>
                                </div>
                                <div className="ml-2">
                                    {item.status === 'good' ? (
                                        <FaCheck className="text-green-500" />
                                    ) : (
                                        <FaExclamationTriangle className="text-yellow-500" />
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Infrastructure Section */}
                <div className="lg:col-span-1 bg-white rounded-xl shadow-md p-5 border border-gray-100">
                    <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
                        <div className="bg-purple-100 p-2 rounded-lg mr-3">
                            <MdConstruction className="w-5 h-5 text-purple-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800">Infrastructure</h3>
                    </div>
                    <ul className="space-y-3">
                        {[
                            {
                                icon: <FaCity className="text-gray-600" />,
                                title: solution.business_location_type,
                                subtitle: 'Location type',
                                status: 'good'
                            },
                            {
                                icon: <FaBus className="text-gray-600" />,
                                title: 'Local Transport',
                                subtitle: solution.availability_of_local_transportation ? 'Available' : 'Limited',
                                status: solution.availability_of_local_transportation
                            },
                            {
                                icon: <FaRoad className="text-gray-600" />,
                                title: `${solution.road_connectivity.distance} km from Major Road`,
                                subtitle: 'Road connectivity',
                                status: solution.road_connectivity.status
                            },
                            {
                                icon: <FaUsers className="text-gray-600" />,
                                title: `${solution.employement.count} ${solution.employement.type} Workers`,
                                subtitle: 'Workforce availability',
                                status: 'good'
                            }
                        ].map((item, index) => (
                            <li key={index} className="flex items-start">
                                <div className="bg-gray-100 p-2 rounded-lg mr-3 text-gray-600">
                                    {item.icon}
                                </div>
                                <div className="flex-1">
                                    <p className="font-medium text-gray-800">{item.title}</p>
                                    <p className="text-xs text-gray-500">{item.subtitle}</p>
                                </div>
                                <div className="ml-2">
                                    {item.status === 'good' ? (
                                        <FaCheck className="text-green-500" />
                                    ) : (
                                        <FaExclamationTriangle className="text-yellow-500" />
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* Suppliers Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Essential Suppliers */}
                <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
                    <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-white">
                        <div className="flex items-center">
                            <div className="bg-blue-100 p-2 rounded-lg mr-3">
                                <FaBoxes className="w-5 h-5 text-blue-600" />
                            </div>
                            <h4 className="text-lg font-semibold text-gray-800">Essential Suppliers</h4>
                        </div>
                        <span className="bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full font-medium">
                            {solution.essential_vendors.length} Available
                        </span>
                    </div>
                    <div className="p-4">
                        <ul className="space-y-3">
                            {solution.essential_vendors.slice(0, 5).map((item, ind) => (
                                <li key={ind} className="flex items-start">
                                    <div className={`p-1 rounded-full mr-3 ${item.status === 'good' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                                        {item.status === 'good' ? (
                                            <FaCheck className="w-4 h-4" />
                                        ) : (
                                            <FaExclamationTriangle className="w-4 h-4" />
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{item.supply}</p>
                                        <p className="text-xs text-gray-500">
                                            {item.total_vendor} suppliers (Nearest: {item.nearest_vendor_distance.toFixed(2)} km)
                                        </p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                        {solution.essential_vendors.length > 5 && (
                            <button
                                className="w-full mt-4 text-sm text-blue-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
                                onClick={() => toggleModal(solution.essential_vendors, 'Essential Suppliers')}
                            >
                                <span>View all {solution.essential_vendors.length} suppliers</span>
                                <FaChevronRight className="w-4 h-4 ml-1" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Non-Essential Suppliers */}
                <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
                    <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-purple-100 to-white">
                        <div className="flex items-center">
                            <div className="bg-purple-100 p-2 rounded-lg mr-3">
                                <MdLocalShipping className="w-5 h-5 text-purple-600" />
                            </div>
                            <h4 className="text-lg font-semibold text-gray-800">Non-Essential Suppliers</h4>
                        </div>
                        <span className="bg-purple-100 text-purple-800 text-xs px-3 py-1 rounded-full font-medium">
                            {solution.nonessential_vendors.length} Available
                        </span>
                    </div>
                    <div className="p-4">
                        <ul className="space-y-3">
                            {solution.nonessential_vendors.slice(0, 5).map((item, index) => (
                                <li key={index} className="flex items-start">
                                    <div className={`p-1 rounded-full mr-3 ${item.status === 'good' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                                        {item.status === 'good' ? (
                                            <FaCheck className="w-4 h-4" />
                                        ) : (
                                            <FaExclamationTriangle className="w-4 h-4" />
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{item.supply}</p>
                                        <p className="text-xs text-gray-500">
                                            {item.total_vendor} suppliers (Nearest: {item.nearest_vendor_distance.toFixed(2)} km)
                                        </p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                        {solution.nonessential_vendors.length > 5 && (
                            <button
                                className="w-full mt-4 text-sm text-purple-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
                                onClick={() => toggleModal(solution.nonessential_vendors, 'Non-Essential Suppliers')}
                            >
                                <span>View all {solution.nonessential_vendors.length} suppliers</span>
                                <FaChevronRight className="w-4 h-4 ml-1" />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Bottom Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Government Incentives */}
                <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
                    <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-green-50 to-white">
                        <div className="flex items-center">
                            <div className="bg-green-100 p-2 rounded-lg mr-3">
                                <RiGovernmentLine className="w-5 h-5 text-green-600" />
                            </div>
                            <h4 className="text-lg font-semibold text-gray-800">Government Incentives</h4>
                        </div>
                        <span className="bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full font-medium">
                            {solution.incentives.length} Available
                        </span>
                    </div>
                    <div className="p-4">
                        <ul className="space-y-2">
                            {solution.incentives.slice(0, 5).map((item, index) => (
                                <li key={index} className="flex items-start">
                                    <div className="bg-gray-100 p-1 rounded-full mr-3 mt-0.5">
                                        <FaRegCheckCircle className="w-3 h-3 text-gray-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-gray-800">{item.incentive_type}</p>
                                        <p className="text-xs text-gray-500">{item.incentive_name}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                        {solution.incentives.length > 5 && (
                            <button
                                className="w-full mt-4 text-sm text-green-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
                                onClick={() => toggleModal(solution.incentives, 'Government Incentives')}
                            >
                                <span>View all {solution.incentives.length} incentives</span>
                                <FaChevronRight className="w-4 h-4 ml-1" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Required Approvals */}
                <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
                    <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-orange-50 to-white">
                        <div className="flex items-center">
                            <div className="bg-orange-100 p-2 rounded-lg mr-3">
                                <MdApproval className="w-5 h-5 text-orange-600" />
                            </div>
                            <h4 className="text-lg font-semibold text-gray-800">Required Approvals</h4>
                        </div>
                        <span className="bg-orange-100 text-orange-800 text-xs px-3 py-1 rounded-full font-medium">
                            {solution.approvals.length} Needed
                        </span>
                    </div>
                    <div className="p-4">
                        <ul className="space-y-3">
                            {solution.approvals.slice(0, 5).map((item, index) => (
                                <li key={index} className="flex items-start">
                                    <div className="bg-gray-100 p-1 rounded-full mr-3">
                                        <FaRegDotCircle className="w-4 h-4 text-gray-500" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{item.approval_name}</p>
                                        <p className="text-xs text-gray-500">{item.government_department}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                        {solution.approvals.length > 5 && (
                            <button
                                className="w-full mt-4 text-sm text-orange-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
                                onClick={() => toggleModal(solution.approvals, 'Required Approvals')}
                            >
                                <span>View all {solution.approvals.length} approvals</span>
                                <FaChevronRight className="w-4 h-4 ml-1" />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Property