// export default PropertyCreation;
import React, { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useFrappeEventListener } from 'frappe-react-sdk';
import LogoLoader from '../Responseloader/LogoLoader';
import { FaXmark } from "react-icons/fa6";
import './assets/style/propertycreationstyle.css';

mapboxgl.accessToken = 'pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ';
const BASE_URL = 'https://marsinfraix.marsbazaar.com';
const API_TOKEN = 'd3de1e0e4e25846:51fd8e403a19045';

function PropertyCreation() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  const [showLoader, setLoaderVisibility] = useState(false);
  const [showModal, setModalVisibility] = useState(false);
  const [loaderTitle, setLoaderTitle] = useState("Processing");

  // Frappe event listener
  useFrappeEventListener("Property_Seg_Status_Update", async ({ message }) => {
    setLoaderTitle(message);
    if (message.includes("Error") || message.includes("Property creating ended")) {
      setLoaderVisibility(false);
    }
    console.log("Event data:", message);
  });
  useEffect(() => {
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [73.133661788180035, 22.308428225686328],
      zoom: 8,
      attributionControl: false
    });

    mapRef.current = map;

    mapRef.current.on('style.load', draw);

    // Context menu logic
    const contextMenu = document.getElementById('contextMenu');
    const createBtn = document.getElementById('createPropertyBtn');
    let lngLat = null;

    // Show custom context menu on right-click
    mapRef.current.on('contextmenu', (e) => {
      e.preventDefault();
      lngLat = e.lngLat;

      contextMenu.style.top = `${e.originalEvent.clientY}px`;
      contextMenu.style.left = `${e.originalEvent.clientX}px`;
      contextMenu.classList.remove('hidden');
    });

    // Hide menu on map click or move
    const hideContextMenu = () => contextMenu.classList.add('hidden');
    mapRef.current.on('click', hideContextMenu);
    mapRef.current.on('movestart', hideContextMenu);

    // Handle click on "Create Property here"
    createBtn.onclick = () => {
      contextMenu.classList.add('hidden');
      console.log("Create Property at:", lngLat);
      setModalVisibility(true);
      // alert(`Create property at:\nLat: ${lngLat.lat}, Lng: ${lngLat.lng}`);
      createMainBlock(lngLat.lat, lngLat.lng);
      // 🔁 Replace this with triggerProSeg or other logic
    };

    // Cleanup
    return () => {
      mapRef.current.remove();
      mapRef.current.off('click', hideContextMenu);
      mapRef.current.off('movestart', hideContextMenu);
      mapRef.current.off('contextmenu');
    };
  }, []);

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
    const res = await getData("Child Block");

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
        position: 'absolute',
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

      const btn = createButton(
        config.label,
        config.color,
        config.leftOffset,
        () => config.buttonClick(coordinates, el.name)
      );

      new mapboxgl.Marker({ element: btn, anchor: 'bottom-left' })
        .setLngLat([lat, lng])
        .addTo(mapRef.current);
    });
    //Create property 
    for (const element of res.data) {
      if (element.status == "Complete") {
        debugger
        const res = await getData("Test Survey No", { "child_block_id": element.name });
        const features = res.data.map(({ name, boundary_coordinates }) => {
          try {
            const coordinates = [JSON.parse(boundary_coordinates)];
            return {
              type: 'Feature',
              properties: { name },
              geometry: {
                type: 'Polygon',
                coordinates: coordinates
              }
            };
          } catch (error) {
            console.error(`Invalid coordinates for ${name}:`, boundary_coordinates, error);
            return null; // skip invalid
          }
        }).filter(Boolean); // remove nulls
        let sourceName = 'survey-polygons_' + element.name;
        let fillLayerName = 'survey-fills_' + element.name;
        let outLineLayerName = 'survey-outlines_' + element.name;
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
      }
    }

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
        <div id="createPropertyBtn">Create Property here</div>
      </div>
    </div>
  );
}

export default PropertyCreation;
