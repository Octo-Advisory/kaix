import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MdAirplanemodeActive, MdFactory } from 'react-icons/md';
import { createRoot } from 'react-dom/client';
import { SlEnergy } from "react-icons/sl"; // Substation
import { CiAirportSign1 } from "react-icons/ci"; // Airport
import { MdDirectionsRailwayFilled } from "react-icons/md"; // Railway station
import { RiShip2Line } from "react-icons/ri"; //seaport
import { FaRoad, FaXmark } from "react-icons/fa6";
import downimage from './assets/caretdown.svg';
import upimage from './assets/caretup.svg';
import checkIcon from './assets/check.png';
import { getDataForSingleLayer } from "./service/apiservice";
import { FaStore } from "react-icons/fa";
import { IoLayersOutline } from "react-icons/io5";
import Vendorresult from '../ResultScreens/Vendorresult';
import { IoMdHome } from "react-icons/io";
import { FaPlus } from "react-icons/fa";
import { FaMinus } from "react-icons/fa";
import { useFrappeGetDoc } from 'frappe-react-sdk';
import { getCurvedLine } from "./utils";
import { nanoid } from "nanoid";

const SingleMap = ({ selectedProperty, intension }) => {
  const copyiedSelectedProperty = structuredClone(selectedProperty);

  const lat = copyiedSelectedProperty?.latitude_longitude[0];
  const lng = copyiedSelectedProperty?.latitude_longitude[1];
  let boundaryCoordinates = copyiedSelectedProperty?.boundary_coordinates;

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isShowEVUpIcon,setShowEVUpIcon] = useState(false);
  const [isShowEVDownIcon,setShowEVDownIcon] = useState(true);
  const [isShowEVCC,setShowEVCC] = useState(false);
  const [isShowNEVUpIcon,setShowNEVUpIcon] = useState(false);
  const [isShowNEVDownIcon,setShowNEVDownIcon] = useState(true);
  const [isShowNEVCC,setShowNEVCC] = useState(false);
  const mapRef = useRef(null);
  const mapContainer = useRef(null);
  const [vendorsToSend, setVendorsToSend] = useState([]);
  const [isMapoptionVisible, setMapOptionVisible] = useState(true);
  const DIRECTIONS = {
    LEFT:- 0.4,
    RIGHT:0.4
  }

  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Mapping")
      const configurations = uiData?.configurations || [];
      const uiConfig = configurations.reduce((acc, curr) => {
        acc[curr.key] = curr.value;
        return acc;
      }, {});

  const { data: adminToken } = useFrappeGetDoc("Mars Configurations", "admin_token")
  const ADMIN_TOKEN = adminToken?.admin_token

  const LAYERS = {
    DEFAULT_LAYER: {
      LABEL: `${uiConfig?.['default_layers'] || 'Default Layers'}`,
      VENDOR: `${uiConfig?.['default_vendors'] || 'Default Vendors'}`,
      SUB_STATIONS: `${uiConfig?.['default_sub_stations'] || 'Default Sub Stations'}`,
      RAILWAY_STATIONS: `${uiConfig?.['default_railway_stations'] || 'Default Railway Stations'}`,
      AIRPORTS: `${uiConfig?.['default_airports'] || 'Default Airports'}`,
      SEAPORTS: `${uiConfig?.['default_seaports'] || 'Default Seaports'}`,
      HIGHWAY: `${uiConfig?.['default_highway'] || 'Default Highway'}`,
    },
    SUB_STATIONS: `${uiConfig?.['checkbox_sub_stations'] || 'Sub Stations'}`,
    RAILWAY_STATIONS: `${uiConfig?.['checkbox_railway_stations'] || 'Railway Stations'}`,
    AIRPORTS: `${uiConfig?.['checkbox_airports'] || 'Airports'}`,
    SEAPORTS: `${uiConfig?.['checkbox_seaports'] || 'Seaports'}`,
    HIGHWAY: `${uiConfig?.['checkbox_highway'] || 'Highway'}`,
    VENDOR: `${uiConfig?.['checkbox_all_vendors'] || 'All Vendors'}`,
    ESSENTIAL_VENDORS: `${uiConfig?.['checkbox_all_essential_vendors'] || 'All Essential Vendors'}`,
    NON_ESSENTIAL_VENDORS: `${uiConfig?.['checkbox_all_non_essential_vendors'] || 'All Non Essential Vendors'}`,
  }
  var allVendors = [];
  var nearestAirportDetail = null;
  var nearestSubstationDetail = null;
  var nearestSeaportDetail = null;
  var nearestRailwayStationDetail = null;
  var highwayCoord = null;
  var nearestHighwayDetail = null;
  const essentialVendors = useRef(null);
  useEffect(() => {
    if (!mapContainer.current || !lat || !lng || !uiData) return;
    mapboxgl.accessToken = `${uiConfig?.['mapmobx_api_token']}`;
    
    mapRef.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      // style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [lng, lat],
      zoom: 14,
      attributionControl: false,
    });

    return () => mapRef.current?.remove();
  }, [lat, lng,uiData]);

  useEffect(() => {
    if (!mapRef.current || !boundaryCoordinates || !uiData) return;

    const parsedBoundary =
      typeof boundaryCoordinates === 'string'
        ? JSON.parse(boundaryCoordinates)
        : boundaryCoordinates;

    if (!Array.isArray(parsedBoundary) || parsedBoundary.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();
    parsedBoundary.forEach((coord) => bounds.extend(coord));

    const sourceId = `boundary-${nanoid()}`;

    mapRef.current.on('load', () => {
      document.querySelector('.accordion-header').click();
      document.querySelectorAll('.accordion-header')[1].click();

      mapRef.current.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [parsedBoundary],
          },
        },
      });

      mapRef.current.addLayer({
        id: `fill-${sourceId}`,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': '#FF0000', // red fill
          'fill-opacity': 0.3,
        },
      });

      mapRef.current.addLayer({
        id: `border-${sourceId}`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#000000', // black border
          'line-width': 2,
        },
      });

      // Fit to bounds
      //  mapRef.current.fitBounds(bounds, { padding: 50 });

      // Custom Marker with MdFactory
      //#region Not in use
      const el = document.createElement('div');
      el.style.top = '12px';
      el.style.width = '40px';
      el.style.height = '40px';
      el.style.display = 'flex';
      el.style.alignItems = 'center';
      el.style.justifyContent = 'center';

      const root = createRoot(el);
      root.render(
        <div style={{
          background: 'white',
          borderRadius: '50%',
          padding: '4px',
          boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
        }}>
          <MdFactory size={24} color="#4A76D1" />
        </div>
      );
      //#endregion
      const marker = new mapboxgl.Marker({ anchor: 'bottom', color: '#ff0000' })
        .setLngLat([lng, lat])
        .addTo(mapRef.current);
      // Apply margin-top or transform
      marker.getElement().style.marginTop = '20px'; // for visual downward shift 
    });
  }, [boundaryCoordinates,uiData]);

  useEffect(() => {
    if (!mapRef.current || !uiData) return;
    const handleStyleLoad = () => {
      (async () => {
        await loadVendorlayer();
        resetZoomlevel();
      })();
    };
    mapRef.current.on('style.load', handleStyleLoad);
    // mapRef.current.on('style.load', () => {

    // });
    document.documentElement.style.setProperty(
      "--check-icon-url",
      `url(${checkIcon})`
    );
    // Get all checkboxes
    const allTrafficCheckbox = document.querySelectorAll(
      "[name='traffic-section'] [type='checkbox']"
    );

    // Define the handler once
    const handleCheckboxChange = (event) => {
      if (event.target.checked) {
        asyncLoadDataForSingleLayer(event.target.name);
      } else {
        // Handle uncheck if needed
        removeMarker(event.target.name);
      }
    };

    // Attach event listener
    allTrafficCheckbox.forEach((element) => {
      element.addEventListener("change", handleCheckboxChange);
    });

    // Cleanup function to remove listeners
    return () => {
      allTrafficCheckbox.forEach((element) => {
        element.removeEventListener("change", handleCheckboxChange);
      });
    };
  }, [uiData]);

  const addConnectivityLayer = (layer, coord, propertyCoord, detail,direction = {}) => {
    // Custom Marker with MdFactory
    const el = document.createElement('div');
    el.name = "marker_" + layer;
    el.style.top = '12px';
    el.style.width = '40px';
    el.style.height = '40px';
    el.style.display = 'flex';
    el.style.alignItems = 'center';
    el.style.justifyContent = 'center';
    el.setAttribute("data-name", "marker_" + layer)

    const root = createRoot(el);
    root.render(
      <div style={{
        background: 'white',
        borderRadius: '50%',
        padding: '4px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
      }}>
        {
          (layer === LAYERS.SUB_STATIONS || layer === LAYERS.DEFAULT_LAYER.SUB_STATIONS) ? <SlEnergy size={24} color="#5f2abb" /> :
            (layer === LAYERS.AIRPORTS || layer === LAYERS.DEFAULT_LAYER.AIRPORTS) ? <MdAirplanemodeActive size={24} color="#5f2abb" /> :
              (layer === LAYERS.SEAPORTS || layer === LAYERS.DEFAULT_LAYER.SEAPORTS) ? <RiShip2Line size={24} color="#5f2abb" /> :
                (layer === LAYERS.RAILWAY_STATIONS || layer === LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS) ? <MdDirectionsRailwayFilled size={24} color="#5f2abb" /> :
                  (layer === LAYERS.HIGHWAY || layer === LAYERS.DEFAULT_LAYER.HIGHWAY) ? <FaRoad size={24} color="#5f2abb" /> :
                    (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR) ? <FaStore size={24} color="#5b96d8" /> :
                      ""
        }


      </div>
    );

    const marker = new mapboxgl.Marker({ element: el, anchor: 'bottom' })
      .setLngLat(coord)
      .addTo(mapRef.current);
    let sourceId = 'line-string' + "_" + layer;
    let lineStringLayerId = 'line-string-layer' + "_" + layer;
    let name = "";
    if (detail != undefined && detail != null) {      
      switch (layer) {
        case LAYERS.DEFAULT_LAYER.SUB_STATIONS:
          name = detail.name+" Sub Station";
          break;
        case LAYERS.DEFAULT_LAYER.AIRPORTS:
          name = detail.title+" Airport";
          break;
        case LAYERS.DEFAULT_LAYER.SEAPORTS:
          name = detail.title+" Seaport";
          break;
        case LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS:
          name = detail.name1+" Railway Station";
          break;
        case LAYERS.DEFAULT_LAYER.HIGHWAY:
          name = detail.title;
          break;
        default:
          break;
      }
      if (name !== "") {
        addInfoPoupp(marker, name);
      }
    }
    // addSingleLineLayer(sourceId, lineStringLayerId, coord, propertyCoord, '#5f2abb');

    const distanceKm = getDistance([propertyCoord[0], propertyCoord[1]], [coord[0], coord[1]]).toFixed(2);
    const midpoint = getMidpointSimple(coord, propertyCoord);
    const labelText = name !== "" ? `${name} </br> ${distanceKm} km` :`${distanceKm} km`;
    generateCurveLine({ sourceId: sourceId, layerId: lineStringLayerId, from: coord, to: propertyCoord, linecolor: '#5f2abb', curvature: direction, labelText: labelText });
    // addDistanceLabel(midpoint, `${distanceKm} km`, "default-connectivity-distance-lable");
  }

  //#region Map Options related code
  const resetZoomlevel = async () => {
    // Calculate the bounding box from your coordinates
    const bounds = new mapboxgl.LngLatBounds();
    allVendors.forEach(item => {
      let coord = item.latitude_longitude.replace(" ", "").split(",").map(Number);
      coord = [coord[1], coord[0]]; // Ensure coordinates are in [lng, lat] format
      bounds.extend(coord);
    });

    // let propertyCoord = solution.latitude_longitude;
    // propertyCoord = [propertyCoord[1], propertyCoord[0]]; // Ensure coordinates are in [lng, lat] format
    bounds.extend([lng, lat]);

    if (
      nearestAirportDetail?.data?.length > 0 &&
      nearestAirportDetail.data[0].coordinates
    ) {
      let airportCoord = nearestAirportDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
      airportCoord = [airportCoord[1], airportCoord[0]]
      bounds.extend(airportCoord);
    }

    if (
      nearestSubstationDetail?.data?.length > 0 &&
      nearestSubstationDetail.data[0].coordinates
    ) {
      let substationCoord = nearestSubstationDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
      substationCoord = [substationCoord[1], substationCoord[0]]
      bounds.extend(substationCoord);
    }

    if (
      nearestSeaportDetail?.data?.length > 0 &&
      nearestSeaportDetail.data[0].coordinates
    ) {
      let seaportCoord = nearestSeaportDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
      seaportCoord = [seaportCoord[1], seaportCoord[0]]
      bounds.extend(seaportCoord);
    }

    if (nearestRailwayStationDetail?.data?.length > 0 &&
      nearestRailwayStationDetail.data[0].coordinates
    ) {
      let railwayCoord = nearestRailwayStationDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
      railwayCoord = [railwayCoord[1], railwayCoord[0]]
      bounds.extend(railwayCoord);
    }

    if (highwayCoord != null && highwayCoord != "") {
      highwayCoord = [highwayCoord[1], highwayCoord[0]]
      bounds.extend(highwayCoord);
    }

    // Fit the map to these bounds with some optional padding
    mapRef.current.fitBounds(bounds, {
      padding: 100,   // Adjusts space around the edges (optional)
      duration: 1000 // Optional: smooth animation
    });
  };
  const loadVendorlayer = async () => {

    let essentialVenorData = copyiedSelectedProperty.essential_vendors.slice(0, 5);
    // Group by vendor_name and join supply names
    const groupedEssentialVendorData = Object.values(
      essentialVenorData.reduce((acc, item) => {
        if (!acc[item.vendor_name]) {
          acc[item.vendor_name] = { vendor_name: item.vendor_name, supplies: [] };
        }
        acc[item.vendor_name].supplies.push(item.supply);
        return acc;
      }, {})
    ).map(vendor => ({
      vendor_name: vendor.vendor_name,
      supplies: vendor.supplies.join(', ')
    }));

    let nonessentialVenorData = copyiedSelectedProperty.nonessential_vendors.slice(0, 5);
    // Group by vendor_name and join supply names
    const groupedNonEssentialVendorData = Object.values(
      nonessentialVenorData.reduce((acc, item) => {
        if (!acc[item.vendor_name]) {
          acc[item.vendor_name] = { vendor_name: item.vendor_name, supplies: [] };
        }
        acc[item.vendor_name].supplies.push(item.supply);
        return acc;
      }, {})
    ).map(vendor => ({
      vendor_name: vendor.vendor_name,
      supplies: vendor.supplies.join(', ')
    }));
    
    const essentialVendorNames = Array.isArray(essentialVenorData) ? essentialVenorData.map(vendor => vendor.vendor_name) : [];
    const nonEssentialVendorNames = Array.isArray(groupedNonEssentialVendorData) ? groupedNonEssentialVendorData.map(vendor => vendor.vendor_name) : [];
    
    var finalEVData = await getVendors(JSON.stringify(essentialVendorNames));
    // var fi0nalNEVData = await getVendors(JSON.stringify(nonEssentialVendorNames));
    
    finalEVData.data.forEach((item) => {
      if (!item.vendor_name) return;
      
      var filteredItem = groupedEssentialVendorData.filter(
        (detail) => detail.vendor_name?.trim() === item.vendor_name.trim()
      );
      
      if(filteredItem.length<=0)
        return;
      
      // Join all supply names with commas if more than one match
      const supplyNames = filteredItem[0].supplies;     
      item.vendor_id = item.vendor_name;
      item.supplyName = supplyNames;
    });
    
    // finalNEVData.data.forEach((item) => {
    //   if (!item.vendor_name) return;
      
    //   var filteredItem = groupedNonEssentialVendorData.filter(
    //     (detail) => detail.vendor_name?.trim() === item.vendor_name.trim()
    //   );
      
    //   if(filteredItem.length<=0)
    //     return;
      
    //   // Join all supply names with commas if more than one match
    //   const supplyNames = filteredItem[0].supplies;     

    //   item.supplyName = supplyNames;
    // });
    essentialVendors.current = finalEVData.data;    
    // copyiedSelectedProperty.essential_vendors.forEach((item) => {
    //   if (!item.vendor_name || !item.supply) return;

    //   var filteredItem = copyiedSelectedProperty.essential_vendor_details.filter(
    //     (detail) => detail.name?.trim() === item.vendor_name.trim()
    //   );
    //   filteredItem.forEach((detail) => {
    //     if (typeof detail.supplyName !== 'undefined') {
    //       detail.supplyName = "";
    //     }
    //   });
    //   filteredItem.forEach((detail) => {
    //     if (!detail.supplyName) {
    //       detail.supplyName = item.supply;
    //     } else {
    //       detail.supplyName = `${detail.supplyName}, ${item.supply}`;
    //     }
    //   });
    // });


    // copyiedSelectedProperty.nonessential_vendors.forEach((item) => {
    //   if (!item.vendor_name || !item.supply) return; // skip if missing

    //   var filteredItem = copyiedSelectedProperty.non_essential_vendor_details.filter(
    //     (detail) => detail.name?.trim() === item.vendor_name.trim()
    //   );
    //   filteredItem.forEach((detail) => {
    //     if (typeof detail.supplyName !== 'undefined') {
    //       detail.supplyName = "";
    //     }
    //   });
    //   filteredItem.forEach((detail) => {
    //     if (!detail.supplyName) {
    //       detail.supplyName = item.supply;
    //     } else {
    //       detail.supplyName += ", " + item.supply;
    //     }
    //   });
    // });
    let data = [
      ...finalEVData.data,
      // ...finalNEVData.data
    ]
    
    // let data = [
    //   ...copyiedSelectedProperty.essential_vendor_details,
    //   ...copyiedSelectedProperty.non_essential_vendor_details
    // ];
    // selectedProperty.essential_vendor_details.forEach((item,index) => {
    //   item.supplyName = selectedProperty.essential_vendors[index].vendor_name;
    // });
    // selectedProperty.non_essential_vendor_details.forEach((item,index) => {

    // });
    if (data.length > 0) {
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          item.coordinates = item.latitude_longitude;
        }
      });
    }
    allVendors = structuredClone(data);
    bindDataOnMap(data, LAYERS.DEFAULT_LAYER.VENDOR);
    //document.querySelector('[name="' + LAYERS.VENDOR + '"]').checked = true; //Check the vendor layer checkbox by default
    document.querySelector('[name="' + LAYERS.DEFAULT_LAYER.LABEL + '"]').checked = true; //Check the vendor layer checkbox by default

    if (data.length > 0) {
      let count = 0;
      let direction = "right";
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          count++;
          let vendorSourceId = 'line-string_' + count + "_" + LAYERS.DEFAULT_LAYER.VENDOR;
          let vendorLayerId = "default-layer_" + LAYERS.DEFAULT_LAYER.VENDOR + "_" + count;
          let coord = item.latitude_longitude.replace(" ", "").split(",").map(Number);
          // addSingleLineLayer(vendorSourceId, vendorLineStringLayerId, [coord[1], coord[0]], [lng, lat], '#5b96d8');
          var [vendorLongitude, vendorLatitude] = item.coordinates.split(",").map(Number);
          const propertyLatitude = copyiedSelectedProperty?.latitude_longitude[0];
          const propertyLongitude = copyiedSelectedProperty?.latitude_longitude[1];
          const distanceKm = getDistance([propertyLongitude, propertyLatitude], [vendorLatitude, vendorLongitude]).toFixed(2);
          const labelText = `${item.supplyName} </br> ${distanceKm} km`;
          let curvedDirectionValue = null;
          if(direction == "right")
          {
            direction = "left";
            curvedDirectionValue = DIRECTIONS.LEFT;
          }            
          else
          {
            direction = "right";
            curvedDirectionValue = DIRECTIONS.RIGHT;
          }
            
          generateCurveLine({ sourceId: vendorSourceId, layerId: vendorLayerId, from: [coord[1], coord[0]], to: [lng, lat], linecolor: '#5b96d8', labelText: labelText,curvature:curvedDirectionValue });
        }
      });
    }

    //#region Add Connectivity Layers
    try {
      if (copyiedSelectedProperty.nearest_airport != null && copyiedSelectedProperty.nearest_airport != "") {
        // const airportCoord = copyiedSelectedProperty.nearest_airport_coord.replace(" ", "").split(",").map(Number);        
        nearestAirportDetail = await getDataForSingleLayer("Airport", { "name": copyiedSelectedProperty?.nearest_airport });
        if (nearestAirportDetail.data.length > 0) {
          const airportCoord = nearestAirportDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.AIRPORTS, [airportCoord[1], airportCoord[0]], [lng, lat], nearestAirportDetail.data[0],DIRECTIONS.LEFT);
        }

      }

      if (copyiedSelectedProperty.nearest_power_source != null && copyiedSelectedProperty.nearest_power_source != "") {
        nearestSubstationDetail = await getDataForSingleLayer("Substation", { "name": copyiedSelectedProperty?.nearest_power_source });
        if (nearestSubstationDetail.data.length > 0) {
          const substationCoord = nearestSubstationDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.SUB_STATIONS, [substationCoord[1], substationCoord[0]], [lng, lat], nearestSubstationDetail.data[0],DIRECTIONS.RIGHT);
        }
      }


      if (copyiedSelectedProperty.nearest_seaport != null && copyiedSelectedProperty.nearest_seaport != "") {
        nearestSeaportDetail = await getDataForSingleLayer("Seaport", { "name": copyiedSelectedProperty?.nearest_seaport });
        if (nearestSeaportDetail.data.length > 0) {
          const seaportCoord = nearestSeaportDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.SEAPORTS, [seaportCoord[1], seaportCoord[0]], [lng, lat], nearestSeaportDetail.data[0],DIRECTIONS.LEFT);
        }
      }


      if (copyiedSelectedProperty.nearest_railway_station != null && copyiedSelectedProperty.nearest_railway_station != "") {
        nearestRailwayStationDetail = await getDataForSingleLayer("Railway Station", { "name": copyiedSelectedProperty?.nearest_railway_station });
        if (nearestRailwayStationDetail.data.length > 0) {
          const railwayCoord = nearestRailwayStationDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS, [railwayCoord[1], railwayCoord[0]], [lng, lat], nearestRailwayStationDetail.data[0],DIRECTIONS.RIGHT);
        }
      }

      if (copyiedSelectedProperty.nearest_highway_coord != null && copyiedSelectedProperty.nearest_highway_coord != "") {
        highwayCoord = copyiedSelectedProperty.nearest_highway_coord.replace(" ", "").split(",").map(Number);
        nearestHighwayDetail = await getDataForSingleLayer("Highway", { "name": copyiedSelectedProperty?.nearest_highway });
        if (nearestHighwayDetail.data.length > 0) {          
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.HIGHWAY, [highwayCoord[1], highwayCoord[0]], [lng, lat],nearestHighwayDetail.data[0] ,DIRECTIONS.LEFT);
        }    
      }
    } catch (error) {
      // console.error("Error in adding marker:", error);
    }
    //#endregion
  }

  const addInfoPoupp = (marker, name) => {
    // Create a popup but don't add it yet
    const popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 25,
      className: 'vendor-popup' // Add a class for custom styling if needed
    }).setText(name);

    // Mouse enter event
    marker.getElement().addEventListener('mouseenter', () => {
      marker.setPopup(popup); // Attach the popup to the marker
      popup.addTo(mapRef.current); // Actually show the popup
      mapRef.current.getCanvas().style.cursor = 'pointer';
    });

    // Mouse leave event
    marker.getElement().addEventListener('mouseleave', () => {
      popup.remove(); // Remove the popup
      mapRef.current.getCanvas().style.cursor = '';
    });
  }

  const addDistanceLabel = (coord, text, id) => {
    const supplyNameEl = document.createElement('div');
    // supplyNameEl.style.background = 'rgba(0, 0, 0, 0.75)';
    // supplyNameEl.style.color = '#fff';
    // supplyNameEl.style.padding = '4px 8px';
    // supplyNameEl.style.borderRadius = '6px';
    // supplyNameEl.style.border = '2px solid grey';
    // supplyNameEl.style.fontSize = '12px';
    // supplyNameEl.style.fontWeight = 'bold';
    // supplyNameEl.style.zIndex=2;
    // supplyNameEl.setAttribute("data-name", "distance-label");
    // supplyNameEl.innerHTML = `${text}`;
    supplyNameEl.style.backgroundColor = '#ffffff';
    supplyNameEl.style.color = '#00000';
    // supplyNameEl.style.color = '#fff';
    supplyNameEl.style.padding = '4px 8px';
    supplyNameEl.style.borderRadius = '6px';
    supplyNameEl.style.fontSize = '10px';
    supplyNameEl.style.whiteSpace = 'nowrap';
    supplyNameEl.style.fontWeight = 'bold';
    supplyNameEl.setAttribute("data-name", "distance-label");
    supplyNameEl.innerHTML = `${text}`;
    supplyNameEl.style.border = '1px solid grey';
    supplyNameEl.style.zIndex = 2;

    new mapboxgl.Marker({
      element: supplyNameEl,
      anchor: 'center'
    })
      .setLngLat(coord)
      .addTo(mapRef.current);
  };

  const asyncLoadDataForSingleLayer = async (layerType) => {
    const layerMapping = {
      [LAYERS.SUB_STATIONS]: "Substation",
      [LAYERS.AIRPORTS]: "Airport",
      [LAYERS.SEAPORTS]: "Seaport",
      [LAYERS.RAILWAY_STATIONS]: "Railway Station"
    };
    if (layerType === LAYERS.DEFAULT_LAYER.LABEL) {
      loadVendorlayer();
    }
    else if (layerType === LAYERS.VENDOR) {
      let data = [
        ...copyiedSelectedProperty.essential_vendor_all_details,
        ...copyiedSelectedProperty.non_essential_vendor_all_details
      ];

      if (data.length > 0) {
        data.forEach((item) => {
          if (item.latitude_longitude != null && item.latitude_longitude != "") {
            item.coordinates = item.latitude_longitude;
          }
        });
      }
      bindDataOnMap(data, LAYERS.VENDOR);
    }
    else if (layerType === LAYERS.ESSENTIAL_VENDORS) {
      const filteredEssentialVendors = copyiedSelectedProperty.essential_vendor_all_details.filter(
          item2 => !essentialVendors.current.some(
            item1 => item1.vendor_name === item2.vendor_name
          )
        );
      let data = filteredEssentialVendors;

      if (data.length > 0) {
        data.forEach((item) => {
          if (item.latitude_longitude != null && item.latitude_longitude != "") {
            item.coordinates = item.latitude_longitude;
          }
        });
      }
      bindDataOnMap(data, LAYERS.ESSENTIAL_VENDORS);
    }
    else if (layerType === LAYERS.NON_ESSENTIAL_VENDORS) {
      let data = copyiedSelectedProperty.non_essential_vendor_all_details;

      if (data.length > 0) {
        data.forEach((item) => {
          if (item.latitude_longitude != null && item.latitude_longitude != "") {
            item.coordinates = item.latitude_longitude;
          }
        });
      }
      bindDataOnMap(data, LAYERS.NON_ESSENTIAL_VENDORS);
    }
    else {
      const docTypeName = layerMapping[layerType];
      if (!docTypeName) return;

      try {
        const res = await getDataForSingleLayer(docTypeName);
        bindDataOnMap(res.data, layerType);
      } catch (error) {
        // console.error(`Failed to load data for ${layerType}:`, error);
      }
    }

  };

  const removeMarker = (layerType) => {
    // let divs =  document.getElement("marker"+layerType);
    const element = document.querySelectorAll('[data-name="marker_' + layerType + '"]');
    element.forEach((div) => {
      div.remove();
    });
    if (layerType === LAYERS.DEFAULT_LAYER.LABEL) {
      let layerListToDelete = [
        LAYERS.DEFAULT_LAYER.VENDOR,
        LAYERS.DEFAULT_LAYER.SUB_STATIONS,
        LAYERS.DEFAULT_LAYER.AIRPORTS,
        LAYERS.DEFAULT_LAYER.SEAPORTS,
        LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS,
        LAYERS.DEFAULT_LAYER.HIGHWAY
      ]
      layerListToDelete.forEach(layerName => {
        const element = document.querySelectorAll('[data-name="marker_' + layerName + '"]');
        element.forEach((div) => {
          div.remove();
        });
      });
      //get the all layer from the map.
      const filteredLayers = mapRef.current
        .getStyle()
        .layers.filter((item) => item.id.includes("Default"));
      //remove layer as per layer id
      for (let item of filteredLayers) {
        mapRef.current.removeLayer(item.id);
      }
      //get all the layer source
      let sources = Object.entries(mapRef.current.getStyle().sources);
      const filteredSource = sources.filter(([key]) => key.includes("Default"));

      for (let [key, value] of filteredSource) {
        mapRef.current.removeSource(key);
      }

      //Remove all vendor distance divs
      let allVendorDiv = document.querySelectorAll('[data-name="vendor_distance"]');
      allVendorDiv.forEach((div) => {
        div.remove();
      });
      //remove all default connectivity distance lable divs
      let allDefaultConnectivityLabelDiv = document.querySelectorAll('[data-name="distance-label"]');
      allDefaultConnectivityLabelDiv.forEach((div) => {
        div.remove();
      });
    }
  }

  function getMidpointSimple(coord1, coord2) {
    const midLat = (coord1[0] + coord2[0]) / 2;
    const midLng = (coord1[1] + coord2[1]) / 2;
    return [midLat, midLng];
  }
  // function getDistance(p1, p2) {
  //   const dx = p2[0] - p1[0];
  //   const dy = p2[1] - p1[1];
  //   return Math.sqrt(dx * dx + dy * dy);
  // }

  function interpolate(p1, p2, t) {
    return [
      p1[0] + (p2[0] - p1[0]) * t,
      p1[1] + (p2[1] - p1[1]) * t
    ];
  }

  function getMidpointByLength(coords) {
    // Step 1: Calculate total length
    let totalLength = 0;
    const segments = [];

    for (let i = 0; i < coords.length - 1; i++) {
      const p1 = coords[i];
      const p2 = coords[i + 1];
      const segmentLength = getDistance(p1, p2);
      segments.push({ p1, p2, length: segmentLength });
      totalLength += segmentLength;
    }

    const halfLength = totalLength / 2;

    // Step 2: Walk until we reach the half-length
    let runningLength = 0;

    for (const { p1, p2, length } of segments) {
      if (runningLength + length >= halfLength) {
        const remaining = halfLength - runningLength;
        const t = remaining / length;
        return interpolate(p1, p2, t);
      }
      runningLength += length;
    }

    // Fallback: return last point
    return coords[coords.length - 1];
  }

  function getDistance(coord1, coord2) {
    const toRad = deg => deg * (Math.PI / 180);
    const R = 6371; // Earth's radius in km
    const dLat = toRad(coord2[1] - coord1[1]);
    const dLon = toRad(coord2[0] - coord1[0]);
    const lat1 = toRad(coord1[1]);
    const lat2 = toRad(coord2[1]);

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  const bindDataOnMap = async (resultData, layer, showVendorDetails = false) => {
    try {
      resultData.forEach(data => {
        if (data.coordinates != null && data.coordinates != "") {
          const storeIconEl = document.createElement('div');
          storeIconEl.style.top = '12px';
          storeIconEl.style.width = '40px';
          storeIconEl.style.height = '40px';
          storeIconEl.style.display = 'flex';
          storeIconEl.style.alignItems = 'center';
          storeIconEl.style.justifyContent = 'center';
          storeIconEl.name = "marker_" + layer;
          storeIconEl.setAttribute("data-name", "marker_" + layer)
          // Create a temporary container for React rendering
          const tempContainer = document.createElement('div');
          storeIconEl.appendChild(tempContainer);
          const root = createRoot(tempContainer);
          root.render(
            <div style={{
              background: 'white',
              borderRadius: '50%',
              padding: '4px',
              boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {
                (layer === LAYERS.SUB_STATIONS || layer === LAYERS.DEFAULT_LAYER.SUB_STATIONS) ? <SlEnergy size={20} color="#5f2abb" /> :
                  (layer === LAYERS.AIRPORTS || layer === LAYERS.DEFAULT_LAYER.AIRPORTS) ? <MdAirplanemodeActive size={20} color="#5f2abb" /> :
                    (layer === LAYERS.SEAPORTS || layer === LAYERS.DEFAULT_LAYER.SEAPORTS) ? <RiShip2Line size={20} color="#5f2abb" /> :
                      (layer === LAYERS.RAILWAY_STATIONS || layer === LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS) ? <MdDirectionsRailwayFilled size={20} color="#5f2abb" /> :
                        (layer === LAYERS.HIGHWAY || layer === LAYERS.DEFAULT_LAYER.HIGHWAY) ? <FaRoad size={20} color="#5f2abb" /> :
                          (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR) ? <FaStore size={20} color="#5b96d8" /> :
                          (layer === LAYERS.ESSENTIAL_VENDORS ) ? <FaStore size={20} color="#5b96d8" /> :
                          (layer === LAYERS.NON_ESSENTIAL_VENDORS ) ? <FaStore size={20} color="#5b96d8" /> :
                            <FaStore size={20} color="#5b96d8" />
              }

            </div>
          );
          data.coordinates = data.coordinates.replace(" ", "");
          const [lat, lng] = data.coordinates.split(",").map(Number);
          var [vendorLongitude, vendorLatitude] = data.coordinates.split(",").map(Number);
          const marker = new mapboxgl.Marker({
            element: storeIconEl,
            anchor: 'bottom' // This ensures the popup appears above the marker
          }).setLngLat([lng, lat])
            .addTo(mapRef.current);

          //If All vendor or Defualt layer is selected
          if (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR || layer === LAYERS.ESSENTIAL_VENDORS || layer === LAYERS.NON_ESSENTIAL_VENDORS || showVendorDetails) {
            //Show label on the marker            
            addInfoPoupp(marker, data.name);

            //clicking on the vendor marker a vendor detail modal will open
            marker.getElement().addEventListener('click', () => {
              //Display the modal with vendor details
              setIsModalOpen(true);
              //set the vendor detail
              setVendorsToSend(data);
            });
            //If default layer is selected
            if (layer === LAYERS.DEFAULT_LAYER.VENDOR) {
              // const propertyLatitude = copyiedSelectedProperty?.latitude_longitude[0];
              // const propertyLongitude = copyiedSelectedProperty?.latitude_longitude[1];
              // // Add Distance Label at Midpoint
              // const midpoint = getMidpointSimple([vendorLongitude, vendorLatitude], [propertyLatitude, propertyLongitude]);
              // const distanceKm = getDistance([propertyLongitude, propertyLatitude], [vendorLatitude, vendorLongitude]).toFixed(2);
              // const supplyNameMidpoint = getMidpointSimple(midpoint, [vendorLongitude, vendorLatitude]);

              // const supplyNameEl = document.createElement('div');
              // supplyNameEl.style.background = 'rgba(0, 0, 0, 0.75)';
              // supplyNameEl.style.color = '#fff';
              // supplyNameEl.style.padding = '4px 8px';
              // supplyNameEl.style.borderRadius = '6px';
              // supplyNameEl.style.fontSize = '12px';
              // supplyNameEl.style.fontWeight = 'bold';
              // supplyNameEl.setAttribute("data-name", "vendor_distance");
              // supplyNameEl.innerHTML = `${data.supplyName} </br> ${distanceKm} km`;

              // new mapboxgl.Marker({
              //   element: supplyNameEl,
              //   anchor: 'center'
              // })
              //   .setLngLat([supplyNameMidpoint[1], supplyNameMidpoint[0]])
              //   .addTo(mapRef.current);
            }

          }
          if (layer != LAYERS.DEFAULT_LAYER.LABEL) {
            let name = "";
            switch (layer) {
              case LAYERS.SUB_STATIONS:
                name = data.name;
                break;
              case LAYERS.AIRPORTS:
                name = data.title;
                break;
              case LAYERS.SEAPORTS:
                name = data.title;
                break;
              case LAYERS.RAILWAY_STATIONS:
                name = data.name1;
                break;
              case LAYERS.ESSENTIAL_VENDORS:
                name = data.vendor_name;
                break; 
              case LAYERS.NON_ESSENTIAL_VENDORS:
                name = data.vendor_name;
                break;
              default:
                name = data.vendor_name;
                break;
            }
            if (name !== "") {
              addInfoPoupp(marker, name);
            }
          }
        }
        else {
          // console.error("Invalid coordinate " + item.coordinates + " for vendor " + data.name)
        }
      });
    } catch (error) {
      // console.error("Error in bindDataOnMap:", error);
    }

  }

  const addSingleLineLayer = (sourceId, layerId, from, to, linecolor) => {
    mapRef.current.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            from,
            to
          ]
        },
        properties: {}
      }
    });
    mapRef.current.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': linecolor,
        'line-width': 2
      }
    });
  }

  const toggleAccordion = (element) => {
    //save element reference
    const elementRef = element.currentTarget ? element.currentTarget : element;

    //handle toggle actions for whole map option box
    const allContent = document.querySelectorAll(
      ".accordion-sub-item .accordion-content"
    );
    //show content
    const upIcons = document.querySelectorAll(
      '.accordion-sub-item [name="upicon"]'
    );
    //hide content
    const downIcons = document.querySelectorAll(
      '.accordion-sub-item [name="downicon"]'
    );

    //add remove classes for show/hide sections
    upIcons.forEach((content, index) => {
      content.classList.add("hide");
      content.classList.remove("show");
    });
    downIcons.forEach((content, index) => {
      content.classList.add("show");
      content.classList.remove("hide");
    });
    // Close all sections and reset their icons
    allContent.forEach((content, index) => {
      if (content !== elementRef.nextElementSibling) {
        content.style.display = "none";
      }
    });

    // Toggle the clicked section
    const content = elementRef.nextElementSibling;
    const icon = elementRef.querySelector("span.icon");
    //if section is visible then make it hidden
    if (content.style.display === "block") {
      content.style.display = "none";
      icon.children[1].classList.add("show");
      icon.children[1].classList.remove("hide");
      icon.children[0].classList.add("hide");
      icon.children[0].classList.remove("show");
    }
    //if section is hidden then make it visible 
    else {
      content.style.display = "block";
      icon.children[0].classList.add("show");
      icon.children[0].classList.remove("hide");
      icon.children[1].classList.add("hide");
      icon.children[1].classList.remove("show");
    }

  }

  //Handle All action  
  const handleAllClick = (sectionName, isForCheck) => {
    if (sectionName === "traffic-section") {
      // Get all checkboxes
      const allTrafficCheckbox = document.querySelectorAll(
        "[name='traffic-section'] [type='checkbox']"
      );
      allTrafficCheckbox.forEach((element) => {
        if (isForCheck) {
          element.checked = true;
          asyncLoadDataForSingleLayer(element.name);
        }
        else {
          element.checked = false;
          removeMarker(element.name);
        }
      });
    }
  }

  const handleVendorCheckboxClick = (event, vendorType, isFallAllVendor) => {
  const { checked, name } = event.target;

  const getVendorData = (type) => {
    if (type === LAYERS.ESSENTIAL_VENDORS)
      return {
        main: copyiedSelectedProperty.essential_vendor_all_details,
        supplies: copyiedSelectedProperty.essential_vendors
      };
    if (type === LAYERS.NON_ESSENTIAL_VENDORS)
      return {
        main: copyiedSelectedProperty.non_essential_vendor_all_details,
        supplies: copyiedSelectedProperty.nonessential_vendors
      };
    return { main: [], supplies: [] };
  };

  // 🔹 Handle "Select All Vendors"
  if (isFallAllVendor) {
    const { main, supplies } = getVendorData(name);
    const supplyNames = Array.isArray(supplies)
      ? supplies.map(v => v.supply)
      : [];

    supplyNames.forEach(supplyName => {
      const checkboxes = document.querySelectorAll(
        `[name='${supplyName}'][type='checkbox']`
      );

      if (checked) {
        // Filter and bind matching vendors
        const filteredVendors = main
          .filter(v => v.best_supply?.includes(supplyName))
          .map(v => ({
            ...v,
            coordinates:
              v.latitude_longitude?.trim() || v.coordinates || ""
          }));

        if (filteredVendors.length > 0) {
          bindDataOnMap(filteredVendors, supplyName, true);
        }

        // ✅ Check all matching checkboxes
        checkboxes.forEach(cb => (cb.checked = true));
      } else {
        // ❌ Remove markers and uncheck
        removeMarker(supplyName);
        checkboxes.forEach(cb => (cb.checked = false));
      }
    });
  }

  // 🔹 Handle single checkbox (non-"All Vendors")
  else {
    if (checked) {
      loadSelectedSupplyVendorDetails(name, vendorType);
    } else {
      removeMarker(name);
    }
  }
};


  const loadSelectedSupplyVendorDetails = (supply,vendorType) =>{    
    let data = vendorType == LAYERS.ESSENTIAL_VENDORS ? copyiedSelectedProperty.essential_vendor_all_details : copyiedSelectedProperty.non_essential_vendor_all_details;
    
    // Filter vendors where best_supply includes 'Nylon'
    const filteredVendors = data.filter(vendor =>
      vendor.best_supply?.includes(supply)
    );
    if (filteredVendors.length > 0) {
        filteredVendors.forEach((item) => {
          if (item.latitude_longitude != null && item.latitude_longitude != "") {
            item.coordinates = item.latitude_longitude;
          }
        });
      }
    bindDataOnMap(filteredVendors, supply, true);
  }

  //Sets the default map location
  const setDefaultMapPosition = () => {
    // Fly the map to the default location
    mapRef.current.flyTo({
      //center: "", //fetches default coordinates
      essential: true, // this animation is considered essential with respect to prefers-reduced-motion
      zoom: 4, //sets default zoom level
    });
  };
  //zoom in the map
  const zoomInMap = () => {
    //get current zoom level
    let currentZoom = mapRef.current.getZoom();
    //increases zoom level by 0.5
    let newZoom = currentZoom + 0.5;
    //sets zoom level
    mapRef.current.zoomTo(newZoom);
  };

  //zoom out the map
  const zoomOutMap = () => {
    //get current zoom level
    let currentZoom = mapRef.current.getZoom();
    //zoom out form current zoom level
    let newZoom = currentZoom === 0 ? currentZoom : currentZoom - 0.5;
    //sets zoom level
    mapRef.current.zoomTo(newZoom);
  };

  const generateCurveLine = ({ sourceId = "", layerId = "", from = "", to = "", linecolor = "", curvature = 0.4, labelText = "" } = {}) => {
    let getCurvedLineCoord = getCurvedLine(from, to, curvature);
    getCurvedLineCoord.push(to);
    mapRef.current.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: getCurvedLineCoord,
        }
      }
    });

    mapRef.current.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      paint: {
        'line-color': linecolor,
        'line-width': 1.5,
        // 'line-dasharray': [1, 1] // very short "dot", longer gap
      }
    });

    if (labelText != "") {
      let midPoinnt = getMidpointByLength(getCurvedLineCoord);
      addDistanceLabel(midPoinnt, labelText, layerId + " lable");

    }
  }
  //#endregion

  //#region Helper Methods
    const getVendors = async (filters) => {
    try {
      const response = await fetch(`/api/resource/Vendor?fields=["*"]&limit=1000&filters=[["name","in",`+filters+`]]`, {
        method: 'GET',
        headers: {
          'Authorization': `token ${ADMIN_TOKEN}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`Error: ${response.statusText}`);
      const data = await response.json();
      return data
    } catch (error) {
      // console.error('Error fetching data:', error);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching Area Name ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
      setSomeError(true)
    }
  }
  //#endregion
  return (
    <div className="relative h-screen w-screen flex items-center justify-center">
      <div
        ref={mapContainer}
        style={{ width: '100%', height: '100%', borderRadius: '12px' }}
      />
      {isModalOpen && (
        <Modal intension={intension} onClose={() => { setIsModalOpen(false); setMapOptionVisible(true); }}>
          <Vendorresult result={vendorsToSend} source="MapComponent" />
        </Modal>
        // <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
        //   <div className='absolute top-[40px] right-[66px] h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setIsModalOpen(false); setMapOptionVisible(true);  }}>
        //     <FaXmark size={28} />
        //   </div>

        //   <div>
        //     <Vendorresult result={vendorsToSend} source="MapComponent" />
        //   </div>

        // </div>
      )}
      {isMapoptionVisible && (<div id="map-ui">
        <div>
          <div className={`map-overlay top ${intension === "From Vendor Screen" ? "top-14-p" : ""}`}>
            <div className="map-overlay-inner">
              <div className="accordion">
                <div className="accordion-item">
                  <div
                    className="accordion-header"
                    onClick={(e) => toggleAccordion(e)}
                  >
                    <span className="text-lg font-bold text-green-600">
                      Map Options
                    </span>
                    <span className="icon">
                      <img
                        src={upimage}
                        margin={10}
                        name="upicon"
                        className="hide"
                        alt="Icon"
                      />
                      <img

                        src={downimage}
                        alt="Icon"
                        name="downicon"
                      />
                    </span>
                    <div></div>
                  </div>

                  <div className="accordion-content">
                    <div className="accordion-sub-item">
                      <div
                        className="accordion-header"
                        onClick={(e) => toggleAccordion(e)}
                      >
                        <span className="text-base font-semibold text-green-600">
                          Basic Layers
                        </span>
                        <br />

                        <span className="icon">
                          <img
                            src={upimage}
                            margin={10}
                            name="upicon"
                            className="hide"
                            alt="Icon"
                          />
                          <img
                            src={downimage}
                            alt="Icon"
                            name="downicon"
                          />
                        </span>
                      </div>
                      <div className="accordion-content">
                        <div className="select-options">
                          <span
                            className="cursor-pointer text-base tracking-wide font-medium text-green-600"
                            onClick={() =>
                              handleAllClick("traffic-section", true)
                            }
                          >
                            Select all
                          </span>{" "}
                          |{" "}
                          <span
                            className="cursor-pointer text-base tracking-wide font-medium text-green-600"
                            onClick={() =>
                              handleAllClick("traffic-section", false)
                            }
                          >
                            Clear all
                          </span>
                          {/* <a href="#">Select: All</a> | <a href="#">None</a> */}
                        </div>
                        <ul name="traffic-section">
                          <li className="li-container">
                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.DEFAULT_LAYER.LABEL}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <IoLayersOutline size={20} className="text-[#5f2abb]" />
                              </span>
                              <span className="text-sm font-medium">
                                {LAYERS.DEFAULT_LAYER.LABEL}
                              </span>
                            </label>
                          </li>
                          <li className="li-container">

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.SUB_STATIONS}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <SlEnergy size={20} className="text-[#5f2abb]" />
                              </span>
                            
                              <span className="text-sm font-medium">
                                {LAYERS.SUB_STATIONS}
                              </span>
                            </label>
                          </li>
                          <li className="li-container">

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.AIRPORTS}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <MdAirplanemodeActive size={20} className="text-[#5f2abb]" />
                              </span>
                            
                              <span className="text-sm font-medium">
                                {LAYERS.AIRPORTS}
                              </span>
                            </label>
                          </li>
                          <li className="li-container">

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.SEAPORTS}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <RiShip2Line size={20} className="text-[#5f2abb]" />
                              </span>
                            
                              <span className="text-sm font-medium">
                                {LAYERS.SEAPORTS}
                              </span>
                            </label>
                          </li>
                          <li className="li-container">

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.RAILWAY_STATIONS}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <MdDirectionsRailwayFilled size={20} className="text-[#5f2abb]" />
                              </span>
                            
                              <span className="text-sm font-medium">
                                {LAYERS.RAILWAY_STATIONS}
                              </span>
                            </label>
                          </li>
                          {/* <li className="li-container">

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.VENDOR}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <FaStore size={20} className="text-[#5f2abb]" />
                              </span>
                              <span className="text-sm font-medium">
                                {LAYERS.VENDOR}
                              </span>
                            </label>
                          </li> */}
                          </ul>
                          <ul>
                          <li className="li-container">
                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.ESSENTIAL_VENDORS}
                                onChange={(e) => handleVendorCheckboxClick(e,LAYERS.ESSENTIAL_VENDORS,true)}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <FaStore size={20} className="text-[#5f2abb]" />
                              </span>
                              <span className="text-sm font-medium">
                                {LAYERS.ESSENTIAL_VENDORS}
                              </span>
                            </label>
                            <span className="icon">
                              {isShowEVUpIcon && (
                                <img
                                  src={upimage}
                                  margin={10}
                                  id="essential-vendor-upicon"
                                  style={{
                                    position: 'relative',
                                    width: '25px',
                                    height: '25px',
                                    cursor: 'pointer',
                                  }}
                                  
                                  alt="Icon"
                                  onClick={() => {
                                    setShowEVDownIcon(true);
                                    setShowEVUpIcon(false);
                                    setShowEVCC(false);
                                  }}
                                />
                              )}

                              {isShowEVDownIcon && (
                                <img
                                  src={downimage}
                                  style={{
                                    position: 'relative',
                                    width: '25px',
                                    height: '25px',
                                    cursor: 'pointer',
                                  }}
                                  alt="Icon"
                                  id="essential-vendor-downicon"
                                  onClick={() => {
                                    setShowEVDownIcon(false);
                                    setShowEVUpIcon(true);
                                    setShowEVCC(true);
                                  }}
                                />
                              )}
                            </span>

                          </li>
                            <li style={{overflowY:'scroll',maxHeight:'140px', display:isShowEVCC?'block':'none'}} id='essential-vendor-checkbox-constainer'>
                            {selectedProperty.essential_vendors.map((vendor, index) => (
                              <li className="li-container" style={{paddingLeft:'25px'}}>
                                <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                                  <input
                                    type="checkbox"
                                    name={vendor.supply}
                                    onChange={(e) => handleVendorCheckboxClick(e,LAYERS.ESSENTIAL_VENDORS,false)}
                                  />
                                  <span className="checkmark"></span>
                                  <span>
                                    <FaStore size={20} className="text-[#5f2abb]" />
                                  </span>
                                  <span className="text-sm font-medium">
                                    {vendor.supply}
                                  </span>
                                </label>
                              </li>
                                  ))}
                          </li>
                          <li className="li-container">

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.NON_ESSENTIAL_VENDORS}
                                onChange={(e) => handleVendorCheckboxClick(e,LAYERS.NON_ESSENTIAL_VENDORS,true)}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <FaStore size={20} className="text-[#5f2abb]" />
                              </span>
                              <span className="text-sm font-medium">
                                {LAYERS.NON_ESSENTIAL_VENDORS}
                              </span>
                            </label>
                            <span className="icon">
                              {isShowNEVUpIcon && (
                                <img
                                  src={upimage}
                                  margin={10}
                                  id="essential-vendor-upicon"
                                  style={{
                                    position: 'relative',
                                    width: '25px',
                                    height: '25px',
                                    cursor: 'pointer',
                                  }}
                                  
                                  alt="Icon"
                                  onClick={() => {
                                    setShowNEVDownIcon(true);
                                    setShowNEVUpIcon(false);
                                    setShowNEVCC(false);
                                  }}
                                />
                              )}

                              {isShowNEVDownIcon && (
                                <img
                                  src={downimage}
                                  style={{
                                    position: 'relative',
                                    width: '25px',
                                    height: '25px',
                                    cursor: 'pointer',
                                  }}
                                  alt="Icon"
                                  id="essential-vendor-downicon"
                                  onClick={() => {
                                    setShowNEVDownIcon(false);
                                    setShowNEVUpIcon(true);
                                    setShowNEVCC(true);
                                  }}
                                />
                              )}
                            </span>
                          </li>
                            <li style={{overflowY:'scroll',maxHeight:'140px', display:isShowNEVCC?'block':'none'}}>
                            {selectedProperty.nonessential_vendors.map((vendor, index) => (
                              <li className="li-container" style={{paddingLeft:'25px'}}>
                                <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                                  <input
                                    type="checkbox"
                                    name={vendor.supply}
                                    onChange={(e) => handleVendorCheckboxClick(e,LAYERS.NON_ESSENTIAL_VENDORS,false)}
                                  />
                                  <span className="checkmark"></span>
                                  <span>
                                    <FaStore size={20} className="text-[#5f2abb]" />
                                  </span>
                                  <span className="text-sm font-medium">
                                    {vendor.supply}
                                  </span>
                                </label>
                              </li>
                                  ))}
                          </li>                          
                        </ul>
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className={`location-btn-container ${intension === "From Vendor Screen" ? "bottom-12" : ""}`}>
            <div id="zoomBtn" className="right-bottom-buttons">
              <span className="save-btn flex-d-column zoom-btn">
                <FaPlus
                  size={13}
                  onClick={() => zoomInMap()}
                />
                <IoMdHome
                  size={16}
                  onClick={() => setDefaultMapPosition()}
                />
                <FaMinus
                  size={13}
                  onClick={() => zoomOutMap()}
                />
              </span>

            </div>

          </div>
        </div>
      </div>)}

    </div>
  );
};

export default SingleMap;

const Modal = ({ intension, children, onClose }) => {
  return (
    <div className="fixed top-0 h-full w-full flex gap-4 items-center z-[12]">
      <div className={`${intension === "From Vendor Screen" ? "top-25 r-45" : "top-50 r-50"} absolute  z-[335] cursor-pointer h-8 w-8 rounded-full bg-white shadow-md flex items-center justify-center`} onClick={onClose}>
        <FaXmark size={20} />
      </div>
      <div className={`modal-content relative h-full w-full flex items-center justify-center `}>
        {children}
      </div>
    </div>
  );
};