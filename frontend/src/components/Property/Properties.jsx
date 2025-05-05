import React, { useState } from "react";
import Property from "./Property";
import "../ResultScreens/Industryresult.css";

function Properties({ solutions, toggleModal }) {
    console.log("properites",solutions)
    const [activeTab, setActiveTab] = useState(0);

    return (
        <div className="w-full h-full">
            {solutions.length > 0 && (
                <div className="tabs-container flex w-full rounded-t-lg gap-1">
                    {solutions.map((_, index) => (
                        <button
                            key={index}
                            className={`tab-item p-3 text-lg font-medium cursor-pointer border border-gray-300 rounded-t-lg transition-all 
                            ${activeTab === index ? "bg-[#f8f9fa] text-blue-900 border-b-0" : "bg-white text-gray-700 hover:bg-[#e9ffee]"}`}
                            onClick={() => setActiveTab(index)}
                        >
                            Option {index + 1}
                        </button>
                    ))}
                </div>
            )}

            <div className="bg-white rounded-lg shadow-lg rounded-tl-none h-[95%] overflow-auto">
                {solutions.length > 0 && <Property solution={solutions[activeTab]} toggleModal={toggleModal} />}
            </div>
        </div>
    );
}

export default Properties;