import React, { useEffect, useState } from "react";
import { FaIndustry, FaSearch, FaBuilding, FaChartLine, FaCalendarAlt, FaFileAlt, FaInfoCircle, FaTag, FaLayerGroup, FaStar, FaPlayCircle, FaStopCircle, FaArrowRight, FaClock, FaSync, FaCheckCircle, FaRunning, FaAward, } from 'react-icons/fa';
import Details from "../Details/Details";
import Backtochat from "../Backtochat/Backtochat";
import DOMPurify from 'dompurify';
import "../ResultScreens/incentives.css"

function Incentiveresult({ result }) {
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
            'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
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
              category_description: JSON.parse(incentive.category_description) || {}
            });
          }
        }
      }

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
      setSelectedIncentive(incentives.length > 0 ? incentives[0] : null);
    } else {
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
      <div className="flex items-center justify-center h-screen w-full" style={{ backgroundColor: '#ADD8E6' }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#295294] mx-auto"></div>
          <p className="mt-4 text-[#295294]">Loading incentives...</p>
        </div>
      </div>
    );
  }

  const getIconForCategory = (category) => {
    switch (category) {
      case 'Eligibility':
        return <FaCheckCircle className="text-[#90EE90]" />;
      case 'Benefits':
        return <FaAward className="text-[#C71585]" />;
      case 'Process':
        return <FaFileAlt className="text-[#488AC7]" />;
      case 'Requirements':
        return <FaInfoCircle className="text-[#295294]" />;
      default:
        return <FaInfoCircle className="text-[#488AC7]" />;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#E6F0FA] via-[#B8D1F3] to-[#7AA6DA]">
  <div className="w-[95%] h-[95%] mx-auto my-0 p-6 rounded-xl shadow-lg flex flex-col bg-white bg-opacity-95 backdrop-blur-sm border border-white border-opacity-40">
    {/* Header */}
    <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#B8D1F3]">
      <div className="flex items-center">
        <div className="p-3 mr-4 rounded-lg bg-gradient-to-r from-[#FF80AB] to-[#9575CD] text-white">
          <FaIndustry className="text-xl" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-[#2C53A3]">Incentives Catalog</h1>
          <p className="text-[#5A7EC7]">Browse available incentive programs</p>
        </div>
      </div>
      <Backtochat />
    </div>

    {/* Search Bar */}
    <div className="relative mb-6">
      <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#FF80AB]" />
      <input
        type="text"
        placeholder="Search by program name or type..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="pl-12 pr-4 py-3 w-full rounded-lg focus:outline-none focus:ring-2 placeholder-[#9CB3D9] border border-[#B8D1F3] bg-white bg-opacity-90 text-[#2C53A3] focus:ring-[#FF80AB]"
      />
    </div>

    {/* Main Content Area */}
    <div className="flex flex-1 min-h-0 overflow-hidden rounded-lg border border-[#B8D1F3] bg-white bg-opacity-90">
      {/* Incentive List - Scrollable */}
      <div className="w-1/3 border-r border-[#B8D1F3] flex flex-col">
        <div className="overflow-y-auto flex-1 list-view p-2 bg-gradient-to-b from-[#E6F0FA]/20 to-transparent">
          {displayedIncentives.length > 0 ? (
            <div className="space-y-2">
              {displayedIncentives.map((incentive) => (
                <div
                  key={incentive.id}
                  className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${
                    selectedIncentive?.id === incentive.id
                      ? "border-l-4 shadow-sm"
                      : "hover:shadow-xs border-l-4 border-transparent"
                  }`}
                  style={{
                    background: selectedIncentive?.id === incentive.id
                      ? 'linear-gradient(to right, rgba(255, 128, 171, 0.08), rgba(255, 255, 255, 0.9))'
                      : 'transparent',
                    borderLeftColor: selectedIncentive?.id === incentive.id ? '#FF80AB' : 'transparent'
                  }}
                  onClick={() => setSelectedIncentive(incentive)}
                >
                  <div className="flex justify-between items-start">
                    <h3 className={`font-medium ${selectedIncentive?.id === incentive.id ? "text-[#FF80AB]" : "text-[#2C53A3]"}`}>
                      {incentive.type}
                    </h3>
                  </div>
                  <div className="flex items-center mt-2 text-sm text-[#5A7EC7]">
                    <FaBuilding className="mr-2" />
                    <span>{incentive.name}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-6">
              <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB] to-[#9575CD] text-white">
                <FaSearch className="text-2xl" />
              </div>
              <h3 className="text-lg font-medium text-[#2C53A3]">No programs found</h3>
              <p className="text-[#5A7EC7]">Try a different search term</p>
            </div>
          )}
        </div>
      </div>

      {/* Detailed View - Scrollable Content */}
      {selectedIncentive && (
        <div className="w-2/3 flex flex-col">
          <div className="overflow-y-auto flex-1 p-6">
            <div className="mb-8">
              <div className="flex items-center mb-4">
                <div className="p-3 mr-3 rounded-lg bg-gradient-to-r from-[#81C784] to-[#9575CD] text-white">
                  <FaChartLine />
                </div>
                <h2 className="text-2xl font-semibold text-[#2C53A3]">{selectedIncentive.type}</h2>
              </div>

              <div className="flex flex-wrap gap-3 mb-6">
                <span className="px-3 py-1 text-sm rounded-full flex items-center text-white bg-gradient-to-r from-[#B8D1F3] to-[#7AA6DA]">
                  <FaTag className="mr-1" /> {selectedIncentive.name}
                </span>
                <span className="px-3 py-1 text-sm rounded-full flex items-center text-white bg-gradient-to-r from-[#FF80AB] to-[#9575CD]">
                  <FaLayerGroup className="mr-1" /> {selectedIncentive.level}
                </span>
                <span className="px-3 py-1 text-sm rounded-full flex items-center text-white bg-gradient-to-r from-[#81C784] to-[#4CAF50]">
                  <FaStar className="mr-1" /> Score: {selectedIncentive.aggregated_score.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Key Dates - Improved Date Display */}
            <div className="mb-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center text-[#2C53A3]">
                    <FaCalendarAlt className="mr-2 text-[#FF80AB]" />
                    Program Period
                  </h3>
                  <div className="p-4 rounded-lg border border-[#B8D1F3]" style={{
                    background: 'linear-gradient(to right, rgba(184, 209, 243, 0.1), rgba(255, 255, 255, 0.9))'
                  }}>
                    <div className="font-medium flex items-center text-[#2C53A3]">
                      <FaPlayCircle className="mr-2 text-[#81C784]" />
                      {formatDate(selectedIncentive.startDate)}
                      <FaArrowRight className="mx-2 text-[#9575CD]" />
                      <FaStopCircle className="mr-2 text-[#FF80AB]" />
                      {formatDate(selectedIncentive.endDate)}
                    </div>
                    {selectedIncentive.startDate !== "N/A" && selectedIncentive.endDate !== "N/A" && (
                      <div className="text-xs mt-1 flex items-center text-[#5A7EC7]">
                        <FaClock className="mr-1" />
                        Duration: {calculateDuration(selectedIncentive.startDate, selectedIncentive.endDate)}
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center text-[#2C53A3]">
                    <FaFileAlt className="mr-2 text-[#9575CD]" />
                    Program Status
                  </h3>
                  <div className="p-4 rounded-lg border border-[#FF80AB]" style={{
                    background: 'linear-gradient(to right, rgba(255, 128, 171, 0.08), rgba(255, 255, 255, 0.9))'
                  }}>
                    <div className="font-medium flex items-center text-[#2C53A3]">
                      {getProgramStatusIcon(selectedIncentive.startDate, selectedIncentive.endDate)}
                      <span className="ml-2">
                        {getProgramStatus(selectedIncentive.startDate, selectedIncentive.endDate)}
                      </span>
                    </div>
                    <div className="text-xs mt-1 flex items-center text-[#5A7EC7]">
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
                <h3 className="text-lg font-semibold mb-3 flex items-center text-[#2C53A3]">
                  <FaFileAlt className="mr-2 text-[#5A7EC7]" />
                  Additional Details
                </h3>
                <div className="p-4 rounded-lg border border-[#81C784]" style={{
                  background: 'linear-gradient(to right, rgba(129, 199, 132, 0.1), rgba(255, 255, 255, 0.9))'
                }}>
                  <div
                    className="prose max-w-none text-[#2C53A3]"
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(selectedIncentive.details),
                    }}
                  />
                </div>
              </div>
            )}

            {/* Features Grid */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4 flex items-center text-[#2C53A3]">
                <FaInfoCircle className="mr-2 text-[#FF80AB]" />
                Program Details
              </h3>

              {selectedIncentive.category_description && Object.keys(selectedIncentive.category_description).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(selectedIncentive.category_description).map(([key, value]) => (
                    <div key={key} className="p-4 rounded-lg border border-[#9575CD]" style={{
                      background: 'linear-gradient(to right, rgba(149, 117, 205, 0.08), rgba(255, 255, 255, 0.9))'
                    }}>
                      <h3 className="text-lg font-semibold mb-3 flex items-center text-[#2C53A3]">
                        {getIconForCategory(key)}
                        <span className="ml-2">{key}</span>
                      </h3>
                      {Array.isArray(value) ? (
                        <ul className="space-y-2">
                          {value.map((item, index) => (
                            <li key={index} className="flex items-start">
                              <span className="mr-2 text-[#FF80AB]">
                                <FaCheckCircle />
                              </span>
                              <span className="text-[#2C53A3]">{item}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-[#2C53A3]">{value}</div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-lg border border-[#B8D1F3] flex items-center text-[#5A7EC7]" style={{
                  background: 'linear-gradient(to right, rgba(184, 209, 243, 0.1), rgba(255, 255, 255, 0.9))'
                }}>
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