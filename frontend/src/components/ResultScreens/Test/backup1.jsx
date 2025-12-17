import React, { useState, useRef, useEffect } from 'react';
import { FaArrowRightLong } from "react-icons/fa6";
import { IoInformationCircleOutline } from "react-icons/io5";
import { FaTrain, FaBus, FaRegQuestionCircle } from "react-icons/fa";
import { BsPatchCheckFill } from "react-icons/bs";
import { MdOfflineBolt } from "react-icons/md";
import { IoWifi } from "react-icons/io5";
import { RiShipFill } from "react-icons/ri";
import { FaRoad } from "react-icons/fa6";
import { IoAirplane } from "react-icons/io5";
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import './neww.css'
import PropertySlider from './PropertySlider';



const CircularInfographic = () => {
   ChartJS.register(ArcElement, Tooltip, Legend);
  const canvasRef = useRef(null);
  const [activeArc, setActiveArc] = useState(null);
  const [showConnectors, setShowConnectors] = useState(true);
  const [aside,setAside] = useState(false)
  const [activeFactor, setActiveFactor] = useState('Approvals')
  const [activeView , setActiveView] = useState('Property Overview')
  // Canvas center coordinates
  const centerX = 300;
  const centerY = 380;
  
  // Fixed start and end positions (in radians)
  const fixedStartAngle = Math.PI / 6;      // 30 degrees
  const fixedEndAngle = 3 * Math.PI / 2;    // 270 degrees
  
  // Arc colors
  // const [arcColors, setArcColors] = useState([
  //   "#FF6B6B", // Red
  //   "#4ECDC4", // Teal
  //   "#FFD166", // Yellow
  //   "#6A0572", // Purple
  //   "#1a2a6c"  // Dark Blue
  // ]);

  const [arcColors, setArcColors] = useState([
  "#0369a1", // Steel Blue
  "#0d9488", // Teal
  "#059669", // Emerald
  "#65a30d", // Olive
  "#4d7c0f"  // Army Green
]);
  
  // Info box positions - ALL BOXES NOW ABOVE THE ARC CENTER (y < 300)
  const infoBoxPositions = [
    { x: 650, y: 40, width: 250, height: 70 },   // Box 1 - Top
    { x: 650, y: 120, width: 250, height: 70 },  // Box 2
    { x: 650, y: 200, width: 250, height: 70 },  // Box 3 - Middle (still above center)
    { x: 650, y: 280, width: 250, height: 70 },  // Box 4
    { x: 650, y: 360, width: 250, height: 70 }   // Box 5
  ];
  
  // Arcs configuration
  // const arcs = [
  //   {
  //     id: 1,
  //     radius: 80,
  //     startAngle: fixedStartAngle + (0.2 * Math.PI),
  //     endAngle: fixedEndAngle,
  //     color: arcColors[0],
  //     strokeWidth: 35,
  //     title: "Approval",
  //     score: 6.5,
  //     description: "Shows the overall approval rating and key areas for improvement."
  //   },
  //   {
  //     id: 2,
  //     radius: 120,
  //     startAngle: fixedStartAngle + (0.15 * Math.PI),
  //     endAngle: fixedEndAngle,
  //     color: arcColors[1],
  //     strokeWidth: 35,
  //     title: "Vendors",
  //     score: 8.5,
  //     description: "Highlights vendor performance in delivery, quality, and satisfaction."
  //   },
  //   {
  //     id: 3,
  //     radius: 160,
  //     startAngle: fixedStartAngle + (0.1 * Math.PI),
  //     endAngle: fixedEndAngle,
  //     color: arcColors[2],
  //     strokeWidth: 35,
  //     title: "Employment",
  //     score: 9.0,
  //     description: "Overview of employee engagement, including satisfaction and retention."
  //   },
  //   {
  //     id: 4,
  //     radius: 200,
  //     startAngle: fixedStartAngle + (0.05 * Math.PI),
  //     endAngle: fixedEndAngle,
  //     color: arcColors[3],
  //     strokeWidth: 35,
  //     score: 4.5,
  //     title: "Incentives",
  //     description: "Evaluates the impact of incentive programs on motivation and productivity."
  //   },
  //   {
  //     id: 5,
  //     radius: 240,
  //     startAngle: fixedStartAngle,
  //     endAngle: fixedEndAngle,
  //     color: arcColors[4],
  //     strokeWidth: 35,
  //     title: "Location Summary",
  //     score: 8.9,
  //     description: "Summarizes performance and conditions across different locations"
  //   }
  // ];
 const arcStrokeWidth = 40;
  const baseRadius = 80; 
  const arcs = [
  {
    id: 1,
    radius: baseRadius, // Innermost arc
    startAngle: fixedStartAngle + (0.2 * Math.PI),
    endAngle: fixedEndAngle,
    color: arcColors[0],
    strokeWidth: arcStrokeWidth,
    title: "Approval",
    score: 6.5,
    description: "Shows the overall approval rating and key areas for improvement.",
    connectorOffset: -120
  },
  {
    id: 2,
    radius: baseRadius + arcStrokeWidth, // Touches the outer edge of arc 1
    startAngle: fixedStartAngle + (0.15 * Math.PI),
    endAngle: fixedEndAngle,
    color: arcColors[1],
    strokeWidth: arcStrokeWidth,
    title: "Vendors",
    score: 8.5,
    description: "Highlights vendor performance in delivery, quality, and satisfaction.",
    connectorOffset: -90
  },
  {
    id: 3,
    radius: baseRadius + (arcStrokeWidth * 2), // Touches the outer edge of arc 2
    startAngle: fixedStartAngle + (0.1 * Math.PI),
    endAngle: fixedEndAngle,
    color: arcColors[2],
    strokeWidth: arcStrokeWidth,
    title: "Employment",
    score: 9.0,
    description: "Overview of employee engagement, including satisfaction and retention.",
    connectorOffset: -60
  },
  {
    id: 4,
    radius: baseRadius + (arcStrokeWidth * 3), // Touches the outer edge of arc 3
    startAngle: fixedStartAngle + (0.05 * Math.PI),
    endAngle: fixedEndAngle,
    color: arcColors[3],
    strokeWidth: arcStrokeWidth,
    title: "Incentives",
    score: 4.5,
    description: "Evaluates the impact of incentive programs on motivation and productivity.",
    connectorOffset: -30
  },
  {
    id: 5,
    radius: baseRadius + (arcStrokeWidth * 4), // Touches the outer edge of arc 4
    startAngle: fixedStartAngle,
    endAngle: fixedEndAngle,
    color: arcColors[4],
    strokeWidth: arcStrokeWidth,
    title: "Location Summary",
    score: 8.9,
    description: "Summarizes performance and conditions across different locations.",
    connectorOffset: 0
  }
];

  // Draw functions
  const drawArc = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw connectors first (so they appear behind arcs)
    if (showConnectors) {
      drawAllConnectors(ctx);
    }
    
    // Draw each arc
    arcs.forEach(arc => {
      drawSingleArc(ctx, arc);
    });
    
    // Draw center elements
    drawCenterElements(ctx);
  };

  const drawSingleArc = (ctx, arc) => {
    // Set line properties
    ctx.lineWidth = arc.strokeWidth;
    
    // Check if this arc is active (clicked)
    // if (activeArc === arc.id) {
      // ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
      // ctx.shadowBlur = 15;
      // ctx.lineWidth = arc.strokeWidth + 5;
    // } if(!activeArc) {
      ctx.shadowColor = 'transparent';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
      ctx.shadowBlur = 15;
    // }
    
    // Set color
    ctx.strokeStyle = arc.color;
    
    // Draw the arc with rounded end at the finish
    ctx.beginPath();
    ctx.arc(centerX, centerY, arc.radius, arc.startAngle, arc.endAngle);
    
    // Set line cap to round for the end of the arc
    ctx.lineCap = 'butt';
    ctx.stroke();
    
    // Draw a small line at the start with butt cap to make it plain
    ctx.beginPath();
    const startX = centerX + arc.radius * Math.cos(arc.startAngle);
    const startY = centerY + arc.radius * Math.sin(arc.startAngle);
    const endX = centerX + arc.radius * Math.cos(arc.startAngle + 0.05);
    const endY = centerY + arc.radius * Math.sin(arc.startAngle + 0.05);
    
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    // ctx.lineWidth = arc.strokeWidth;
    // ctx.lineCap = 'butt';
    // ctx.strokeStyle = arc.color;
    // ctx.stroke();
  };

  const drawAllConnectors = (ctx) => {
    arcs.forEach((arc, index) => {
      drawNorthThenEastConnector(ctx, arc, index);
    });
  };

