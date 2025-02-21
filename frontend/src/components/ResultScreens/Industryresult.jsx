import React, { useEffect, useState } from 'react'
import useEmblaCarousel from 'embla-carousel-react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import { FaCheckCircle } from 'react-icons/fa';
import { FaTimesCircle } from 'react-icons/fa';
import { GoAlertFill } from "react-icons/go";
// import { result } from './data'
import './Industryresult.css'
import Model from './Model';

function Industryresult({ result }) {
// function Industryresult() {
    console.log("result in indeustry solution screen",result);
    const analytics_response = result["Analytics_response"]
    console.log("Analytics_response", analytics_response);

    const [resultLen, setResultLen] = useState(0)
    const [solutions, setSolutions] = useState([])
    const [emblaRef, emblaApi] = useEmblaCarousel({ dragFree: true, watchDrag: false });

    // Add model states to handle modal
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalData, setModalData] = useState([]);
    const [modalTitle, setModalTitle] = useState('');

    //Toggle modal on click of button
    const toggleModal = (data, title) => {
        setModalData(data);
        setModalTitle(title);
        setIsModalOpen(!isModalOpen);
    };

    const statusIcon = {
        good: <FaCheckCircle size={20} color="green" />,
        bad: <FaTimesCircle size={20} color="red" />,
        warning: <GoAlertFill size={20} color="yellow" />,
        danger: <GoAlertFill size={20} color="red" />,
    }

    const fetchData = async (property) => {
        console.log("proprtis here", property);

        try {
            const response = await fetch(`http://172.17.244.12/api/resource/Survey No?fields=["*"]&filters=[["name","=","${property}"]]&order_by=modified asc`, {
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
        const nonEssential_supply_vendor_lookup_df = JSON.parse(analytics_response['Non_essential_supply_vendor_lookup_df'])

        // for employemnt 
        const Employment_lookup_df = JSON.parse(analytics_response['Employment_lookup_df'])

        // for incenetive
        const Solution_lookup_df = JSON.parse(analytics_response['Solution_lookup_df'])

        //for approvals
        const Approval_lookup_df = JSON.parse(analytics_response['Approval_lookup_df'])
        console.log("Approval_lookup_df", Approval_lookup_df);

        const promises = Object.entries(property_id).map(async ([key, value]) => {
            console.log(`key ${key} value ${value}`);
            try {
                const get_data = await fetchData(value)
                const data = get_data[0]
                // console.log("actual result data", data);

                if (data) {
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
                    console.log("hahah😒",Essential_supply_vendor_lookup_df["supply_id"]);
                    
                    const ess_supply_id = Essential_supply_vendor_lookup_df["supply_id"][key]
                    const ess_No_of_vendors_found = Essential_supply_vendor_lookup_df["No_of_vendors_found"][key]
                    const ess_Distance = Essential_supply_vendor_lookup_df["Distance"][key]

                    const noness_supply_id = nonEssential_supply_vendor_lookup_df["supply_id"][key]
                    const noness_No_of_vendors_found = nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key]
                    const noness_Distance = nonEssential_supply_vendor_lookup_df["Distance"][key]


                    const essential_supply_and_vendor = []
                    const nonessential_supply_and_vendor = []

                    ess_supply_id.forEach((supply, index) => {
                        const supply_vendor = { supply: supply, total_vendor: ess_No_of_vendors_found[index], nearest_venodor_distance: ess_Distance[index],status: get_status_for_distance(ess_Distance[index])}
                        essential_supply_and_vendor.push(supply_vendor)
                    })
                    noness_supply_id.forEach((supply, index) => {
                        const supply_vendor = { supply: supply, total_vendor: noness_No_of_vendors_found[index], nearest_venodor_distance: noness_Distance[index],status: get_status_for_distance(noness_Distance[index]) }
                        nonessential_supply_and_vendor.push(supply_vendor)
                    })

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
                        road_connectivity: { distance: road_connectivity, status: get_status_for_distance(road_connectivity) }
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

    // Update the resultLen after the solutions are fetched
    useEffect(() => {
        setResultLen(solutions.length);
        console.log("final solutions2", solutions);
    }, [solutions])

    const goToNext = () => {
        if (emblaApi) {
            emblaApi.scrollNext();
        }
    };

    const goToPrev = () => {
        if (emblaApi) {
            emblaApi.scrollPrev();
        }
    };
    useEffect(() => {
        if (emblaApi) {
            emblaApi.on('select', () => {
                document.querySelectorAll('.embla__slide').forEach(slide => {
                    slide.style.backgroundColor = 'rgb(135 197 235 / 41%)';
                });
            });
        }
    }, [emblaApi]);

    // Define default Leaflet icon
    const defaultIcon = L.icon({
        iconUrl: markerIconPng,
        iconSize: [25, 41],
        iconAnchor: [12, 41]
    });

    return (
        <div className="reuslt-container flex flex-col w-full h-full">
            <div className="result-title w-full h-[5%] flex items-center justify-center p-5 text-2xl">
                We Found <p className='font-bold text-red-600 px-1'>{resultLen}</p> Results For Your Query
            </div>
            <div className="solutions px-16 h-[95%] pb-6">
                <div className="embla h-full" ref={emblaRef}>
                    <div className="embla__container border-black h-full" >
                        {solutions.map((solution, index) => (
                            <div key={index} className="embla__slide rounded-md">
                                <div className="slide-content flex flex-col h-full">
                                    <div className="addres w-full h-[6%] p-2 flex items-center text-start text-2xl">{solution.address}</div>
                                    <div className="first-row flex w-full h-[33%]">
                                        <div className="location-image w-[25%] h-full">
                                            <MapContainer center={solution.lat_long} zoom={13} style={{ height: '100%', width: '100%' }} className='rounded-xl' attributionControl={false} zoomControl={false}>
                                                <TileLayer
                                                    attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                                                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                                                />
                                                <Marker position={solution.lat_long} icon={defaultIcon}>
                                                    <Popup>
                                                        Location: <br />
                                                        Latitude: {solution.lat_long[0]} <br />
                                                        Longitude: {solution.lat_long[1]}
                                                    </Popup>
                                                </Marker>
                                            </MapContainer>
                                        </div>
                                        <div className="details w-[75%] flex flex-col">
                                            <div className="title px-5 text-start text-xl text-dodgerblue">Land Maping</div>
                                            <div className="Content flex px-5 py-5 gap-2">
                                                <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon.good}</div><div className="text">{solution.property_type}</div></div>
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon.good}</div><div className="text">{solution.total_area} Acre</div></div>
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon[solution.seaport.status]}</div><div className="text">{solution.seaport['distance']} Kms From Seaport</div></div>
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon[solution.railway.status]}</div><div className="text">{solution.railway['distance']} Kms From Railway Line</div></div>
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon[solution.power.status]}</div><div className="text">{solution.power['distance']} Kms From Power Plant</div></div>
                                                </div>
                                                <div className="right flex-1 text-start flex flex-col gap-3">
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.business_location_type}</div></div>
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon[solution.availability_of_local_transportation]}</div><div className="text">Avaibility Of Local Transportaion</div></div>
                                                    <div className="items flex gap-3"><div className="icon">{statusIcon[solution.road_connectivity.status]}</div><div className="text">{solution.road_connectivity['distance']} Kms From Road Connectivity</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">Available {solution.employement['count']} {solution.employement['type']} Manpower</div></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="second-row flex flex-col py-5 gap-1">
                                        <div className="section-title text-start text-xl text-dodgerblue">Vendors & Suppliers Mapping</div>
                                        <div className="Content flex px-2 py-2 gap-2">
                                            <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                                                {solution.essential_vendors.slice(0, 5).map((item, ind) => {
                                                    return (<div key={ind} className="items flex gap-3"><div className="icon">{statusIcon[item.status]}</div><div className="text">{item.total_vendor} suppliers for {item.supply} with the top choice {item.nearest_venodor_distance} km away</div></div>)
                                                })}
                                                {solution.essential_vendors.length > 5 && <button className='text-sm' onClick={() => toggleModal(solution.essential_vendors, 'Vendors')}>Show More...</button>}
                                            </div>
                                            <div className="right flex-1 text-start flex flex-col gap-3">
                                                {solution.nonessential_vendors.slice(0, 5).map((item, index) => {
                                                    return (<div key={index} className="items flex gap-3"><div className="icon">{statusIcon[item.status]}</div><div className="text">{item.total_vendor} suppliers for {item.supply} with the top choice {item.nearest_venodor_distance} km away</div></div>)
                                                })}
                                                {solution.nonessential_vendors.length >5 &&<button className='text-sm' onClick={() => toggleModal(solution.nonessential_vendors, 'Vendors')}>Show More...</button>}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="third-row flex flex-col pt-5">
                                        <div className="section-title text-start text-xl text-dodgerblue">Incentive & Approvals
                                        </div>
                                        <div className="Content flex px-2 py-2 gap-2">
                                            <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                                                {solution.incentives.slice(0, 5).map((item, index) => {
                                                    return (<div key={index} className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{item.incentive_name}</div></div>)
                                                })}
                                                {solution.incentives.length && <button className='text-sm' onClick={() => toggleModal(solution.incentives, 'Incentives')}>Show More...</button>}
                                            </div>
                                            <div className="right flex-1 text-start flex flex-col gap-3">
                                                {solution.approvals.slice(0, 5).map((item, index) => {
                                                    return (<div key={index} className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{item.approval_name}</div></div>)
                                                })}
                                                {solution.approvals.length >5 && <button className='text-sm' onClick={() => toggleModal(solution.approvals, 'Approvals')}>Show More...</button>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                <button className="embla__prev" onClick={goToPrev}>Prev</button>
                <button className="embla__next" onClick={goToNext}>Next</button>
                <Model isOpen={isModalOpen} onClose={() =>(setIsModalOpen(false))} title={modalTitle} data={modalData}/>
            </div>
        </div>
    )
}

export default Industryresult
