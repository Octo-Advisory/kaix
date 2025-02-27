import React,{useState} from 'react'
import { FaList, FaStar, FaAward } from "react-icons/fa";

function Vendorresult({ result }) {
  const [viewMode, setViewMode] = useState("all");
  console.log("result from vendor", result);
  const analytics_response = result["Analytics_response"]
  console.log("Analytics_response", analytics_response);

  const best_vendors = JSON.parse(analytics_response["final"])
  const better_vendors = JSON.parse(analytics_response["better"])
  const all_vendors = JSON.parse(analytics_response["all"])
  console.log("best", best_vendors);
  console.log("better", better_vendors);
  console.log("all", all_vendors);

  const best_json = [];
  const better_json = [];
  const all_json = []

  Object.keys(best_vendors["supply_score"]).forEach(index => {
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

  Object.keys(all_vendors["Final_Score_With_Features"]).forEach(index => {
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
            {/* Title Section */}
            <div className="title w-full p-1 h-[10%]">
              <div className="text-5xl text-center it">Supply & Vendors</div>
            </div>
            {/* Buttons */}
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
            {/* Vendors data */}
            <div className="py-5 h-[80%]">
              <div className="overflow-auto h-full">
              <table className="w-full">
                  <thead>
                    <tr>
                      <th className="p-3 border">Supply</th>
                      <th className="p-3 border">Final Score</th>
                      <th className="p-3 border">Vendor Name</th>
                      <th className="p-3 border">Vendor Supply Capacity</th>
                      <th className="p-3 border">Distance(Km)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedData.map((val, index) => {
                      return (<tr key={index} className="border text-center hover:bg-gray-100">
                        <td className="p-3 border">{val.supply_id}</td>
                        <td className="p-3 border">{val.supply_score ? val.supply_score.toFixed(2) : "NA"}</td>
                        <td className="p-3 border">{val.vendor_id}</td>
                        <td className="p-3 border">{val.vendor_supply_capacity}</td>
                        <td className="p-3 border">{val.Distance ? val.Distance.toFixed(2) : "NA"}</td>
                      </tr>)
                    })}
                  </tbody>
                </table>
              </div>
                
            </div>
          </div>
        </div>
  )
}

export default Vendorresult