const drawNorthThenEastConnector = (ctx, arc, boxIndex) => {
    const box = infoBoxPositions[boxIndex];
    const offset = -300;
    const Yoffset = -50;
    const yoffSets = [-40,-5,20,55,85];
    
    // Calculate arc start point
    const arcStartX = centerX + arc.radius * Math.cos(arc.startAngle);
    const arcStartY = centerY + arc.radius * Math.sin(arc.startAngle);
    
    // Target Y position - center of the info box
    const targetBoxCenterY = box.y + (box.height / 2);
    
    // STEP 1: Go NORTH (straight up) to the level of the info box
    const northX = arcStartX;
    const northY = targetBoxCenterY + yoffSets[boxIndex];
    
    // STEP 2: Go EAST (right) to connect to info box left edge
    const eastX = box.x - offset;
    const eastY = northY;
    
    // Draw connector lines with smooth curved corners
    ctx.strokeStyle = arc.color;
    ctx.lineWidth = 4;
    ctx.setLineDash([]);
    ctx.lineCap = 'round';
    
    // Add slight shadow to connectors
    ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
    ctx.shadowBlur = 4;
    
    // Curve radius for rounded corners (adjust this for more/less curve)
    const curveRadius = 20;
    
    ctx.beginPath();
    
    // Start from arc point
    ctx.moveTo(arcStartX, arcStartY);
    
    // Calculate the corner point where vertical meets horizontal
    const cornerX = northX;
    const cornerY = northY;
    
    // Draw vertical line UP, stopping before the corner
    const verticalEndY = cornerY + curveRadius;
    ctx.lineTo(cornerX, verticalEndY);
    
    // Create smooth curve at the corner using quadratic curve
    // Control point is at the sharp corner, endpoint is on the horizontal line
    ctx.quadraticCurveTo(
        cornerX, cornerY,  // Control point (the sharp corner)
        cornerX + curveRadius, cornerY  // End point (start of horizontal line)
    );
    
    // Alternative: Use arc for perfectly circular rounded corner
    // Uncomment this section and comment out the quadraticCurveTo above to use arc method
    /*
    // Draw arc at corner for smooth rounded join
    ctx.arcTo(
        cornerX, cornerY,  // Corner point
        eastX, eastY,      // Next point (horizontal line end)
        curveRadius        // Radius of the curve
    );
    */
    
    // Draw horizontal line to the right
    ctx.lineTo(eastX, eastY);
    
    // Stroke the entire path
    ctx.stroke();
    
    // Reset shadow
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
};


  const drawCenterElements = (ctx) => {
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 50);
    gradient.addColorStop(0, '#2d3748');
    gradient.addColorStop(1, '#1a202c');

    let tempColor;
    let tempTitle;
    let tempScore = 6.5;
    if(activeArc) {
      tempColor = arcs[activeArc-1].color
      tempTitle = arcs[activeArc-1].title
      tempScore = arcs[activeArc-1].score
    }
    else {
      tempColor = gradient
      tempTitle = 'Overall'
      tempScore = 8.2
    }
    // Draw center circle with gradient
   
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, 62, 0, 2 * Math.PI);
    ctx.fillStyle = tempColor;
    ctx.fill();
    
    // Add border to center circle
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    // Add text in center
    ctx.fillStyle = "white";
    ctx.font = "bold 16px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(tempTitle, centerX, centerY - 10);
    ctx.font = "bold 24px Arial";
    ctx.fillText(tempScore, centerX, centerY + 12);
  };

  // Check if a point is on an arc
  const isPointOnArc = (x, y, arc) => {
    const canvas = canvasRef.current;
    if (!canvas) return false;
    
    const rect = canvas.getBoundingClientRect();
    const clickX = x - rect.left;
    const clickY = y - rect.top;
    
    // Calculate distance from center
    const distance = Math.sqrt(Math.pow(clickX - centerX, 2) + Math.pow(clickY - centerY, 2));
    
    // Check if distance is within arc range
    const inRadius = distance > arc.radius - arc.strokeWidth/2 && 
                    distance < arc.radius + arc.strokeWidth/2;
    
    if (!inRadius) return false;
    
    // Calculate angle of click point
    let angle = Math.atan2(clickY - centerY, clickX - centerX);
    if (angle < 0) angle += 2 * Math.PI;
    
    // Check if angle is within arc range
    return angle >= arc.startAngle && angle <= arc.endAngle;
  };

  // Canvas click handler
  const handleCanvasClick = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Check each arc to see if it was clicked
    for (let i = 0; i < arcs.length; i++) {
      if (isPointOnArc(event.clientX, event.clientY, arcs[i])) {
        setActiveArc(activeArc === arcs[i].id ? null : arcs[i].id);
        return;
      }
    }
    
    // If no arc was clicked, reset active arc
    setActiveArc(null);
  };

  // Info box click handler
  const handleInfoBoxClick = (arcId) => {
    if (!aside) {
      setAside(true)
    }
    setActiveArc(arcId);
  };

  useEffect(()=>{
    if(!aside) {
      setActiveArc(null)
    }
  },[aside])

  // Change colors function
  const changeColors = () => {
    const newColors = [...arcColors];
    const firstColor = newColors.shift();
    newColors.push(firstColor);
    setArcColors(newColors);
  };

  // Reset canvas function
  const resetCanvas = () => {
    setActiveArc(null);
  };

  useEffect(()=>{
    console.log(arcs[activeArc-1]?.title, activeArc)
  },[activeArc])
  // Initialize and redraw when dependencies change
  useEffect(() => {
    drawArc();
  }, [activeArc, showConnectors, arcColors]);

  

  const approvals = [
  { name: "FSSAI License", department: "Ministry of Health & Family Welfare", days: "7–10 Days" },
  { name: "GST Registration", department: "Ministry of Finance", days: "3–5 Days" },
  { name: "Fire Safety NOC", department: "Department of Fire & Emergency Services", days: "10–15 Days" },
  { name: "Environmental Clearance", department: "Ministry of Environment & Forests", days: "20–30 Days" },
  { name: "Building Plan Approval", department: "Urban Development Authority", days: "12–18 Days" },
  { name: "ISO Certification", department: "Quality & Standards Bureau", days: "15–20 Days" },
];
const incentives = [
  { name: "Startup India Recognition", category: "Startup Incentive" },
  { name: "MSME Subsidy", category: "Small & Medium Enterprise Incentive" },
  { name: "R&D Tax Benefit", category: "Research & Development Incentive" },
  { name: "Export Promotion Scheme", category: "Trade & Export Incentive" },
  { name: "Clean Energy Subsidy", category: "Environment & Energy Incentive" },
  // { name: "Skill Development Grant", category: "Training & Employment Incentive" },
  { name: "Digital Transformation Grant", category: "Technology & Innovation Incentive" },
];

