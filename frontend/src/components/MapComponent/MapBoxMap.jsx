import React, { useRef, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import { createRoot } from 'react-dom/client';
import { FaStore } from 'react-icons/fa';
import 'mapbox-gl/dist/mapbox-gl.css';
import './style.css';
import { getDistance, getCurvedLine, addInfoPopup } from "./utils";
import { useFrappeGetDoc } from "frappe-react-sdk";

const MapBoxMap = ({ lat, lng, zoom = 10, source, vendorCoord, vendorName }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Mapping")
  const configurations = uiData?.configurations || [];
  const uiConfig = configurations.reduce((acc, curr) => {
    acc[curr.key] = curr.value;
    return acc;
  }, {});
  useEffect(() => {
    if (!mapContainer.current || !uiData) return;
    mapboxgl.accessToken = `${uiConfig?.['mapmobx_api_token']}`;
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [lng, lat],
      zoom: zoom,
      pitch: 35,
      // bearing: 180,
      interactive: false,
      antialias: true,
    });

    map.current.on('style.load', () => {
      if (source === "FromVendor" && vendorCoord) {
        drawStraightLineWithDistanceLabel(
          map.current,
          vendorCoord,      // propertyCoord (📍 red marker)
          [lng, lat],       // vendorCoord (🏪 FaStore)
          vendorName
        );
      } else if (source === "FromProperty") {
        addMarker(map.current, [lng, lat], 'red'); // 📍 Property only
      } else {
        addVendorMarker(map.current, [lng, lat], vendorName); // 🏪 Vendor only
      }
    });

    return () => map.current.remove();
  }, [lat, lng, zoom, source, vendorCoord, vendorName, uiData]);

  const generateCurveLine = ({ sourceId = "", layerId = "", from = "", to = "", linecolor = "", curvature = 0.4, labelText = "" } = {}) => {
    let getCurvedLineCoord = getCurvedLine(from, to, curvature);
    getCurvedLineCoord.push(to);
    map.current.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: getCurvedLineCoord,
        }
      }
    });

    map.current.addLayer({
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
      .addTo(map.current);
  };
  // 📍 Generic Marker (Red or other colors)
  function addMarker(map, coord, color) {
    new mapboxgl.Marker({ color })
      .setLngLat(coord)
      .addTo(map);
  }

  // 🏪 Vendor Marker with Hover Label
  function addVendorMarker(map, vendorCoord, vendorName) {
    const vendorEl = document.createElement('div');
    vendorEl.style.width = '40px';
    vendorEl.style.height = '40px';
    vendorEl.style.display = 'flex';
    vendorEl.style.alignItems = 'center';
    vendorEl.style.justifyContent = 'center';

    const root = createRoot(vendorEl);
    root.render(
      <div style={{
        background: 'white',
        borderRadius: '50%',
        padding: '4px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
        position: 'relative'
      }}>
        <FaStore size={24} color="#4A76D1" />
        <div className="vendor-label" style={{
          display: 'none',
          position: 'absolute',
          top: '-30px',
          background: 'rgba(0,0,0,0.75)',
          color: '#fff',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '12px',
          whiteSpace: 'nowrap'
        }}>
          {vendorName || 'Vendor'}
        </div>
      </div>
    );

    const marker = new mapboxgl.Marker({
      element: vendorEl,
      anchor: 'bottom'
    })
      .setLngLat(vendorCoord)
      .addTo(map);

    addInfoPopup(mapboxgl,map, marker, vendorName);

    // vendorEl.addEventListener('mouseenter', () => {
    //   vendorEl.querySelector('.vendor-label').style.display = 'block';
    // });
    // vendorEl.addEventListener('mouseleave', () => {
    //   vendorEl.querySelector('.vendor-label').style.display = 'none';
    // });
  }

  // ➖ Draw Straight Line and Center Distance Label
  function drawStraightLineWithDistanceLabel(map, propertyCoord, vendorCoord, vendorName) {
    // 📍 Add Markers
    addMarker(map, propertyCoord, '#ff0000'); // Red for Property
    addVendorMarker(map, vendorCoord, vendorName); // 🏪 FaStore for Vendor
    let distanceKm = getDistance(propertyCoord, vendorCoord).toFixed(2);
    const labelText = `${distanceKm} km`;

    const curvedLineSourceId = 'property-vendor-line';
    const curvedLineLayerId = 'property-vendor-line-layer';
    // const labelText = name !== "" ? `${name} </br> ${distanceKm} km` : `${distanceKm} km`;
    generateCurveLine({ sourceId: curvedLineSourceId, layerId: curvedLineLayerId, from: propertyCoord, to: vendorCoord, linecolor: '#5f2abb', labelText: labelText });
    // ➖ Add Line Source
    // map.addSource('property-vendor-line', {
    //   type: 'geojson',
    //   data: {
    //     type: 'Feature',
    //     geometry: {
    //       type: 'LineString',
    //       coordinates: [propertyCoord, vendorCoord],
    //     }
    //   }
    // });

    // // ➖ Add Line Layer
    // map.addLayer({
    //   id: 'property-vendor-line-layer',
    //   type: 'line',
    //   source: 'property-vendor-line',
    //   layout: {
    //     'line-join': 'round',
    //     'line-cap': 'round'
    //   },
    //   paint: {
    //     'line-color': '#41b655', // Solid Green
    //     'line-width': 4,
    //     'line-opacity': 0.9
    //   }
    // });

    // 🏷️ Add Distance Label at Midpoint
    // const midpoint = [
    //   (propertyCoord[0] + vendorCoord[0]) / 2,
    //   (propertyCoord[1] + vendorCoord[1]) / 2
    // ];

    // const distanceKm = getDistance(propertyCoord, vendorCoord).toFixed(2);

    // const labelEl = document.createElement('div');
    // labelEl.style.background = 'rgba(0, 0, 0, 0.75)';
    // labelEl.style.color = '#fff';
    // labelEl.style.padding = '4px 8px';
    // labelEl.style.borderRadius = '6px';
    // labelEl.style.fontSize = '12px';
    // labelEl.style.fontWeight = 'bold';
    // labelEl.innerText = `${distanceKm} km`;

    // new mapboxgl.Marker({
    //   element: labelEl,
    //   anchor: 'center'
    // })
    //   .setLngLat(midpoint)
    //   .addTo(map);

    // 🗺️ Fit map bounds to line
    const bounds = [propertyCoord, vendorCoord].reduce(
      (b, coord) => b.extend(coord),
      new mapboxgl.LngLatBounds(propertyCoord, propertyCoord)
    );
    map.fitBounds(bounds, { padding: 60, duration: 1000 });
  }

  return (
    <div
      ref={mapContainer}
      className="rounded-xl"
      style={{ width: '100%', height: '100%' }}
    />
  );
};
export default MapBoxMap;
