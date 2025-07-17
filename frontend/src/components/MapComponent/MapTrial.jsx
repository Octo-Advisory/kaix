import React, { useEffect, useRef, useState } from "react";
import './style.css'
import { useSelector } from 'react-redux';
import markerImage from '../../assets/markerImage.png'
import Property from "../Property/Property";
import Vendorcards from "../ResultScreens/Vendorcards";
import IndustryResultScreen from "../ResultScreens/IndustryResultScreen";
import Vendorresult from "../ResultScreens/Vendorresult";
import { FaXmark } from "react-icons/fa6";

function MapTrial({ solutions, toggleModal, source }) {
  console.log("solutions from map", solutions);
  const validation_result = useSelector((state) => state.validate.validation_result)
  console.log("propertyCoord1", validation_result);
  let propertyCoord = validation_result?.[0]?.[1]?.latitude_longitude?.split(",").map(Number).reverse() ?? null;
  console.log("propertyCoord2", propertyCoord);
  const [solution, setSolution] = useState({})
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [polygons, setPolygons] = useState([]);
  const [polylines, setPolylines] = useState([]);

  const mapContainerRef = useRef(null);
  const latLongArray = Object.values(solutions).map(item => [...item.latitude_longitude].reverse());

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

  useEffect(() => {
    // Initialize the map after the component mounts
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyCoC0x7VGaq82aBoGTZStt6qfqO03_HiG8&libraries=drawing,geometry`;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
      
      script.onload = () => {
        initMap();
      };
    } else {
      initMap();
    }

    return () => {
      // Cleanup markers, polygons, and polylines when component unmounts
      markers.forEach(marker => marker.setMap(null));
      polygons.forEach(polygon => polygon.setMap(null));
      polylines.forEach(polyline => polyline.setMap(null));
      if (map) {
        // Google Maps doesn't have a direct remove() method, but we can detach it
        const mapElement = mapContainerRef.current;
        if (mapElement) {
          mapElement.innerHTML = '';
        }
      }
    };
  }, []);

  const initMap = () => {
    const google = window.google;
    const mapOptions = {
      center: new google.maps.LatLng(22.308428225686328, 73.133661788180035), // [lat, lng]
      zoom: 14,
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      disableDefaultUI: true,
      gestureHandling: 'greedy'
    };

    const newMap = new google.maps.Map(mapContainerRef.current, mapOptions);
    setMap(newMap);
    draw(newMap);
  };

  const draw = (map) => {
    if (!map) return;

    // Filter out invalid coordinates
    const validCoordinates = latLongArray.filter(isValidLatLng);
    if (validCoordinates.length === 0) return;

    // Create bounds and add markers
    const bounds = new window.google.maps.LatLngBounds();
    const newMarkers = [];
    const newPolygons = [];
    const newPolylines = [];

    // Add markers for each solution
    solutions.forEach((item, index) => {
      const coords = [...item.latitude_longitude].reverse();
      if (!isValidLatLng(coords)) return;

      const latLng = new window.google.maps.LatLng(coords[1], coords[0]);
      bounds.extend(latLng);

      const marker = new window.google.maps.Marker({
        position: latLng,
        map: map,
        // icon: {
        //   url: markerImage,
        //   scaledSize: new window.google.maps.Size(30, 30),
        //   origin: new window.google.maps.Point(0, 0),
        //   anchor: new window.google.maps.Point(15, 15)
        // }
      });

      // Add click event to show solution details
      marker.addListener('click', () => {
        setSolution(item);
        setIsModalOpen(true);
      });

      newMarkers.push(marker);

      // Draw polygon for Industry_Result
      if (item.result_type === "Industry_Result") {
        try {
          const parsedCoord = JSON.parse(item.boundary_coordinates);
          const polygonCoords = parsedCoord.map(coord => ({
            lat: coord[1],
            lng: coord[0]
          }));

          const polygon = new window.google.maps.Polygon({
            paths: polygonCoords,
            strokeColor: "#000000",
            strokeOpacity: 1,
            strokeWeight: 2,
            fillColor: "#ff0000",
            fillOpacity: 0.5,
            map: map
          });

          // Add click event to polygon
          polygon.addListener('click', () => {
            setSolution(item);
            setIsModalOpen(true);
          });

          newPolygons.push(polygon);
        } catch (error) {
          console.error("Error parsing boundary coordinates:", error);
        }
      }
    });

    // Draw lines between property and vendors
    const hasVendorResult = solutions.some(item => item.result_type === "Vendor");
    if (hasVendorResult) {
      if (!propertyCoord) {
        propertyCoord = source === 'SolutionScreen' ? solution : solutions
          .filter(item => Array.isArray(item?.user_lat_long) && item.user_lat_long.length > 0)
          .map(item => item?.user_lat_long.slice().reverse());
        propertyCoord = propertyCoord[0];
      }

      if (propertyCoord && isValidLatLng(propertyCoord)) {
        const propertyLatLng = new window.google.maps.LatLng(propertyCoord[1], propertyCoord[0]);
        bounds.extend(propertyLatLng);

        // Add property marker
        const propertyMarker = new window.google.maps.Marker({
          position: propertyLatLng,
          map: map,
        //   icon: {
        //     url: markerImage,
        //     scaledSize: new window.google.maps.Size(40, 40),
        //     origin: new window.google.maps.Point(0, 0),
        //     anchor: new window.google.maps.Point(20, 20)
        //   }
        });
        newMarkers.push(propertyMarker);

        // Draw lines to each vendor
        validCoordinates.forEach(vendorCoord => {
          const vendorLatLng = new window.google.maps.LatLng(vendorCoord[1], vendorCoord[0]);
          
          const line = new window.google.maps.Polyline({
            path: [propertyLatLng, vendorLatLng],
            geodesic: true,
            strokeColor: '#ff0000',
            strokeOpacity: 1.0,
            strokeWeight: 2,
            map: map
          });

          newPolylines.push(line);
        });
      }
    }

    // Fit bounds with padding
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, {
        top: 50,
        bottom: 50,
        left: 50,
        right: 50
      });
    }

    setMarkers(newMarkers);
    setPolygons(newPolygons);
    setPolylines(newPolylines);
  };

  useEffect(() => {
    console.log('this is the solution of selected', solution);
  }, [solution]);

  return (
    <div className="main-map h-screen w-screen flex items-center justify-center">
      <div
        id="map-container"
        ref={mapContainerRef}
        style={{ width: "100%", height: "100%" }}
      />
      {isModalOpen && solution && (
        <Modal key={solution.result_type} onClose={() => setIsModalOpen(false)} type={solution.result_type}>
          {solution.result_type === "Vendor" && <Vendorresult result={solution} source="MapComponent" />}
          {solution.result_type === "Industry_Result" && <IndustryResultScreen result={solution} source="MapComponent" />}
        </Modal>
      )}
    </div>
  );
}

export default MapTrial;

const Modal = ({ children, onClose, type }) => {
  return (
    <div className="fixed top-0 h-full w-full flex gap-4 items-center">
      <div className={`${type === 'Vendor' ? 'top-7 right-12' : type === "Industry_Result" ? 'top-5 right-5' : ''} absolute z-[335] cursor-pointer h-8 w-8 rounded-full bg-white shadow-md flex items-center justify-center`} onClick={onClose}>
        <FaXmark size={20} />
      </div>
      <div className={`modal-content relative h-full w-full flex items-center justify-center ${type === "Industry_Result" ? 'overflow-y-auto' : ''}`}>
        {children}
      </div>
    </div>
  );
};