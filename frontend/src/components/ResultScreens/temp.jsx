import React, { useEffect, useState } from "react";
import { FaSearch, FaCalendarAlt, FaInfoCircle, FaCheckCircle, FaAward, FaIndustry, FaBuilding, FaChartLine, FaFileAlt } from "react-icons/fa";
import DOMPurify from "dompurify";
import '../src/App.css'

export default function IncentiveList() {  
  const [selectedIncentive, setSelectedIncentive] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const processIncentives = (data) => {
    return data["Incentive ID"]
      ? Object.keys(data["Incentive ID"]).map((id) => ({
          id,
          name: data["Incentive ID"]?.[id] || "Unnamed Incentive",
          name1: data["Incentive Name"]?.[id],
          type: data["Incentive Type"]?.[id] || "N/A",
          rank: data["Incentive Rank"]?.[id] || "N/A",
          aggregated_score: data["aggregated_score"]?.[id] || 0,
          details: data["Incentive Details"]?.[id] || "N/A",
          startDate: data["Incentive Start Date"]?.[id]
            ? new Date(data["Incentive Start Date"][id]).toLocaleDateString()
            : "N/A",
          endDate: data["Incentive End Date"]?.[id]
            ? new Date(data["Incentive End Date"][id]).toLocaleDateString()
            : "N/A",
          level: data["Level"]?.[id] || "N/A",
          description: data["description"]?.[id] || "No description available",
        }))
      : [];
  };

  const incentive_data = JSON.parse(Analytics_response["Incentive Data"]);
  const incentives = processIncentives(incentive_data).sort(
    (a, b) => b.aggregated_score - a.aggregated_score
  );

  const displayedIncentives = incentives.filter(
    (incentive) =>
      incentive.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incentive.type?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    if (searchQuery === "") {
      setSelectedIncentive(incentives.length > 0 ? incentives[0] : null);
    } else {
      setSelectedIncentive(
        displayedIncentives.length > 0 ? displayedIncentives[0] : null
      );
    }
  }, [searchQuery]);

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-gray-50 overflow-hidden">
      <div className="w-[95%] h-[95%] mx-auto my-0 p-6 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 mb-4">
          <div className="flex items-center">
            <div className="p-3 mr-4 bg-blue-50 rounded-lg">
              <FaIndustry className="text-xl text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-gray-800">Incentives Catalog</h1>
              <p className="text-gray-500">Browse available incentive programs</p>
            </div>
          </div>
        </div>
  
        {/* Search Bar */}
        <div className="relative mb-4">
          <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by program name or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-12 pr-4 py-3 w-full border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 placeholder-gray-400 text-gray-700"
          />
        </div>
  
        {/* Main Content Area */}
        <div className="flex flex-1 min-h-0 overflow-hidden bg-white rounded-lg border border-gray-200">
          {/* Incentive List - Scrollable */}
          <div className="w-1/3 border-r border-gray-200 flex flex-col">
            <div className="overflow-y-auto flex-1">
              {displayedIncentives.length > 0 ? (
                <div className="space-y-2 p-2">
                  {displayedIncentives.map((incentive) => (
                    <div
                      key={incentive.id}
                      className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${
                        selectedIncentive?.id === incentive.id
                          ? "bg-blue-50 border-l-4 border-blue-500"
                          : "hover:bg-gray-50 border-l-4 border-transparent"
                      }`}
                      onClick={() => setSelectedIncentive(incentive)}
                    >
                      <div className="flex justify-between items-start">
                        <h3 className={`font-medium ${
                          selectedIncentive?.id === incentive.id ? "text-blue-700" : "text-gray-700"
                        }`}>
                          {incentive.type}
                        </h3>
                        {/* {selectedIncentive?.id === incentive.id && (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                            Selected
                          </span>
                        )} */}
                      </div>
                      {/* <div className="flex items-center mt-2 text-sm text-gray-500">
                        <FaBuilding className="mr-2" />
                        <span>{incentive.level}</span>
                      </div> */}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                  <FaSearch className="text-gray-300 text-3xl mb-3" />
                  <h3 className="text-lg font-medium text-gray-500">No programs found</h3>
                  <p className="text-gray-400">Try a different search term</p>
                </div>
              )}
            </div>
          </div>
  
          {/* Detailed View - Scrollable Content */}
          {selectedIncentive && (
            <div className="w-2/3 flex flex-col">
              <div className="overflow-y-auto flex-1 p-6">
                <div className="mb-8">
                  <div className="flex items-center mb-2">
                    <div className="p-2 mr-3 bg-blue-100 rounded-lg">
                      <FaChartLine className="text-blue-600" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-800">{selectedIncentive.name1}</h2>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full">
                      {selectedIncentive.type}
                    </span>
                    <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                      {selectedIncentive.level}
                    </span>
                  </div>
                </div>

                
  
                {/* Key Dates */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex items-center">
                      <FaCalendarAlt className="mr-3 text-gray-500" />
                      <div>
                        <div className="text-sm text-gray-500 mb-1">Start Date</div>
                        <div className="font-medium text-gray-700">{selectedIncentive.startDate}</div>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex items-center">
                      <FaCalendarAlt className="mr-3 text-gray-500" />
                      <div>
                        <div className="text-sm text-gray-500 mb-1">End Date</div>
                        <div className="font-medium text-gray-700">{selectedIncentive.endDate}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Additional Details Section */}
                {selectedIncentive.details !== "N/A" && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                      <FaFileAlt className="mr-2 text-blue-500" />
                      Additional Details
                    </h3>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                      <div
                        className="prose text-gray-700 max-w-none"
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(selectedIncentive.details),
                        }}
                      />
                    </div>
                  </div>
                )}
  
                {/* Program Description */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <FaInfoCircle className="mr-2 text-blue-500" />
                    Program Details
                  </h3>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <div
                      className="prose text-gray-700 max-w-none"
                      dangerouslySetInnerHTML={{
                        __html: DOMPurify.sanitize(selectedIncentive.description),
                      }}
                    />
                  </div>
                </div>

                
  
                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                      <FaCheckCircle className="mr-2 text-green-500" />
                      Eligibility Criteria
                    </h3>
                    <ul className="space-y-2">
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Registered business entity</span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Minimum 2 years in operation</span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Annual revenue over $100k</span>
                      </li>
                    </ul>
                  </div>
  
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                      <FaAward className="mr-2 text-yellow-500" />
                      Key Benefits
                    </h3>
                    <ul className="space-y-2">
                      <li className="flex items-start">
                        <span className="text-yellow-500 mr-2">★</span>
                        <span className="text-gray-700">Tax credit opportunities</span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-yellow-500 mr-2">★</span>
                        <span className="text-gray-700">Equipment and technology grants</span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-yellow-500 mr-2">★</span>
                        <span className="text-gray-700">Energy efficiency rebates</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
              
              {/* Fixed Footer with CTA */}
              {/* <div className="p-4 border-t border-gray-200 bg-white">
                <button className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition duration-200">
                  Apply for This Program
                </button>
              </div> */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}