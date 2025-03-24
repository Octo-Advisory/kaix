import mapboxgl from "mapbox-gl";
import React, { useEffect, useRef, useState } from "react";
import '.././MapComponent/style.css'
import { useSelector } from 'react-redux';
import 'leaflet/dist/leaflet.css';
import markerImage from '../../assets/markerImage.png'
import Property from "../Property/Property";
import Vendorcards from "../ResultScreens/Vendorcards";

function MapComponent({ solutions }) {
  console.log("solutons from map", solutions);
  const validation_result = useSelector((state) => state.validate.validation_result)
  console.log("propertyCoord1", validation_result);
  let propertyCoord = validation_result?.[0]?.[1]?.latitude_longitude?.split(",").map(Number).reverse() ?? null;
  console.log("propertyCoord2",propertyCoord);
  const [solution, setSolution] = useState({})
  const [isModalOpen, setIsModalOpen] = useState(false);
  // console.log("solutoinis from  map", solutions);

  const latLongArray = Object.values(solutions).map(item => [...item.latitude_longitude].reverse());

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
  const draw = async () => {
    // Filter out invalid coordinates
    const validCoordinates = latLongArray.filter(isValidLatLng);

    // Define your three coordinates (longitude, latitude)
    //const coordinates = latLongArray

    const coordinates = validCoordinates;

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


    solutions.forEach(item => {
      //#region Code to draw Property Boundry on the map
      if (item.result_type === "Industry_Result") {
        let parsedCoord = JSON.parse(item.boundary_coordinates);
        let sourceId = `Custom_Source_${crypto.randomUUID()}`;
        // Add polygon source
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
        }

        );
        let layerId1 = `Custom_polygon_fill_${crypto.randomUUID()}`;
        let layerId2 = `Custom_polygon-border_${crypto.randomUUID()}`;
        // Add fill layer for polygon
        map.addLayer({
          id: layerId1,
          type: "fill",
          source: sourceId,
          layout: {},
          paint: {
            "fill-color": "#ff0000", // Red color
            "fill-opacity": 0.5, // 50% transparent
          },
        });

        // Add border for polygon
        map.addLayer({
          id: layerId2,
          type: "line",
          source: sourceId,
          layout: {},
          paint: {
            "line-color": "#000000", // Black border
            "line-width": 2,
          },
        });
      }

      //#endregion


    })

    //#region Draw connected line between vendor and search city/State
    let layerId = `Custom_property_vendor_lines_layer_${crypto.randomUUID()}`;
    const hasVendorResult = solutions.some(item => item.result_type === "Vendor");
    
    if (hasVendorResult) {
      if(!propertyCoord){
        propertyCoord = solution
      .filter(item => Array.isArray(item?.user_lat_long) && item.user_lat_long.length > 0)
      .map(item => item.user_lat_long[0].split(",").map(Number))
      .reverse();
      }
      // Generate LineString Features
      const lines = latLongArray.map(vendorCoord => ({
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [propertyCoord, vendorCoord] // Draw a line between property and vendor
        },
        properties: {}
      }));

      // Add Line Source
      map.addSource('property-vendor-lines', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: lines
        }
      });

      // Add Line Layer
      map.addLayer({
        id: layerId,
        type: 'line',
        source: 'property-vendor-lines',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#ff0000', // Red color lines
          'line-width': 2
        }
      });
    }

    //#endregion

    //#region Add the pointer on the map
    addPointerOnMap(elements, crypto.randomUUID())
    //#endregion    


  }
  const addPointerOnMap = async (elements, layerType) => {
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
    // Generate a unique ID for the source
    let sourceId = `polygon-${crypto.randomUUID()}`;
    // const sourceId = layerType
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
        "icon-size": 0.07, // Adjust the icon size as necessary
        'icon-allow-overlap': true,  // Allow overlap
        // 'icon-ignore-placement': true // Ignore placement rules
      },
    });
    // map.on("click", layerId, (e) => {
    //   let id = e.features[0].properties.id;
    //   // console.log("id", id);

    //   try {
    //     let parsedId = JSON.parse(id); // Convert string to array
    //     // console.log("Parsed Array:", parsedId);

    //     if (Array.isArray(parsedId)) {
    //       let targetLatLong = parsedId.reverse(); // Reverse the array
    //       const sol = Object.entries(solutions).find(([item, value]) => {
    //         // console.log("value.lat_long", value.lat_long);
    //         // console.log("targetLatLong", targetLatLong);

    //         return (
    //           Array.isArray(value.lat_long) &&
    //           Array.isArray(targetLatLong) &&
    //           value.lat_long.length === targetLatLong.length &&
    //           value.lat_long.every((num, index) => num === targetLatLong[index])
    //         );
    //       });

    //       // console.log("sol is",sol[1]);


    //       setSolution(sol[1])
    //     }
    //   } catch (error) {
    //     console.error("Error parsing id:", error);
    //   }
    //   // console.log("solutoin is",solution);

    //   <Property solution={solution} />

    // });
    // Change the cursor to a pointer when the mouse is over the places layer.

    map.on("click", layerId, (e) => {
      let id = e.features[0].properties.id;

      try {
        let parsedId = JSON.parse(id);
        let targetLatLong = parsedId.reverse();

        const foundSolution = Object.values(solutions).find(value =>
          JSON.stringify(value.latitude_longitude) === JSON.stringify(targetLatLong)
        );

        console.log("foundsolution is",foundSolution);
        
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
        <Modal key={solution.result_type} onClose={() => setIsModalOpen(false)}>
          {solution.result_type === "Industry_Result" && <Property solution={solution} />}
          {solution.result_type === "Vendor" && <Vendorcards supplier={solution} />}
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