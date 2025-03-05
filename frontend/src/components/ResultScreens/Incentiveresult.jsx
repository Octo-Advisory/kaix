import React from 'react';
import { useNavigate } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";
import Details from '../Details/Details';
import Backtochat from '../Backtochat/Backtochat';

function Incentiveresult({ result }) {
    console.log("Result from incentive:", result);
    const navigate = useNavigate();
    // Safely parse JSON and handle errors
    let Analytics_response;
    try {
        Analytics_response = JSON.parse(result?.Analytics_response || '{}');
    } catch (error) {
        console.error("Error parsing Analytics_response:", error);
        Analytics_response = {};
    }

    // Extract incentives and types with fallback values
    const incentives = Object.values(Analytics_response["Incentive Name"] || {});
    const incentive_types = Object.values(Analytics_response["Incentive Type"] || {});

    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
            <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
                {/* Title Section */}
                <div className="top-header flex items-center justify-between">
                                    <div className="title w-full p-1 h-[10%] flex-1">
                                        <div className="text-5xl">Incentives</div>
                                    </div>
                                    <Backtochat/>
                                </div>
                
                {/* Incentive Data */}
                <div className="py-3 h-[90%] overflow-auto">
                    <div className="h-full overflow-auto border border-gray-300 rounded-lg">
                        <table className="w-full border-collapse">
                            <thead className="sticky top-0 bg-[#19a282] text-white">
                                <tr>
                                    <th className="p-4 text-lg font-semibold border border-gray-300">No.</th>
                                    <th className="p-4 text-lg font-semibold border border-gray-300">Incentive Name</th>
                                    <th className="p-4 text-lg font-semibold border border-gray-300">Incentive Type</th>
                                </tr>
                            </thead>
                            <tbody>
                                {incentives.length > 0 ? (
                                    incentives.map((incentive, index) => (
                                        <tr key={index} className="hover:bg-[#19a282]/20 transition-all">
                                            <td className="p-4 text-gray-800 border border-gray-300">{index + 1}</td>
                                            <td className="p-4 text-gray-800 border border-gray-300">{incentive}</td>
                                            <td className="p-4 text-gray-800 border border-gray-300">{incentive_types[index]}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="3" className="p-4 text-center text-gray-500 border border-gray-300">
                                            No incentives found
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>  
                </div>
            </div>
            <Details/>
        </div>
    );
}

export default Incentiveresult;
