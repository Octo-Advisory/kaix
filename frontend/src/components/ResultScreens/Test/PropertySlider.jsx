import React, { useState } from 'react';

const PropertySlider = () => {
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

  return (
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
  );
};

export default PropertySlider;