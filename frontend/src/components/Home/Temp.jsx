<div className="p-6 bg-[#f8f9fa]">
  {/* Header Section */}
  <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8">
    <div>
      <h2 className="text-xl lg:text-2xl font-medium text-gray-600 uppercase tracking-wider">Industrial Property Solution</h2>
      <h1 className="text-2xl lg:text-4xl font-bold text-gray-900 mt-1">{solution.property_type}</h1>
      <p className="text-gray-500 mt-2 flex items-center">
        <svg className="w-4 h-4 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
        </svg>
        {solution.address}
      </p>
    </div>
    <div className="mt-4 lg:mt-0 bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100">
      <span className="text-sm font-medium text-gray-700">{solution.total_area} Acres Total Area</span>
    </div>
  </div>

  {/* Main Grid */}
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
    {/* Map Section */}
    <div className="lg:col-span-1 h-64 bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
      <div className="p-3 bg-gray-50 border-b flex items-center">
        <svg className="w-4 h-4 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M12 1.586l-4 4v12.828l4-4V1.586zM3.707 3.293A1 1 0 002 4v10a1 1 0 00.293.707L6 18.414V5.586L3.707 3.293zM17.707 5.293L14 1.586v12.828l2.293 2.293A1 1 0 0018 16V6a1 1 0 00-.293-.707z" clipRule="evenodd" />
        </svg>
        <span className="text-sm font-medium text-gray-600">Location Overview</span>
      </div>
      <MapContainer
        key={solution.address}
        center={solution.latitude_longitude || [0, 0]}
        zoom={13}
        style={{ height: 'calc(100% - 40px)', width: '100%' }}
        className='rounded-b-lg'
        attributionControl={false}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        />
        <Marker position={solution.latitude_longitude || [0, 0]} icon={defaultIcon}>
          <Popup className="font-medium">{solution.property_type}</Popup>
        </Marker>
      </MapContainer>
    </div>

    {/* Specifications Section */}
    <div className="lg:col-span-1 bg-white rounded-xl shadow-md p-5 border border-gray-100">
      <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
        <div className="bg-blue-100 p-2 rounded-lg mr-3">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-800">Specifications</h3>
      </div>
      <ul className="space-y-3">
        {[
          { 
            icon: '🏭', 
            title: solution.property_type, 
            subtitle: 'Industrial property type',
            status: 'good'
          },
          { 
            icon: '📏', 
            title: `${solution.total_area} Acres`, 
            subtitle: 'Total land area',
            status: 'good'
          },
          { 
            icon: '🚢', 
            title: `${solution.seaport.distance} km from Seaport`, 
            subtitle: 'Nearest port facility',
            status: solution.seaport.status
          },
          { 
            icon: '🚂', 
            title: `${solution.railway.distance} km from Railway`, 
            subtitle: 'Nearest railway station',
            status: solution.railway.status
          }
        ].map((item, index) => (
          <li key={index} className="flex items-start">
            <div className="bg-gray-100 p-2 rounded-lg mr-3 text-gray-600">
              {item.icon}
            </div>
            <div className="flex-1">
              <p className="font-medium text-gray-800">{item.title}</p>
              <p className="text-xs text-gray-500">{item.subtitle}</p>
            </div>
            <div className="ml-2">
              {statusIcon[item.status]}
            </div>
          </li>
        ))}
      </ul>
    </div>

    {/* Infrastructure Section */}
    <div className="lg:col-span-1 bg-white rounded-xl shadow-md p-5 border border-gray-100">
      <div className="flex items-center mb-4 pb-2 border-b border-gray-100">
        <div className="bg-purple-100 p-2 rounded-lg mr-3">
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-800">Infrastructure</h3>
      </div>
      <ul className="space-y-3">
        {[
          {
            icon: '🏙️',
            title: solution.business_location_type,
            subtitle: 'Location type',
            status: 'good'
          },
          {
            icon: '🚌',
            title: 'Local Transport',
            subtitle: solution.availability_of_local_transportation ? 'Available' : 'Limited',
            status: solution.availability_of_local_transportation
          },
          {
            icon: '🛣️',
            title: `${solution.road_connectivity.distance} km from Major Road`,
            subtitle: 'Road connectivity',
            status: solution.road_connectivity.status
          },
          {
            icon: '👷',
            title: `${solution.employement.count} ${solution.employement.type} Workers`,
            subtitle: 'Workforce availability',
            status: 'good'
          }
        ].map((item, index) => (
          <li key={index} className="flex items-start">
            <div className="bg-gray-100 p-2 rounded-lg mr-3 text-gray-600">
              {item.icon}
            </div>
            <div className="flex-1">
              <p className="font-medium text-gray-800">{item.title}</p>
              <p className="text-xs text-gray-500">{item.subtitle}</p>
            </div>
            <div className="ml-2">
              {statusIcon[item.status]}
            </div>
          </li>
        ))}
      </ul>
    </div>
  </div>

  {/* Suppliers Section */}
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
    {/* Essential Suppliers */}
    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-white">
        <div className="flex items-center">
          <div className="bg-blue-100 p-2 rounded-lg mr-3">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-800">Essential Suppliers</h4>
        </div>
        <span className="bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full font-medium">
          {solution.essential_vendors.length} Available
        </span>
      </div>
      <div className="p-4">
        <ul className="space-y-3">
          {solution.essential_vendors.slice(0, 5).map((item, ind) => (
            <li key={ind} className="flex items-start">
              <div className={`p-1 rounded-full mr-3 ${item.status === 'good' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                {item.status === 'good' ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-800">{item.supply}</p>
                <p className="text-xs text-gray-500">
                  {item.total_vendor} suppliers (Nearest: {item.nearest_vendor_distance.toFixed(2)} km)
                </p>
              </div>
            </li>
          ))}
        </ul>
        {solution.essential_vendors.length > 5 && (
          <button 
            className="w-full mt-4 text-sm text-blue-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
            onClick={() => toggleModal(solution.essential_vendors, 'Essential Suppliers')}
          >
            <span>View all {solution.essential_vendors.length} suppliers</span>
            <svg className="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>

    {/* Non-Essential Suppliers */}
    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-purple-50 to-white">
        <div className="flex items-center">
          <div className="bg-purple-100 p-2 rounded-lg mr-3">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-800">Support Services</h4>
        </div>
        <span className="bg-purple-100 text-purple-800 text-xs px-3 py-1 rounded-full font-medium">
          {solution.nonessential_vendors.length} Available
        </span>
      </div>
      <div className="p-4">
        <ul className="space-y-3">
          {solution.nonessential_vendors.slice(0, 5).map((item, index) => (
            <li key={index} className="flex items-start">
              <div className={`p-1 rounded-full mr-3 ${item.status === 'good' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                {item.status === 'good' ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-800">{item.supply}</p>
                <p className="text-xs text-gray-500">
                  {item.total_vendor} services (Nearest: {item.nearest_vendor_distance.toFixed(2)} km)
                </p>
              </div>
            </li>
          ))}
        </ul>
        {solution.nonessential_vendors.length > 5 && (
          <button 
            className="w-full mt-4 text-sm text-purple-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
            onClick={() => toggleModal(solution.nonessential_vendors, 'Support Services')}
          >
            <span>View all {solution.nonessential_vendors.length} services</span>
            <svg className="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  </div>

  {/* Bottom Cards */}
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    {/* Government Incentives */}
    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-green-50 to-white">
        <div className="flex items-center">
          <div className="bg-green-100 p-2 rounded-lg mr-3">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2zM10 8.5a.5.5 0 11-1 0 .5.5 0 011 0zm5 5a.5.5 0 11-1 0 .5.5 0 011 0z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-800">Government Incentives</h4>
        </div>
        <span className="bg-green-100 text-green-800 text-xs px-3 py-1 rounded-full font-medium">
          {solution.incentives.length} Available
        </span>
      </div>
      <div className="p-4">
        <ul className="space-y-2">
          {solution.incentives.slice(0, 5).map((item, index) => (
            <li key={index} className="flex items-start">
              <div className="bg-gray-100 p-1 rounded-full mr-3 mt-0.5">
                <svg className="w-3 h-3 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-800">{item.incentive_name}</p>
                <p className="text-xs text-gray-500">{item.incentive_type}</p>
              </div>
            </li>
          ))}
        </ul>
        {solution.incentives.length > 5 && (
          <button 
            className="w-full mt-4 text-sm text-green-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
            onClick={() => toggleModal(solution.incentives, 'Government Incentives')}
          >
            <span>View all {solution.incentives.length} incentives</span>
            <svg className="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>

    {/* Required Approvals */}
    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-orange-50 to-white">
        <div className="flex items-center">
          <div className="bg-orange-100 p-2 rounded-lg mr-3">
            <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-800">Required Approvals</h4>
        </div>
        <span className="bg-orange-100 text-orange-800 text-xs px-3 py-1 rounded-full font-medium">
          {solution.approvals.length} Needed
        </span>
      </div>
      <div className="p-4">
        <ul className="space-y-3">
          {solution.approvals.slice(0, 5).map((item, index) => (
            <li key={index} className="flex items-start">
              <div className="bg-gray-100 p-1 rounded-full mr-3">
                <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-800">{item.approval_name}</p>
                <p className="text-xs text-gray-500">{item.government_department}</p>
              </div>
            </li>
          ))}
        </ul>
        {solution.approvals.length > 5 && (
          <button 
            className="w-full mt-4 text-sm text-orange-600 font-medium hover:underline inline-flex items-center justify-center py-2 border-t border-gray-100"
            onClick={() => toggleModal(solution.approvals, 'Required Approvals')}
          >
            <span>View all {solution.approvals.length} approvals</span>
            <svg className="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  </div>
</div>