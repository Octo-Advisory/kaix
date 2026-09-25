import mapboxgl from "mapbox-gl";
import React, { useEffect, useRef, useState } from "react";
import './style.css'
import { useSelector } from 'react-redux';
import 'leaflet/dist/leaflet.css';
import markerImage from '../../assets/markerImage.png'
import Property from "../Property/Property";
import Vendorcards from "../ResultScreens/Vendorcards";
import IndustryResultScreen from "../ResultScreens/IndustryResultScreen";
import Vendorresult from "../ResultScreens/Vendorresult";
import { FaRoad, FaXmark } from "react-icons/fa6";
import { FaStore, FaTimes } from "react-icons/fa";
import { createRoot } from 'react-dom/client';
import downimage from './assets/caretdown.svg';
import upimage from './assets/caretup.svg';
import checkIcon from './assets/check.png';
import { SlEnergy } from "react-icons/sl"; // Substation
import { CiAirportSign1 } from "react-icons/ci"; // Airport
import { MdDirectionsRailwayFilled } from "react-icons/md"; // Railway station
import { RiShip2Line } from "react-icons/ri"; //seaport
import { getDataForSingleLayer } from "./service/apiservice";
import { IoLayersOutline } from "react-icons/io5";
import { getMidpointSimple, getDistance, getMidpointByLength, getCurvedLine } from "./utils";
import { IoMdHome } from "react-icons/io";
import { FaPlus } from "react-icons/fa";
import { FaMinus } from "react-icons/fa";
import { MdAirplanemodeActive } from "react-icons/md";
import { use } from "react";
import { useFrappeGetDoc } from "frappe-react-sdk";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { HiOutlineBolt, HiOutlineMap } from "react-icons/hi2";
import { nanoid } from "nanoid";

