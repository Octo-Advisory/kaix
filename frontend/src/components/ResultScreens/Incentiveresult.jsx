import React, { useEffect, useState } from "react";
import Details from "../Details/Details";
import Backtochat from "../Backtochat/Backtochat";
import { FaSearch } from "react-icons/fa";
import DOMPurify from 'dompurify';

function Incentiveresult({ result }) {
// function Incentiveresult() {
  console.log("result in incentives", result);
  const Analytics_response = result["Analytics_response"];
  const [selectedIncentive, setSelectedIncentive] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const processIncentives = (data) => {
    return data["Incentive ID"]
      ? Object.keys(data["Incentive ID"]).map((id) => ({
          id,
          name: data["Incentive ID"]?.[id] || "Unnamed Incentive",
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

  console.log("analytocs res",Analytics_response);
  const incentive_data = JSON.parse(Analytics_response["Incentive Data"])

  const incentives = processIncentives(incentive_data).sort(
    (a, b) => b.aggregated_score - a.aggregated_score
  );

  // 🔹 Search only by name or type
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



  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
      <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        <div className="top-header flex items-center justify-between pb-1">
          <div className="title w-full p-1 h-[10%] flex-1">
            <div className="text-5xl">Incentives</div>
          </div>
          <Backtochat />
        </div>

        <div className="h-[95%]">
          {/* Search Bar */}
          <div className="bg-white shadow p-4 flex items-center my-4 rounded-lg">
            <div className="relative w-full">
              <input
                type="text"
                placeholder="Search incentives by name or type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-2 border rounded-lg pl-10 w-full"
              />
              <FaSearch className="absolute left-3 top-3 text-gray-500" />
            </div>
          </div>

          {/* Incentive List and Details */}
          <div className="flex h-[81%] overflow-y-auto bg-white shadow">
            {/* Incentive List */}
            <div className="w-2/3">
              {displayedIncentives.length > 0 ? (
                displayedIncentives.map((incentive) => (
                  <div
                    key={incentive.id}
                    className={`p-4 border cursor-pointer shadow-sm ${
                      selectedIncentive?.id === incentive.id
                        ? "bg-[#242f6a] border-gray-400 text-white border-none"
                        : "bg-white border-gray-300"
                    }`}
                    onClick={() => setSelectedIncentive(incentive)}
                  >
                    <span className="font-semibold">{incentive.name}</span>
                  </div>
                ))
              ) : (
                <p className="text-gray-500">No incentives found.</p>
              )}
            </div>

            {/* Incentive Details */}
            {selectedIncentive && (
              <div className="w-1/3 bg-[#242f6a] shadow p-4 text-white sticky top-0 h-[70vh] overflow-y-auto">
                <h2 className="text-xl font-bold">{selectedIncentive.name}</h2>
                <p className="mt-2 text-sm"><strong>Type:</strong> {selectedIncentive.type}</p>
                <p className="mt-2 text-sm"><strong>Rank:</strong> {selectedIncentive.rank}</p>
                <p className="mt-2 text-sm"><strong>Score:</strong> {selectedIncentive.aggregated_score.toFixed(4)}</p>
                <p className="mt-2 text-sm"><strong>Details:</strong> {selectedIncentive.details}</p>
                <p className="mt-2 text-sm"><strong>Start Date:</strong> {selectedIncentive.startDate}</p>
                <p className="mt-2 text-sm"><strong>End Date:</strong> {selectedIncentive.endDate}</p>
                <p className="mt-2 text-sm"><strong>Level:</strong> {selectedIncentive.level}</p>
                <p className="mt-2 text-sm">
                  <strong>Description:</strong>{" "}
                  <span
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(selectedIncentive.description),
                    }}
                  />
                </p>
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
