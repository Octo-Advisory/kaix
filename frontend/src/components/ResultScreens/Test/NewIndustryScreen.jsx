import React, { useState, useRef, useEffect } from 'react';
import { FaArrowRightLong } from "react-icons/fa6";
import { IoInformationCircleOutline } from "react-icons/io5";
import { FaTrain, FaBus, FaRegQuestionCircle,FaArrowRight } from "react-icons/fa";
import { BsPatchCheckFill } from "react-icons/bs";
import { MdOfflineBolt } from "react-icons/md";
import { IoWifi } from "react-icons/io5";
import { RiShipFill } from "react-icons/ri";
import { FaRoad,FaXmark } from "react-icons/fa6";
import { IoAirplane } from "react-icons/io5";
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { FaChevronRight } from "react-icons/fa6";
import { FaChevronLeft,FaTriangleExclamation,FaCircleXmark } from "react-icons/fa6";
import { FaArrowUp } from "react-icons/fa6";
import { IoCheckmarkDone } from "react-icons/io5";
import { RiCoinsLine } from "react-icons/ri";
import { BsShop } from "react-icons/bs";
import { FaMapLocationDot } from "react-icons/fa6";
import { FaUserGroup } from "react-icons/fa6";
import './neww.css'
import GaugeMeter from './GuageMeter';
import MapImage2 from './Screenshot 2025-09-23 133619.png'
// import backImage from './Gemini_Generated_Image_g98ff2g98ff2g98f.png'
import backImage from './Gemini_Generated_Image_wkudyawkudyawkud.png'
import { useFrappeGetDoc } from 'frappe-react-sdk';
import Approvalresult from '../Approvalresult';
import Incentiveresult from '../Incentiveresult';
import Vendorresult from '../Vendorresult';




const NewIndustryScreen = ({solutions}) => {
   ChartJS.register(ArcElement, Tooltip, Legend);
  const canvasRef = useRef(null);
  const [activeArc, setActiveArc] = useState(1);
  const [showConnectors, setShowConnectors] = useState(true);
  const [aside,setAside] = useState(true)
  const [activeFactor, setActiveFactor] = useState('Approvals')
  const [activeView , setActiveView] = useState('Property Overview')
  const [selectedProperty, setSelectedProperty] = useState()

  const [approvalsWindow, setApprovalWindow] = useState(false)
  const [approvalsToSend, setApprovalsToSend] = useState()
  const [incentivesWindow, setIncentivesWindow] = useState(false)
  const [incentivesToSend, setIncentivesToSend] = useState()
  const [vendorsWindow, setVendorsWindow] = useState(false)
  const [vendorsToSend, setVendorsToSend] = useState()


  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Build From Scratch")
    const configurations = uiData?.configurations || [];
    const uiConfig = configurations.reduce((acc, curr) => {
      acc[curr.key] = curr.value;
      return acc;
    }, {});
  // Canvas center coordinates
  const centerX = 300;
  const centerY = 350;
  
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
    { x: 650, y: 100, width: 250, height: 70 },  // Box 2
    { x: 650, y: 180, width: 250, height: 70 },  // Box 3 - Middle (still above center)
    { x: 650, y: 250, width: 250, height: 70 },  // Box 4
    { x: 650, y: 295, width: 250, height: 120 }   // Box 5
  ];

  // drawInfoBox(ctx, 650, 40, 250, 70, arcs[0]);
  
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
 const arcStrokeWidth = 35;
  const baseRadius = 72; 
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
    connectorOffset: -120,
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
    connectorOffset: -90,
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
    connectorOffset: -60,
    
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
    connectorOffset: -30,
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
    connectorOffset: 0,  
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

const drawInfoBox = (ctx, x, y, width, height, arc, boxIndex) => {
    const isActive = activeArc === arc.id;
    
    // Draw box background
    ctx.fillStyle = isActive ? arc.color : 'rgba(255, 255, 255, 0.95)';
    // ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
    // ctx.shadowBlur = 10;
    // ctx.shadowOffsetY = 2;
    
    // Draw rounded rectangle
    const borderRadius = 12;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, borderRadius);
    ctx.fill();
    
    // Reset shadow
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    
    // Draw left border
    ctx.fillStyle = isActive ? 'white' : arc.color;
    ctx.fillRect(x, y, 4, height);
    
    // Draw content
    const padding = 16;
    
    // // Draw icon (colored circle)
    // const iconX = x + padding;
    // const iconY = y + (height / 2);
    
    // ctx.fillStyle = isActive ? 'white' : arc.color;
    // ctx.beginPath();
    // ctx.arc(iconX, iconY, 16, 0, 2 * Math.PI);
    // ctx.fill();
    
    // Draw title
    const titleX = x + padding + 30;
    const titleY = y + (height / 2);
    
    ctx.fillStyle = isActive ? 'white' : '#1f2937';
    ctx.font = isActive ? 'bold 18px Arial' : 'bold 16px Arial';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(arc.title, titleX, titleY);
    
    // Draw score
    const scoreX = x + width - padding;
    const scoreY = y + (height / 2);
    
    ctx.fillStyle = isActive ? 'white' : '#1f2937';
    ctx.font = isActive ? 'bold 24px Arial' : 'bold 20px Arial';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(arc.score.toString(), scoreX, scoreY);
    
    // Store box position for click detection
    if (!window.infoBoxes) window.infoBoxes = [];
    window.infoBoxes[boxIndex] = {
        x: x,
        y: y, 
        width: width,
        height: height,
        arcId: arc.id
    };
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


    drawInfoBox(ctx, 550, 0, 250, 70, arcs[0],0);
    drawInfoBox(ctx, 550, 90, 250, 70, arcs[1],1);
    drawInfoBox(ctx, 550, 200, 250, 70, arcs[2],2);
    drawInfoBox(ctx, 550, 300, 250, 70, arcs[3],3);
    drawInfoBox(ctx, 550, 400, 250, 70, arcs[4],4);
};

  const drawCenterElements = (ctx) => {
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 50);
    gradient.addColorStop(0, '#2d3748');
    gradient.addColorStop(1, '#1a202c');

    // let tempColor;
    // let tempTitle;
    // let tempScore = 6.5;
    // if(activeArc) {
    //   tempColor = arcs[activeArc-1].color
    //   tempTitle = arcs[activeArc-1].title
    //   tempScore = arcs[activeArc-1].score
    // }
    // else {
    //   tempColor = gradient
    //   tempTitle = 'Overall'
    //   tempScore = 8.2
    // }
    // Draw center circle with gradient
   
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, 54, 0, 2 * Math.PI);
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Add border to center circle
    // ctx.strokeStyle = 'white';
    // ctx.lineWidth = 3;
    // ctx.stroke();
    
    // Add text in center
    ctx.fillStyle = "white";
    ctx.font = "bold 16px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText('Overall', centerX, centerY - 10);
    ctx.font = "bold 24px Arial";
    ctx.fillText('8.2', centerX, centerY + 12);
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
    
    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;
    
    // First check if any info box was clicked
    if (window.infoBoxes) {
        for (let i = 0; i < window.infoBoxes.length; i++) {
            const box = window.infoBoxes[i];
            if (box && 
                clickX >= box.x && clickX <= box.x + box.width &&
                clickY >= box.y && clickY <= box.y + box.height) {
                setActiveArc(box.arcId);
                handleInfoBoxClick(box.arcId);
                return;
            }
        }
    }
    
    // Then check if any arc was clicked
    for (let i = 0; i < arcs.length; i++) {
        if (isPointOnArc(event.clientX, event.clientY, arcs[i])) {
            setActiveArc(arcs[i].id);
            return;
        }
    }
};

  // Info box click handler
  const handleInfoBoxClick = (arcId) => {
    if (!aside) {
      setAside(true)
    }
    setActiveArc(arcId);
  };

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
  { name: "FSSAI License", department: "Ministry of Health & Family Welfare", days: "7-10 Days" },
  { name: "GST Registration", department: "Ministry of Finance", days: "3-5 Days" },
  { name: "Fire Safety NOC", department: "Department of Fire & Emergency Services", days: "10-15 Days" },
  { name: "Environmental Clearance", department: "Ministry of Environment & Forests", days: "20-30 Days" },
  { name: "Building Plan Approval", department: "Urban Development Authority", days: "12-18 Days" },
  { name: "ISO Certification", department: "Quality & Standards Bureau", days: "15-20 Days" },
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
  // if(activeArc) {
  //   setActiveArc(null)
  //   setAside(false)
  // }
}, [activeView]);

