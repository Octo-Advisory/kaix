import React, { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import { FaCheckCircle } from 'react-icons/fa';
import { FaTimesCircle } from 'react-icons/fa';
import { GoAlertFill } from "react-icons/go";
import Model from '../ResultScreens/Model';

function Property({ solution, toggleModal }) {
    console.log("soluyoin from property is", solution);

    // Define default Leaflet icona
    const defaultIcon = L.icon({
        iconUrl: markerIconPng,
        iconSize: [25, 41],
        iconAnchor: [12, 41]
    });

    const statusIcon = {
        good: <FaCheckCircle size={20} color="green" />,
        bad: <FaTimesCircle size={20} color="red" />,
        warning: <GoAlertFill size={20} color="yellow" />,
        danger: <GoAlertFill size={20} color="red" />,
    }

    // Create a ref for the map
    const mapRef = useRef(null);

    // Use effect to update the map view when solution changes
    useEffect(() => {
        if (mapRef.current && solution.latitude_longitude) {
            mapRef.current.setView(solution.latitude_longitude, 13);
        }
    }, [solution]);

    return (
        <div className="embla__slide rounded-b-lg">
            <div className="slide-content flex flex-col h-full overflow-y-auto">
                <div className="addres w-full h-[6%] py-2 flex items-center text-start text-xl">{solution.address}</div>
                <div className="first-row flex w-full h-[33%]">
                    <div className="location-image w-[25%] h-full">
                        <MapContainer
                            key={solution.address}
                            center={solution.latitude_longitude || [0, 0]}
                            zoom={13}
                            style={{ height: '100%', width: '100%' }}
                            className='rounded-xl'
                            attributionControl={false}
                            zoomControl={false}
                            whenCreated={(map) => {
                                mapRef.current = map;
                            }}
                        >
                            <TileLayer
                                attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                            />
                            <Marker position={solution.latitude_longitude || [0, 0]} icon={defaultIcon}>
                                {/* <Popup>
                                    Location: <br />
                                    Latitude: {(solution.latitude_longitude && solution.latitude_longitude[0]) || 0} <br />
                                    Longitude: {(solution.latitude_longitude && solution.latitude_longitude[1]) || 0}
                                </Popup> */}
                            </Marker>
                        </MapContainer>
                    </div>
                    <div className="details w-[75%] flex flex-col">
                        <div className="title px-5 text-start text-xl text-dodgerblue">Land Mapping</div>
                        <div className="Content flex px-5 py-5 gap-2 text-lg">
                            <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon.good}</div><div className="text">{solution.property_type}</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon.good}</div><div className="text">{solution.total_area} Acre</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon[solution.seaport.status]}</div><div className="text">{solution.seaport['distance']} Kms From Seaport</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon[solution.railway.status]}</div><div className="text">{solution.railway['distance']} Kms From Railway Line</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon[solution.power.status]}</div><div className="text">{solution.power['distance']} Kms From Power Plant</div></div>
                            </div>
                            <div className="right flex-1 text-start flex flex-col gap-3">
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon.good}</div><div className="text">{solution.business_location_type}</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon[solution.availability_of_local_transportation]}</div><div className="text">Availability of Local Transportation</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon[solution.road_connectivity.status]}</div><div className="text">{solution.road_connectivity['distance']} Kms From Road Connectivity</div></div>
                                <div className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon.good}</div><div className="text">Available {solution.employement['count']} {solution.employement['type']} Manpower</div></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="second-row flex flex-col py-5 gap-1 text-lg">
                    <div className="section-title text-start text-xl text-dodgerblue">Vendors & Suppliers Mapping</div>
                    <div className="Content flex px-2 py-2 gap-2">
                        <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                            {solution.essential_vendors.length > 0 ? (
                                solution.essential_vendors.slice(0, 5).map((item, ind) => {
                                    const roundedDistance = parseFloat(item.nearest_vendor_distance.toFixed(2));
                                    return (
                                        <div key={ind} className="items flex gap-3">
                                            <div className="icon flex items-center justify-center">{statusIcon[item.status]}</div>
                                            <div className="text">
                                                {item.total_vendor} suppliers for {item.supply} with the top choice {roundedDistance} km away
                                            </div>
                                        </div>
                                    );
                                })
                            ) : (
                                <div>No supplier available</div>
                            )}
                            {solution.essential_vendors.length > 5 && <button className='text-xs' onClick={() => toggleModal(solution.essential_vendors, 'Vendors')}>Show More...</button>}
                        </div>
                        <div className="right flex-1 text-start flex flex-col gap-3">
                            {solution.nonessential_vendors.slice(0, 5).map((item, index) => {
                                const roundedDistance = parseFloat(item.nearest_vendor_distance.toFixed(2));
                                return (<div key={index} className="items flex gap-3"><div className="icon flex items-center justify-center">{statusIcon[item.status]}</div><div className="text">{item.total_vendor} suppliers for {item.supply} with the top choice {roundedDistance} km away</div></div>)
                            })}
                            {solution.nonessential_vendors.length > 5 && <button className='text-xs' onClick={() => toggleModal(solution.nonessential_vendors, 'Vendors')}>Show More...</button>}
                        </div>
                    </div>
                </div>
                <div className="third-row flex flex-col gap-1 text-lg">
                    <div className="section-title text-start text-xl text-dodgerblue flex">
                        <div className="section-title text-xl flex-1">Incentives</div>
                        <div className="section-title text-xl flex-1">Approvals</div>
                    </div>
                    <div className="Content flex px-2 py-2 gap-2">
                        {/* Left Side - Incentives */}
                        <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">

                            {solution.incentives.slice(0, 5).map((item, index) => (
                                <div key={index} className="items flex gap-3">
                                    <div className="icon flex items-center justify-center">{statusIcon.good}</div>
                                    <div className="text">{item.incentive_type}</div>
                                </div>
                            ))}
                            {solution.incentives.length > 5 && (
                                <button className="text-xs" onClick={() => toggleModal(solution.incentives, 'Incentives')}>
                                    Show More...
                                </button>
                            )}
                        </div>

                        {/* Right Side - Approvals */}
                        <div className="right flex-1 text-start flex flex-col gap-3">

                            {solution.approvals.slice(0, 5).map((item, index) => (
                                <div key={index} className="items flex gap-3">
                                    <div className="icon flex items-center justify-center">{statusIcon.good}</div>
                                    <div className="text">{item.approval_name}</div>
                                </div>
                            ))}
                            {solution.approvals.length > 5 && (
                                <button className="text-xs" onClick={() => toggleModal(solution.approvals, 'Approvals')}>
                                    Show More...
                                </button>
                            )}
                        </div>
                    </div>
                </div>



            </div>
        </div>
    )
}

export default Property