const locationData = [
    { title: 'Highway', distance: '21.00 km', status: 'success', icon: '🚗' },
    { title: 'Railway', distance: '4.20 km', status: 'success', icon: '🚆' },
    { title: 'Seaport', distance: '170.09 km', status: 'warning', icon: '⚓' },
    { title: 'Airport', distance: '15.54 km', status: 'success', icon: '✈️' },
    { title: 'Power Source', distance: '11.00 km', status: 'success', icon: '⚡' },
    { title: 'Availability of Local Transportation', distance: 'bad', status: 'error', icon: '🚌' },
    { title: 'Network Availability', distance: '4G', status: 'warning', icon: '📶' },
  ];

  const employeeData = {
  "skilled_no": 4000,
  "semi_skilled_no": 5000,
  "unskilled_no": 1000
}



 const [isFlipped, setIsFlipped] = useState(false);

  const flipCard = () => {
    setIsFlipped(!isFlipped);
  };

  

useEffect(() => {
  if (canvasRef.current) {
    const ctx = canvasRef.current.getContext('2d');
    drawArc(ctx);
  }
  if(activeArc) {
    setActiveArc(null)
    setAside(false)
  }
}, [activeView]);

const totalProperties = 20;
  const [currentIndex, setCurrentIndex] = useState(0);
    
  // Generate property data with detailed information
  const properties = Array.from({ length: totalProperties }, (_, i) => ({
    id: i + 1,
    name: `Riverside Industrial Park ${i + 1}`,
    location: 'Vadodara, India',
    type: 'Industrial Land',
    area: `${35 + i} Acres`,
    businessType: 'GIDC',
    image: `https://picsum.photos/300/200?random=${i + 1}`, // Random placeholder images
    label: `Property ${i + 1}`
  }));

  const nextProperty = () => {
    if (currentIndex === totalProperties - 1) {
      setCurrentIndex(0);
    } else {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const prevProperty = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  // Get the properties to display based on current index
  const getVisibleProperties = () => {
    const visible = [];
    
    // Always show current active property
    visible.push({
      ...properties[currentIndex],
      position: 'active',
      index: currentIndex
    });

    // Show properties to the right (if any)
    if (currentIndex < totalProperties - 1) {
      const nextIndex = currentIndex + 1;
      visible.push({
        ...properties[nextIndex],
        position: 'right-blurred',
        index: nextIndex
      });
    }

    if (currentIndex < totalProperties - 2) {
      const nextNextIndex = currentIndex + 2;
      visible.push({
        ...properties[nextNextIndex],
        position: 'right-blurred',
        index: nextNextIndex
      });
    }

    // Show property to the left (if any, and not at start)
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      visible.push({
        ...properties[prevIndex],
        position: 'left-blurred',
        index: prevIndex
      });
    }

    return visible;
  };

  const getPropertyStyles = (position, index) => {
    const baseStyles = "absolute w-72 h-80 rounded-xl flex flex-col transition-all duration-500 ease-in-out shadow-lg overflow-hidden bg-white";
    
    switch (position) {
      case 'active':
        return `${baseStyles} z-20 transform scale-105 border-4 border-yellow-400`;
      
      case 'right-blurred':
        return `${baseStyles} z-10 filter blur-[2px] opacity-80 transform scale-70`;
      
      case 'left-blurred':
        return `${baseStyles} z-10 filter blur-[2px] opacity-80 transform scale-70`;
      
      default:
        return baseStyles;
    }
  };

  const getPropertyPosition = (position, index) => {
    const SPACING = 320; // Increased spacing for larger cards
    
    switch (position) {
      case 'active':
        return { left: '50%', transform: 'translateX(-50%) scale(1.05)' };
      
      case 'right-blurred':
        const rightSpacing = (index - currentIndex) * 250;
        return { left: `calc(50% + ${rightSpacing}px)`, transform: 'translateX(-50%) scale(0.95)' };
      
      case 'left-blurred':
        const leftSpacing = (index - currentIndex) * 350;
        return { left: `calc(50% + ${leftSpacing}px)`, transform: 'translateX(-50%) scale(0.95)' };
      
      default:
        return { left: '50%', transform: 'translateX(-50%)' };
    }
  };

  // Render property content based on active state
  const renderPropertyContent = (property, position) => {
    const isActive = position === 'active';
    
    return (
      <>
        {/* Image Section - Top 50% */}
        <div className="h-1/2 w-full relative">
          <img 
            src={property.image} 
            alt={property.name}
            className="w-full h-full object-cover"
          />
          {/* Property Index Badge */}
          <div className={`absolute top-3 left-3 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
            isActive ? 'bg-yellow-500 text-white' : 'bg-gray-600 text-white'
          }`}>
            {property.id}
          </div>
        </div>

        {/* Content Section - Bottom 50% */}
        <div className="h-1/2 p-4 flex flex-col justify-between">
          {isActive ? (
            // Active Property - Full Details
            <>
              <div>
                <h3 className="text-lg font-bold text-gray-800 mb-1">{property.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{property.location}</p>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Property Type</span>
                    <span className="text-sm font-semibold text-gray-800">{property.type}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Total Area</span>
                    <span className="text-sm font-semibold text-gray-800">{property.area}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Business Location Type</span>
                    <span className="text-sm font-semibold text-gray-800">{property.businessType}</span>
                  </div>
                </div>
              </div>
              
              {/* Active Indicator */}
              <div className="text-center">
                <span className="inline-block px-2 py-1 bg-yellow-500 text-white text-xs font-bold rounded">
                  ★ ACTIVE
                </span>
              </div>
            </>
          ) : (
            // Non-active Property - Basic Info Only
            <>
              <div className="flex-1 flex flex-col justify-center items-center text-center">
                <h3 className="text-base font-semibold text-gray-800 mb-1">{property.name}</h3>
                <p className="text-sm text-gray-600">{property.location}</p>
              </div>
              
              {/* Position Indicator */}
              <div className="text-center">
                <span className="text-xs text-gray-500 font-medium">
                  {position === 'right-blurred' && '→ NEXT'}
                  {position === 'left-blurred' && '← PREV'}
                </span>
              </div>
            </>
          )}
        </div>
      </>
    );
  };

  const visibleProperties = getVisibleProperties();

const scorePercentage = (8.5 / 10) * 100;


  return (<>
            <div className='absolute top-5 right-25 p-3 w-120 h-fit z-[111] rounded-md justify-evenly bg-black/70 backdrop-blur-[10px] flex flex-row items-center gap-4'>
              <div className={`font-semibold text-lg ${activeView==='Property Overview' ? 'text-green-500' : 'text-white'}`} onClick={()=>{setActiveView('Property Overview')}}>Property Overview</div>
              <div className={`font-semibold text-lg ${activeView==='Map' ? 'text-green-500' : 'text-white'}`} onClick={()=>{setActiveView('Map')}}>Map</div>
              <div className={`font-semibold text-lg ${activeView==='Comparison' ? 'text-green-500' : 'text-white'}`} onClick={()=>{setActiveView('Comparison')}}>Comparison</div>
            </div>

    {activeView==='Property Overview' && (<div className="h-screen overflow-y-auto w-screen overflow-x-hidden flex flex-col items-center  ">
      
        
        
        {/* Property List Section */}
        <div className='relative h-screen min-h-screen w-screen bg-red-200'>
          <div className='absolute flex flex-col items-start gap-1 top-5 left-8'>
            <h1 className='text-3xl font-bold'>Industrial Property Solutions</h1>
            <h1 className='text-3xl font-bold '> that fit your Chemical Industry Search</h1>
          </div>

          <div className='absolute top-30 left-5 w-[80%]'>
            <div className="w-full max-w-4xl rounded-2xl p-8">
              <div className="relative h-[400px] flex items-center justify-center overflow-hidden rounded-xl">
                {/* Previous Button */}
                {currentIndex !== 0 && (
                  <button
                    onClick={prevProperty}
                    className="absolute left-6 z-30 w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold transition-all duration-300 shadow-lg bg-white text-gray-700 hover:bg-gray-100 hover:scale-110 border border-gray-300"
                  >
                    ‹
                  </button>
                )}

                {/* Properties Container */}
                <div className="relative w-full h-full flex items-center justify-center">
                  {visibleProperties.map((property) => (
                    <div
                      key={property.id}
                      className={getPropertyStyles(property.position, property.index)}
                      style={getPropertyPosition(property.position, property.index)}
                    >
                      {renderPropertyContent(property, property.position)}
                    </div>
                  ))}
                </div>

                {/* Next Button */}
                <button
                  onClick={nextProperty}
                  className="absolute right-6 z-30 w-14 h-14 bg-white rounded-full flex items-center justify-center text-2xl font-bold text-gray-700 hover:bg-gray-100 hover:scale-110 transition-all duration-300 shadow-lg border border-gray-300"
                >
                  ›
                </button>
              </div>

              {/* Counter */}
              <div className="text-center mt-4">
                <div className="text-gray-700 text-lg font-semibold">
                  Property <span className="text-yellow-600 font-bold">{currentIndex + 1}</span> of{" "}
                  <span className="text-gray-600">{totalProperties}</span>
                </div>
              </div>

            </div>
          </div>

          <div className='absolute bottom-20 right-20 h-fit h-fit'>

            <Doughnut data={{
                labels: ['Property Score'],
                datasets: [
                  {
                    data: [scorePercentage, 100 - scorePercentage],
                    backgroundColor: ['#4CAF50', '#E0E0E0'], // Green for filled portion, gray for empty
                    borderWidth: 0, // Removes border lines between segments
                  },
                ],
              }} 
              options={{
                responsive: true,
                cutout: '80%', // Makes it a donut chart
                plugins: {
                  tooltip: {
                    enabled: false, // Disables the default tooltip
                  },
                  legend: {
                    display: false, // Hides the legend
                  },
                },
              }} />
              <div className="absolute inset-0 flex flex-col items-center items-center justify-center text-5xl font-bold text-black">
          <h1 className='relative text-7xl font-bold'>8.5</h1>
          <h1 className='relative text-2xl font-bold'>/10</h1>
        </div>
          </div>

        </div>


        {/* Content Section for Factors */}
        <div className="relative min-h-screen h-screen flex flex-row  justify-center bg-gradient-to-br from-gray-50 to-gray-100 lg:flex-row w-screen gap-6">
          {/* Canvas Container */}
          <div className={`flex flex-row justify-center ${aside ? '-left-70': '-left-16 z-[1]'} transition-all duration-700 ease-in-out min-w-0 h-full w-full rounded-2xl p-8  relative`}>
            <canvas
              ref={canvasRef}
              width={750}
              height={650}
              className=" rounded-xl cursor-pointer"
              onClick={handleCanvasClick}
            />

            {/* Info Boxes Overlay */}
            <div className={` ${aside ? 'right-40' : 'right-16'} relative flex flex-col gap-8 w-64`}>
              {arcs.map((arc, index) => (
                <div
                  key={arc.id}
                  className={`bg-white/95 backdrop-blur-sm h-20 max-h-20 ${aside ? 'w-64' : 'w-112'} rounded-xl p-2 shadow-lg transition-all duration-700 cursor-pointer border-l-4 ${
                    activeArc === arc.id 
                      ? 'scale-105 shadow-2xl' 
                      : 'hover:scale-102 hover:shadow-xl'
                  }`}
                  style={{ 
                    borderLeftColor: arc.color,
                    ...(activeArc === arc.id && { ringColor: arc.color })
                  }}
                  onClick={() => {handleInfoBoxClick(arc.id)}}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-md"
                      style={{ backgroundColor: arc.color }}
                    >
                      {arc.id}
                    </div>
                    <h3 className="text-base font-bold text-gray-800">{arc?.title}</h3>
                  </div>
                  <p className="text-xs pl-2 text-gray-600 leading-relaxed">{arc?.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className={` absolute right-8 flex flex-col items-center justify-end p-4 bg-transparent h-full w-[40%] duration-700 transition-all ${aside ? 'opacity-100 flex' : 'opacity-0 z-[0]'}  self-start `}>
              
              {activeArc && arcs[activeArc-1]?.title === 'Approval' && ( <div className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''}`} style={{ perspective: '1000px', height: '90%' }}>
                <div 
                  className="flip-card-inner relative w-full h-full transition-transform duration-700"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  {/* FRONT SIDE - Your existing code */}
                  <div 
                    className="flip-card-front absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md`}  style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg flex flex-row items-center gap-3'>Compliance & Regulatory Checklist <IoInformationCircleOutline className='relative top-0.3 cursor-pointer' /></h1>
                      <div className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3' style={{ color: arcs[activeArc-1].color }}>100 found</div>
                    </div>
                    <div className='relative flex flex-col gap-2 p-4 items-start flex-1 w-full'>
                      <h2 className='relative text-sm font-semibold text-left italic'>Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.</h2>
                    <h2 onClick={flipCard}className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full">Know More About Compliance <FaArrowRightLong className="relative top-0.5" /> </h2>

                      {/* <h2 className='relative text-sm font-semibold text-left italic'>Our process focuses on accuracy, transparency, and trust. Every approval displayed here is verified through official records, validated for authenticity, and mapped to its respective department or governing body.</h2> */}
                      <div className="divide-y divide-gray-100 w-full">
                        {approvals.map((item, index) => (
                          <div
                            key={index}
                            className="flex items-start justify-between py-3"
                          >
                            <div className="flex items-start gap-2">
                              <span className="mt-2 w-2 h-2  rounded-full" style={{ backgroundColor: arcs[activeArc-1].color }}/>
                              <div>
                                <h3 className="text-sm font-semibold text-gray-800">
                                  {item.name}
                                </h3>
                                <p className="text-xs text-gray-500">{item?.department}</p>
                              </div>
                            </div>

                            <div className="text-right">
                              <p className="text-xs uppercase text-gray-400 font-medium">
                                Est. Duration
                              </p>
                              <p className="text-xs font-semibold text-gray-700">
                                {item.days}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      {/* Flip Button */}
                      {/* bg-gradient-to-br from-pink-600 to-pink-700 hover:from-pink-700 hover:to-pink-800 hover:shadow-pink-500/40*/}
                      <div className=" w-full flex  absolute bottom-4 justify-center items-center">
                        <button 
                          className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full  transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg  text-sm"
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          Explore Insights <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500' />
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* BACK SIDE - Empty for now with same height */}
                  <div 
                    className="flip-card-back absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ 
                      backfaceVisibility: 'hidden',
                      transform: 'rotateY(180deg)'
                    }}
                  >
                    <div className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white' style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg'>Approval Insights & Analysis</h1>
                    </div>
                    <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Stay Complient, Stay Confident</h1>
                        <h3 className='relative tracking-wide text-sm'>Every approval listed here is more than just a certificate—it's a guarantee that your business meets essential legal and safety standards. With these in place, you can operate smoothly without surprises.</h3>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>What You Need to Know:</h1>
                        <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                          <li>Issued By: Relevant government or regulatory authority.</li>
                          <li>Purpose: Ensures safety, quality, and legality across operations.</li>
                          <li>Renewal: Some approvals expire, so tracking dates keeps you stress-free.</li>
                        </ul>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Why It Matters to You:</h1>
                        <h3 className='relative tracking-wide text-sm'>Think of approvals as your business's shield—they protect you from legal issues, fines, and delays, while also building trust with clients and partners.</h3>
                      </div>
                      
                      {/* Back Button */}
                      <div className="text-center pt-4 w-full">
                        <button 
                          className="back-btn px-6 py-2 text-white font-semibold rounded-full cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg hover:shadow-gray-500/30 text-sm"
                          onClick={flipCard}
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          ↺ Back to List
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>)}

              {activeArc&& arcs[activeArc-1]?.title === 'Incentives' && (<div className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''}`} style={{ perspective: '1000px', height: '90%' }} >
                <div 
                  className="flip-card-inner relative w-full h-full transition-transform duration-700"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  {/* FRONT SIDE - Your existing code */}
                  <div 
                    className="flip-card-front absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md`}  style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg flex flex-row items-center gap-3'>Subsidy & Support Matrix <IoInformationCircleOutline className='relative top-0.3 cursor-pointer' /></h1>
                      <div className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3' style={{ color: arcs[activeArc-1].color }}>100 found</div>
                    </div>
                    <div className='relative flex flex-col gap-2 p-4 items-start flex-1 w-full'>
                      <h2 className='relative text-sm font-semibold text-left italic'>Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.</h2>
                    <h2 onClick={flipCard}className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full">Know More About Incentives <FaArrowRightLong className="relative top-0.5" /> </h2>

                      {/* <h2 className='relative text-sm font-semibold text-left italic'>Our process focuses on accuracy, transparency, and trust. Every approval displayed here is verified through official records, validated for authenticity, and mapped to its respective department or governing body.</h2> */}
                      <div className="divide-y divide-gray-100 w-full">
                        {incentives.map((item, index) => (
                          <div
                            key={index}
                            className="flex items-start justify-between py-3"
                          >
                            <div className="flex items-start gap-2">
                              <span className="mt-2 w-2 h-2  rounded-full" style={{ backgroundColor: arcs[activeArc-1].color }}/>
                              <div>
                                <h3 className="text-sm font-semibold text-gray-800">
                                  {item.name}
                                </h3>
                                <p className="text-xs text-gray-500">{item?.category}</p>
                              </div>
                            </div>

                          </div>
                        ))}
                      </div>
                      
                      {/* Flip Button */}
                      {/* bg-gradient-to-br from-pink-600 to-pink-700 hover:from-pink-700 hover:to-pink-800 hover:shadow-pink-500/40*/}
                      <div className=" w-full flex absolute bottom-4 justify-center items-center">
                        <button 
                          className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full  transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg  text-sm"
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          Explore Insights <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500' />
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* BACK SIDE - Empty for now with same height */}
                  <div 
                    className="flip-card-back absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ 
                      backfaceVisibility: 'hidden',
                      transform: 'rotateY(180deg)'
                    }}
                  >
                    <div className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white' style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg'>Approval Insights & Analysis</h1>
                    </div>
                    <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Stay Complient, Stay Confident</h1>
                        <h3 className='relative tracking-wide text-sm'>Every approval listed here is more than just a certificate—it's a guarantee that your business meets essential legal and safety standards. With these in place, you can operate smoothly without surprises.</h3>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>What You Need to Know:</h1>
                        <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                          <li>Issued By: Relevant government or regulatory authority.</li>
                          <li>Purpose: Ensures safety, quality, and legality across operations.</li>
                          <li>Renewal: Some approvals expire, so tracking dates keeps you stress-free.</li>
                        </ul>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Why It Matters to You:</h1>
                        <h3 className='relative tracking-wide text-sm'>Think of approvals as your business's shield—they protect you from legal issues, fines, and delays, while also building trust with clients and partners.</h3>
                      </div>
                      
                      {/* Back Button */}
                      <div className="text-center pt-4 w-full">
                        <button 
                          className="back-btn px-6 py-2 text-white font-semibold rounded-full cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg hover:shadow-gray-500/30 text-sm"
                          onClick={flipCard}
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          ↺ Back to List
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>)}

              {activeArc && arcs[activeArc-1]?.title === 'Vendors' &&  (<div className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''}`} style={{ perspective: '1000px', height: '90%' }} >
                <div 
                  className="flip-card-inner relative w-full h-full transition-transform duration-700"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  {/* FRONT SIDE - Your existing code */}
                  <div 
                    className="flip-card-front absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md`}  style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg flex flex-row items-center gap-3'>Supply Chain Accessibility <IoInformationCircleOutline className='relative top-0.3 cursor-pointer' /></h1>
                      {/* <div className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3' style={{ color: arcs[activeArc-1].color }}>100 found</div> */}
                    </div>
                    <div className='relative flex flex-col gap-3 p-4 items-start flex-1 w-full'>
                      <h2 className='relative text-sm font-semibold text-left italic'>Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.</h2>
                    <h2 onClick={flipCard} className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full">Know More About Incentives <FaArrowRightLong className="relative top-0.5" /> </h2>

                      <div className='relative grid grid-cols-2 w-full gap-3 items-center'>
                        <div className='relative py-1 px-6 mt-4 rounded-full text-sm w-fit text-orange-500 bg-orange-100 font-bold flex justify-self-center items-center justify-center'>Essential</div>
                        <div className='relative py-1 px-6 mt-4 rounded-full text-sm  w-fit text-blue-500 bg-blue-100 font-bold flex justify-self-center items-center justify-center'>Non - Essential</div>

                        <div className='relative flex flex-col gap-1 items-start mt-3 p-2 bg-orange-50  border border-orange-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start mt-3 p-2 bg-blue-50  border border-blue-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start p-2 bg-orange-50  border border-orange-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start p-2 bg-blue-50  border border-blue-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start p-2 bg-orange-50  border border-orange-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start p-2 bg-blue-50  border border-blue-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start p-2 bg-orange-50  border border-orange-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>
                        <div className='relative flex flex-col gap-1 items-start p-2 bg-blue-50  border border-blue-200 rounded-md '>
                          <h1 className='relative font-semibold text-sm'>Polyesters</h1>
                          <h3 className='relative text-xs'>Vendors Found: 32 </h3>
                          <h3 className='relative text-xs'>Nearby Distance: 82.87 km</h3>
                        </div>


                      </div>
                    
                    </div>
                  </div>
                  
                  {/* BACK SIDE - Empty for now with same height */}
                  <div 
                    className="flip-card-back absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ 
                      backfaceVisibility: 'hidden',
                      transform: 'rotateY(180deg)'
                    }}
                  >
                    <div className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white' style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg'>Location Intelligence Summary</h1>
                    </div>
                    <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Stay Complient, Stay Confident</h1>
                        <h3 className='relative tracking-wide text-sm'>Every approval listed here is more than just a certificate—it's a guarantee that your business meets essential legal and safety standards. With these in place, you can operate smoothly without surprises.</h3>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>What You Need to Know:</h1>
                        <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                          <li>Issued By: Relevant government or regulatory authority.</li>
                          <li>Purpose: Ensures safety, quality, and legality across operations.</li>
                          <li>Renewal: Some approvals expire, so tracking dates keeps you stress-free.</li>
                        </ul>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Why It Matters to You:</h1>
                        <h3 className='relative tracking-wide text-sm'>Think of approvals as your business's shield—they protect you from legal issues, fines, and delays, while also building trust with clients and partners.</h3>
                      </div>
                      
                      {/* Back Button */}
                      <div className="text-center pt-4 w-full">
                        <button 
                          className="back-btn px-6 py-2 text-white font-semibold rounded-full cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg hover:shadow-gray-500/30 text-sm"
                          onClick={flipCard}
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          ↺ Back to List
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>)}

              {activeArc&& arcs[activeArc-1]?.title=== 'Employment' && (<div className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''}`} style={{ perspective: '1000px', height: '90%' }} >
                  <div 
                  className="flip-card-inner relative w-full h-full transition-transform duration-700"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  {/* FRONT SIDE - Your existing code */}
                  <div 
                    className="flip-card-front absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md`}  style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg flex flex-row items-center gap-3'>Workforce Availability Insights <IoInformationCircleOutline className='relative top-0.3 cursor-pointer' /></h1>
                      {/* <div className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3' style={{ color: arcs[activeArc-1].color }}>100 found</div> */}
                    </div>
                    <div className='relative flex flex-col gap-3 p-4 items-start flex-1 w-full'>
                      <h2 className='relative text-sm font-semibold text-left italic'>Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.</h2>
                    <h2 onClick={flipCard} className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full">Know More About Incentives <FaArrowRightLong className="relative top-0.5" /> </h2>

                      <div className='relative flex flex-col mt-8 min-h-[60%] w-full'>
                        <div className="h-full relative w-full">
                          <Doughnut data={{
                            labels: ['Skilled', 'Semi-Skilled', 'Unskilled'],
                            datasets: [{
                              data: [employeeData.skilled_no, employeeData.semi_skilled_no, employeeData.unskilled_no],
                              backgroundColor: ['#2563EB', '#16A34A', '#D97706'],
                              borderWidth: 1,
                            }]
                          }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              cutout: '60%', // thinner ring (default is ~50%)
                              plugins: {
                                legend: {
                                  display: false // hide legend
                                },
                              },
                            }}
                            className="w-ful  l h-full" // This will make the chart fill its container
                          />
                  </div>
                  <div className="mt-2 h-fit grid grid-cols-3 gap-2">
                    <div className="text-center flex flex-col gap-2">
                      <div className="text-xs font-medium">Skilled</div>
                      <div className="text-sm text-blue-600 font-semibold">{employeeData.skilled_no} workers</div>
                    </div>
                    <div className="text-center flex flex-col gap-2">
                      <div className="text-xs font-medium">Semi-skilled</div>
                      <div className="text-sm text-green-600 font-semibold">{employeeData.semi_skilled_no} workers</div>
                    </div>
                    <div className="text-center flex flex-col gap-2">
                      <div className="text-xs font-medium">Unskilled</div>
                      <div className="text-sm text-amber-600 font-semibold">{employeeData.unskilled_no} workers</div>
                    </div>
                  </div>
                      </div>
                    
                    </div>
                  </div>
                  
                  {/* BACK SIDE - Empty for now with same height */}
                  <div 
                    className="flip-card-back absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ 
                      backfaceVisibility: 'hidden',
                      transform: 'rotateY(180deg)'
                    }}
                  >
                    <div className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white' style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg'>Location Intelligence Summary</h1>
                    </div>
                    <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Stay Complient, Stay Confident</h1>
                        <h3 className='relative tracking-wide text-sm'>Every approval listed here is more than just a certificate—it's a guarantee that your business meets essential legal and safety standards. With these in place, you can operate smoothly without surprises.</h3>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>What You Need to Know:</h1>
                        <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                          <li>Issued By: Relevant government or regulatory authority.</li>
                          <li>Purpose: Ensures safety, quality, and legality across operations.</li>
                          <li>Renewal: Some approvals expire, so tracking dates keeps you stress-free.</li>
                        </ul>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Why It Matters to You:</h1>
                        <h3 className='relative tracking-wide text-sm'>Think of approvals as your business's shield—they protect you from legal issues, fines, and delays, while also building trust with clients and partners.</h3>
                      </div>
                      
                      {/* Back Button */}
                      <div className="text-center pt-4 w-full">
                        <button 
                          className="back-btn px-6 py-2 text-white font-semibold rounded-full cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg hover:shadow-gray-500/30 text-sm"
                          onClick={flipCard}
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          ↺ Back to List
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                  
              </div>)}


              {activeArc&& arcs[activeArc-1]?.title==='Location Summary' && (<div className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''}`} style={{ perspective: '1000px', height: '90%' }}>
                <div 
                  className="flip-card-inner relative w-full h-full transition-transform duration-700"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  {/* FRONT SIDE - Your existing code */}
                  <div 
                    className="flip-card-front absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md`}  style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg flex flex-row items-center gap-3'>Location Intelligence Summary <IoInformationCircleOutline className='relative top-0.3 cursor-pointer' /></h1>
                      {/* <div className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3' style={{ color: arcs[activeArc-1].color }}>100 found</div> */}
                    </div>
                    <div className='relative flex flex-col gap-3 p-4 items-start flex-1 w-full'>
                      <h2 className='relative text-sm font-semibold text-left italic'>Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.</h2>
                    <h2 onClick={flipCard} className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full">Know More About Incentives <FaArrowRightLong className="relative top-0.5" /> </h2>

                      <div className="flex flex-col gap-8 w-full">
                  {/* Transportation Access Section - Two Column Grid */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Transportation Access</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <div>
                          <div className="text-sm font-medium text-gray-900">Highway</div>
                          <div className="text-xs text-gray-600">Major road access</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">21.00 km</div>
                          <div className="text-xs text-green-600 font-medium">Good</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <div>
                          <div className="text-sm font-medium text-gray-900">Railway</div>
                          <div className="text-xs text-gray-600">Rail connectivity</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">4.20 km</div>
                          <div className="text-xs text-green-700 font-medium">Excellent</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <div>
                          <div className="text-sm font-medium text-gray-900">Airport</div>
                          <div className="text-xs text-gray-600">Air transport hub</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">15.54 km</div>
                          <div className="text-xs text-green-600 font-medium">Good</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b border-gray-100">
                        <div>
                          <div className="text-sm font-medium text-gray-900">Seaport</div>
                          <div className="text-xs text-gray-600">Maritime access</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">170.09 km</div>
                          <div className="text-xs text-yellow-600 font-medium">Fair</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Infrastructure & Services Section - Flex Column */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Infrastructure & Services</h3>
                    <div className="flex flex-col gap-3">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">Power Infrastructure</span>
                          <span className="text-sm text-gray-700">11.00 km</span>
                        </div>
                        <div className="text-xs text-green-700 mt-1">Adequate access to power grid</div>
                      </div>
                      
                      <div className="bg-red-50 border border-red-200 rounded-lg p-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">Local Transportation</span>
                          <span className="text-sm text-red-700">Limited</span>
                        </div>
                        <div className="text-xs text-red-700 mt-1">Poor local transit options</div>
                      </div>
                      
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">Network Coverage</span>
                          <span className="text-sm text-yellow-700">4G</span>
                        </div>
                        <div className="text-xs text-yellow-700 mt-1">Basic connectivity available</div>
                      </div>
                    </div>
                  </div>
                </div>
                    
                    </div>
                  </div>
                  
                  {/* BACK SIDE - Empty for now with same height */}
                  <div 
                    className="flip-card-back absolute w-full h-full bg-white border border-black rounded-md flex flex-col items-start backface-hidden"
                    style={{ 
                      backfaceVisibility: 'hidden',
                      transform: 'rotateY(180deg)'
                    }}
                  >
                    <div className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white' style={{ backgroundColor: arcs[activeArc-1].color }}>
                      <h1 className='relative font-bold text-lg'>Location Intelligence Summary</h1>
                    </div>
                    <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Stay Complient, Stay Confident</h1>
                        <h3 className='relative tracking-wide text-sm'>Every approval listed here is more than just a certificate—it's a guarantee that your business meets essential legal and safety standards. With these in place, you can operate smoothly without surprises.</h3>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>What You Need to Know:</h1>
                        <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                          <li>Issued By: Relevant government or regulatory authority.</li>
                          <li>Purpose: Ensures safety, quality, and legality across operations.</li>
                          <li>Renewal: Some approvals expire, so tracking dates keeps you stress-free.</li>
                        </ul>
                      </div>
                      <div className='relative flex flex-col items-start '>
                        <h1 className='relative font-semibold text-base'>Why It Matters to You:</h1>
                        <h3 className='relative tracking-wide text-sm'>Think of approvals as your business's shield—they protect you from legal issues, fines, and delays, while also building trust with clients and partners.</h3>
                      </div>
                      
                      {/* Back Button */}
                      <div className="text-center pt-4 w-full">
                        <button 
                          className="back-btn px-6 py-2 text-white font-semibold rounded-full cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg hover:shadow-gray-500/30 text-sm"
                          onClick={flipCard}
                          style={{ backgroundColor: arcs[activeArc-1].color }}
                        >
                          ↺ Back to List
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>)}
          </div>

        </div>

    </div>)}
    </>
  );
};

export default CircularInfographic;