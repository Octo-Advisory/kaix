import React, { useEffect, useState } from 'react'
import useEmblaCarousel from 'embla-carousel-react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import { FaCheckCircle } from 'react-icons/fa';
import { FaTimesCircle } from 'react-icons/fa';
import { GoAlertFill } from "react-icons/go";

// function Industryresult({result}) {
function Industryresult() {

    const [resultLen, setResultLen] = useState(0)
    const [solutions, setSolutions] = useState([])
    const [emblaRef, emblaApi] = useEmblaCarousel({ dragFree: true, watchDrag: false });
    const [currentIndex, setCurrentIndex] = useState(0);

    const statusIcon = {
        good: <FaCheckCircle size={20} color="green" />,
        bad: <FaTimesCircle size={20} color="red" />,
        warning: <GoAlertFill size={20} color="yellow" />,
        danger: <GoAlertFill size={20} color="red" />,
    }

    const result = {
        "Analytics_response": {
            "0": {
                "Property_ID": "30--Borsad-Anand",
                "Property-Wise Suitability Score (PWSS)": 5.7894736842,
                "Property-Wise Employment Score (PWES)": 5.0,
                "Skill_Type": "Semi-skilled",
                "Property-Wise Incentive Score (PWIS)": 5,
                "Property-Wise Approval Score (PWAS)": 5.0,
                "Property-Wise Vendor Score (PWVS)": 10.0,
                "Aggregate Property Performance Score (APPS)": 6.7105263158,
                "Supply": ["Carbon Dioxide", "Chlorine", "Polyisoprene", "Polypropylene", "UV Inks"],
                "property_supply_distance": [98.68, 100.5, 208.39, 144.08, 7.13]
            },
            "1": {
                "Property_ID": "6144--Ankleshwar-Bharuch",
                "Property-Wise Suitability Score (PWSS)": 4.8421052632,
                "Property-Wise Employment Score (PWES)": 5.0,
                "Skill_Type": "Semi-skilled",
                "Property-Wise Incentive Score (PWIS)": 5,
                "Property-Wise Approval Score (PWAS)": 5.0,
                "Property-Wise Vendor Score (PWVS)": 1.0,
                "Aggregate Property Performance Score (APPS)": 3.7203947368,
                "Supply": ["Carbon Dioxide", "Chlorine", "Polyisoprene", "Polypropylene", "UV Inks"],
                "property_supply_distance": [107.28, 109.1, 214.38, 150.08, 17.52]
            }
        },
        "Is_Error": false
    }

    const analyticsResponse = result["Analytics_response"];
    console.log("anakytics response", analyticsResponse);


    const fetchData = async (property) => {
        console.log("proprtis here", property);

        try {
            const response = await fetch(`api/resource/Survey No?fields=["*"]&filters=[["name","=","${property}"]]&order_by=modified asc`, {
                method: 'GET',
                headers: {
                    // 'Authorization': 'token your_api_token', // Replace with actual token
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
            // Optionally, store it in your state or handle further logic
        } catch (error) {
            console.error('Error fetching data:', error); // Handles errors
        }
    }

    const fetchPropertyData = async (analyticsResponse) => {
        let fetchedSolutions = [];

        // Loop over all properties and fetch the data using frappe methods
        for (let [index, property] of Object.entries(analyticsResponse)) {
            try {
                // Use frappe.db.get_doc to fetch the data for each property
                const get_data = await fetchData(property["Property_ID"])
                const data = get_data[0]
                console.log("actual result data", data);

                if (data) {
                    const latLong = data.latitude_longitude
                    const latLongArray = latLong.split(', ').map(coord => parseFloat(coord));
                    const solution = {
                        id: parseInt(index) + 1,
                        area: data.city,
                        district: data.district,
                        availability_of_local_transportation: data.availability_of_local_transportation,
                        road_connectivity: data.road_connectivity,
                        rate_negotiation_options: data.rate_negotiation_options,
                        area_acre: data.area_acre,
                        taluka: data.taluka,
                        state: data.state,
                        nature: data.land_use,
                        status: data.status,
                        property_type: data.property_type,
                        lat_long: latLongArray,
                        business_location_type: data.business_location_type,
                        distance_from_power_source: data.distance_from_power_source,
                        distance_from_nearest_railway_station: data.distance_from_nearest_railway_station,
                        distance_from_nearest_airport: data.distance_from_nearest_airport,
                        distance_from_nearest_seaport: data.distance_from_nearest_seaport,
                        require_shifting_of_any_electricity_line_or_pole: data.require_shifting_of_any_electricity_line_or_pole,
                        vicinity_of: data.vicinity_of,
                    };
                    console.log("dkjbjiwbob", solution);

                    fetchedSolutions.push(solution);
                }
            } catch (error) {
                console.error('Error fetching property data:', error);
            }
        }

        // Update the state once all data is fetched
        setSolutions(fetchedSolutions);
    };

    useEffect(() => {
        fetchPropertyData(analyticsResponse);
    }, []); // Empty dependency array ensures it runs only once after initial render

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
                                    <div className="addres w-full h-[6%] p-2 flex items-center text-start text-2xl">{solution.area}, {solution.district}, {solution.state}</div>
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
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.property_type}</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.area_acre} Acre</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.distance_from_nearest_seaport} Kms From Seaport</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.distance_from_nearest_railway_station} Kms From Railway Line</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.distance_from_power_source} Kms From Power Plant</div></div>
                                                </div>
                                                <div className="right flex-1 text-start flex flex-col gap-3">
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">Rate Negotiation Option</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.road_connectivity} Kms From Road Connectivity</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaTimesCircle size={20} color="red" /></div><div className="text">Avaibility Of Local Transportaion</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.business_location_type}</div></div>
                                                    <div className="items flex gap-3"><div className="icon"><GoAlertFill size={20} color='red' /></div><div className="text">Easy Access To Unskilled Manpower</div></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="second-row flex flex-col py-5 gap-1">
                                        <div className="section-title text-start text-xl text-dodgerblue">Vendors & Suppliers Mapping</div>
                                        <div className="Content flex px-2 py-2 gap-2">
                                            <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.property_type}</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.area_acre} Acre</div></div>
                                                <div className="items flex gap-3"><div className="icon"><GoAlertFill size={20} color='yellow' /></div><div className="text">{solution.distance_from_nearest_seaport} Kms From Seaport</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.distance_from_nearest_railway_station} Kms From Railway Line</div></div>
                                            </div>
                                            <div className="right flex-1 text-start flex flex-col gap-3">
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">Rate Negotiation Option</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.road_connectivity} Kms From Road Connectivity</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaTimesCircle size={20} color="red" /></div><div className="text">Avaibility Of Local Transportaion</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.business_location_type}</div></div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="third-row flex flex-col pt-5">
                                        <div className="section-title text-start text-xl text-dodgerblue">Laws & Policies Mapping
                                        </div>
                                        <div className="Content flex px-2 py-2 gap-2">
                                            <div className="left flex flex-1 text-start flex-col gap-3 border-r border-black">
                                                <div className="items flex gap-3"><div className="icon"><GoAlertFill size={20} color='yellow' /></div><div className="text">{solution.property_type}</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.area_acre} Acre</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.distance_from_nearest_seaport} Kms From Seaport</div></div>
                                            </div>
                                            <div className="right flex-1 text-start flex flex-col gap-3">
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">Rate Negotiation Option</div></div>
                                                <div className="items flex gap-3"><div className="icon"><FaCheckCircle size={20} color="green" /></div><div className="text">{solution.road_connectivity} Kms From Road Connectivity</div></div>
                                                <div className="items flex gap-3"><div className="icon"><GoAlertFill size={20} color='red' /></div><div className="text">Avaibility Of Local Transportaion</div></div>
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
            </div>
        </div>
    )
}

export default Industryresult
