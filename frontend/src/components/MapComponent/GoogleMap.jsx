import React, { useEffect, useRef } from "react";

const GoogleMap = ({ lat, lng, tooltipText }) => {
  const mapRef = useRef(null);

  useEffect(() => {
    // Load Google Maps script if not already loaded
    if (!window.google) {
      const script = document.createElement("script");
      script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyCoC0x7VGaq82aBoGTZStt6qfqO03_HiG8`;
      script.async = true;
      script.defer = true;
      script.onload = () => initializeMap();
      document.head.appendChild(script);
    } else {
      initializeMap();
    }

    function initializeMap() {
      const coords = { lat: parseFloat(lat), lng: parseFloat(lng) };

      const map = new window.google.maps.Map(mapRef.current, {
        zoom: 12,
        center: coords,
        // ✅ Disable default controls like zoom, map type, etc.
        disableDefaultUI: true,
        // Optional: Enable only specific controls (commented out here)
        // zoomControl: false,
        // mapTypeControl: false,
        // streetViewControl: false,
        // fullscreenControl: false
      });

      const marker = new window.google.maps.Marker({
        position: coords,
        map: map,
      });

      const infoWindow = new window.google.maps.InfoWindow({
        content: tooltipText || "Location Marker",
      });

      // Open InfoWindow on marker hover
      marker.addListener("mouseover", () => {
        infoWindow.open(map, marker);
      });

      // Close InfoWindow on mouseout
      marker.addListener("mouseout", () => {
        infoWindow.close();
      });
    }
  }, [lat, lng, tooltipText]);

  return <div ref={mapRef} style={{ width: "100%", height: "100%" }} />;
};

export default GoogleMap;
