import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MdFactory } from 'react-icons/md';
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

mapboxgl.accessToken = 'pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ';

const SingleMap = ({ selectedProperty, intension }) => {
  const copyiedSelectedProperty = structuredClone(selectedProperty);

  const lat = copyiedSelectedProperty?.latitude_longitude[0];
  const lng = copyiedSelectedProperty?.latitude_longitude[1];
  let boundaryCoordinates = copyiedSelectedProperty?.boundary_coordinates;

  console.log("Selected property");
  console.log(copyiedSelectedProperty);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const mapRef = useRef(null);
  const mapContainer = useRef(null);
  const [vendorsToSend, setVendorsToSend] = useState([]);
  const [isMapoptionVisible, setMapOptionVisible] = useState(true);
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
    SUB_STATIONS: "Sub Stations",
    RAILWAY_STATIONS: "Railway Stations",
    AIRPORTS: "Airports",
    SEAPORTS: "Seaports",
    HIGHWAY: "Highway",
    VENDOR: "All Vendors"
  }
  useEffect(() => {
    if (!mapContainer.current || !lat || !lng) return;

    mapRef.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      // style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [lng, lat],
      zoom: 14,
      attributionControl: false,

    });

    return () => mapRef.current?.remove();
  }, [lat, lng]);

  useEffect(() => {
    if (!mapRef.current || !boundaryCoordinates) return;

    const parsedBoundary =
      typeof boundaryCoordinates === 'string'
        ? JSON.parse(boundaryCoordinates)
        : boundaryCoordinates;

    if (!Array.isArray(parsedBoundary) || parsedBoundary.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();
    parsedBoundary.forEach((coord) => bounds.extend(coord));

    const sourceId = `boundary-${crypto.randomUUID()}`;

    mapRef.current.on('load', () => {
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
      mapRef.current.fitBounds(bounds, { padding: 50 });

      // Custom Marker with MdFactory
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

      new mapboxgl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat([lng, lat])
        .addTo(mapRef.current);

    });
  }, [boundaryCoordinates]);

  useEffect(() => {
    mapRef.current.on('style.load', () => {
      //load deafult layers
      loadVendorlayer();
    });
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
        console.log("Checkbox changed:", event.target.name, event.target.checked);
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

  const addConnectivityLayer = (layer, coord, propertyCoord) => {
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
            (layer === LAYERS.AIRPORTS || layer === LAYERS.DEFAULT_LAYER.AIRPORTS) ? <CiAirportSign1 size={24} color="#5f2abb" /> :
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
    addSingleLineLayer(sourceId, lineStringLayerId, coord, propertyCoord, '#5f2abb');
  }

  //#region Map Options related code

  const loadVendorlayer = async () => {

    copyiedSelectedProperty.essential_vendors.forEach((item) => {
      if (!item.vendor_name || !item.supply) return;

      var filteredItem = copyiedSelectedProperty.essential_vendor_details.filter(
        (detail) => detail.name?.trim() === item.vendor_name.trim()
      );

      filteredItem.forEach((detail) => {
        if (!detail.supplyName) {
          detail.supplyName = item.supply;
        } else {
          detail.supplyName = `${detail.supplyName}, ${item.supply}`;
        }
      });
    });


    copyiedSelectedProperty.nonessential_vendors.forEach((item) => {
      if (!item.vendor_name || !item.supply) return; // skip if missing

      var filteredItem = copyiedSelectedProperty.non_essential_vendor_details.filter(
        (detail) => detail.name?.trim() === item.vendor_name.trim()
      );

      filteredItem.forEach((detail) => {
        if (!detail.supplyName) {
          detail.supplyName = item.supply;
        } else {
          detail.supplyName += ", " + item.supply;
        }
      });
    });

    let data = [
      ...copyiedSelectedProperty.essential_vendor_details,
      ...copyiedSelectedProperty.non_essential_vendor_details
    ];
    // selectedProperty.essential_vendor_details.forEach((item,index) => {
    //   item.supplyName = selectedProperty.essential_vendors[index].vendor_name;
    // });
    // selectedProperty.non_essential_vendor_details.forEach((item,index) => {

    // });
    console.log("data in loadVendorlayer", data);
    if (data.length > 0) {
      data.forEach((item) => {
        if (item.supplyName === undefined || item.supplyName === null) {
          console.log("Supply name in loadVendorlayer", item.supplyName);
        }

        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          item.coordinates = item.latitude_longitude;
        }
      });
    }
    bindDataOnMap(data, LAYERS.DEFAULT_LAYER.VENDOR);
    //document.querySelector('[name="' + LAYERS.VENDOR + '"]').checked = true; //Check the vendor layer checkbox by default
    document.querySelector('[name="' + LAYERS.DEFAULT_LAYER.LABEL + '"]').checked = true; //Check the vendor layer checkbox by default

    if (data.length > 0) {
      let count = 0;
      data.forEach((item) => {
        if (item.latitude_longitude != null && item.latitude_longitude != "") {
          count++;
          let vendorSourceId = 'line-string_' + count + "_" + LAYERS.DEFAULT_LAYER.VENDOR;
          let vendorLineStringLayerId = 'line-string-layer_' + count + "_" + LAYERS.DEFAULT_LAYER.VENDOR;
          let coord = item.latitude_longitude.replace(" ", "").split(",").map(Number);
          addSingleLineLayer(vendorSourceId, vendorLineStringLayerId, [coord[1], coord[0]], [lng, lat], '#5b96d8');
        }
      });
    }

    //#region Add Connectivity Layers
    try {
      if (copyiedSelectedProperty.nearest_airport_coord != null && copyiedSelectedProperty.nearest_airport_coord != "") {
        const airportCoord = copyiedSelectedProperty.nearest_airport_coord.replace(" ", "").split(",").map(Number);
        addConnectivityLayer(LAYERS.DEFAULT_LAYER.AIRPORTS, [airportCoord[1], airportCoord[0]], [lng, lat]);
      }

      if (copyiedSelectedProperty.nearest_power_source_coord != null && copyiedSelectedProperty.nearest_power_source_coord != "") {
        const substationCoord = copyiedSelectedProperty.nearest_power_source_coord.replace(" ", "").split(",").map(Number);
        addConnectivityLayer(LAYERS.DEFAULT_LAYER.SUB_STATIONS, [substationCoord[1], substationCoord[0]], [lng, lat]);
      }


      if (copyiedSelectedProperty.nearest_seaport_coord != null && copyiedSelectedProperty.nearest_seaport_coord != "") {
        const seaportCoord = copyiedSelectedProperty.nearest_seaport_coord.replace(" ", "").split(",").map(Number);
        addConnectivityLayer(LAYERS.DEFAULT_LAYER.SEAPORTS, [seaportCoord[1], seaportCoord[0]], [lng, lat]);
      }


      if (copyiedSelectedProperty.nearest_railway_station_coord != null && copyiedSelectedProperty.nearest_railway_station_coord != "") {
        const railwayCoord = copyiedSelectedProperty.nearest_railway_station_coord.replace(" ", "").split(",").map(Number);
        addConnectivityLayer(LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS, [railwayCoord[1], railwayCoord[0]], [lng, lat]);
      }


      if (copyiedSelectedProperty.nearest_highway_coord != null && copyiedSelectedProperty.nearest_highway_coord != "") {
        const highwayCoord = copyiedSelectedProperty.nearest_highway_coord.replace(" ", "").split(",").map(Number);
        addConnectivityLayer(LAYERS.DEFAULT_LAYER.HIGHWAY, [highwayCoord[1], highwayCoord[0]], [lng, lat]);
      }
    } catch (error) {
      console.error("Error in adding marker:", error);
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
    else {
      const docTypeName = layerMapping[layerType];
      if (!docTypeName) return;

      try {
        const res = await getDataForSingleLayer(docTypeName);
        bindDataOnMap(res.data, layerType);
      } catch (error) {
        console.error(`Failed to load data for ${layerType}:`, error);
      }
    }

  };

  const removeMarker = (layerType) => {
    // let divs =  document.getElement("marker"+layerType);
    const element = document.querySelectorAll('[data-name="marker_' + layerType + '"]');
    element.forEach((div) => {
      console.log("Removing marker", div);
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
          console.log("Removing marker for default layer", div);
          div.remove();
        });
      });
      //get the all layer from the map.
      const filteredLayers = mapRef.current
        .getStyle()
        .layers.filter((item) => item.id.includes("Default"));
      console.log("Filtered layers to remove", filteredLayers);
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
    }
  }
  function getMidpointSimple(coord1, coord2) {
    const midLat = (coord1[0] + coord2[0]) / 2;
    const midLng = (coord1[1] + coord2[1]) / 2;
    return [midLat, midLng];
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
  const bindDataOnMap = async (resultData, layer) => {
    try {
      console.log("Layer type in bindDataOnMap", layer);
      resultData.forEach(data => {
        if (data.coordinates != null && data.coordinates != "") {
          console.log("data in binddataonmap", data);
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
                (layer === LAYERS.SUB_STATIONS || layer === LAYERS.DEFAULT_LAYER.SUB_STATIONS) ? <SlEnergy size={24} color="#5f2abb" /> :
                  (layer === LAYERS.AIRPORTS || layer === LAYERS.DEFAULT_LAYER.AIRPORTS) ? <CiAirportSign1 size={24} color="#5f2abb" /> :
                    (layer === LAYERS.SEAPORTS || layer === LAYERS.DEFAULT_LAYER.SEAPORTS) ? <RiShip2Line size={24} color="#5f2abb" /> :
                      (layer === LAYERS.RAILWAY_STATIONS || layer === LAYERS.DEFAULT_LAYER.RAILWAY_STATIONS) ? <MdDirectionsRailwayFilled size={24} color="#5f2abb" /> :
                        (layer === LAYERS.HIGHWAY || layer === LAYERS.DEFAULT_LAYER.HIGHWAY) ? <FaRoad size={24} color="#5f2abb" /> :
                          (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR) ? <FaStore size={24} color="#5b96d8" /> :
                            ""
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

          if (layer === LAYERS.VENDOR || layer === LAYERS.DEFAULT_LAYER.VENDOR) {
            // Create a popup but don't add it yet
            addInfoPoupp(marker, data.name);

            marker.getElement().addEventListener('click', () => {
              setIsModalOpen(true);
              setVendorsToSend(data);
            });
            if (layer === LAYERS.DEFAULT_LAYER.VENDOR) {
              const propertyLatitude = copyiedSelectedProperty?.latitude_longitude[0];
              const propertyLongitude = copyiedSelectedProperty?.latitude_longitude[1];
              // 🏷️ Add Distance Label at Midpoint
              const midpoint = getMidpointSimple([vendorLongitude, vendorLatitude], [propertyLatitude, propertyLongitude]);
              const distanceKm = getDistance([propertyLatitude, propertyLongitude], [vendorLongitude, vendorLatitude]).toFixed(2);
              console.log(vendorLongitude, vendorLatitude, propertyLatitude, propertyLongitude, midpoint, distanceKm);
              const supplyNameMidpoint = getMidpointSimple(midpoint, [vendorLongitude, vendorLatitude]);
              console.log("supplyNameMidpoint", supplyNameMidpoint);

              const labelEl = document.createElement('div');
              labelEl.style.background = 'rgba(0, 0, 0, 0.75)';
              labelEl.style.color = '#fff';
              labelEl.style.padding = '4px 8px';
              labelEl.style.borderRadius = '6px';
              labelEl.style.fontSize = '12px';
              labelEl.style.fontWeight = 'bold';
              labelEl.innerText = `${data.supplyName} - ${distanceKm} km`;

              new mapboxgl.Marker({
                element: labelEl,
                anchor: 'center'
              })
                .setLngLat([midpoint[1], midpoint[0]])
                .addTo(mapRef.current);

              const supplyNameEl = document.createElement('div');
              supplyNameEl.style.background = 'rgba(0, 0, 0, 0.75)';
              supplyNameEl.style.color = '#fff';
              supplyNameEl.style.padding = '4px 8px';
              supplyNameEl.style.borderRadius = '6px';
              supplyNameEl.style.fontSize = '12px';
              supplyNameEl.style.fontWeight = 'bold';
              supplyNameEl.innerHTML = `${data.supplyName} </br> ${distanceKm} km`;

              new mapboxgl.Marker({
                element: supplyNameEl,
                anchor: 'center'
              })
                .setLngLat([supplyNameMidpoint[1], supplyNameMidpoint[0]])
                .addTo(mapRef.current);

              // const supplyNameEl = document.createElement('div');
              // supplyNameEl.style.background = 'rgba(0, 0, 0, 0.75)';
              // supplyNameEl.style.color = '#fff';
              // supplyNameEl.style.padding = '4px 8px';
              // supplyNameEl.style.borderRadius = '6px';
              // supplyNameEl.style.fontSize = '12px';
              // supplyNameEl.style.fontWeight = 'bold';
              // supplyNameEl.innerText = `${data.supplyName}`;

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
              default:
                break;
            }
            addInfoPoupp(marker, name);
          }
        }
        else {
          console.error("Invalid coordinate " + item.coordinates + " for vendor " + data.name)
        }
      });
    } catch (error) {
      console.error("Error in bindDataOnMap:", error);
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