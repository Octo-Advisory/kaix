import React, { useState, useContext } from "react";
import { FrappeContext } from "frappe-react-sdk";
import { FaList, FaStar, FaAward } from "react-icons/fa";

function ChatScreen() {
  const [viewMode, setViewMode] = useState("all");
  const analytics_response = {
    final: {
      supply_id: { 0: "Boxes", 1: "Packaging Materials" },
      supply_score: { 0: 6.8412660905, 1: 6.4206700697 },
      vendor_id: {
        0: "MS Paper and Engineering Works",
        1: "Kirti Paper Bag Sales Agency",
      },
      vendor_supply_capacity: { 0: 5000.0, 1: 10000.0 },
      Distance: { 0: 6.09, 1: 2.18 },
    },
    better: {
      supply_id: { 10: "Boxes", 7: "Packaging Materials" },
      supply_score: { 10: 6.5, 7: 6.2 },
      vendor_id: {
        10: "Swiss Pac Pvt Ltd",
        7: "Expert Kraft",
      },
      vendor_supply_capacity: { 10: 8000.0, 7: 9000.0 },
      Distance: { 10: 4.5, 7: 3.1 },
    },
    all: {
      supply_id: {
        10: "Boxes",
        17: "Boxes",
        11: "Boxes",
        0: "Boxes",
        14: "Boxes",
        5: "Boxes",
        1: "Boxes",
        8: "Boxes",
        7: "Packaging Materials",
        12: "Packaging Materials",
        13: "Packaging Materials",
        15: "Packaging Materials",
        20: "Packaging Materials",
        21: "Packaging Materials",
        22: "Packaging Materials",
        23: "Packaging Materials",
        24: "Packaging Materials",
        25: "Packaging Materials",
        26: "Packaging Materials",
        27: "Packaging Materials",
        28: "Packaging Materials",
      },
      Final_Score_With_Features: {
        10: 6.84,
        17: 6.33,
        11: 6.30,
        0: 6.07,
        14: 5.76,
        5: 5.72,
        1: 5.38,
        8: 3.77,
        7: 6.42,
        12: 6.39,
        13: 6.39,
        15: 6.39,
        20: 6.39,
        21: 6.39,
        22: 6.39,
        23: 6.39,
        24: 6.39,
        25: 6.39,
        26: 6.39,
        27: 6.39,
        28: 6.39,
      },
      vendor_id: {
        10: "MS Paper and Engineering Works",
        17: "Swiss Pac Pvt Ltd",
        11: "Nagdev Plastic Industries",
        0: "A1 Enterprise",
        14: "RSTRADERS",
        5: "Himja Vacuum Packaging",
        1: "Aaaka Plastics",
        8: "Krishna Plastic and Packaging Industries",
        7: "Kirti Paper Bag Sales Agency",
        12: "Nagdev Plastic Industries",
        13: "Nagdev Plastic Industries",
        15: "Nagdev Plastic Industries",
        20: "Nagdev Plastic Industries",
        21: "Nagdev Plastic Industries",
        22: "Nagdev Plastic Industries",
        23: "Nagdev Plastic Industries",
        24: "Nagdev Plastic Industries",
        25: "Nagdev Plastic Industries",
        26: "Nagdev Plastic Industries",
        27: "Nagdev Plastic Industries",
        28: "Nagdev Plastic Industries",
      },
      vendor_supply_capacity: {
        10: 5000.0,
        17: 5000.0,
        11: 5000.0,
        0: 100000.0,
        14: 5000.0,
        5: 5000.0,
        1: 5000.0,
        8: 5000.0,
        7: 10000.0,
        12: 10000.0,
        13: 10000.0,
        15: 10000.0,
        20: 10000.0,
        21: 10000.0,
        22: 10000.0,
        23: 10000.0,
        24: 10000.0,
        25: 10000.0,
        26: 10000.0,
        27: 10000.0,
        28: 10000.0,
      },
      Dist: {
        10: 6.09,
        17: 15.46,
        11: 5.53,
        0: 3.79,
        14: 1.94,
        5: 3.49,
        1: 2.68,
        8: 101.47,
        7: 2.17,
        12: 5.53,
        13: 5.53,
        15: 5.53,
        20: 5.53,
        21: 5.53,
        22: 5.53,
        23: 5.53,
        24: 5.53,
        25: 5.53,
        26: 5.53,
        27: 5.53,
        28: 5.53,
      },
    },
  };

  const best_vendors = analytics_response["final"]
  const better_vendors = analytics_response["better"]
  const all_vendors = analytics_response["all"]
  console.log("best", best_vendors);
  console.log("better", better_vendors);
  console.log("all", all_vendors);

  const best_json = [];
  const better_json = [];
  const all_json = []

  Object.keys(best_vendors["supply_id"]).forEach(index => {
    best_json.push({
      "supply_id": best_vendors["supply_id"][index],
      "supply_score": best_vendors["supply_score"][index],
      "vendor_id": best_vendors["vendor_id"][index],
      "vendor_supply_capacity": best_vendors["vendor_supply_capacity"][index],
      "Distance": best_vendors["Distance"][index]
    });
  });

  // Object.keys(better_vendors["supply_id"]).forEach(index => {
  //   better_json.push({
  //     "supply_id": best_vendors["supply_id"][index],
  //     "supply_score": best_vendors["supply_score"][index],
  //     "vendor_id": best_vendors["vendor_id"][index],
  //     "vendor_supply_capacity": best_vendors["vendor_supply_capacity"][index],
  //     "Distance": best_vendors["Distance"][index]
  //   });
  // });

  Object.keys(all_vendors["supply_id"]).forEach(index => {
    all_json.push({
      "supply_id": all_vendors["supply_id"][index],
      "vendor_id": all_vendors["vendor_id"][index],
      "vendor_supply_capacity": all_vendors["vendor_supply_capacity"][index],
      "Distance": all_vendors["Dist"][index],
      "supply_score": all_vendors["Final_Score_With_Features"][index]
    })
  })

  const displayedData = viewMode === "best" ? best_json : viewMode === "better" ? better_json : all_json;

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
      <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        <div className="title w-full p-1 h-[10%]">
          <div className="text-5xl text-center it">Supply & Vendors</div>
        </div>

        <div className="select-sections py-2 h-[10%]">
          <div className="flex items-center gap-2">
            <button className="cursor-pointer bg-gradient-to-r from-green-400 to-green-600 text-white inline-flex items-center gap-2 rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 hover:from-green-500 hover:to-green-700 h-9 px-3" onClick={() => setViewMode("all")}>
              <FaList size={22} />
              All Vendors
            </button>

            <button className="cursor-pointer bg-gradient-to-r from-yellow-400 to-yellow-600 text-white inline-flex items-center gap-2 rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 hover:from-yellow-500 hover:to-yellow-700 h-9 px-3" onClick={() => setViewMode("better")}>
              <FaStar size={22} />
              Better Vendors
            </button>

            <button className="cursor-pointer bg-gradient-to-r from-red-400 to-red-600 text-white inline-flex items-center gap-2 rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 hover:from-red-500 hover:to-red-700 h-9 px-3" onClick={() => setViewMode("best")}>
              <FaAward size={22} />
              Best Vendors
            </button>
          </div>
        </div>

        <div className="venodr-listing py-5 h-[80%]">
          <div className="overflow-auto h-full">
          <table className="w-full">
              <thead>
                <tr>
                  <th className="p-3 border">Supply ID</th>
                  <th className="p-3 border">Final Score</th>
                  <th className="p-3 border">Vendor ID</th>
                  <th className="p-3 border">Vendor Supply Capacity</th>
                  <th className="p-3 border">Distance(Km)</th>
                </tr>
              </thead>
              <tbody>
                {displayedData.map((val, index) => {
                  return (<tr key={index} className="border text-center hover:bg-gray-100">
                    <td className="p-3 border">{val.supply_id}</td>
                    <td className="p-3 border">{val.supply_score.toFixed(2)}</td>
                    <td className="p-3 border">{val.vendor_id}</td>
                    <td className="p-3 border">{val.vendor_supply_capacity}</td>
                    <td className="p-3 border">{val.Distance.toFixed(2)}</td>
                  </tr>)
                })}
              </tbody>
            </table>
          </div>
            
        </div>
      </div>
    </div>
  );
}

export default ChatScreen;