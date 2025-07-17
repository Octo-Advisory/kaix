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
import { FaXmark } from "react-icons/fa6";
import { FaStore } from "react-icons/fa";
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

function MapComponent({ solutions, toggleModal, source, intension }) {
  console.log("source in map component", source);
  console.log("intension in map component", intension);
  console.log("solutons from map", solutions);
  const validation_result = useSelector((state) => state.validate.validation_result)
  console.log("validation_result", validation_result);
  let propertyCoord = validation_result?.[0]?.[1]?.latitude_longitude?.split(",").map(Number).reverse() ?? null;
  console.log("propertyCoord", propertyCoord);
  const [solution, setSolution] = useState({})
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMapoptionVisible, setMapOptionVisible] = useState(true);

  const latLongArray = Object.values(solutions).map(item => [...item.latitude_longitude].reverse());

  var map = null;
  const mapContainerRef = useRef(null); // Create a ref for the map container
  mapboxgl.accessToken = 'pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ';
  const LAYERS = {
    DEFAULT_LAYER: {
      LABEL: "Default Layers",
      VENDOR: "Default Vendors",
      SUB_STATIONS: "Default Sub Stations",
      RAILWAY_STATIONS: "Default Railway Stations",
      AIRPORTS: "Default Airports",
      SEAPORTS: "Default Seaports",
      HIGHWAY: "Default Highways",
    },
    SUB_STATIONS: "SUB_STATIONS",
    RAILWAY_STATIONS: "RAILWAY_STATIONS",
    AIRPORTS: "AIRPORTS",
    SEAPORTS: "SEAPORTS",
    VENDOR: "VENDOR"
  }
  useEffect(() => {
    // Initialize the map after the component mounts
    map = new mapboxgl.Map({
      container: mapContainerRef.current, // Use the ref to attach the map
      style: "mapbox://styles/mapbox/streets-v12", // Map style URL
      center: [73.133661788180035, 22.308428225686328], // Starting position [lng, lat]
      zoom: 14, // Starting zoom
      attributionControl: false,
    });
    map.on('style.load', () => {
      draw();
      //load deafult layers
      // loadVendorlayer();
    });
    return () => map.remove(); // Cleanup the map instance on unmount
  }, []); // Empty dependency array to run only once

  useEffect(() => {
    // Get all checkboxes
    const allTrafficCheckbox = document.querySelectorAll(
      "[name='traffic-section'] [type='checkbox']"
    );

    // Define the handler once
    const handleCheckboxChange = (event) => {
      if (event.target.checked) {
        debugger;
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
  }, []);

  useEffect(() => {
    if (isMapoptionVisible) {
      const mapUI = document.getElementById("map-ui");
      if (mapUI) {
        // Get all checkboxes
        const allTrafficCheckbox = document.querySelectorAll(
          "[name='traffic-section'] [type='checkbox']"
        );

        // Define the handler once
        const handleCheckboxChange = (event) => {
          if (event.target.checked) {
            debugger;
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
        console.log("Rebind click event");
        // Cleanup function to remove listeners
        return () => {
          allTrafficCheckbox.forEach((element) => {
            element.removeEventListener("change", handleCheckboxChange);
          });
        };
      }
    }
  }, [isMapoptionVisible]);


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
    console.log("intention is", intension);
    // Filter out invalid coordinates
    const validCoordinates = latLongArray.filter(isValidLatLng);
    console.log(validCoordinates, latLongArray, 'Coordinates LAtLongArray');

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
    map.fitBounds(bounds, {
      padding: 50,    // Adds padding around the points
      maxZoom: 10,    // Prevents zooming in too much
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
          let sourceId = `Custom_Source_${crypto.randomUUID()}`;

          map.addSource(sourceId, {
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

          let layerId1 = `Custom_polygon_fill_${crypto.randomUUID()}`;
          let layerId2 = `Custom_polygon_border_${crypto.randomUUID()}`;

          map.addLayer({
            id: layerId1,
            type: "fill",
            source: sourceId,
            layout: {},
            paint: {
              "fill-color": "#ff0000",
              "fill-opacity": 0.5,
            },
          });

          map.addLayer({
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
    console.log(solution, solutions, hasVendorResult, 'Okay');

    if (hasVendorResult) {
      //if propertyCoord is not available, then it means it is for all vendor results
      if (!propertyCoord) {
        let some = source === 'SolutionScreen' ? solution : solutions;
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
        .addTo(map);

      // Generate LineString Features
      let layerId = `Custom_property_vendor_lines_layer_${crypto.randomUUID()}`;
      const lines = latLongArray.map(vendorCoord => ({
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [propertyCoord, vendorCoord]
        },
        properties: {}
      }));

      map.addSource('property-vendor-lines', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: lines
        },
        lineMetrics: true
      });

      map.addLayer({
        id: layerId,
        type: 'line',
        source: 'property-vendor-lines',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-width': 3,
          'line-opacity': 0.9,
          'line-gradient': [
            'interpolate',
            ['linear'],
            ['line-progress'],
            0, '#0e2044',
            1, '#41b655'
          ]
        }
      });

      // Removed distance labels code here
    }

    //#region Add markers to map - Modified for vendors/properties
    await addPointersToMap(elements, crypto.randomUUID());

    //#region set check icon manually
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
        debugger;
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
  }

  const asyncLoadDataForSingleLayer = async (layerType) => {
    const layerMapping = {
      [LAYERS.SUB_STATIONS]: "Substation",
      [LAYERS.AIRPORTS]: "Airport",
      [LAYERS.SEAPORTS]: "Seaport",
      [LAYERS.RAILWAY_STATIONS]: "Railway Station"
    };

    const docTypeName = layerMapping[layerType];
    if (!docTypeName) return;

    try {
      const res = await getDataForSingleLayer(docTypeName);
      bindDataOnMap(res.data, layerType);
    } catch (error) {
      console.error(`Failed to load data for ${layerType}:`, error);
    }
  };

  const removeMarker = (layerType) => {
    debugger
    // let divs =  document.getElement("marker"+layerType);
    const element = document.querySelectorAll('[data-name="marker_' + layerType + '"]');
    element.forEach((div) => {
      div.remove();
    })

  }

  const bindDataOnMap = async (resultData, layer) => {
    resultData.forEach(data => {
      console.log("data in binddataonmap", data);
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
            layer === LAYERS.SUB_STATIONS ? <SlEnergy size={24} color="#4A76D1" /> :
              layer === LAYERS.AIRPORTS ? <CiAirportSign1 size={24} color="#4A76D1" /> :
                layer === LAYERS.SEAPORTS ? <RiShip2Line size={24} color="#4A76D1" /> :
                  <MdDirectionsRailwayFilled size={24} color="#4A76D1" />
          }
        </div>
      );
      data.coordinates = data.coordinates.replace(" ", "");
      const [lat, lng] = data.coordinates.split(",").map(Number);
      const marker = new mapboxgl.Marker({
        element: storeIconEl,
        anchor: 'bottom' // This ensures the popup appears above the marker
      }).setLngLat([lng, lat])
        .addTo(map);
    });
  }

  // Modified marker adding function
  const addPointersToMap = async (elements, layerType) => {
    // Create lookups for vendor names and solutions
    const vendorNameLookup = {};
    const solutionLookup = {};

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
        .addTo(map);

      marker.getElement().addEventListener('click', () => {
        const solution = solutionLookup[data.coordinates.toString()];
        if (solution) {
          setSolution(solution);
          setIsModalOpen(true);
          setMapOptionVisible(false);
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
        .addTo(map);

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
        popup.addTo(map); // Actually show the popup
        map.getCanvas().style.cursor = 'pointer';
      });

      // Mouse leave event
      marker.getElement().addEventListener('mouseleave', () => {
        popup.remove(); // Remove the popup
        map.getCanvas().style.cursor = '';
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
    const sourceId = `polygon-${crypto.randomUUID()}`;
    const layerId = "Custom_" + layerType;

    map.addSource(sourceId, {
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

    map.addLayer({
      id: layerId,
      type: "symbol",
      source: sourceId,
      layout: {
        "icon-image": "custom-marker_MakkerImage",
        "icon-size": 0.07,
        "icon-allow-overlap": true,
      },
    });

    map.on("click", layerId, (e) => {
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
      map.loadImage(url, (error, image) => {
        if (error) reject(error);
        else resolve(image);
      });
    });
  }

  useEffect(() => {
    console.log('this is the solution of selected', solution, solutions)
  }, [solution, solutions])

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
  const loadVendorlayer = async () => {
    let data = [
      ...selectedProperty.essential_vendor_details,
      ...selectedProperty.non_essential_vendor_details
    ];
    console.log("data in loadVendorlayer", data);
    if (data.length > 0) {
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          item.coordinates = item.latitude_longitude;
        }
      });
    }
    bindDataOnMap(data, LAYERS.VENDOR);
    document.querySelector('[name="' + LAYERS.VENDOR + '"]').checked = true; //Check the vendor layer checkbox by default

    if (data.length > 0) {
      let count = 0;
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          count++;
          let vendorSourceId = 'line-string_' + count + "_" + LAYERS.VENDOR;
          let vendorLineStringLayerId = 'line-string-layer_' + count + "_" + LAYERS.VENDOR;
          let coord = item.latitude_longitude.replace(" ", "").split(",").map(Number);
          addSingleLineLayer(vendorSourceId, vendorLineStringLayerId, [coord[1], coord[0]], [lng, lat], '#5b96d8');
        }
      });
    }
  }

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
          {solution.result_type === "Vendor" && <Vendorresult result={solution} source="MapComponent" />}
          {solution.result_type === "Industry_Result" && <IndustryResultScreen result={solution} source="MapComponent" />}

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
                    <span className="main-header-font color-green">
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
                        <span className="child-header-font color-green">
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
                            className="cusor-pointer font-14 font-b color-green"
                            onClick={() =>
                              handleAllClick("traffic-section", true)
                            }
                          >
                            Select all
                          </span>{" "}
                          |{" "}
                          <span
                            className="cusor-pointer font-14 font-b color-green"
                            onClick={() =>
                              handleAllClick("traffic-section", false)
                            }
                          >
                            Clear all
                          </span>
                          {/* <a href="#">Select: All</a> | <a href="#">None</a> */}
                        </div>
                        <ul>
                          {intension === "For Property to Vendor" && (
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
                          )}
                          <li className="li-container">

                            <label className="custom-checkbox">
                              <input
                                type="checkbox"
                                name={LAYERS.SUB_STATIONS}
                              />
                              <span className="checkmark"></span>
                            </label>
                            <span>
                              <SlEnergy size={20} color="black" />
                            </span>
                            {/* <img
                              src={<SlEnergy />}
                              alt="Icon"
                            /> */}
                            <span className="ml-5 color-black">
                              {LAYERS.SUB_STATIONS}
                            </span>
                          </li>
                          <li className="li-container">

                            <label className="custom-checkbox">
                              <input
                                type="checkbox"
                                name={LAYERS.AIRPORTS}
                              />
                              <span className="checkmark"></span>
                            </label>
                            <span>
                              <CiAirportSign1 size={20} color="black" />
                            </span>
                            {/* <img
                            src={getIcon(
                              enumData.trafficLayerType.CONSTRUCTION_ALERT
                            )}
                            alt="Icon"
                          /> */}
                            <span className="ml-5 color-black">
                              {LAYERS.AIRPORTS}
                            </span>
                          </li>
                          <li className="li-container">

                            <label className="custom-checkbox">
                              <input
                                type="checkbox"
                                name={LAYERS.SEAPORTS}
                              />
                              <span className="checkmark"></span>
                            </label>
                            <span>
                              <RiShip2Line size={20} color="black" />
                            </span>
                            {/* <img
                            src={getIcon(
                              enumData.trafficLayerType.TRAFFIC_INCIDENT
                            )}
                            alt="Icon"
                          /> */}
                            <span className="ml-5 color-black">
                              {LAYERS.SEAPORTS}
                            </span>
                          </li>
                          <li className="li-container">

                            <label className="custom-checkbox">
                              <input
                                type="checkbox"
                                name={LAYERS.RAILWAY_STATIONS}
                              />
                              <span className="checkmark"></span>
                            </label>
                            <span>
                              <MdDirectionsRailwayFilled size={20} color="black" />
                            </span>
                            {/* <img
                            src={getIcon(
                              enumData.trafficLayerType.CONSTRUCTION_ALERT
                            )}
                            alt="Icon"
                          /> */}
                            <span className="ml-5 color-black">
                              {LAYERS.RAILWAY_STATIONS}
                            </span>
                          </li>
                          <li className="li-container">

                            <label className="custom-checkbox">
                              <input
                                type="checkbox"
                                name={LAYERS.VENDOR}
                              />
                              <span className="checkmark"></span>
                            </label>
                            <span>
                              <FaStore size={20} color="black" />
                            </span>
                            <span className="ml-5 color-black">
                              {LAYERS.VENDOR}
                            </span>
                          </li>
                        </ul>
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>)}
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