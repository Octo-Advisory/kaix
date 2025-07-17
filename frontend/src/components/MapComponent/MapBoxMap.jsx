import React, { useRef, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import { createRoot } from 'react-dom/client';
import { FaStore } from 'react-icons/fa';
import 'mapbox-gl/dist/mapbox-gl.css';
import './style.css';

mapboxgl.accessToken = 'pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ';

const MapBoxMap = ({ lat, lng, zoom = 12, source, vendorCoord, vendorName }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [lng, lat],
      zoom: zoom,
      pitch: 35,
      // bearing: 180,
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
  }, [lat, lng, zoom, source, vendorCoord, vendorName]);

  return (
    <div
      ref={mapContainer}
      className="rounded-xl"
      style={{ width: '100%', height: '100%' }}
    />
  );
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

  vendorEl.addEventListener('mouseenter', () => {
    vendorEl.querySelector('.vendor-label').style.display = 'block';
  });
  vendorEl.addEventListener('mouseleave', () => {
    vendorEl.querySelector('.vendor-label').style.display = 'none';
  });
}

// ➖ Draw Straight Line and Center Distance Label
function drawStraightLineWithDistanceLabel(map, propertyCoord, vendorCoord, vendorName) {
  // 📍 Add Markers
  addMarker(map, propertyCoord, '#ff0000'); // Red for Property
  addVendorMarker(map, vendorCoord, vendorName); // 🏪 FaStore for Vendor

  // ➖ Add Line Source
  map.addSource('property-vendor-line', {
    type: 'geojson',
    data: {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [propertyCoord, vendorCoord],
      }
    }
  });

  // ➖ Add Line Layer
  map.addLayer({
    id: 'property-vendor-line-layer',
    type: 'line',
    source: 'property-vendor-line',
    layout: {
      'line-join': 'round',
      'line-cap': 'round'
    },
    paint: {
      'line-color': '#41b655', // Solid Green
      'line-width': 4,
      'line-opacity': 0.9
    }
  });

  // 🏷️ Add Distance Label at Midpoint
  const midpoint = [
    (propertyCoord[0] + vendorCoord[0]) / 2,
    (propertyCoord[1] + vendorCoord[1]) / 2
  ];

  const distanceKm = getDistance(propertyCoord, vendorCoord).toFixed(2);

  const labelEl = document.createElement('div');
  labelEl.style.background = 'rgba(0, 0, 0, 0.75)';
  labelEl.style.color = '#fff';
  labelEl.style.padding = '4px 8px';
  labelEl.style.borderRadius = '6px';
  labelEl.style.fontSize = '12px';
  labelEl.style.fontWeight = 'bold';
  labelEl.innerText = `${distanceKm} km`;

  new mapboxgl.Marker({
    element: labelEl,
    anchor: 'center'
  })
    .setLngLat(midpoint)
    .addTo(map);

  // 🗺️ Fit map bounds to line
  const bounds = [propertyCoord, vendorCoord].reduce(
    (b, coord) => b.extend(coord),
    new mapboxgl.LngLatBounds(propertyCoord, propertyCoord)
  );
  map.fitBounds(bounds, { padding: 50, duration: 1000 });
}

// 📏 Haversine Formula for Distance in KM
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

export default MapBoxMap;
