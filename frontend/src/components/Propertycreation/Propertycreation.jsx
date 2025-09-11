// export default PropertyCreation;
import React, { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useFrappeEventListener } from 'frappe-react-sdk';
import LogoLoader from '../Responseloader/LogoLoader';
import { FaXmark } from "react-icons/fa6";
import './assets/style/propertycreationstyle.css';
import { useFrappeGetDoc } from "frappe-react-sdk";

const BASE_URL = window.location.origin;
const API_TOKEN = 'd3de1e0e4e25846:51fd8e403a19045';

function PropertyCreation() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  const [showLoader, setLoaderVisibility] = useState(false);
  const [showModal, setModalVisibility] = useState(false);
  const [loaderTitle, setLoaderTitle] = useState("Processing");
  var childBlockData = null;

  // Frappe event listener
  useFrappeEventListener("Property_Seg_Status_Update", async ({ message }) => {
    setLoaderTitle(message);
    if (message.includes("Error") || message.includes("Property creating ended")) {
      setLoaderVisibility(false);
    }
    console.log("Event data:", message);
  });

  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Mapping")
  const configurations = uiData?.configurations || [];
  const uiConfig = configurations.reduce((acc, curr) => {
    acc[curr.key] = curr.value;
    return acc;
  }, {});
  useEffect(() => {
    if (!uiData) return;
    mapboxgl.accessToken = `${uiConfig?.['mapmobx_api_token']}`;
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      // style:'mapbox://styles/mapbox/standard-satellite',
      center: [73.133661788180035, 22.308428225686328],
      zoom: 8,
      attributionControl: false
    });

    mapRef.current = map;

    mapRef.current.on('style.load', draw);


    // Cleanup
    // return () => {
    //   mapRef.current.remove();
    //   mapRef.current.off('click', hideContextMenu);
    //   mapRef.current.off('movestart', hideContextMenu);
    //   mapRef.current.off('contextmenu');
    // };
  }, [uiData]);

  // Handle API call
  const getData = async (doctypeName, filters = null) => {
    try {
      let url = `${BASE_URL}/api/resource/${doctypeName}?fields=["*"]&limit=1000`;
      if (filters) {
        url += `&filters=${encodeURIComponent(JSON.stringify(filters))}`;
      }
      const headers = {
        'Authorization': `token ${API_TOKEN}`,
        'Content-Type': 'application/json'
      };
      const response = await axios.get(url, { headers });
      return response.data;
    } catch (error) {
      console.error('Error fetching data:', error);
      throw error;
    }
  };

  // Trigger property segmentation
  const triggerProSeg = (array, childBlockId) => {
    fetch(`${BASE_URL}/api/method/StartPropertySegmentation`, {
      method: 'POST',
      headers: {
        'Authorization': `token ${API_TOKEN}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        polygonArray: array,
        childBlockId
      })
    })
      .then(res => res.json())
      .then(data => console.log('Response:', data))
      .catch(err => console.error('Error:', err));
  };

  const createMainBlock = (lat, lon) => {
    fetch(`${BASE_URL}/api/method/CreateMainBlockRecord`, {
      method: 'POST',
      headers: {
        'Authorization': `token ${API_TOKEN}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        lat: lat,
        lon: lon
      })
    })
      .then(res => res.json())
      .then(data => console.log('Response:', data))
      .catch(err => console.error('Error:', err));
  };
  // Draw map content
  const draw = useCallback(async () => {
    childBlockData = await getData("Child Block");

    // Context menu logic
    const contextMenu = document.getElementById('contextMenu');
    const createBtn = document.getElementById('createPropertyBtn');
    let lngLat = null;

    // Show custom context menu on right-click
    mapRef.current.on('contextmenu', (e) => {
      e.preventDefault();
      lngLat = e.lngLat;
      const isInside = checkPointInsideBoundingBoxes([lngLat.lng, lngLat.lat], childBlockData.data);
      if (!isInside) {
        contextMenu.style.top = `${e.originalEvent.clientY}px`;
        contextMenu.style.left = `${e.originalEvent.clientX}px`;
        contextMenu.classList.remove('hidden');
      }
    });

    // Hide menu on map click or move
    const hideContextMenu = () => contextMenu.classList.add('hidden');
    mapRef.current.on('click', hideContextMenu);
    mapRef.current.on('movestart', hideContextMenu);

    // Handle click on "Create Property here"
    createBtn.onclick = () => {
      contextMenu.classList.add('hidden');
      setModalVisibility(true);
      // alert(`Create property at:\nLat: ${lngLat.lat}, Lng: ${lngLat.lng}`);
      createMainBlock(lngLat.lat, lngLat.lng);
      // 🔁 Replace this with triggerProSeg or other logic
    };



    const res = childBlockData;
    const statusConfig = {
      Pending: {
        label: "Create Properties",
        color: "#007bff",
        fillColor: "#6dc9e8",
        leftOffset: "-38px",
        buttonClick: (feature, id) => {
          triggerProSeg(JSON.stringify(feature), id);
          setModalVisibility(true);
        }
      },
      Processing: {
        label: "Error in Extration",
        color: "#E55050",
        fillColor: "#e86d82",
        leftOffset: "-45px",
        buttonClick: (feature, id) => {
          triggerProSeg(JSON.stringify(feature), id);
          setModalVisibility(true);
        }
      },
      Complete: {
        label: "View Properties",
        color: "#088",
        fillColor: "#088",
        leftOffset: "-38px",
        buttonClick: (_, id) => {
          window.open(`${BASE_URL}/app/test-survey-no?child_block_id=${id}`, '_blank');
        }
      }
    };

    const createButton = (label, bgColor, leftOffset, onClick) => {
      const btn = document.createElement('button');
      btn.innerText = label;
      btn.className = 'map-button';
      btn.name = "btnCreateProperty";
      btn.disabled = label == "Error in Extration" ? true : false;
      Object.assign(btn.style, {
        padding: '2px 6px',
        fontSize: '10px',
        top: '6px',
        left: leftOffset,
        backgroundColor: bgColor,
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        // position: 'absolute',
        display: 'none'
      });
      btn.onclick = onClick;
      return btn;
    };

    const featuresByStatus = {
      Pending: [],
      Processing: [],
      Complete: []
    };

    res.data.forEach(el => {
      const coordinates = JSON.parse(el.bounding_box);
      const feature = {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [coordinates]
        }
      };
      const [lat, lng] = el.center_coordinate.split(',').map(Number);
      const config = statusConfig[el.status];
      if (!config) return;

      featuresByStatus[el.status].push(feature);
      // Create a container div for holding both buttons
      const container = document.createElement("div");
      container.style.display = "flex";
      container.style.flexDirection = "column"; // stack buttons vertically
      container.style.gap = "6px"; // space between buttons
      container.style.top = "24px";
      container.style.left = "-42px";

      const btn1 = createButton(
        config.label,
        config.color,
        config.leftOffset,
        () => config.buttonClick(coordinates, el.name)
      );

      // Append both buttons into container
      container.appendChild(btn1);

      if (el.status == "Complete") {
        const btn2 = createButton(
          "View Shape",
          config.color,
          config.leftOffset,
          () => showLandBoundryForBlock(el.name)
        );
        container.appendChild(btn2);
      }


      new mapboxgl.Marker({ element: container, anchor: 'bottom-left' })
        .setLngLat([lat, lng])
        .addTo(mapRef.current);
    });

    // Add status layers
    Object.keys(featuresByStatus).forEach(status => {
      const sourceId = `${status.toLowerCase()}-source`;
      const fillId = `${status.toLowerCase()}-fill`;
      const lineId = `${status.toLowerCase()}-outline`;

      mapRef.current.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: featuresByStatus[status]
        }
      });

      mapRef.current.addLayer({
        id: fillId,
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': statusConfig[status].fillColor,
          'fill-opacity': 0.4
        }
      });

      mapRef.current.addLayer({
        id: lineId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': statusConfig[status].fillColor,
          'line-width': 2
        }
      });
    });

    // Toggle button visibility based on zoom
    mapRef.current.on('zoom', () => {
      const show = mapRef.current.getZoom() >= 13;
      document.getElementsByName("btnCreateProperty").forEach(btn => {
        btn.style.display = show ? "block" : "none";
      });
    });
  }, []);

  const showLandBoundryForBlock = async (childblockid) => {
    var filteredRecord = childBlockData.data.filter((x) => x.name == childblockid);
    if (filteredRecord.length > 0) {
      if (filteredRecord[0].status == "Complete") {
        setLoaderVisibility(true);        
        const surveyNoData = await getData("Test Survey No", { "child_block_id": filteredRecord[0].name });
        var centerCoord = filteredRecord[0].center_coordinate.replaceAll(" ","").split(",");
        mapRef.current.flyTo({
          center: [centerCoord[0],centerCoord[1]],
          zoom: 15,
          speed: 1.5
        });
        const features = surveyNoData.data.map(({ name, boundary_coordinates, latitude_longitude }) => {
          try {
            const coordinates = [JSON.parse(boundary_coordinates)];
            return {
              type: 'Feature',
              properties: { name, latitude_longitude },
              geometry: {
                type: 'Polygon',
                coordinates: coordinates
              }
            };
          } catch (error) {
            setLoaderVisibility(false);
            console.error(`Invalid coordinates for ${name}:`, boundary_coordinates, error);
            return null; // skip invalid
          }
        }).filter(Boolean); // remove nulls
        let sourceName = 'survey-polygons_' + filteredRecord[0].name;
        let fillLayerName = 'survey-fills_' + filteredRecord[0].name;
        let outLineLayerName = 'survey-outlines_' + filteredRecord[0].name;
        mapRef.current.addSource(sourceName, {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: features
          }
        });
        // Fill layer
        mapRef.current.addLayer({
          id: fillLayerName,
          type: 'fill',
          source: sourceName,
          paint: {
            'fill-color': '#088',
            'fill-opacity': 0.5
          }
        });

        // Outline layer
        mapRef.current.addLayer({
          id: outLineLayerName,
          type: 'line',
          source: sourceName,
          paint: {
            'line-color': '#000',
            'line-width': 2
          }
        });
        // Load info icon explicitly (only once)
        if (!mapRef.current.hasImage('info-icon')) {
          mapRef.current.loadImage(
            'https://docs.mapbox.com/mapbox-gl-js/assets/custom_marker.png', // sample icon
            (error, image) => {
              if (error) throw error;
              if (!mapRef.current.hasImage('info-icon')) {
                mapRef.current.addImage('info-icon', image);
              }
            }
          );
        }


        // Following code is to show icon when user hover on the shape

        let highlightLayerName = 'highlight-boundary_' + filteredRecord[0].name;

        // --- Add highlight source ---
        mapRef.current.addSource(highlightLayerName + '_src', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: []
          }
        });

        // --- Add highlight line layer ---
        mapRef.current.addLayer({
          id: highlightLayerName,
          type: 'line',
          source: highlightLayerName + '_src',
          paint: {
            'line-color': '#ff0000',   // Highlight color
            'line-width': 4            // Highlight thickness
          }
        });

        // --- Hover events ---
        mapRef.current.on('mouseenter', fillLayerName, (e) => {
          const zoom = mapRef.current.getZoom();
          if (zoom > 14) {
            mapRef.current.getCanvas().style.cursor = 'pointer';

            if (e.features.length > 0) {
              const feature = e.features[0];

              // Highlight this boundary
              mapRef.current.getSource(highlightLayerName + '_src').setData({
                type: 'FeatureCollection',
                features: [feature]
              });
            }
          }
          
        });

        mapRef.current.on('mouseleave', fillLayerName, () => {
          mapRef.current.getCanvas().style.cursor = '';

          // Remove highlight
          mapRef.current.getSource(highlightLayerName + '_src').setData({
            type: 'FeatureCollection',
            features: []
          });
        });

        // --- Click event ---
        mapRef.current.on('click', fillLayerName, (e) => {
          if (e.features.length > 0) {
            const { name } = e.features[0].properties;
            // Redirect to another page
            window.open(`/app/test-survey-no/${name}`, '_blank');
          }
        });

        setLoaderVisibility(false);
      }
    }
  }
  const isPointInSquare = (point, squareCoords) => {
    const [lng, lat] = point;

    // squareCoords is a 2D array, take min/max
    const lons = squareCoords.map(c => c[0]);
    const lats = squareCoords.map(c => c[1]);

    const minLng = Math.min(...lons);
    const maxLng = Math.max(...lons);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);

    return (
      lng >= minLng &&
      lng <= maxLng &&
      lat >= minLat &&
      lat <= maxLat
    );
  }

  const checkPointInsideBoundingBoxes = (point, boxes) => {
    return boxes.some(box => {
      const coords = JSON.parse(box.bounding_box); // parse string
      return isPointInSquare(point, coords);
    });
  }
  return (
    <div>
      {showLoader && (
        <div className="flex items-center justify-center h-screen w-screen">
          <LogoLoader text={loaderTitle} />
        </div>
      )}

      <div
        ref={mapContainerRef}
        style={{ height: '800px', width: '100%' }}
        className="maplibregl-map"
      />

      {showModal && (
        <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div
            className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex items-center justify-center z-[345]'
            onClick={() => setModalVisibility(false)}
          >
            <FaXmark size={28} />
          </div>
          <div className='model-content text-lg text-center mt-10'>
            <p>Processing started. Please check back in a few moments and refresh the page.</p>
          </div>
        </div>
      )}
      <div
        id="contextMenu"
        className="context-menu hidden"
        style={{ position: 'absolute', zIndex: 1000 }}
      >
        <div id="createPropertyBtn">Create Main Block Here</div>
      </div>
    </div>
  );
}

export default PropertyCreation;