function MapComponent({ solutions, toggleModal, source, intension }) {
  //var copyiedSelectedProperty = null;
  var allVendors = [];
  var nearestAirportDetail = null;
  var nearestSubstationDetail = null;
  var nearestSeaportDetail = null;
  var nearestRailwayStationDetail = null;
  var highwayCoord = null;
  var nearestHighwayDetail = null;

  const validation_result = useSelector((state) => state.validate.validation_result)
  let propertyCoord = validation_result?.[0]?.[1]?.latitude_longitude?.split(",").map(Number).reverse() ?? null;
  const [solution, setSolution] = useState({})
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMapoptionVisible, setMapOptionVisible] = useState(true);
  const [isConfirmationModalOpen, setIsConfirmationModalOpen] = useState(false);
  const essentialVendors = useRef(null);
  const latLongArray = Object.values(solutions).map(item => [...item.latitude_longitude].reverse());

  var map = null;
  const mapContainerRef = useRef(null); // Create a ref for the map container
  const mapRef = useRef(null); // Store map instance
  const copyiedSelectedProperty = useRef(null); // Store the real solution object

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

  const DIRECTIONS = {
    LEFT: - 0.4,
    RIGHT: 0.4
  }
  const [isShowEVUpIcon,setShowEVUpIcon] = useState(false);
  const [isShowEVDownIcon,setShowEVDownIcon] = useState(true);
  const [isShowEVCC,setShowEVCC] = useState(false);
  const [isShowNEVUpIcon,setShowNEVUpIcon] = useState(false);
  const [isShowNEVDownIcon,setShowNEVDownIcon] = useState(true);
  const [isShowNEVCC,setShowNEVCC] = useState(false);
  useEffect(() => {
    if (!uiData) return;
    mapboxgl.accessToken = `${uiConfig?.['mapmobx_api_token']}`;
    // Initialize the map after the component mounts
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current, // Use the ref to attach the map
      style: "mapbox://styles/mapbox/streets-v12", // Map style URL
      center: [73.133661788180035, 22.308428225686328], // Starting position [lng, lat]
      zoom: 14, // Starting zoom
      attributionControl: false,
    });

    map = mapRef.current; // Assign the map instance to the variable
    mapRef.current.on('style.load', () => {
      draw();
      document.querySelector('.accordion-header').click();
      document.querySelectorAll('.accordion-header')[1].click();
    });
    return () => mapRef.current.remove(); // Cleanup the map instance on unmount
  }, [uiData]); // Empty dependency array to run only once

  // Function to validate latitude and longitude
  function isValidLatLng(coord) {
    return (
      Array.isArray(coord) &&
      coord.length === 2 &&
      typeof coord[0] === 'number' &&
      typeof coord[1] === 'number' &&
      coord[1] >= -90 && coord[1] <= 90 && // Latitude range
      coord[0] >= -180 && coord[0] <= 180  // Longitude range
    );
  }
  // Add this distance calculation function at the top of your file
  function calculateDistance(coord1, coord2) {
    const R = 6371; // Radius of the Earth in km
    const dLat = (coord2[1] - coord1[1]) * Math.PI / 180;
    const dLon = (coord2[0] - coord1[0]) * Math.PI / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(coord1[1] * Math.PI / 180) * Math.cos(coord2[1] * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  const draw = async () => {
    // Filter out invalid coordinates
    const validCoordinates = latLongArray.filter(isValidLatLng);
    const coordinates = validCoordinates;

    // Get the bounding box
    const bounds = coordinates.reduce(
      (bounds, coord) => bounds.extend(coord),
      new mapboxgl.LngLatBounds(coordinates[0], coordinates[0])
    );

    let elements = coordinates.map(item => {
      let id = item[0].toString() + item[1].toString();
      let coordinates = item;
      item = [];
      item.id = id;
      item.coordinates = coordinates;
      return item;
    });
    // Fit the map to the bounds
    mapRef.current.fitBounds(bounds, {
      padding: 200,    // Adds padding around the points
      // maxZoom: 10,    // Prevents zooming in too much
      duration: 1000  // Animation duration in milliseconds
    });

    // Draw polygons for Industry_Result
    //This logic is for All property listing directly from the solutions screen
    const hasPropertyResult = solutions.some(item => item.result_type === "Industry_Result");
    if (hasPropertyResult) {
      solutions.forEach(item => {
        if (item.result_type === "Industry_Result") {
          //#region Draw boundry for properties
          let parsedCoord = JSON.parse(item.boundary_coordinates);
          let sourceId = `Custom_Source_${nanoid()}`;

          mapRef.current.addSource(sourceId, {
            type: "geojson",
            data: {
              type: "Feature",
              properties: {},
              geometry: {
                type: "Polygon",
                coordinates: [parsedCoord],
              },
            },
          });

          let layerId1 = `Custom_polygon_fill_${nanoid()}`;
          let layerId2 = `Custom_polygon_border_${nanoid()}`;

          mapRef.current.addLayer({
            id: layerId1,
            type: "fill",
            source: sourceId,
            layout: {},
            paint: {
              "fill-color": "#ff0000",
              "fill-opacity": 0.5,
            },
          });

          mapRef.current.addLayer({
            id: layerId2,
            type: "line",
            source: sourceId,
            layout: {},
            paint: {
              "line-color": "#000000",
              "line-width": 2,
            },
          });
          //#endregion

        }
      });
    }


    //#region Draw connected lines with distance labels
    const hasVendorResult = solutions.some(item => item.result_type === "Vendor");

    if (hasVendorResult) {
      //if propertyCoord is not available, then it means it is for all vendor results
      if (!propertyCoord) {
        let some = source === 'SolutionScreen' ? solutions : ''
        propertyCoord = some
          .filter(item => Array.isArray(item?.user_lat_long) && item.user_lat_long.length > 0)
          .map(item => {
            if (typeof item.user_lat_long[0] === 'string' && item.user_lat_long[0].includes(',')) {
              const [lat, lng] = item.user_lat_long[0].split(",").map(Number);
              return [lng, lat];
            } else if (Array.isArray(item.user_lat_long) && item.user_lat_long.length === 2) {
              return item.user_lat_long.slice().reverse();
            }
            return null;
          })
          .filter(Boolean);
        propertyCoord = propertyCoord[0];
      }

      // Add Property Marker - Simple red marker
      new mapboxgl.Marker({ color: '#ff0000' })
        .setLngLat(propertyCoord)
        .addTo(mapRef.current);

      // Generate LineString Features

      let count = 1;
      let direction = "right";
      latLongArray.forEach(vendorCoord => {
        if (!isValidLatLng(vendorCoord)) return; // Skip invalid coordinates
        let sourceId = 'property-vendor-lines-' + count;
        let layerId = `Custom_property_vendor_lines_layer_${nanoid()}`;
        let curvedDirectionValue = null;
        if (direction == "right") {
          direction = "left";
          curvedDirectionValue = DIRECTIONS.LEFT;
        }
        else {
          direction = "right";
          curvedDirectionValue = DIRECTIONS.RIGHT;
        }
        const distanceKm = getDistance(propertyCoord, vendorCoord).toFixed(2);
        const labelText = `${distanceKm} km`;
        // Generate curved line coordinates
        generateCurveLine({ from: propertyCoord, to: vendorCoord, layerId: layerId, sourceId: sourceId, curvature: curvedDirectionValue, linecolor: '#5b96d8', labelText: labelText });
        count++;
      });

      let vendorArrayForFitBounds = structuredClone(latLongArray); // clone vendory array
      vendorArrayForFitBounds.push(propertyCoord); //push property coordinates to the vendor array for fit bounds
      // Get the bounding box
      const bounds = vendorArrayForFitBounds.reduce(
        (bounds, coord) => bounds.extend(coord),
        new mapboxgl.LngLatBounds(coordinates[0], coordinates[0])
      );
      // Fit the map to the bounds
      mapRef.current.fitBounds(bounds, {
        padding: 150,    // Adds padding around the points
        // maxZoom: 10,    // Prevents zooming in too much
        duration: 1000  // Animation duration in milliseconds
      });

      // const lines = latLongArray.map(vendorCoord => ({
      //   type: 'Feature',
      //   geometry: {
      //     type: 'LineString',
      //     coordinates: [propertyCoord, vendorCoord]
      //   },
      //   properties: {}
      // }));

      // mapRef.current.addSource('property-vendor-lines', {
      //   type: 'geojson',
      //   data: {
      //     type: 'FeatureCollection',
      //     features: lines
      //   },
      //   lineMetrics: true
      // });

      // mapRef.current.addLayer({
      //   id: layerId,
      //   type: 'line',
      //   source: 'property-vendor-lines',
      //   layout: {
      //     'line-join': 'round',
      //     'line-cap': 'round'
      //   },
      //   paint: {
      //     'line-width': 3,
      //     'line-opacity': 0.9,
      //     'line-gradient': [
      //       'interpolate',
      //       ['linear'],
      //       ['line-progress'],
      //       0, '#0e2044',
      //       1, '#41b655'
      //     ]
      //   }
      // });

      // Removed distance labels code here
    }

    //#region Add markers to map - Modified for vendors/properties
    await addPointersToMap(elements, nanoid());

    //#region set check icon manually
    document.documentElement.style.setProperty(
      "--check-icon-url",
      `url(${checkIcon})`
    );
  }

  const asyncLoadDataForSingleLayer = async (layerType) => {
    const layerMapping = {
      [LAYERS.SUB_STATIONS]: "Substation",
      [LAYERS.AIRPORTS]: "Airport",
      [LAYERS.SEAPORTS]: "Seaport",
      [LAYERS.RAILWAY_STATIONS]: "Railway Station"
    };

    try {
      if (layerType === LAYERS.VENDOR) {
        if (copyiedSelectedProperty.current?.essential_vendor_all_details) {
        let data = [
          ...copyiedSelectedProperty.current.essential_vendor_all_details,
          ...copyiedSelectedProperty.current.non_essential_vendor_all_details
        ];

        if (data.length > 0) {
          data.forEach((item) => {
            if (item.latitude_longitude != null && item.latitude_longitude != "") {
              item.coordinates = item.latitude_longitude;
            }
          });
        }

        let uniqueVendorNames = Array.from(
          new Map(data.map(item => [item.name, item])).values()
        );
        bindDataOnMap(uniqueVendorNames, LAYERS.VENDOR);
        }
      }
      else if (layerType === LAYERS.ESSENTIAL_VENDORS) {
        const filteredEssentialVendors = copyiedSelectedProperty.current.essential_vendor_all_details.filter(
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
        let data = copyiedSelectedProperty.current.non_essential_vendor_all_details;

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
        const res = await getDataForSingleLayer(docTypeName);
        bindDataOnMap(res.data, layerType);
      }
    } catch (error) {
      // console.error(`Failed to load data for ${layerType}:`, error);
    }
  };

  const removeMarker = (layerType) => {
    // let divs =  document.getElement("marker"+layerType);
    const element = document.querySelectorAll('[data-name="marker_' + layerType + '"]');
    element.forEach((div) => {
      div.remove();
    })
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
      let allDefaultConnectivityLabelDiv = document.querySelectorAll('[data-name="distance-label"]');
      allDefaultConnectivityLabelDiv.forEach((div) => {
        div.remove();
      });
    }
  }

  const bindDataOnMap = async (resultData, layer, showVendorDetails = false) => {
    resultData.forEach(data => {
      const storeIconEl = document.createElement('div');
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
      //       <div class="relative w-8 h-8">
      //   <!-- Pin Circle -->
      //   <div class="absolute z-[10] inset-0 bg-[#E91E63] rounded-full flex items-center justify-center ">
      //       ✨
      //   </div>

      //   <!-- Pointer Tip -->
      //   <div class="absolute z-[9] left-1/2 bg-[#E91E63] pin-tip"></div>
      // </div>
      root.render(
        <div className="relative w-8 h-8">
          <div className="absolute z-[10] inset-0 bg-white rounded-full flex items-center justify-center">
            {
              layer === LAYERS.SUB_STATIONS ? <SlEnergy size={20} color="#5f2abb" /> :
                layer === LAYERS.AIRPORTS ? <MdAirplanemodeActive size={20} color="#5f2abb" /> :
                  layer === LAYERS.SEAPORTS ? <RiShip2Line size={20} color="#5f2abb" /> :
                    (layer === LAYERS.RAILWAY_STATIONS || layer === LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS) ? <MdDirectionsRailwayFilled size={20} color="#5f2abb" /> :
                      (layer === LAYERS.HIGHWAY || layer === LAYERS.DEFAULT_LAYER.HIGHWAY) ? <FaRoad size={20} color="#5f2abb" /> :
                        (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR) ? <FaStore size={20} color="#5b96d8" /> :
                          (layer === LAYERS.ESSENTIAL_VENDORS ) ? <FaStore size={20} color="#5b96d8" /> :
                          (layer === LAYERS.NON_ESSENTIAL_VENDORS ) ? <FaStore size={20} color="#5b96d8" /> :
                            <FaStore size={20} color="#5b96d8" />
            }
          </div>
          <div className="absolute z-[9] left-1/2 bg-white pin-tip"></div>
        </div>

        // <div style={{
        //   background: 'white',
        //   borderRadius: '50%',
        //   padding: '4px',
        //   boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
        //   display: 'flex',
        //   alignItems: 'center',
        //   justifyContent: 'center',
        //   marginTop: '20px'
        // }}>
        //   {
        //     layer === LAYERS.SUB_STATIONS ? <SlEnergy size={24} color="#5f2abb" /> :
        //       layer === LAYERS.AIRPORTS ? <MdAirplanemodeActive size={24} color="#5f2abb" /> :
        //         layer === LAYERS.SEAPORTS ? <RiShip2Line size={24} color="#5f2abb" /> :
        //           (layer === LAYERS.RAILWAY_STATIONS || layer === LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS) ? <MdDirectionsRailwayFilled size={24} color="#5f2abb" /> :
        //             (layer === LAYERS.HIGHWAY || layer === LAYERS.DEFAULT_LAYER.HIGHWAY) ? <FaRoad size={24} color="#5f2abb" /> :
        //               (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR) ? <FaStore size={24} color="#5b96d8" /> :
        //                 ""
        //   }
        // </div>
      );
      data.coordinates = data.coordinates.replace(" ", "");
      const [lat, lng] = data.coordinates.split(",").map(Number);

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
          //set the vendor detail
          data.result_type = "Vendor";
          //Display the modal with vendor details          
          setIsModalOpen(true);
          setSolution(data);

        });
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
            break;
        }
        if (name !== "") {
          addInfoPoupp(marker, name);
        }
      }
    });
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
  const increaseSelectedPropertyMarkerSize = (propertyId) => {
    let propertyDivs = document.querySelectorAll('[data-name="Property-Marker"]');
    propertyDivs.forEach(element => {
      let dataId = element.getAttribute("data-id");
      let idToCheck = "Property-marker-" + propertyId;
      if (dataId == idToCheck) {
        const svgElement = element.querySelector('svg');
        svgElement.style.height = "55px";
        svgElement.style.width = "55px";
        element.classList.add("property-marker-margin");
      }
      else {
        const svgElement = element.querySelector('svg');
        svgElement.style.height = "41px";
        svgElement.style.width = "27px";
        element.classList.remove("property-marker-margin");
      }
    });
  }
  // Modified marker adding function
  const addPointersToMap = async (elements, layerType) => {
    // Create lookups for vendor names and solutions
    const vendorNameLookup = {};
    const solutionLookup = {};
    console.log(solutions,'Solutions from Map')
    solutions.forEach(solution => {
      if (solution.latitude_longitude) {
        const coords = solution.latitude_longitude.slice().reverse();
        const coordsString = coords.toString();
        solutionLookup[coordsString] = solution;

        if (solution.result_type === "Vendor") {
          vendorNameLookup[coordsString] = solution.vendor_name || solution.name || 'Vendor';
        }
      }
    });

    // Separate property and vendor coordinates
    const propertyCoords = [];
    const vendorCoords = [];

    elements.forEach(data => {
      const coordsString = data.coordinates.toString();
      if (solutionLookup[coordsString]?.result_type === "Vendor") {
        vendorCoords.push(data);
      } else {
        propertyCoords.push(data);
      }
    });

    // Add property markers (red pins with click functionality)
    propertyCoords.forEach(data => {
      const marker = new mapboxgl.Marker({ color: '#ff0000' })
        .setLngLat(data.coordinates)
        .addTo(mapRef.current);
      const filtered = solutions.filter(item => {
        return (
          item.latitude_longitude[0] === data.coordinates[1] &&
          item.latitude_longitude[1] === data.coordinates[0]
        );
      });
      if (filtered.length > 0) {
        marker.getElement().dataset.id = "Property-marker-" + filtered[0].property_id;
        marker.getElement().dataset.name = "Property-Marker";
      }

      marker.getElement().addEventListener('click', () => {
        const solution = solutionLookup[data.coordinates.toString()];
        if (solution) {
          setSolution(solution);
          setIsConfirmationModalOpen(true);
          // setIsModalOpen(true);
          // setMapOptionVisible(false);
        }
      });
    });

    // Add vendor markers (blue store icons with hover labels)
    // Add vendor markers (blue store icons with hover labels)
    vendorCoords.forEach(data => {
      const storeIconEl = document.createElement('div');
      storeIconEl.style.width = '40px';
      storeIconEl.style.height = '40px';
      storeIconEl.style.display = 'flex';
      storeIconEl.style.alignItems = 'center';
      storeIconEl.style.justifyContent = 'center';

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
          <FaStore size={24} color="#4A76D1" />
        </div>
      );

      const marker = new mapboxgl.Marker({
        element: storeIconEl,
        anchor: 'bottom' // This ensures the popup appears above the marker
      }).setLngLat(data.coordinates)
        .addTo(mapRef.current);

      // Get the vendor name
      const vendorName = vendorNameLookup[data.coordinates.toString()] || 'Vendor';

      // Create a popup but don't add it yet
      const popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false,
        offset: 25,
        className: 'vendor-popup' // Add a class for custom styling if needed
      }).setText(vendorName);

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

      // Click event
      marker.getElement().addEventListener('click', () => {
        const solution = solutionLookup[data.coordinates.toString()];
        if (solution) {
          setSolution(solution);
          setIsModalOpen(true);
        }
      });
    });

    // Keep original layer click functionality as fallback
    const sourceId = `polygon-${nanoid()}`;
    const layerId = "Custom_" + layerType;

    mapRef.current.addSource(sourceId, {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: elements.map(data => ({
          type: "Feature",
          properties: { id: data.coordinates },
          geometry: {
            type: "Point",
            coordinates: data.coordinates,
          },
        })),
      },
    });

    mapRef.current.addLayer({
      id: layerId,
      type: "symbol",
      source: sourceId,
      layout: {
        "icon-image": "custom-marker_MakkerImage",
        "icon-size": 0.07,
        "icon-allow-overlap": true,
      },
    });

    mapRef.current.on("click", layerId, (e) => {
      if (e.features?.length > 0) {
        const coordsString = e.features[0].geometry.coordinates.toString();
        const solution = solutionLookup[coordsString];
        if (solution) {
          setSolution(solution);
          setIsModalOpen(true);
        }
      }
    });
  }

  const loadMapboxImage = (map, url) => {
    return new Promise((resolve, reject) => {
      mapRef.current.loadImage(url, (error, image) => {
        if (error) reject(error);
        else resolve(image);
      });
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
      //Remove all data
      removeMarker(LAYERS.SUB_STATIONS);
      removeMarker(LAYERS.AIRPORTS);
      removeMarker(LAYERS.SEAPORTS);
      removeMarker(LAYERS.RAILWAY_STATIONS);

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
  const loadDefaultLayer = async () => {
    copyiedSelectedProperty.current = structuredClone(solution);
    let essentialVenorData = copyiedSelectedProperty.current.essential_vendors.slice(0, 5);
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
    copyiedSelectedProperty.current.essential_vendors.forEach((item) => {
      if (!item.vendor_name || !item.supply) return;

      var filteredItem = copyiedSelectedProperty.current.essential_vendor_details.filter(
        (detail) => detail.name?.trim() === item.vendor_name.trim()
      );
      filteredItem.forEach((detail) => {
        if (typeof detail.supplyName !== 'undefined') {
          detail.supplyName = "";
        }
      });
      filteredItem.forEach((detail) => {
        if (!detail.supplyName) {
          detail.supplyName = item.supply;
        } else {
          detail.supplyName = `${detail.supplyName}, ${item.supply}`;
        }
      });
    });


    copyiedSelectedProperty.current.nonessential_vendors.forEach((item) => {
      if (!item.vendor_name || !item.supply) return; // skip if missing

      var filteredItem = copyiedSelectedProperty.current.non_essential_vendor_details.filter(
        (detail) => detail.name?.trim() === item.vendor_name.trim()
      );
      filteredItem.forEach((detail) => {
        if (typeof detail.supplyName !== 'undefined') {
          detail.supplyName = "";
        }
      });
      filteredItem.forEach((detail) => {
        if (!detail.supplyName) {
          detail.supplyName = item.supply;
        } else {
          detail.supplyName += ", " + item.supply;
        }
      });
    });
    const essentialVendorNames = Array.isArray(essentialVenorData) ? essentialVenorData.map(vendor => vendor.vendor_name) : [];
    var finalEVData = await getVendors(JSON.stringify(essentialVendorNames));
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
    essentialVendors.current  = finalEVData.data; 

    let data = [
      ...finalEVData.data,
      // ...finalNEVData.data
    ]
    // let data = [
    //   ...copyiedSelectedProperty.current.essential_vendor_details,
    //   ...copyiedSelectedProperty.current.non_essential_vendor_details
    // ];

    if (data.length > 0) {
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          item.coordinates = item.latitude_longitude;
        }
      });
    }
    allVendors = structuredClone(data);
    bindDataOnMap(data, LAYERS.DEFAULT_LAYER.VENDOR);
    let lat = solution.latitude_longitude[0];
    let lng = solution.latitude_longitude[1];
    const propertyLatitude = copyiedSelectedProperty.current?.latitude_longitude[0];
    const propertyLongitude = copyiedSelectedProperty.current?.latitude_longitude[1];

    if (data.length > 0) {
      let count = 0;
      let direction = "right";
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          count++;
          let vendorSourceId = 'line-string_' + count + "_" + LAYERS.DEFAULT_LAYER.VENDOR;
          let vendorLayerId = "default-layer_" + LAYERS.DEFAULT_LAYER.VENDOR + "_" + count;
          let coord = item.latitude_longitude.replace(" ", "").split(",").map(Number);
          var [vendorLongitude, vendorLatitude] = item.coordinates.split(",").map(Number);
          const distanceKm = getDistance([propertyLongitude, propertyLatitude], [vendorLatitude, vendorLongitude]).toFixed(2);
          const labelText = `${item.supplyName} ${distanceKm} km`;
          // const labelText = `${item.supplyName} </br> ${distanceKm} km`;
          let curvedDirectionValue = null;
          if (direction == "right") {
            direction = "left";
            curvedDirectionValue = DIRECTIONS.LEFT;
          }
          else {
            direction = "right";
            curvedDirectionValue = DIRECTIONS.RIGHT;
          }
          generateCurveLine({ sourceId: vendorSourceId, layerId: vendorLayerId, from: [coord[1], coord[0]], to: [lng, lat], linecolor: '#5b96d8', labelText: labelText, curvature: curvedDirectionValue });
        }
      });
    }

    //#region Add Connectivity Layers
    try {

      if (copyiedSelectedProperty.current.nearest_airport != null && copyiedSelectedProperty.current.nearest_airport != "") {
        nearestAirportDetail = await getDataForSingleLayer("Airport", { "name": copyiedSelectedProperty.current?.nearest_airport });
        if (nearestAirportDetail.data.length > 0) {
          const airportCoord = nearestAirportDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.AIRPORTS, [airportCoord[1], airportCoord[0]], [lng, lat], nearestAirportDetail.data[0], DIRECTIONS.LEFT);
        }

      }

      if (copyiedSelectedProperty.current.nearest_power_source != null && copyiedSelectedProperty.current.nearest_power_source != "") {
        nearestSubstationDetail = await getDataForSingleLayer("Substation", { "name": copyiedSelectedProperty.current?.nearest_power_source });
        if (nearestSubstationDetail.data.length > 0) {
          const substationCoord = nearestSubstationDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.SUB_STATIONS, [substationCoord[1], substationCoord[0]], [lng, lat], nearestSubstationDetail.data[0], DIRECTIONS.RIGHT);
        }
      }


      if (copyiedSelectedProperty.current.nearest_seaport != null && copyiedSelectedProperty.current.nearest_seaport != "") {
        nearestSeaportDetail = await getDataForSingleLayer("Seaport", { "name": copyiedSelectedProperty.current?.nearest_seaport });
        if (nearestSeaportDetail.data.length > 0) {
          const seaportCoord = nearestSeaportDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.SEAPORTS, [seaportCoord[1], seaportCoord[0]], [lng, lat], nearestSeaportDetail.data[0], DIRECTIONS.LEFT);
        }
      }


      if (copyiedSelectedProperty.current.nearest_railway_station != null && copyiedSelectedProperty.current.nearest_railway_station != "") {
        nearestRailwayStationDetail = await getDataForSingleLayer("Railway Station", { "name": copyiedSelectedProperty.current?.nearest_railway_station });
        if (nearestRailwayStationDetail.data.length > 0) {
          const railwayCoord = nearestRailwayStationDetail.data[0].coordinates.replace(" ", "").split(",").map(Number);
          addConnectivityLayer(LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS, [railwayCoord[1], railwayCoord[0]], [lng, lat], nearestRailwayStationDetail.data[0], DIRECTIONS.RIGHT);
        }
      }

      if (copyiedSelectedProperty.current.nearest_highway_coord != null && copyiedSelectedProperty.current.nearest_highway_coord != "") {
        highwayCoord = copyiedSelectedProperty.current.nearest_highway_coord.replace(" ", "").split(",").map(Number);
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

  const addConnectivityLayer = (layer, coord, propertyCoord, detail, direction = {}) => {
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
    let lineStringLayerId = 'default-layer' + "_" + layer;
    let name = "";
    if (detail != undefined && detail != null) {
      switch (layer) {
        case LAYERS.DEFAULT_LAYER.SUB_STATIONS:
          name = detail.name + " Sub Station";
          break;
        case LAYERS.DEFAULT_LAYER.AIRPORTS:
          name = detail.title + " Airport";
          break;
        case LAYERS.DEFAULT_LAYER.SEAPORTS:
          name = detail.title + " Seaport";
          break;
        case LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS:
          name = detail.name1 + " Railway Station";
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
    const distanceKm = getDistance([propertyCoord[0], propertyCoord[1]], [coord[0], coord[1]]).toFixed(2);
    const labelText = name !== "" ? `${name} ${distanceKm} km` : `${distanceKm} km`;
    // const labelText = name !== "" ? `${name} </br> ${distanceKm} km` : `${distanceKm} km`;
    generateCurveLine({ sourceId: sourceId, layerId: lineStringLayerId, from: coord, to: propertyCoord, linecolor: '#5f2abb', curvature: direction, labelText: labelText });
  }

  const addDistanceLabel = (coord, text, id) => {

    const supplyNameEl = document.createElement('div');
    // supplyNameEl.style.background = 'rgba(0, 0, 0, 0.75)';
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
  const resetZoomlevel = async () => {
    // Calculate the bounding box from your coordinates
    const bounds = new mapboxgl.LngLatBounds();
    allVendors.forEach(item => {
      let coord = item.latitude_longitude.replace(" ", "").split(",").map(Number);
      coord = [coord[1], coord[0]]; // Ensure coordinates are in [lng, lat] format
      bounds.extend(coord);
    });

    let propertyCoord = solution.latitude_longitude;
    propertyCoord = [propertyCoord[1], propertyCoord[0]]; // Ensure coordinates are in [lng, lat] format
    bounds.extend(propertyCoord);

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
      padding: 200,   // Adjusts space around the edges (optional)
      duration: 1000 // Optional: smooth animation
    });
  };
  const changeMarkerOpacity = () => {
    let proeprtyMarkers = document.querySelectorAll("[data-name='Property-Marker']");
    proeprtyMarkers.forEach(element => {
      let idToBeChecked = element.getAttribute("data-id");
      let currentId = "Property-marker-" + solution.property_id;
      if (idToBeChecked != currentId) {
        element.classList.add("property-marker-opacity");
      }
      else {
        let currentMarker = document.querySelector("[data-id=" + currentId + "]");
        currentMarker.classList.remove("property-marker-opacity");
      }
    });
  }
  const showNearestConnectivity = async (e) => {
    setIsConfirmationModalOpen(false);
    removeMarker(LAYERS.DEFAULT_LAYER.LABEL);
    await loadDefaultLayer();
    resetZoomlevel();
    // document.querySelector("[data-name='checkbox-container-supply']").style.display = "block"; //Disable the vendor layer checkbox
    document.querySelector("[data-name='checkbox-container-" + LAYERS.ESSENTIAL_VENDORS + "']").style.display = "flex"; //Disable the vendor layer checkbox
    document.querySelector("[data-name='checkbox-container-" + LAYERS.NON_ESSENTIAL_VENDORS + "']").style.display = "flex"; //Disable the vendor layer checkbox
    // document.querySelector("[data-name='checkbox-container-" + LAYERS.VENDOR + "']").style.flexDirection = "flex-row"; //Disable the vendor layer checkbox
    // document.querySelector("[data-name='checkbox-container-" + LAYERS.VENDOR + "']").style.gap = "5px"; //Disable the vendor layer checkbox
    changeMarkerOpacity();
    increaseSelectedPropertyMarkerSize(solution.property_id);

  };
  const showPropertyDetails = async (e) => {
    // setMapOptionVisible(false);
    setIsConfirmationModalOpen(false);
    removeMarker(LAYERS.DEFAULT_LAYER.LABEL);
    await loadDefaultLayer();
    resetZoomlevel();
    // document.querySelector("[data-name='checkbox-container-supply']").style.display = "block"; //Disable the vendor layer checkbox
    document.querySelector("[data-name='checkbox-container-" + LAYERS.ESSENTIAL_VENDORS + "']").style.display = "flex"; //Disable the vendor layer checkbox
    document.querySelector("[data-name='checkbox-container-" + LAYERS.NON_ESSENTIAL_VENDORS + "']").style.display = "flex"; //Disable the vendor layer checkbox
    changeMarkerOpacity();
    setIsModalOpen(true);
    increaseSelectedPropertyMarkerSize(solution.property_id);
  };

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

  //close confirmation box
  const closeConfirmPoup = () => {
    setIsConfirmationModalOpen(false);
    // let proeprtyMarkers = document.querySelectorAll("[data-name='Property-Marker']");
    // proeprtyMarkers.forEach(element => {
    //   element.classList.remove("property-marker-opacity");
    // });
  }

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
  const handleSingleCheckbox = (event) => {
    if (event.target.checked) {
      asyncLoadDataForSingleLayer(event.target.name);
    } else {
      // Handle uncheck if needed
      removeMarker(event.target.name);
    }
  }

  const optionPopup = useRef()
  useGSAP(() => {
    if (optionPopup.current) {
      gsap.from(optionPopup.current, {
        opacity: 0,
        y: 30,
        duration: 0.4,
        ease: "power2.out",
      });
    }
  }, { dependencies: [isConfirmationModalOpen], scope: optionPopup });
  const handleVendorCheckboxClick = (event, vendorType, isFallAllVendor) => {
    const { checked, name } = event.target;

    const getVendorData = (type) => {
      if (type === LAYERS.ESSENTIAL_VENDORS)
        return {
          main: copyiedSelectedProperty.current.essential_vendor_all_details,
          supplies: copyiedSelectedProperty.current.essential_vendors
        };
      if (type === LAYERS.NON_ESSENTIAL_VENDORS)
        return {
          main: copyiedSelectedProperty.current.non_essential_vendor_all_details,
          supplies: copyiedSelectedProperty.current.nonessential_vendors
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
            bindDataOnMap(filteredVendors, supplyName,true);
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
    let data = vendorType == LAYERS.ESSENTIAL_VENDORS ? copyiedSelectedProperty.current.essential_vendor_all_details : copyiedSelectedProperty.current.non_essential_vendor_all_details;
    
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
    bindDataOnMap(filteredVendors, supply,true);
}

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
    <div className="main-map h-screen w-screen flex items-center justify-center">
      <div
        id="map-container"
        ref={mapContainerRef} // Attach ref to this container
        style={{ width: "100%", height: "100%" }} // Set width and height for the map container
      />

      {isModalOpen && solution && (
        <Modal key={solution.result_type} onClose={() => { setIsModalOpen(false); setMapOptionVisible(true); }} type={solution.result_type}>
          {/* {solution.result_type === "Industry_Result" && <Property solution={solution} toggleModal={toggleModal} />} */}
          {/* {solution.result_type === "Vendor" && <Vendorcards supplier={solution} />} */}
          {solution.result_type === "Vendor" && <Vendorresult result={solution} source="MapComponent" rerender={1} />}
          {solution.result_type === "Industry_Result" && <IndustryResultScreen result={solution} source="MapComponent" rerender={1} />}

        </Modal>
      )}

      {isMapoptionVisible && (<div id="map-ui">
        <div>
          <div className="map-overlay top">
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
                    <div className="accordion-sub-item" name="traffic-section">
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
                        <ul>
                          {/* {intension === "For Property to Vendor" && (
                            <li className="li-container">
                              <label className="custom-checkbox">
                                <input
                                  type="checkbox"
                                  name={LAYERS.DEFAULT_LAYER.LABEL}
                                />
                                <span className="checkmark"></span>
                              </label>
                              <span>
                                <IoLayersOutline size={20} color="black" />
                              </span>
                              <span className="ml-5 color-black">
                                {LAYERS.DEFAULT_LAYER.LABEL}
                              </span>
                            </li>
                          )} */}
                          <li className="li-container"  >

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.SUB_STATIONS}
                                onChange={(e) => handleSingleCheckbox(e)}
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
                          <li className="li-container" >

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.AIRPORTS}
                                onChange={(e) => handleSingleCheckbox(e)}
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
                                onChange={(e) => handleSingleCheckbox(e)}
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
                                onChange={(e) => handleSingleCheckbox(e)}
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
                          {/* <li className="li-container" style={{ display: "none" }} data-name={"checkbox-container-" + LAYERS.VENDOR}>
                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.VENDOR}
                                onChange={(e) => handleSingleCheckbox(e)}
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
                            <li className="li-container" style={{ display: "none" }}  data-name={"checkbox-container-" + LAYERS.ESSENTIAL_VENDORS}>
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
                           <li style={{overflowY:'scroll',maxHeight:'140px', display:isShowEVCC?'block':'none'}} data-name={"checkbox-container-supply"}>
                             {copyiedSelectedProperty?.current?.essential_vendors.map((vendor, index) => (
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
                          <li className="li-container"  style={{ display: "none" }}  data-name={"checkbox-container-" + LAYERS.NON_ESSENTIAL_VENDORS}>                          
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
                              {copyiedSelectedProperty?.current?.nonessential_vendors.map((vendor, index) => (
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
                          {/* <li className="li-container" style={{ display: "none" }}  data-name={"checkbox-container-" + LAYERS.ESSENTIAL_VENDORS}>
                          
                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.ESSENTIAL_VENDORS}
                                onChange={(e) => handleSingleCheckbox(e)}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <FaStore size={20} className="text-[#5f2abb]" />
                              </span>
                              <span className="text-sm font-medium">
                                {LAYERS.ESSENTIAL_VENDORS}
                              </span>
                            </label>
                          </li>
                          <li className="li-container" style={{ display: "none" }}  data-name={"checkbox-container-" + LAYERS.NON_ESSENTIAL_VENDORS}>

                            <label style={{ display: 'flex', gap: '5px', flexDirection: 'row' }}>
                              <input
                                type="checkbox"
                                name={LAYERS.NON_ESSENTIAL_VENDORS}
                                onChange={(e) => handleSingleCheckbox(e)}
                              />
                              <span className="checkmark"></span>
                              <span>
                                <FaStore size={20} className="text-[#5f2abb]" />
                              </span>
                              <span className="text-sm font-medium">
                                {LAYERS.NON_ESSENTIAL_VENDORS}
                              </span>
                            </label>
                          </li> */}
                        </ul>
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className={`location-btn-container map-component-zoom-control`}>
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
      {isConfirmationModalOpen && (
        // <div ref={optionPopup} className='h-screen w-screen fixed inset-0 z-[444] flex items-center justify-center bg-black bg-opacity-20'>
        //   <div className='relative h-fit w-[30%] flex flex-col items-center gap-4 bg-white rounded-md border py-6 px-8'>
        //     <div className={`absolute top-2 right-2 z-[335] cursor-pointer h-8 w-8 rounded-full bg-white flex self-end items-center justify-center`} onClick={() => { closeConfirmPoup() }}>
        //       <FaXmark size={20} />
        //     </div>
        //     <h2 className="relative  tracking-wide text-lg text-center ">Do you want to see nearest connectivity or property details?</h2>
        //     <div className="relative flex flex-row gap-3">
        //       <button className="relative py-1 px-4 text-sm transition-all duration-200 hover:-translate-y-0.5 flex items-center text-white justify-center bg-gradient-to-br rounded-md from-[#2C53A3] to-[#70A1D9]" onClick={(e) => { showNearestConnectivity() }}>Nearest Connectivity</button>
        //       <button className="relative py-1 px-4 text-sm transition-all duration-200 hover:-translate-y-0.5 flex items-center text-white justify-center bg-gradient-to-br rounded-md from-[#2C53A3] to-[#70A1D9]" onClick={(e) => { showPropertyDetails() }}>Property Detail</button>
        //     </div>
        //   </div>
        // </div>
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div ref={optionPopup} className="min-w-[340px]  w-fit mb-6 bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-[#0e2044] flex flex-row justify-between p-6  text-white relative">
              <div className="relative flex flex-col gap-1 items-start">
                <span className="flex flex-row gap-2 items-center p-2">
                  <h2 className="text-lg font-semibold text-white">{solution.area}</h2>
                  <h2 className="text-md tracking-wide text-white">{solution.address}</h2>
                </span>
                <p className="text-md opacity-90">What would you like to explore?</p>
              </div>
              <button
                className="absolute top-3 right-3 text-white hover:opacity-80"
                onClick={() => { closeConfirmPoup() }}
              >
                <FaTimes size={20} />
              </button>
            </div>

            {/* Options */}
            <div className="p-4 space-y-3">
              <button
                onClick={(e) => { showNearestConnectivity() }}
                className="flex items-center gap-3 hover:-translate-y-0.5 p-3 rounded-md border hover:shadow-sm w-full text-left"
              >
                <div className="h-10 w-10 bg-blue-100 text-blue-600 flex items-center justify-center rounded-full">
                  <HiOutlineBolt size={20} />
                </div>
                <div>
                  <p className="text-sm font-semibold">Nearest Connectivity</p>
                  <p className="text-xs text-gray-600">
                    View distances to key infrastructure points
                  </p>
                </div>
              </button>

              <button
                onClick={() => { showPropertyDetails() }}
                className="flex items-center gap-3 p-3 hover:-translate-y-0.5 rounded-md border hover:shadow-sm w-full text-left"
              >
                <div className="h-10 w-10 bg-green-100 text-green-600 flex items-center justify-center rounded-full">
                  <HiOutlineMap size={20} />
                </div>
                <div>
                  <p className="text-sm font-semibold">Property Details</p>
                  <p className="text-xs text-gray-600">
                    View comprehensive property information
                  </p>
                </div>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MapComponent;


const Modal = ({ children, onClose, type }) => {
  return (
    <div className="fixed top-0 h-full w-full flex gap-4 items-center z-[12]">
      <div className={`${type === 'Vendor' ? 'top-7 right-12' : type === "Industry_Result" ? 'top-5 right-5' : ''} absolute  z-[335] cursor-pointer h-8 w-8 rounded-full bg-white shadow-md flex items-center justify-center`} onClick={onClose}>
        <FaXmark size={20} />
      </div>
      <div className={`modal-content relative h-full w-full flex items-center justify-center ${type === "Industry_Result" ? 'overflow-y-auto' : ''}`}>
        {children}
      </div>
    </div>
  );
};