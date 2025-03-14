import React, { useEffect, useState } from "react";
import Details from "../Details/Details";
import Backtochat from "../Backtochat/Backtochat";
import { FaSearch } from "react-icons/fa";

function Incentiveresult({ result }) {
  const [selectedIncentive, setSelectedIncentive] = useState(null);
  const [filtered, setFiltered] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  let Analytics_response = {};
  try {
    Analytics_response = result?.Analytics_response || "{}";
  } catch (error) {
    console.error("Error parsing Analytics_response:", error);
  }

  const hasFilteredData = !!Analytics_response["Filtered Incentive Data"];
  const dataKey = hasFilteredData && filtered ? "Filtered Incentive Data" : "Unfiltered Incentive Data";

  let parsedData = {};
  try {
    parsedData = JSON.parse(Analytics_response[dataKey] || "{}");
  } catch (error) {
    console.error(`Error parsing ${dataKey}:`, error);
  }

  const incentives = parsedData["Incentive ID"]
    ? Object.keys(parsedData["Incentive ID"]).map((id) => ({
        id,
        name: parsedData["Incentive ID"]?.[id] || "Unnamed Incentive",
        type: parsedData["Incentive Type"]?.[id] || "N/A",
        rank: parsedData["Incentive Rank"]?.[id] || "N/A",
        details: parsedData["Incentive Details"]?.[id] || "N/A",
        startDate: parsedData["Incentive Start Date"]?.[id]
          ? new Date(parsedData["Incentive Start Date"][id]).toLocaleDateString()
          : "N/A",
        endDate: parsedData["Incentive End Date"]?.[id]
          ? new Date(parsedData["Incentive End Date"][id]).toLocaleDateString()
          : "N/A",
        level: parsedData["Incentive Level"]?.[id]
          ? JSON.parse(parsedData["Incentive Level"][id])
          : "N/A",
      })).sort((a, b) => b.rank - a.rank)
    : [];

  const filteredIncentives = incentives.filter((incentive) =>
    incentive.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    setSelectedIncentive(null);
  }, [filtered]);

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
      <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        <div className="top-header flex items-center justify-between pb-1">
          <div className="title w-full p-1 h-[10%] flex-1">
            <div className="text-5xl">Incentives</div>
          </div>
          <Backtochat />
        </div>

        <div className="p-3 h-[90%] overflow-auto">
          <div className="bg-white shadow p-4 flex justify-between items-center my-4 rounded-lg">
            <div className="flex space-x-2">
              {hasFilteredData && (
                <button
                  className={`px-4 py-2 rounded ${
                    filtered ? "bg-blue-500 text-white" : "bg-gray-300 text-gray-700"
                  }`}
                  onClick={() => setFiltered(true)}
                >
                  Show Filtered Data
                </button>
              )}
              <button
                className={`px-4 py-2 rounded ${
                  filtered ? "bg-gray-300 text-gray-700" : "bg-blue-500 text-white"
                }`}
                onClick={() => setFiltered(false)}
              >
                Show Unfiltered Data
              </button>
            </div>
            <div className="relative">
              <input
                type="text"
                placeholder="Search incentives..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-2 border rounded-lg pl-10"
              />
              <FaSearch className="absolute left-3 top-3 text-gray-500" />
            </div>
          </div>

          <div className="flex h-[80%] overflow-y-auto bg-white shadow rounded-lg p-4">
            <div className="w-2/3">
              {filteredIncentives.length > 0 ? (
                filteredIncentives.map((incentive) => (
                  <div
                    key={incentive.id}
                    className={`p-4 border cursor-pointer shadow-sm ${
                      selectedIncentive?.id === incentive.id
                        ? "bg-[#242f6a] border-gray-400 text-white"
                        : "bg-white border-gray-300"
                    }`}
                    onClick={() => setSelectedIncentive(incentive)}
                  >
                    <span className="font-semibold">{incentive.name}</span>
                  </div>
                ))
              ) : hasFilteredData ? (
                <p className="text-gray-500">No incentives found.</p>
              ) : (
                incentives.length === 0 && <p className="text-gray-500">No incentives found.</p>
              )}
            </div>

            {selectedIncentive && (
              <div className="w-1/3 bg-[#242f6a] shadow p-4 text-white sticky top-0">
                <h2 className="text-xl font-bold">{selectedIncentive.name}</h2>
                <p className="mt-2 text-sm"><strong>Type:</strong> {selectedIncentive.type}</p>
                <p className="mt-2 text-sm"><strong>Rank:</strong> {selectedIncentive.rank}</p>
                <p className="mt-2 text-sm"><strong>Details:</strong> {selectedIncentive.details}</p>
                <p className="mt-2 text-sm"><strong>Start Date:</strong> {selectedIncentive.startDate}</p>
                <p className="mt-2 text-sm"><strong>End Date:</strong> {selectedIncentive.endDate}</p>
                <p className="mt-2 text-sm"><strong>Level:</strong> {selectedIncentive.level}</p>
              </div>
            )}
          </div>
        </div>
      </div>
      <Details />
    </div>
  );
}

export default Incentiveresult;
