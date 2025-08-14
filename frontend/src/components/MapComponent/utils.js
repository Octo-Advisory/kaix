export const getMidpointSimple = (coord1, coord2) => {
  const midLat = (coord1[0] + coord2[0]) / 2;
  const midLng = (coord1[1] + coord2[1]) / 2;
  return [midLat, midLng];
}

export const getDistance = (coord1, coord2) => {
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

export const getDistanceForMidpoint = (p1, p2) => {
  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];
  return Math.sqrt(dx * dx + dy * dy);
}

export const interpolate = (p1, p2, t) => {
  return [
    p1[0] + (p2[0] - p1[0]) * t,
    p1[1] + (p2[1] - p1[1]) * t
  ];
}

export const getMidpointByLength = (coords) => {
  // Step 1: Calculate total length
  let totalLength = 0;
  const segments = [];

  for (let i = 0; i < coords.length - 1; i++) {
    const p1 = coords[i];
    const p2 = coords[i + 1];
    const segmentLength = getDistanceForMidpoint(p1, p2);
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

// Function to generate curved (Bézier) coordinates
export const getCurvedLine = (start, end, curvature = 0.4, numPoints = 150) => {
  const [x0, y0] = start;
  const [x2, y2] = end;

  // Midpoint between start and end
  const mx = (x0 + x2) / 2;
  const my = (y0 + y2) / 2;

  // Direction vector from start to end
  const dx = x2 - x0;
  const dy = y2 - y0;

  // ✅ These two lines define the direction and strength of the curve
  //    Change the sign of `curvature` to bend left or right
  const offsetX = -dy * curvature; // Perpendicular to the line (left/right deviation)
  const offsetY = dx * curvature;  // Perpendicular to the line (left/right deviation)

  // Control point: the "pull" of the curve
  const cx = mx + offsetX;
  const cy = my + offsetY;

  // Generate points along a quadratic Bézier curve
  const curve = [];
  for (let t = 0; t <= 1; t += 1 / numPoints) {
    const x = (1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * cx + t * t * x2;
    const y = (1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * cy + t * t * y2;
    curve.push([x, y]);
  }

  return curve;
}
export const addInfoPopup = (mapboxgl,map, marker, name) => {
  console.log("Map: ", map);
  // Create a popup but don't add it yet
  const popup = new mapboxgl.Popup({
    closeButton: false,
    closeOnClick: false,
    offset: 25,
    className: '' // Add a class for custom styling if needed
  }).setText(name);
  console.log("Marker: ", marker);
  console.log("Popup: ", popup);
  
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
}