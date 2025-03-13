import React, { useState } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import Details from '../Details/Details';

function Approvalresult({ result }) {
    const [viewMode, setViewMode] = useState("Pre-Operation");
    const Analytics_response = result["Analytics_response"];
    const approval_data = JSON.parse(Analytics_response["Approval Data"]);
    const approval_name = approval_data["Approval Name"];
    const stages = approval_data["Stages"];

    const total_effective_time = Analytics_response["Total Effective Time"];
    const online_percentage = Analytics_response["Online Percentage"];

    const items = Object.keys(approval_name).map(key => ({
        approvalName: approval_name[key],
        stage: stages[key]
    }));

    const finalData = items.reduce((acc, item) => {
        if (!acc[item.stage]) {
            acc[item.stage] = [];
        }
        acc[item.stage].push(item.approvalName);
        return acc;
    }, {});

    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
            <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
                <div className="top-header flex items-center justify-between">
                    <div className="title w-full p-1 h-[10%] flex-1">
                        <div className="text-5xl">Approvals</div>
                    </div>
                    <Backtochat />
                </div>

                <div className="select-sections py-2 h-[10%] flex items-center justify-between w-full">
                    <div className="flex gap-2">
                        {["Pre-Operation", "Pre-Establishment", "Pre-Requisite", "Others"].map(mode => (
                            <button
                                key={mode}
                                className={`bg-gradient-to-r text-white px-3 py-2 rounded-md 
                                ${viewMode === mode ? "from-green-400 to-green-600" : "from-gray-400 to-gray-600"}`}
                                onClick={() => setViewMode(mode)}
                            >
                                {mode}
                            </button>
                        ))}
                    </div>
                    <div className="flex gap-4 text-gray-700 text-lg">
                        <span><strong>Total Effective Time:</strong> {total_effective_time} Days</span>
                        <span><strong>Online Percentage:</strong> {online_percentage}%</span>
                    </div>
                </div>

                <div className="h-[80%] overflow-auto">
                    <table className="w-full border border-gray-300 rounded-lg shadow-md">
                        <thead className="bg-gray-200 text-black sticky top-0 z-10 shadow-md border-b-2 border-gray-300">
                            <tr>
                                <th className="p-2 border border-gray-300 text-2xl">Approval Name</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white">
                            {finalData[viewMode] && finalData[viewMode].length > 0 ? (
                                finalData[viewMode].map((item, index) => (
                                    <tr key={index} className="border border-gray-300 hover:bg-gray-100">
                                        <td className="p-3 border border-gray-300">{item}</td>
                                    </tr>
                                ))
                            ) : (
                                <tr className="border border-gray-300 hover:bg-gray-100">
                                    <td className="p-3 border border-gray-300" colSpan="100%">No Approvals Available</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
            <Details />
        </div>
    );
}

export default Approvalresult;