const totalProperties = solutions.length;
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
    setActiveArc(1)
    if (currentIndex === totalProperties - 1) {
      setCurrentIndex(0);
    } else {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const prevProperty = () => {
    setActiveArc(1)
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  // Get the properties to display based on current index
  const getVisibleProperties = () => {
    const visible = [];
    
    // Always show current active property
    visible.push({
      ...solutions[currentIndex],
      position: 'active',
      index: currentIndex,
      image: `https://picsum.photos/300/200?random=${currentIndex}`,
    });

    // Show properties to the right (if any)
    if (currentIndex < totalProperties - 1) {
      const nextIndex = currentIndex + 1;
      visible.push({
        ...solutions[nextIndex],
        position: 'right-blurred',
        index: nextIndex,
        image: `https://picsum.photos/300/200?random=${nextIndex}`, 
      });
    }

    if (currentIndex < totalProperties - 2) {
      const nextNextIndex = currentIndex + 2;
      visible.push({
        ...solutions[nextNextIndex],
        position: 'right-blurred',
        index: nextNextIndex,
        image: `https://picsum.photos/300/200?random=${nextNextIndex}`,
      });
    }

    // Show property to the left (if any, and not at start)
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      visible.push({
        ...solutions[prevIndex],
        position: 'left-blurred',
        index: prevIndex,
        image: `https://picsum.photos/300/200?random=${prevIndex}`,
      });
    }
    return visible;
  };

  const getPropertyStyles = (position, index) => {
    const baseStyles = "absolute w-72 h-80 rounded-xl flex flex-col transition-all duration-500 ease-in-out shadow-lg overflow-hidden bg-white";
    
    switch (position) {
      case 'active':
        return `${baseStyles} z-20 transform scale-105 cursor-pointer border-1 h-96 w-78 border-[#41b655]`;
      
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
        const rightSpacing = (index - currentIndex) * 350;
        return { left: `calc(50% + ${rightSpacing}px)`, transform: 'translateX(-50%) scale(0.95)' };
      
      case 'left-blurred':
        const leftSpacing = (index - currentIndex) * 350;
        return { left: `calc(50% + ${leftSpacing}px)`, transform: 'translateX(-50%) scale(0.95)' };
      
      default:
        return { left: '50%', transform: 'translateX(-50%)' };
    }
  };

  // Render property content based on active state
  const renderPropertyContent = (property, position,id) => {
    const isActive = position === 'active';
    
    return (
      <>
        {/* Image Section - Top 50% */}
        <div className="h-[50%] w-full relative">
          <img 
            src={MapImage2} 
            alt={property.property_id}
            className="w-full h-full object-cover"
          />
          {/* Property Index Badge */}
          <div className={`absolute top-3 left-3 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
            isActive ? 'bg-[#41b655] text-white' : 'bg-gray-600 text-white'
          }`}>
            {id}
          </div>
        </div>

        {/* Content Section - Bottom 50% */}
        <div className="h-[50%] p-4 flex flex-col justify-between">
          {isActive ? (
            // Active Property - Full Details
            <>
              <div>
                <h3 className="text-lg font-bold text-gray-800 mb-1">{property.property_id}</h3>
                <p className="text-sm text-gray-600 mb-5">{property.address}</p>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Property Type</span>
                    <span className="text-sm font-semibold text-gray-800">{property.property_type}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Total Area</span>
                    <span className="text-sm font-semibold text-gray-800">{property.area}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Business Location Type</span>
                    <span className="text-sm font-semibold text-gray-800">{property.business_location_type}</span>
                  </div>
                </div>
              </div>
              

            </>
          ) : (
            // Non-active Property - Basic Info Only
            <>
              <div className="flex-1 flex flex-col justify-center items-center text-center">
                <h3 className="text-base font-semibold text-gray-800 mb-1">{property.property_id}</h3>
                <p className="text-sm text-gray-600">{property.address}</p>
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
  console.log(visibleProperties, 'oka',solutions)

  useEffect(()=>{
    console.log(currentIndex, solutions,selectedProperty)
  },[currentIndex, solutions,selectedProperty])
  
const [isScrolled, setIsScrolled] = useState(false);
const [isMenuOpen, setIsMenuOpen] = useState(false);
const scrollContainerRef = useRef(null);
const section2Ref = useRef(null); // Add ref for section 2

useEffect(() => {
  const scrollContainer = scrollContainerRef.current;
  const section2 = section2Ref.current;
  
  if (!scrollContainer || !section2) return;

  const handleScroll = () => {
    // Get section 2's position relative to the scroll container
    const section2Top = section2.offsetTop;
    const scrollPosition = scrollContainer.scrollTop;    
    // Shrink when we're 50px away from section 2 (adjust this value)
    const shouldShrink = scrollPosition >= section2Top - 50;
    setIsScrolled(shouldShrink);
    
    if (!shouldShrink) {
      setIsMenuOpen(false);
    }
  };

  scrollContainer.addEventListener("scroll", handleScroll);
  return () => scrollContainer.removeEventListener("scroll", handleScroll);
}, []);

const scrollToTop = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: 0,
        behavior: "smooth", // smooth scrolling
      });
    }
  };

  const scrollToSection = () => {
    section2Ref.current?.scrollIntoView({
      behavior: "smooth", // makes it smooth
      block: "start",     // aligns the section at the top
    });
  };

   const scrolltoProperty = () => {
    // setSelectedProperty(null)
    propertyRef.current?.scrollIntoView({
      behavior:"smooth",
      block:'start',
    });
  };


   function createVendorData(essential, essential_all, nonessential, nonessential_all, latitude_longitude) {
    let result = {
      Analytics_response: {
        "Unfiltered All IS Supplier": null,
        "Best IS Supplier": null,
        "Unfiltered Essential Supplier": essential_all,
        "Best Essential Supplier": essential,
        "Better Supplier": null,
        "Unfiltered Non-Essential Supplier": nonessential_all,
        "Best Non-Essential Supplier": nonessential
      },
      latitude_longitude: latitude_longitude,
      propertyData: selectedProperty
    };
    return result
  }
  const handleShowVendor = () => {
    console.log('okay executed');
    
    const data = createVendorData(selectedProperty?.essential_vendor_details, selectedProperty?.essential_vendor_all_details, selectedProperty?.non_essential_vendor_details, selectedProperty?.non_essential_vendor_all_details, selectedProperty?.latitude_longitude);
    setVendorsToSend(data);
    setVendorsWindow(true)
  }
  function createIncentiveData(incentives) {
    return incentives
  }
  const handleShowIncentive = () => {
    const data = createIncentiveData(selectedProperty?.incentives);
    setIncentivesToSend(data);
    setIncentivesWindow(true)
  }
  function createApprovalData(approval) {

    return {
      // "Approval Data": JSON.stringify(approvalData),
      "Approval Data": approval.approvals,
      "Pre-Requisite": approval.pre_requisite,
      "Pre-Operation": approval.pre_operation,
      "Pre-Establishment": approval.pre_establishment,
      "Others": approval.others,
      "Online Percentage": approval.online_percentage,
      "Total Effective Time": approval.total_effective_time,
      "Mode_Pre-Requisite": approval.mode_requisite,
      "Mode_Pre-Operation": approval.mode_operation,
      "Mode_Pre-Establishment": approval.mode_establishment,
      "Mode_Others": approval.mode_others
    };
  }
  const handleShowApprovals = () => {
    const data = createApprovalData(selectedProperty);
    setApprovalsToSend(data);
    setApprovalWindow(true)
  }

  


  return (
  <>
  <div className='relative flex flex-col w-screen h-full min-h-fit top-0 no-scroll'>
  
  {/* <div 
  className={`absolute top-5 right-15 z-[99] rounded-md bg-white/65 backdrop-blur-[10px] transition-all duration-300 ${
    (isScrolled && !aside)
      ? (isMenuOpen ? 'p-3 w-120 h-fit' : 'p-3 w-14 h-14')
      : 'p-3 w-120 h-fit'
  }`}
  onMouseEnter={() => {
    if (isScrolled && !aside) setIsMenuOpen(true);
  }}
  onMouseLeave={() => {
    if (isScrolled && !aside) setIsMenuOpen(false);
  }}
>
 
  {isScrolled && !isMenuOpen && !aside && (
    <div className="flex flex-col gap-1.5 cursor-pointer justify-center items-center h-full">
      <div className="w-6 h-0.5 bg-white rounded"></div>
      <div className="w-6 h-0.5 bg-white rounded"></div>
      <div className="w-6 h-0.5 bg-white rounded"></div>
    </div>
  )}

  
  {(!isScrolled || aside || (isScrolled && isMenuOpen)) && (
    <div className="flex flex-row items-center justify-evenly gap-4 w-full">
      <div 
        className={`text-base cursor-pointer transition-colors whitespace-nowrap ${
          activeView === 'Property Overview' ? 'text-green-500 font-semibold' : ' font-thin text-black hover:text-green-400'
        }`} 
        onClick={() => setActiveView('Property Overview')}
      >
        Property Overview
      </div>
      <div 
        className={`text-base cursor-pointer transition-colors whitespace-nowrap ${
          activeView === 'Map' ? 'text-green-500 font-semibold' : 'font-thin text-black hover:text-green-400'
        }`} 
        onClick={() => setActiveView('Map')}
      >
        Map
      </div>
      <div 
        className={`text-base cursor-pointer transition-colors whitespace-nowrap ${
          activeView === 'Comparison' ? 'text-green-500 font-semibold' : 'font-thin text-black hover:text-green-400'
        }`} 
        onClick={() => setActiveView('Comparison')}
      >
        Comparison
      </div>
    </div>
  )}
</div> */}

{/* Background Image  */}

{/* <div className='fixed z-[2] top-0 left-0 h-screen w-screen bg-gradient-to-bl  from-[var(--color-brand1)]/70 to-[var(--color-brand2)]/70  backdrop-blur-xs'></div> */}
    <div className='fixed z-[2] top-0 left-0 h-screen w-screen overlay-gradient '></div>

    <div className='fixed z-[1] top-0 right-0 h-screen w-screen'>
      <img src={backImage} className='h-full w-full object-cover '/>
    </div>
           
        {/* Property List Section */}
        <div className='relative z-[3]  h-screen min-h-screen w-screen bg-transparent '>
          {/* <div className='absolute flex flex-col items-start gap-1 top-5 left-8'>
            <h1 className='text-2xl font-bold'>{totalProperties} Industrial Property Solutions</h1>
            <h1 className='text-2xl font-bold '> that fit your Chemical Industry Search</h1>
          </div> */}
          {/* <div className='absolute h-screen w-[50%] top-0 right-0 backdrop-blur-[2px]'></div> */}
          <div className='absolute top-8 left-5 w-[80%]'>
            <div className="w-full max-w-4xl rounded-2xl p-8">
              <div className="relative h-[500px]  flex items-center justify-center overflow-hidden rounded-xl">
                {/* Previous Button */}
                {currentIndex !== 0 && (
                  <button
                    onClick={prevProperty}
                    className="absolute left-6 z-30 cursor-pointer w-14 h-14 rounded-full flex items-center justify-center text-2xl font-bold transition-all duration-300 shadow-lg bg-white text-gray-700 hover:bg-gray-100 hover:scale-110 border border-gray-300"
                  >
                    <FaChevronLeft />
                  </button>
                )}

                {/* Properties Container */}
                <div className="relative w-full h-full flex items-center justify-center">
                  {visibleProperties.map((property,index) => (
                    <div
                      key={property.id}
                      className={getPropertyStyles(property.position, property.index)}
                      style={getPropertyPosition(property.position, property.index)} 
                      onClick={() => {
                        if(currentIndex === property.index) scrollToSection();
                        setSelectedProperty(solutions[property.propertyIndex-1])
                        // if(currentIndex === property.index) document.getElementById("factors-section")?.scrollIntoView({ behavior: "smooth" });
                      }}
                    >
                      {renderPropertyContent(property, property.position,property.propertyIndex)}
                    </div>
                  ))}
                </div>

                {/* Next Button */}
                <button
                  onClick={nextProperty}
                  className="absolute right-6 cursor-pointer z-30 w-14 h-14 bg-white rounded-full flex items-center justify-center text-2xl font-bold text-gray-700 hover:bg-gray-100 hover:scale-110 transition-all duration-300 shadow-lg border border-gray-300"
                >
                  <FaChevronRight />
                </button>
              </div>

              {/* Counter */}
              <div className="text-center -mt-3">
                <div className="font-semibold text-base text-black">
                  Property <span className="text-[#41b655] text-lg font-bold">{currentIndex + 1}</span> of{" "}
                  <span className=" text-black font-semibold text-black">{totalProperties}</span>
                </div>
              </div>

            </div>
          </div>

          <div className='absolute bottom-10 right-5  z-[3] w-[600px] h-[600px]'>
                  {/* <ScoreGuage value={80} /> */}
                  <GaugeMeter value={7.3} />
          </div>

                {/* <button
                  onClick={() => {
                    document
                      .getElementById("factors-section")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
                  className=" flex absolute bottom-10 left-[45%] p-3 items-center justify-center w-fit gap-2 bg-white/40 backdrop-blur-sm font-medium cursor-pointer  rounded-full py-2 transition-all duration-300"
                >
                  View Property Factors
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    stroke="currentColor"
                    className="w-4 relative top-1 h-4 animate-bounce"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button> */}


        </div>


        {/* Content Section for Factors */}
        <div ref={section2Ref} id='factors-section'  className="relative  h-fit min-h-[90vh] flex flex-row  justify-center lg:flex-row w-screen gap-6">
          
          {/* <div onClick={scrollToTop} className='absolute bottom-5 left-5 p-2 h-14 w-14 flex items-center justify-center   rounded-full z-[4] select-none cursor-pointer' title='Back To Top'><FaArrowUp className='animate-bounce text-xl' /> </div> */}
          {selectedProperty?.property_id && (<div className='absolute top-0 bg-white left-0 w-fit h-fit p-2 rounded-md z-[99] select-none'>{selectedProperty?.property_id}</div>)}

          {/* Canvas Container */}
          <div className={`flex flex-row justify-center ${aside ? '-left-80 z-[3]': '-left-8  z-[3]'} transition-all duration-700 ease-in-out min-w-0 h-full w-full rounded-2xl p-8  relative`}>
            <canvas
              ref={canvasRef}
              width={800}
              height={600}
              className=" rounded-xl cursor-pointer"
              onClick={handleCanvasClick}
            />

            {/* Info Boxes Overlay */}
            
          </div>

          <div className={` absolute right-8 h-full top-0 flex flex-col items-start justify-start p-4 bg-transparent w-[40%] duration-700 transition-all ${aside ? 'opacity-100 flex z-[3]' : 'opacity-0 z-[0]'}  self-start  `}>
              
              {activeArc && arcs[activeArc-1]?.title === 'Approval' && ( 
                <div 
                  className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''} card-entering`}
                  style={{ perspective: '1000px', height: '90%' }}
                >
                  <div 
                    className="flip-card-inner relative w-full h-full transition-transform duration-700"
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    {/* FRONT SIDE */}
                    <div 
                      className="flip-card-front absolute w-full h-full bg-white rounded-md flex flex-col items-start backface-hidden animate-fade-in-up"
                      style={{ backfaceVisibility: 'hidden' }}
                    >
                      <div 
                        className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md `}  
                        style={{ backgroundColor: arcs[activeArc-1].color, animationDelay: '0.1s' }}
                      >
                        <h1 className='relative font-bold text-lg flex flex-row items-center gap-3 opacity-0 animate-fade-in' style={{animationDelay: '0.2s'}}>
                          Compliance & Regulatory Checklist <IoInformationCircleOutline onClick={flipCard} className='relative top-0.3 cursor-pointer' />
                        </h1>
                        <div 
                          className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3 opacity-0 animate-fade-in'
                          style={{ color: arcs[activeArc-1].color, animationDelay: '0.2s' }}
                        >
                          100 found
                        </div>
                      </div>
                      
                      {/* <div className='relative flex flex-col gap-2 p-4 items-start flex-1 w-full'>

                        <div className="divide-y divide-gray-100 w-full opacity-0 animate-fade-in" style={{animationDelay: '0.5s'}}>
                          {approvals.map((item, index) => (
                            <div
                              key={index}
                              className="flex items-start justify-between py-3 opacity-0 animate-fade-in-up"
                              style={{animationDelay: `${0.6 + (index * 0.1)}s`}}
                            >
                              <div className="flex items-start gap-2">
                                <span 
                                  className="mt-2 w-2 h-2 rounded-full opacity-0 animate-scale-in"
                                  style={{ 
                                    backgroundColor: arcs[activeArc-1].color,
                                    animationDelay: `${0.7 + (index * 0.1)}s`
                                  }}
                                />
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
                        

                        <div className="w-full flex absolute bottom-4 justify-center items-center opacity-0 animate-fade-in" style={{animationDelay: '1s'}}>
                          <button 
                            className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg text-sm opacity-0 animate-scale-in"
                            style={{ 
                              backgroundColor: arcs[activeArc-1].color,
                              animationDelay: '1.1s'
                            }}
                          >
                            Explore Insights <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500' />
                          </button>
                        </div>
                      </div> */}
                      <div className='relative flex flex-col gap-2 p-4 items-start flex-1 w-full'>
                        
                        {/* Animated Approvals Grid */}
                        <div className="relative w-full grid grid-cols-4 gap-6 p-4 opacity-0 animate-fade-in" style={{animationDelay: '0.5s'}}>
                          {selectedProperty && selectedProperty?.approvals?.slice(0, 6).map((approval, index) => (
                            <>
                              <div 
                                key={`${index}-name`} 
                                className="relative flex flex-row items-start w-full gap-2 col-span-3 opacity-0 animate-fade-in-up"
                                style={{animationDelay: `${0.6 + (index * 0.1)}s`}}
                              >
                                <span 
                                  className="mt-2 w-2 h-2 rounded-full flex-shrink-0 opacity-0 animate-scale-in"
                                  style={{ 
                                    backgroundColor: arcs[activeArc-1]?.color || '#E91E63',
                                    animationDelay: `${0.7 + (index * 0.1)}s`
                                  }}
                                />
                                <div className='relative flex flex-col'>
                                  <span className="text-sm font-medium opacity-0 animate-fade-in" style={{animationDelay: `${0.8 + (index * 0.1)}s`}}>
                                    {approval.approval_name}
                                  </span>
                                  <span className='text-xs text-gray-500 opacity-0 animate-fade-in' style={{animationDelay: `${0.9 + (index * 0.1)}s`}}>
                                    {approval.government_department}
                                  </span>
                                </div>
                              </div>
                              <div 
                                key={`${index}-duration`} 
                                className="relative flex flex-row items-center gap-2 whitespace-nowrap col-span-1 justify-self-end opacity-0 animate-fade-in-up"
                                style={{animationDelay: `${0.6 + (index * 0.1)}s`}}
                              >
                                <div className='relative flex flex-col'>
                                  <p className='relative text-gray-600 text-xs opacity-0 animate-fade-in' style={{animationDelay: `${0.8 + (index * 0.1)}s`}}>
                                    {uiConfig?.['approval_duration'] || 'Est. Duration'}
                                  </p>
                                  <span className="text-sm text-black opacity-0 animate-fade-in" style={{animationDelay: `${0.9 + (index * 0.1)}s`}}>
                                    {approval.time_taken} days
                                  </span>
                                </div>
                              </div>
                            </>
                          ))}
                        </div>

                        {/* View More Button with Animation */}
                        {selectedProperty?.approvals?.length > 0 && (
                          <div className="w-full flex justify-center absolute bottom-4 items-center opacity-0 animate-fade-in" style={{animationDelay: '1s'}}>
                            <button 
                              className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg text-sm opacity-0 animate-scale-in"
                              style={{ 
                                backgroundColor: arcs[activeArc-1]?.color || '#E91E63',
                                animationDelay: '1.1s'
                              }}
                              onClick={handleShowApprovals}
                            >
                              {uiConfig?.['approval_list_button_title'] || "View Approvals"} 
                              <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500' />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* BACK SIDE */}
                    <div 
                      className="flip-card-back absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden"
                      style={{ 
                        backfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)'
                      }}
                    >
                      {/* Back side content with similar animations */}
                      <div className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white' style={{ backgroundColor: arcs[activeArc-1].color, animationDelay: '0.1s' }}>
                        <h1 className='relative font-bold text-lg opacity-0 animate-fade-in' style={{animationDelay: '0.2s'}}>Approval Insights & Analysis</h1>
                      </div>
                      
                      <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                        {/* Back side content with staggered animations */}
                        <div className='relative flex flex-col items-start opacity-0 animate-fade-in-up' style={{animationDelay: '0.3s'}}>
                          <h1 className='relative font-semibold text-base'>Stay Compliant, Stay Confident</h1>
                          <h3 className='relative tracking-wide text-sm'>Every approval listed here is more than just a certificate—it's a guarantee that your business meets essential legal and safety standards. With these in place, you can operate smoothly without surprises.</h3>
                        </div>
                        
                        <div className='relative flex flex-col items-start opacity-0 animate-fade-in-up' style={{animationDelay: '0.4s'}}>
                          <h1 className='relative font-semibold text-base'>What You Need to Know:</h1>
                          <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                            <li>Issued By: Relevant government or regulatory authority.</li>
                            <li>Purpose: Ensures safety, quality, and legality across operations.</li>
                            <li>Renewal: Some approvals expire, so tracking dates keeps you stress-free.</li>
                          </ul>
                        </div>
                        
                        <div className='relative flex flex-col items-start opacity-0 animate-fade-in-up' style={{animationDelay: '0.5s'}}>
                          <h1 className='relative font-semibold text-base'>Why It Matters to You:</h1>
                          <h3 className='relative tracking-wide text-sm'>Think of approvals as your business's shield—they protect you from legal issues, fines, and delays, while also building trust with clients and partners.</h3>
                        </div>
                        
                        {/* Back Button */}
                        <div className="text-center absolute bottom-3 flex items-center justify-center pt-4 w-full opacity-0 animate-fade-in" style={{animationDelay: '0.6s'}}>
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
                </div>
              )}

              {activeArc && arcs[activeArc-1]?.title === 'Incentives' && (
                <div 
                  className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''} card-entering`}
                  style={{ perspective: '1000px', height: '90%' }}
                >
                  <div 
                    className="flip-card-inner relative w-full h-full transition-transform duration-700"
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    {/* FRONT SIDE */}
                    <div 
                      className="flip-card-front absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden animate-fade-in-up"
                      style={{ backfaceVisibility: 'hidden' }}
                    >
                      <div 
                        className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md `}  
                        style={{ 
                          backgroundColor: arcs[activeArc-1].color,
                          animationDelay: '0.1s'
                        }}
                      >
                        <h1 className='relative font-bold text-lg flex flex-row items-center gap-3 opacity-0 animate-fade-in' style={{animationDelay: '0.2s'}}>
                          Subsidy & Support Matrix <IoInformationCircleOutline onClick={flipCard} className='relative top-0.3 cursor-pointer' />
                        </h1>
                        <div 
                          className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3 opacity-0 animate-fade-in'
                          style={{ 
                            color: arcs[activeArc-1].color,
                            animationDelay: '0.3s'
                          }}
                        >
                          100 found
                        </div>
                      </div>
                      
                      {/* <div className='relative flex flex-col gap-2 p-4 items-start flex-1 w-full'>

                        <div 
                          className="divide-y divide-gray-100 w-full opacity-0 animate-fade-in"
                          style={{animationDelay: '0.6s'}}
                        >
                          {incentives.map((item, index) => (
                            <div
                              key={index}
                              className="flex items-start justify-between py-3 opacity-0 animate-fade-in-up"
                              style={{animationDelay: `${0.7 + (index * 0.1)}s`}}
                            >
                              <div className="flex items-start gap-2">
                                <span 
                                  className="mt-2 w-2 h-2 rounded-full opacity-0 animate-scale-in"
                                  style={{ 
                                    backgroundColor: arcs[activeArc-1].color,
                                    animationDelay: `${0.8 + (index * 0.1)}s`
                                  }}
                                />
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
                        
                        <div 
                          className="w-full flex absolute bottom-4 justify-center items-center opacity-0 animate-fade-in"
                          style={{animationDelay: '1.2s'}}
                        >
                          <button 
                            className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg text-sm opacity-0 animate-scale-in"
                            style={{ 
                              backgroundColor: arcs[activeArc-1].color,
                              animationDelay: '1.3s'
                            }}
                          >
                            Explore Insights <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500' />
                          </button>
                        </div>
                      </div> */}
                      <div className="flex flex-col gap-6 relative w-full p-4 h-full opacity-0 animate-fade-in" style={{animationDelay: '0.5s'}}>
                        {selectedProperty?.incentives?.sort((a, b) => a.incentive_rank - b.incentive_rank).slice(0, 6).map((incentive, index) => (
                          <div 
                            key={index} 
                            className="flex items-start relative flex-row gap-2 opacity-0 animate-fade-in-up"
                            style={{animationDelay: `${0.6 + (index * 0.1)}s`}}
                          >
                            <div 
                              className="w-2 h-2 rounded-full mt-2 opacity-0 animate-scale-in"
                              style={{ 
                                backgroundColor: arcs[activeArc-1]?.color || '#4CAF50',
                                animationDelay: `${0.7 + (index * 0.1)}s`
                              }}
                            ></div>
                            <div className='relative flex flex-col items-start'>
                              <h3 
                                className="text-sm font-medium opacity-0 animate-fade-in"
                                style={{animationDelay: `${0.8 + (index * 0.1)}s`}}
                              >
                                {incentive.type}
                              </h3>
                              <p 
                                className="text-xs text-gray-600 opacity-0 animate-fade-in"
                                style={{animationDelay: `${0.9 + (index * 0.1)}s`}}
                              >
                                {incentive.name}
                              </p>
                            </div>
                          </div>
                        ))}
                        
                        {selectedProperty?.incentives?.length > 0 && (
                          <div className="flex flex-row gap-2 absolute bottom-4 items-center text-sm justify-center p-2 self-center cursor-pointer opacity-0 animate-fade-in" style={{animationDelay: '1s'}}>
                            <button 
                              className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg text-sm opacity-0 animate-scale-in"
                              style={{ 
                                backgroundColor: arcs[activeArc-1]?.color || '#4CAF50',
                                animationDelay: '1.1s'
                              }}
                              onClick={handleShowIncentive}
                            >
                              {uiConfig?.['incentives_list_button_title'] || "View Incentives"} 
                              <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500' />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* BACK SIDE */}
                    <div 
                      className="flip-card-back absolute w-full h-full bg-white rounded-md flex flex-col items-start backface-hidden"
                      style={{ 
                        backfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)'
                      }}
                    >
                      <div 
                        className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white opacity-0 animate-slide-down'
                        style={{ 
                          backgroundColor: arcs[activeArc-1].color,
                          animationDelay: '0.1s'
                        }}
                      >
                        <h1 
                          className='relative font-bold text-lg opacity-0 animate-fade-in'
                          style={{animationDelay: '0.2s'}}
                        >
                          Incentives Insights & Analysis
                        </h1>
                      </div>
                      
                      <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.3s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Maximize Your Benefits</h1>
                          <h3 className='relative tracking-wide text-sm'>Government incentives and subsidies are designed to support your business growth. From tax benefits to financial grants, these programs can significantly reduce your operational costs and boost competitiveness.</h3>
                        </div>
                        
                       
                        
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.9s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Strategic Advantage:</h1>
                          <h3 className='relative tracking-wide text-sm'>Properly utilized incentives can be the difference between breaking even and profitable growth. They demonstrate government commitment to fostering business development in key sectors.</h3>
                        </div>

                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '1s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Common Incentive Types:</h1>
                          <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.1s'}}>Tax Credits & Exemptions</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.2s'}}>Cash Grants & Subsidies</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.3s'}}>Low-Interest Loans</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.4s'}}>Training & Employment Support</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.5s'}}>Infrastructure Assistance</li>
                          </ul>
                        </div>
                        
                        {/* Back Button */}
                        <div 
                          className="text-center pt-4 w-full opacity-0 animate-fade-in"
                          style={{animationDelay: '1.6s'}}
                        >
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
                </div>
              )}

              {activeArc && arcs[activeArc-1]?.title === 'Vendors' && (
                <div 
                  className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''} card-entering`}
                  style={{ perspective: '1000px', height: '90%' }}
                >
                  <div 
                    className="flip-card-inner relative w-full h-full transition-transform duration-700"
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    {/* FRONT SIDE */}
                    <div 
                      className="flip-card-front absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden animate-fade-in-up"
                      style={{ backfaceVisibility: 'hidden' }}
                    >
                      <div 
                        className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md `}  
                        style={{ 
                          backgroundColor: arcs[activeArc-1].color,
                          animationDelay: '0.1s'
                        }}
                      >
                        <h1 
                          className='relative font-bold text-lg flex flex-row items-center gap-3 opacity-0 animate-fade-in'
                          style={{animationDelay: '0.2s'}}
                        >
                          Supply Chain Accessibility <IoInformationCircleOutline onClick={flipCard} className='relative top-0.3 cursor-pointer' />
                        </h1>
                      </div>
                      
                      <div className='relative flex flex-col gap-3 p-4 items-start flex-1 w-full'>
                        {/* <h2 
                          className='relative text-sm font-semibold text-left italic opacity-0 animate-fade-in'
                          style={{animationDelay: '0.3s'}}
                        >
                          Each approval listed below represents an essential compliance or certification required across different sectors.
                        </h2> */}
                        
                        {/* <h2 
                          onClick={flipCard}
                          className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full opacity-0 animate-fade-in"
                          style={{animationDelay: '0.4s'}}
                        >
                          Know More About Vendors <FaArrowRightLong className="relative top-0.5" />
                        </h2> */}

                        <div className='relative grid grid-cols-2 w-full gap-3 items-center opacity-0 animate-fade-in' style={{animationDelay: '0.5s'}}>
                          {/* Category Headers */}
                          <div 
                            className='relative py-1 px-6 mt-4 mb-4 rounded-full text-sm w-fit text-orange-500 bg-orange-100 font-bold flex justify-self-center items-center justify-center opacity-0 animate-scale-in'
                            style={{animationDelay: '0.6s'}}
                          >
                            Essential
                          </div>
                          <div 
                            className='relative py-1 px-6 mt-4 mb-4 rounded-full text-sm w-fit text-blue-500 bg-blue-100 font-bold flex justify-self-center items-center justify-center opacity-0 animate-scale-in'
                            style={{animationDelay: '0.6s'}}
                          >
                            Non - Essential
                          </div>

                          {/* Vendor Cards - Staggered Animation */}
                          {selectedProperty?.essential_vendors?.slice(0, 8)?.map((essentials, index) => {
                            const isEssential = index % 2 === 0;
                            const bgColor = isEssential ? 'bg-orange-50' : 'bg-blue-50';
                            const borderColor = isEssential ? 'border-orange-200' : 'border-blue-200';
                            const delay = 0.7 + (index * 0.1);
                            
                            return (
                              <div
                                key={index}
                                className={`relative flex flex-col gap-1 items-start p-2 ${bgColor} border ${borderColor} rounded-md opacity-0 animate-fade-in-up`}
                                style={{animationDelay: `${delay}s`}}
                              >
                                <h1 className='relative font-semibold text-sm opacity-0 animate-fade-in' style={{animationDelay: `${delay + 0.1}s`}}>
                                  {essentials.supply}
                                </h1>
                                <h3 className='relative text-xs opacity-0 animate-fade-in' style={{animationDelay: `${delay + 0.2}s`}}>
                                  {uiConfig?.['no_of_vendors'] || 'Vendors Found:'} {essentials.total_vendor}
                                </h3>
                                <div className='flex flex-row items-center gap-1 opacity-0 animate-fade-in' style={{animationDelay: `${delay + 0.3}s`}}>
                                  <h3 className='relative text-xs'>
                                    {uiConfig?.['nearest_vendor'] || 'Nearby Distance:'} {essentials.nearest_vendor_distance.toFixed(2)} km
                                  </h3>
                                  {essentials.status === 'good' ? (
                                    <BsPatchCheckFill className="text-green-500 text-sm" />
                                  ) : essentials.status === 'warning' ? (
                                    <FaTriangleExclamation className="text-yellow-500 text-sm" />
                                  ) : (
                                    <FaCircleXmark className="text-red-500 text-sm" />
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="w-full flex absolute bottom-4 justify-center items-center opacity-0 animate-fade-in" style={{animationDelay: '1s'}}>
                          <button 
                            className="explore-btn relative flex flex-row cursor-pointer group items-center gap-2 px-6 py-2 text-white font-semibold rounded-full transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg text-sm opacity-0 animate-scale-in"
                            style={{ 
                              backgroundColor: arcs[activeArc-1].color,
                              animationDelay: '1.1s'
                            }}
                            onClick={handleShowVendor}
                          >
                            Explore More Vendors  <FaArrowRightLong className='relative top-0.5 group-hover:left-1 transition-all duration-500'  />
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    {/* BACK SIDE */}
                    <div 
                      className="flip-card-back absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden"
                      style={{ 
                        backfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)'
                      }}
                    >
                      <div 
                        className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white '
                        style={{ 
                          backgroundColor: arcs[activeArc-1].color,
                          animationDelay: '0.1s'
                        }}
                      >
                        <h1 
                          className='relative font-bold text-lg opacity-0 animate-fade-in'
                          style={{animationDelay: '0.2s'}}
                        >
                          Location Intelligence Summary
                        </h1>
                      </div>
                      
                      <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.3s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Optimize Your Supply Chain</h1>
                          <h3 className='relative tracking-wide text-sm'>Strategic vendor placement ensures reliable material flow and reduces operational costs. Our location intelligence helps you identify the most accessible and reliable suppliers in your region.</h3>
                        </div>
                        
                        
                        
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.9s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Strategic Advantages:</h1>
                          <h3 className='relative tracking-wide text-sm'>Local vendor networks reduce transportation costs by 15-25%, improve delivery reliability, and enable faster response to market demands. Essential materials are prioritized within 100km radius.</h3>
                        </div>

                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '1s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Key Metrics Tracked:</h1>
                          <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.1s'}}>Average Distance to Vendors</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.2s'}}>Vendor Concentration Index</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.3s'}}>Supply Chain Resilience Score</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.4s'}}>Logistics Cost Projections</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '1.5s'}}>Alternative Sourcing Options</li>
                          </ul>
                        </div>
                        
                        {/* Back Button */}
                        <div 
                          className="text-center absolute bottom-3 flex items-center justify-center pt-4 w-full opacity-0 animate-fade-in"
                          style={{animationDelay: '1.6s'}}
                        >
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
                </div>
              )}

              {activeArc && arcs[activeArc-1]?.title === 'Employment' && (
                <div className={`flip-card relative w-full rounded-md  ${isFlipped ? 'flipped' : ''} card-entering`} style={{ perspective: '1000px', height: '90%' }} >
                  <div 
                  className="flip-card-inner relative w-full h-full transition-transform duration-700"
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  {/* FRONT SIDE - Your existing code */}
                  <div 
                    className="flip-card-front absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden animate-fade-in-up"
                    style={{ backfaceVisibility: 'hidden' }}
                  >
                    <div className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md`}  style={{ backgroundColor: arcs[activeArc-1].color,animationDelay: '0.1s' }}>
                      <h1 className='relative font-bold text-lg flex flex-row items-center gap-3 opacity-0 animate-fade-in' style={{animationDelay: '0.2s'}}>Workforce Availability Insights <IoInformationCircleOutline onClick={flipCard} className='relative top-0.3 cursor-pointer' /></h1>
                      {/* <div className='py-1 px-4 rounded-full bg-gray-100 text-xs font-semibold tracking-wide top-0.3' style={{ color: arcs[activeArc-1].color }}>100 found</div> */}
                    </div>
                    <div className='relative flex flex-col gap-3 p-4 items-start flex-1 w-full'>
                      {/* <h2 className='relative text-sm font-semibold text-left italic opacity-0 animate-fade-in' style={{animationDelay: '0.3s'}}> Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.</h2> */}
                    {/* <h2 onClick={flipCard}  style={{animationDelay: '0.4s'}} className=" opacity-0 animate-fade-in relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full">Know More About Incentives <FaArrowRightLong className="relative top-0.5" /> </h2> */}

                      <div className='relative flex flex-col gap-8 mt-8 min-h-[60%] w-full'>
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
                          <div className="text-center flex flex-col gap-2 opacity-0 animate-fade-in-up" style={{animationDelay: '0.5s'}} >
                            <div className="text-xs font-medium">Skilled</div>
                            <div className="text-sm text-blue-600 font-semibold">{employeeData.skilled_no} workers</div>
                          </div>
                          <div className="text-center flex flex-col gap-2 opacity-0 animate-fade-in-up" style={{animationDelay: '0.6s'}}>
                            <div className="text-xs font-medium">Semi-skilled</div>
                            <div className="text-sm text-green-600 font-semibold">{employeeData.semi_skilled_no} workers</div>
                          </div>
                          <div className="text-center flex flex-col gap-2 opacity-0 animate-fade-in-up" style={{animationDelay: '0.7s'}}>
                            <div className="text-xs font-medium">Unskilled</div>
                            <div className="text-sm text-amber-600 font-semibold">{employeeData.unskilled_no} workers</div>
                          </div>
                        </div>
                      </div>
                    
                    </div>
                  </div>
                  
                  {/* BACK SIDE - Empty for now with same height */}
                  <div 
                    className="flip-card-back absolute w-full h-full bg-white rounded-md flex flex-col items-start backface-hidden"
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
                      <div className="text-center absolute bottom-3 flex items-center justify-center pt-4 w-full">
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
                  
              </div>
              )}

              {activeArc && arcs[activeArc-1]?.title === 'Location Summary' && (
                <div 
                  className={`flip-card relative w-full rounded-md ${isFlipped ? 'flipped' : ''} card-entering`}
                  style={{ perspective: '1000px', height: '90%' }}
                >
                  <div 
                    className="flip-card-inner relative w-full h-full transition-transform duration-700"
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    {/* FRONT SIDE */}
                    <div 
                      className="flip-card-front absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden animate-fade-in-up"
                      style={{ backfaceVisibility: 'hidden' }}
                    >
                      <div 
                        className={`relative h-fit py-3 px-4 flex flex-row items-center justify-between items-start w-full rounded-tl-md text-white rounded-tr-md `}  
                        style={{ 
                          backgroundColor: arcs[activeArc-1].color,
                          animationDelay: '0.1s'
                        }}
                      >
                        <h1 
                          className='relative font-bold text-lg flex flex-row items-center gap-3 opacity-0 animate-fade-in'
                          style={{animationDelay: '0.2s'}}
                        >
                          Location Intelligence Summary <IoInformationCircleOutline onClick={flipCard} className='relative top-0.3 cursor-pointer' />
                        </h1>
                      </div>
                      
                      <div className='relative flex flex-col gap-3 p-4 items-start flex-1 w-full'>
                        {/* <h2 
                          className='relative text-sm font-semibold text-left italic opacity-0 animate-fade-in'
                          style={{animationDelay: '0.3s'}}
                        >
                          Each approval listed below represents an essential compliance or certification required across different sectors. These ensure that operations meet the legal, safety, and quality standards set by respective government departments.
                        </h2> */}
                        
                        {/* <h2 
                          onClick={flipCard}
                          className="relative flex items-center gap-1 cursor-pointer text-blue-700 transition-all hover:gap-2 duration-500 after:content-[''] after:absolute after:left-0 after:bottom-0 after:h-[2px] after:bg-blue-700 after:w-0 after:transition-all after:duration-500 hover:after:w-full opacity-0 animate-fade-in"
                          style={{animationDelay: '0.4s'}}
                        >
                          Know More About Location <FaArrowRightLong className="relative top-0.5" />
                        </h2> */}

                        <div className="flex flex-col gap-8 w-full opacity-0 animate-fade-in" style={{animationDelay: '0.5s'}}>
                          {/* Transportation Access Section */}
                          <div className="opacity-0 animate-fade-in-up" style={{animationDelay: '0.6s'}}>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">Transportation Access</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {[
                                { 
                                  name: uiConfig?.['location_summary_highway_title'] || "Highway", 
                                  desc: 'Major road access', 
                                  distance: `${selectedProperty?.road_connectivity?.distance?.toFixed(2)} km`, 
                                  status: selectedProperty?.road_connectivity?.status === 'good' ? 'Good' : selectedProperty?.road_connectivity?.status === 'warning' ? 'Fair' : 'Poor',
                                  color: selectedProperty?.road_connectivity?.status === 'good' ? '#16a34a' : selectedProperty?.road_connectivity?.status === 'warning' ? '#d97706' : '#dc2626'
                                },
                                { 
                                  name: uiConfig?.['location_summary_railway_title'] || "Railway", 
                                  desc: 'Rail connectivity', 
                                  distance: `${selectedProperty?.railway?.distance?.toFixed(2)} km`, 
                                  status: selectedProperty?.railway?.status === 'good' ? 'Excellent' : selectedProperty?.railway?.status === 'warning' ? 'Fair' : 'Poor',
                                  color: selectedProperty?.railway?.status === 'good' ? '#15803d' : selectedProperty?.railway?.status === 'warning' ? '#d97706' : '#dc2626'
                                },
                                { 
                                  name: uiConfig?.['location_summary_airport_title'] || "Airport", 
                                  desc: 'Air transport hub', 
                                  distance: `${selectedProperty?.airport?.distance?.toFixed(2)} km`, 
                                  status: selectedProperty?.airport?.status === 'good' ? 'Good' : selectedProperty?.airport?.status === 'warning' ? 'Fair' : 'Poor',
                                  color: selectedProperty?.airport?.status === 'good' ? '#16a34a' : selectedProperty?.airport?.status === 'warning' ? '#d97706' : '#dc2626'
                                },
                                { 
                                  name: uiConfig?.['location_summary_seaport_title'] || "Seaport", 
                                  desc: 'Maritime access', 
                                  distance: `${selectedProperty?.seaport?.distance?.toFixed(2)} km`, 
                                  status: selectedProperty?.seaport?.status === 'good' ? 'Good' : selectedProperty?.seaport?.status === 'warning' ? 'Fair' : 'Poor',
                                  color: selectedProperty?.seaport?.status === 'good' ? '#16a34a' : selectedProperty?.seaport?.status === 'warning' ? '#d97706' : '#dc2626'
                                }
                              ].map((item, index) => (
                                <div 
                                  key={index}
                                  className="flex items-center justify-between py-2 border-b border-gray-100 opacity-0 animate-fade-in-up"
                                  style={{animationDelay: `${0.7 + (index * 0.1)}s`}}
                                >
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">{item.name}</div>
                                    <div className="text-xs text-gray-600">{item.desc}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-sm font-medium text-gray-900">{item.distance}</div>
                                    <div className="text-xs font-medium" style={{ color: item.color }}>{item.status}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          {/* Infrastructure & Services Section */}
                          <div className="opacity-0 animate-fade-in-up" style={{animationDelay: '1.1s'}}>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">Infrastructure & Services</h3>
                            <div className="flex flex-col gap-3">
                              {[
                                { 
                                  name: uiConfig?.['location_summary_power_source_title'] || "Power Source", 
                                  distance: `${selectedProperty?.power?.distance?.toFixed(2)} km`, 
                                  status: selectedProperty?.power?.status === 'good' ? 'Adequate access to power grid' : selectedProperty?.power?.status === 'warning' ? 'Limited power access' : 'Poor power infrastructure',
                                  bgColor: selectedProperty?.power?.status === 'good' ? '#f0fdf4' : selectedProperty?.power?.status === 'warning' ? '#fefce8' : '#fef2f2',
                                  borderColor: selectedProperty?.power?.status === 'good' ? '#bbf7d0' : selectedProperty?.power?.status === 'warning' ? '#fde68a' : '#fecaca',
                                  textColor: selectedProperty?.power?.status === 'good' ? '#166534' : selectedProperty?.power?.status === 'warning' ? '#92400e' : '#991b1b'
                                },
                                { 
                                  name: uiConfig?.['location_summary_transportation_title'] || "Local Transportation", 
                                  distance: selectedProperty?.availability_of_local_transportation, 
                                  status: selectedProperty?.availability_of_local_transportation === 'good' ? 'Good local transit options' : selectedProperty?.availability_of_local_transportation === 'warning' ? 'Limited local transit' : 'Poor local transit options',
                                  bgColor: selectedProperty?.availability_of_local_transportation === 'good' ? '#f0fdf4' : selectedProperty?.availability_of_local_transportation === 'warning' ? '#fefce8' : '#fef2f2',
                                  borderColor: selectedProperty?.availability_of_local_transportation === 'good' ? '#bbf7d0' : selectedProperty?.availability_of_local_transportation === 'warning' ? '#fde68a' : '#fecaca',
                                  textColor: selectedProperty?.availability_of_local_transportation === 'good' ? '#166534' : selectedProperty?.availability_of_local_transportation === 'warning' ? '#92400e' : '#991b1b'
                                },
                                { 
                                  name: uiConfig?.['location_summary_network_title'] || "Network Coverage", 
                                  distance: selectedProperty?.network_availability, 
                                  status: selectedProperty?.network_availability === '4G & 5G' ? 'Excellent connectivity' : selectedProperty?.network_availability === '4G' ? 'Basic connectivity available' : 'Poor network coverage',
                                  bgColor: selectedProperty?.network_availability === '4G & 5G' ? '#f0fdf4' : selectedProperty?.network_availability === '4G' ? '#fefce8' : '#fef2f2',
                                  borderColor: selectedProperty?.network_availability === '4G & 5G' ? '#bbf7d0' : selectedProperty?.network_availability === '4G' ? '#fde68a' : '#fecaca',
                                  textColor: selectedProperty?.network_availability === '4G & 5G' ? '#166534' : selectedProperty?.network_availability === '4G' ? '#92400e' : '#991b1b'
                                }
                              ].map((item, index) => (
                                <div 
                                  key={index}
                                  className="rounded-lg p-2 opacity-0 animate-fade-in-up border"
                                  style={{
                                    animationDelay: `${1.2 + (index * 0.1)}s`,
                                    backgroundColor: `${item.bgColor}`,
                                    borderColor: `${item.borderColor}`
                                  }}
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-900">{item.name}</span>
                                    <span className="text-sm" style={{ color: item.textColor }}>{item.distance}</span>
                                  </div>
                                  <div className="text-xs mt-1" style={{ color: item.textColor }}>{item.status}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* BACK SIDE */}
                    <div 
                      className="flip-card-back absolute w-full h-full bg-white  rounded-md flex flex-col items-start backface-hidden"
                      style={{ 
                        backfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)'
                      }}
                    >
                      <div 
                        className='relative h-fit py-3 px-4 flex flex-col gap-2 items-start bg-gray-200 w-full rounded-tl-md rounded-tr-md text-white '
                        style={{ 
                          backgroundColor: arcs[activeArc-1].color,
                          animationDelay: '0.1s'
                        }}
                      >
                        <h1 
                          className='relative font-bold text-lg opacity-0 animate-fade-in'
                          style={{animationDelay: '0.2s'}}
                        >
                          Location Intelligence Summary
                        </h1>
                      </div>
                      
                      <div className='relative flex flex-col gap-8 p-4 items-start flex-1 w-full'>
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.3s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Strategic Location Advantages</h1>
                          <h3 className='relative tracking-wide text-sm'>Your location offers unique logistical benefits and infrastructure access that can significantly impact operational efficiency and cost-effectiveness.</h3>
                        </div>
                        
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.4s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Key Location Insights:</h1>
                          <ul className='pl-8 relative gap-2' style={{listStyleType:'disc' }}>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '0.5s'}}>Transportation: Excellent rail connectivity with good highway access</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '0.6s'}}>Infrastructure: Reliable power supply with basic network coverage</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '0.7s'}}>Logistics: Strategic positioning for regional distribution</li>
                            <li className="opacity-0 animate-fade-in" style={{animationDelay: '0.8s'}}>Connectivity: Multiple transport options for supply chain flexibility</li>
                          </ul>
                        </div>
                        
                        <div 
                          className='relative flex flex-col items-start opacity-0 animate-fade-in-up'
                          style={{animationDelay: '0.9s'}}
                        >
                          <h1 className='relative font-semibold text-base'>Why Location Matters:</h1>
                          <h3 className='relative tracking-wide text-sm'>Strategic location selection can reduce transportation costs by 15-25%, improve supply chain reliability, and provide competitive advantages in market access and distribution.</h3>
                        </div>
                        
                        {/* Back Button */}
                        <div 
                          className="text-center absolute bottom-3 flex items-center justify-center pt-4 w-full opacity-0 animate-fade-in"
                          style={{animationDelay: '1.0s'}}
                        >
                          <button 
                            className="back-btn px-6 py-2 text-white font-semibold rounded-full cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:shadow-lg hover:shadow-gray-500/30 text-sm"
                            onClick={flipCard}
                            style={{ backgroundColor: arcs[activeArc-1].color }}
                          >
                            ↺ Back to Details
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}


          </div>
          
          <div className='absolute bottom-10 z-[99] left-3 p-2 bg-white rounded-full w-fit h-fit select-none text-xs flex flex-row gap-2 items-center cursor-pointer' onClick={()=>{scrolltoProperty()}}>Back to Property List <div className='animate-bounce transition-all duration-300'> <FaArrowUp /></div></div>
        </div>

    
    </div>

    {approvalsWindow && approvalsToSend && (
        <div className='fixed top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setApprovalWindow(false), setApprovalsToSend() }} >
            <FaXmark size={22} />
          </div>
          <Approvalresult result={approvalsToSend} source="FromScratch" rerender={1} />
        </div>
      )}
      {incentivesWindow && incentivesToSend && (
        <div className='fixed top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setIncentivesWindow(false), setIncentivesToSend() }}>
            <FaXmark size={28} />
          </div>
          <Incentiveresult res={incentivesToSend} source="FromScratch" rerender={1} />
        </div>
      )}
      {vendorsWindow && vendorsToSend && (
        <div className='fixed top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setVendorsWindow(false), setVendorsToSend() }}>
            <FaXmark size={28} />
          </div>
          <Vendorresult result={vendorsToSend} source="FromScratch" />
        </div>
      )}
    </>
  );
};

export default NewIndustryScreen;