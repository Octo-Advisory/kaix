import mapboxgl from "mapbox-gl";
import React, { useEffect, useRef, useState } from "react";
import '.././MapComponent/style.css'
import { useSelector } from 'react-redux';
import 'leaflet/dist/leaflet.css';
import markerImage from '../../assets/markerImage.png'
import Property from "../Property/Property";

function MapComponent({ solutions }) {
  const [solution, setSolution] = useState({})
  const [isModalOpen, setIsModalOpen] = useState(false);
  console.log("solutoinis from  map", solutions);
  const latLongArray = Object.values(solutions).map(item => [...item.lat_long].reverse());
  console.log("lanlomg", latLongArray);

  var map = null;
  const mapContainerRef = useRef(null); // Create a ref for the map container
  mapboxgl.accessToken = 'pk.eyJ1IjoiYW5hbnRhY2hhcnlhbWFycyIsImEiOiJjbTdtemhyZjUwb2xlMmtyMHlsZXR4cXN5In0.QykgfaU-rz_SP4Hz_UsufQ';

  useEffect(() => {
    // Initialize the map after the component mounts
    map = new mapboxgl.Map({
      container: mapContainerRef.current, // Use the ref to attach the map
      style: "mapbox://styles/mapbox/streets-v12", // Map style URL
      center: [73.133661788180035, 22.308428225686328], // Starting position [lng, lat]
      zoom: 14, // Starting zoom
      attributionControl: false
    });
    map.on('style.load', () => {
      draw();
    });
    return () => map.remove(); // Cleanup the map instance on unmount
  }, []); // Empty dependency array to run only once

  const draw = async () => {
    // Define your three coordinates (longitude, latitude)
    const coordinates = latLongArray

    // Get the bounding box
    const bounds = coordinates.reduce((bounds, coord) => bounds.extend(coord), new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));
    let elements = coordinates.map((item) => {
      let id = item[0].toString() + item[1].toString();
      let coordinates = item
      item = []
      item.id = id;
      item.coordinates = coordinates;
      return item
    })
    // Fit the map to the bounds
    map.fitBounds(bounds, {
      padding: 50,   // Adds padding around the points
      maxZoom: 10,   // Prevents zooming in too much
      duration: 1000 // Animation duration in milliseconds
    });

    // // Add a LineString feature to connect these points
    // map.addSource('straight-line', {
    //   type: 'geojson',
    //   data: {
    //     type: 'Feature',
    //     geometry: {
    //       type: 'LineString',
    //       coordinates: coordinates  // Use your existing coordinates
    //     }
    //   }
    // });
 
    // // Add a layer to display the line
    // map.addLayer({
    //   id: 'straight-line-layer',
    //   type: 'line',
    //   source: 'straight-line',
    //   layout: {
    //     'line-join': 'round',
    //     'line-cap': 'round'
    //   },
    //   paint: {
    //     'line-color': '#ff0000', // Red color
    //     'line-width': 3
    //   }
    // });

    
    solutions.forEach(item=>{
      debugger
      if(item.result_type === "Industry_Result"){
        let parsedCoord = JSON.parse(item.boundary_coordinates);
        // Add polygon source
        map.addSource("polygon", {
          type: "geojson",
          data: {
              type: "Feature",
              properties: {},
              geometry: {
                  type: "Polygon",
                  coordinates: [parsedCoord],
              },
          },
      }
    
    );

      // Add fill layer for polygon
      map.addLayer({
          id: "polygon-fill",
          type: "fill",
          source: "polygon",
          layout: {},
          paint: {
              "fill-color": "#ff0000", // Red color
              "fill-opacity": 0.5, // 50% transparent
          },
      });

      // Add border for polygon
      map.addLayer({
          id: "polygon-border",
          type: "line",
          source: "polygon",
          layout: {},
          paint: {
              "line-color": "#000000", // Black border
              "line-width": 2,
          },
      });
      }

    })
    laodbindDataOnMap(elements, "Property")
    
 
  }
  const laodbindDataOnMap = async (elements, layerType) => {
    let featureCollectionArray = []
    //loop over all the elements in the array and create feature array
    elements.forEach((data) => {
      let arr = {
        type: "Feature",
        properties: { id: data.coordinates },
        geometry: {
          type: "Point",
          coordinates: data.coordinates, // Change coordinates as needed
        },
      };

      featureCollectionArray.push(arr);
    });

    //laod the image
    let image = await loadMapboxImage(map, markerImage);
    //create imageId and image name
    const imagenameId = "MakkerImage"
    const imagename = "custom-marker_" + imagenameId;
    map.addImage(imagename, image);

    //create sourceId and layerID
    const sourceId = layerType
    const layerId = "Custom_" + layerType
    // Add a GeoJSON source with the point where you want to display the marker
    map.addSource(sourceId, {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: featureCollectionArray,
      },
    });

    // Add a layer to use the image as a symbol layer
    map.addLayer({
      id: layerId,
      type: "symbol",
      source: sourceId,
      layout: {
        "icon-image": imagename,
        "icon-size": 0.09, // Adjust the icon size as necessary
        //'icon-allow-overlap': true,  // Allow overlap
        // 'icon-ignore-placement': true // Ignore placement rules
      },
    });
    // map.on("click", layerId, (e) => {
    //   let id = e.features[0].properties.id;
    //   console.log("id", id);

    //   try {
    //     let parsedId = JSON.parse(id); // Convert string to array
    //     console.log("Parsed Array:", parsedId);

    //     if (Array.isArray(parsedId)) {
    //       let targetLatLong = parsedId.reverse(); // Reverse the array
    //       const sol = Object.entries(solutions).find(([item, value]) => {
    //         console.log("value.lat_long", value.lat_long);
    //         console.log("targetLatLong", targetLatLong);

    //         return (
    //           Array.isArray(value.lat_long) &&
    //           Array.isArray(targetLatLong) &&
    //           value.lat_long.length === targetLatLong.length &&
    //           value.lat_long.every((num, index) => num === targetLatLong[index])
    //         );
    //       });

    //       console.log("sol is",sol[1]);


    //       setSolution(sol[1])
    //     }
    //   } catch (error) {
    //     console.error("Error parsing id:", error);
    //   }
    //   console.log("solutoin is",solution);

    //   <Property solution={solution} />

    // });
    // Change the cursor to a pointer when the mouse is over the places layer.

    map.on("click", layerId, (e) => {
      let id = e.features[0].properties.id;

      try {
        let parsedId = JSON.parse(id);
        let targetLatLong = parsedId.reverse();

        const foundSolution = Object.values(solutions).find(value =>
          JSON.stringify(value.lat_long) === JSON.stringify(targetLatLong)
        );

        if (foundSolution) {
          setSolution(foundSolution);
          setIsModalOpen(true);
        }
      } catch (error) {
        console.error("Error parsing id:", error);
      }
    });

    map.on("mouseenter", layerId, () => {
      map.getCanvas().style.cursor = "pointer";
    });

    // Change it back to a pointer when it leaves.
    map.on("mouseleave", layerId, () => {
      map.getCanvas().style.cursor = "";
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

  return (
    <div className="main-map h-full w-full">
      <div
        id="map-container"
        ref={mapContainerRef} // Attach ref to this container
        style={{ width: "100%", height: "90%" }} // Set width and height for the map container
      />

      {isModalOpen && solution && (
        <Modal onClose={() => setIsModalOpen(false)}>
          <Property solution={solution} />
        </Modal>
      )}

    </div>
  );
}

export default MapComponent;


const Modal = ({ children, onClose }) => {
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="close-button" onClick={onClose}>×</button>
        {children}
      </div>
    </div>
  );
};