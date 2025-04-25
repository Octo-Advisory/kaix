import React, { useEffect, useState } from "react";
import {
  FaIndustry,
  FaSearch,
  FaBuilding,
  FaChartLine,
  FaCalendarAlt,
  FaFileAlt,
  FaInfoCircle,
  FaTag,
  FaLayerGroup,
  FaStar,
  FaPlayCircle,
  FaStopCircle,
  FaArrowRight,
  FaClock,
  FaSync,
  FaCheckCircle,
  FaRunning,
  FaAward,
} from 'react-icons/fa';
import Details from "../Details/Details";
import Backtochat from "../Backtochat/Backtochat";
import DOMPurify from 'dompurify';
import "../ResultScreens/incentives.css"

function Incentiveresult({result}) {
  console.log("result is", result);

  const [selectedIncentive, setSelectedIncentive] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [incentives, setIncentives] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchIncentivesDetails = async () => {
    try {
      if (!result || !result["Incentive ID"]) {
        setIncentives([]);
        setLoading(false);
        return;
      }

      const incentiveIds = Object.values(result["Incentive ID"]);
      const fetchedIncentives = [];

      for (const [index, id] of incentiveIds.entries()) {
        const filters = JSON.stringify([["name", "=", id]]);
        const fields = JSON.stringify(["*"]);

        const url = `/api/resource/Incentive?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': 'token d3de1e0e4e25846:3d3be60aaa3b67c',
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.data && data.data.length > 0) {
            const incentive = data.data[0];

            fetchedIncentives.push({
              id: incentive.name,
              name: incentive.incentive_name,
              type: incentive.incentive_type || "N/A",
              rank: result["Incentive Rank"]?.[index] ?? "N/A",
              aggregated_score: result["aggregated_score"]?.[index] ?? 0,
              details: incentive.quantum_of_assistance || "N/A",
              startDate: incentive.incentive_operation_start_date || "N/A",
              endDate: incentive.incentive_operation_end_date || "N/A",
              level: result["Level"]?.[index] ?? "N/A",
              // description: incentive.description || "No description available",
              category_description: JSON.parse(incentive.category_description) || {}
            });
          }
        }
      }

      // Sort by aggregated score
      const sortedIncentives = fetchedIncentives.sort(
        (a, b) => b.aggregated_score - a.aggregated_score
      );

      setIncentives(sortedIncentives);
      setSelectedIncentive(sortedIncentives.length > 0 ? sortedIncentives[0] : null);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching incentives:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncentivesDetails();
  }, [result]);

  const displayedIncentives = incentives.filter(
    (incentive) =>
      incentive.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incentive.type?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    if (searchQuery === "") {
      // If no search is applied, select the first incentive from the full list
      setSelectedIncentive(incentives.length > 0 ? incentives[0] : null);
    } else {
      // If search results are available, select the first from the filtered list
      setSelectedIncentive(displayedIncentives.length > 0 ? displayedIncentives[0] : null);
    }
  }, [searchQuery]);

  const formatDate = (dateString) => {
    if (!dateString || dateString === "N/A") return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateDuration = (startDate, endDate) => {
    if (startDate === "N/A" || endDate === "N/A") return "N/A";

    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 30) return `${diffDays} days`;
    if (diffDays < 365) return `${Math.round(diffDays / 30)} months`;
    return `${Math.round(diffDays / 365)} years`;
  };

  const getProgramStatusIcon = (startDate, endDate) => {
    const now = new Date();
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (now < start) return <FaClock className="text-yellow-500 mr-1" />;
    if (now >= start && now <= end) return <FaRunning className="text-green-500 mr-1" />;
    return <FaCheckCircle className="text-gray-500 mr-1" />;
  };

  const getProgramStatus = (startDate, endDate) => {
    if (startDate === "N/A" || endDate === "N/A") return "Status unavailable";

    const today = new Date();
    const start = new Date(startDate);
    const end = new Date(endDate);

    if (today < start) return "Upcoming";
    if (today > end) return "Closed";
    return "Active";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen w-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading incentives...</p>
        </div>
      </div>
    );
  }

  const getIconForCategory = (category) => {
    switch (category) {
      case 'Eligibility':
        return <FaCheckCircle className="text-green-500" />;
      case 'Benefits':
        return <FaAward className="text-yellow-500" />;
      case 'Process':
        return <FaFileAlt className="text-blue-500" />;
      case 'Requirements':
        return <FaInfoCircle className="text-purple-500" />;
      default:
        return <FaInfoCircle className="text-gray-500" />;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9] overflow-hidden">
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
      <Backtochat />
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
        <div className="overflow-y-auto flex-1 list-view">
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
                      {incentive.name}
                    </h3>
                  </div>
                  <div className="flex items-center mt-2 text-sm text-gray-500">
                    <FaBuilding className="mr-2" />
                    <span>{incentive.type}</span>
                  </div>
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
                <h2 className="text-2xl font-semibold text-gray-800">{selectedIncentive.name}</h2>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full flex items-center">
                  <FaTag className="mr-1" /> {selectedIncentive.type}
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full flex items-center">
                  <FaLayerGroup className="mr-1" /> {selectedIncentive.level}
                </span>
                <span className="px-3 py-1 bg-green-50 text-green-700 text-sm rounded-full flex items-center">
                  <FaStar className="mr-1" /> Score: {selectedIncentive.aggregated_score.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Key Dates - Improved Date Display */}
            <div className="mb-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <FaCalendarAlt className="mr-2 text-blue-500" />
                    Program Period
                  </h3>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="font-medium text-gray-700 flex items-center">
                      <FaPlayCircle className="mr-2 text-green-500" />
                      {formatDate(selectedIncentive.startDate)} 
                      <FaArrowRight className="mx-2 text-gray-400" />
                      <FaStopCircle className="mr-2 text-red-500" />
                      {formatDate(selectedIncentive.endDate)}
                    </div>
                    {selectedIncentive.startDate !== "N/A" && selectedIncentive.endDate !== "N/A" && (
                      <div className="text-xs text-gray-400 mt-1 flex items-center">
                        <FaClock className="mr-1" />
                        Duration: {calculateDuration(selectedIncentive.startDate, selectedIncentive.endDate)}
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <FaFileAlt className="mr-2 text-blue-500" />
                    Program Status
                  </h3>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="font-medium text-gray-700 flex items-center">
                      {getProgramStatusIcon(selectedIncentive.startDate, selectedIncentive.endDate)}
                      <span className="ml-2">
                        {getProgramStatus(selectedIncentive.startDate, selectedIncentive.endDate)}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1 flex items-center">
                      <FaSync className="mr-1" />
                      Last updated: {formatDate(new Date().toISOString())}
                    </div>
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

            {/* Features Grid */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <FaInfoCircle className="mr-2 text-blue-500" />
                Program Details
              </h3>

              {selectedIncentive.category_description && Object.keys(selectedIncentive.category_description).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(selectedIncentive.category_description).map(([key, value]) => (
                    <div key={key} className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                      <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                        {getIconForCategory(key)}
                        <span className="ml-2">{key}</span>
                      </h3>
                      {Array.isArray(value) ? (
                        <ul className="space-y-2">
                          {value.map((item, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-blue-500 mr-2">
                                <FaCheckCircle />
                              </span>
                              <span className="text-gray-700">{item}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-gray-700">{value}</div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-100 text-gray-500 flex items-center">
                  <FaInfoCircle className="mr-2" />
                  No additional details available
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  </div>
  <Details />
</div>
  );
}

export default Incentiveresult;