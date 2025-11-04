// import React from "react";

// const GaugeMeter = ({ value = 7.5 }) => {
//   // Convert value out of 10 to percentage for arc calculation
//   const percentage = (value / 10) * 100;
  
//   // Determine color and label based on value
//   const getStatusInfo = (val) => {
//     if (val >= 8) return { label: "Excellent Property", color: "#10b981" };
//     if (val >= 6) return { label: "Good Property", color: "#3b82f6" };
//     if (val >= 4) return { label: "Fair Property", color: "#f59e0b" };
//     return { label: "Needs Improvement", color: "#ef4444" };
//   };

//   const statusInfo = getStatusInfo(value);

//   return (
//     <div className="flex flex-col z-[3] items-center justify-center p-8 rounded-2xl">
//       <div className="relative">
//         <svg width="650" height="450" viewBox="0 0 560 390">
//           <defs>
//             <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
//               <stop offset="0%" stopColor="#10b981" />
//               <stop offset="50%" stopColor="#06b6d4" />
//               <stop offset="100%" stopColor="#3b82f6" />
//             </linearGradient>
//           </defs>
          
//           {/* Background arc */}
//           <path
//             d="M 98 280 A 182 182 0 0 1 462 280"
//             fill="none"
//             stroke="#e5e7eb"
//             strokeWidth="56"
//             strokeLinecap="round"
//           />
          
//           {/* Score arc */}
//           <path
//             d="M 98 280 A 182 182 0 0 1 462 280"
//             fill="none"
//             stroke="url(#scoreGradient)"
//             strokeWidth="56"
//             strokeLinecap="round"
//             strokeDasharray={`${(percentage / 100) * 571.8} 571.8`}
//             style={{ transition: 'stroke-dasharray 0.5s ease' }}
//           />
          
//           {/* Score value */}
//           <text
//             x="280"
//             y="224"
//             textAnchor="middle"
//             dominantBaseline="middle"
//             fontSize="67"
//             fontWeight="bold"
//             fill="#1f2937"
//           >
//             {value}
//           </text>
          
//           {/* Label */}
//           <text
//             x="280"
//             y="273"
//             textAnchor="middle"
//             dominantBaseline="middle"
//             fontSize="28"
//             fill="#6b7280"
//           >
//             /10
//           </text>
//         </svg>
//       </div>

//       {/* Status label */}
//       <div className="absolute bottom-32 flex items-center gap-2">
//         <div 
//           className="w-3 h-3 rounded-full" 
//           style={{ backgroundColor: statusInfo.color }}
//         />
//         <span className="text-lg font-semibold text-gray-700">
//           {statusInfo.label}
//         </span>
//       </div>
//     </div>
//   );
// };

// export default GaugeMeter;

import React, { useState, useEffect } from "react";

const GaugeMeter = ({ value = 7.5 }) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const [dashOffset, setDashOffset] = useState(571.8); // Start with full dash offset
  
  // Convert value out of 10 to percentage for arc calculation
  const percentage = (value / 10) * 100;
  const targetDashValue = (percentage / 100) * 571.8;
  
  // Determine color and label based on value
  const getStatusInfo = (val) => {
    if (val >= 8) return { label: "Excellent Property", color: "#10b981" };
    if (val >= 6) return { label: "Good Property", color: "#3b82f6" };
    if (val >= 4) return { label: "Fair Property", color: "#f59e0b" };
    return { label: "Needs Improvement", color: "#ef4444" };
  };

  const statusInfo = getStatusInfo(value);

  useEffect(() => {
    // Reset animation state
    setAnimatedValue(0);
    setDashOffset(571.8);
    
    // Animate the value counter
    const duration = 500; // 1.5 seconds
    const steps = 60;
    const increment = value / steps;
    const stepTime = duration / steps;
    
    let currentStep = 0;
    const valueTimer = setInterval(() => {
      currentStep++;
      setAnimatedValue(prev => {
        const newValue = prev + increment;
        return newValue >= value ? value : newValue;
      });
      
      if (currentStep >= steps) {
        clearInterval(valueTimer);
      }
    }, stepTime);

    // Animate the arc drawing
    const arcDuration = 500; // 1.2 seconds
    const arcSteps = 50;
    const arcStepTime = arcDuration / arcSteps;
    
    let currentArcStep = 0;
    const arcTimer = setInterval(() => {
      currentArcStep++;
      setDashOffset(prev => {
        const progress = currentArcStep / arcSteps;
        const newOffset = 571.8 - (targetDashValue * progress);
        return newOffset <= 571.8 - targetDashValue ? 571.8 - targetDashValue : newOffset;
      });
      
      if (currentArcStep >= arcSteps) {
        clearInterval(arcTimer);
      }
    }, arcStepTime);

    // Cleanup timers on unmount
    return () => {
      clearInterval(valueTimer);
      clearInterval(arcTimer);
    };
  }, [value, targetDashValue]);

  return (
    <div className="flex flex-col z-[3] items-center justify-center p-8 rounded-2xl">
      <div className="relative">
        <svg width="650" height="450" viewBox="0 0 560 390">
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="50%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#3b82f6" />
            </linearGradient>
          </defs>
          
          {/* Background arc */}
          <path
            d="M 98 280 A 182 182 0 0 1 462 280"
            fill="none"
            stroke="#ffffff"
            strokeWidth="50"
            strokeLinecap="round"
          />
          
          {/* Animated Score arc */}
          <path
            d="M 98 280 A 182 182 0 0 1 462 280"
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth="50"
            strokeLinecap="round"
            strokeDasharray="571.8"
            strokeDashoffset={dashOffset}
            style={{ 
              transition: 'stroke-dashoffset 0.05s ease-out',
              transform: 'rotate(0.1deg)', // Force hardware acceleration
              transformOrigin: 'center center'
            }}
          />
          
          {/* Animated Score value */}
          <text
            x="280"
            y="224"
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="67"
            fontWeight="bold"
            fill="white"
            // fill="#1f2937"
          >
            {animatedValue.toFixed(1)}
          </text>
          
          {/* Label */}
          <text
            x="280"
            y="273"
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="28"
            fontWeight="bold"
            fill="white"
          >
            /10
          </text>
        </svg>
      </div>

      {/* Status label */}
      <div className="absolute bottom-32 flex items-center gap-2">
        <div 
          className="w-3 h-3 rounded-full" 
          style={{ backgroundColor: statusInfo.color }}
        />
        <span className="text-lg font-semibold text-white">
          {statusInfo.label}
        </span>
      </div>
    </div>
  );
};

export default GaugeMeter;