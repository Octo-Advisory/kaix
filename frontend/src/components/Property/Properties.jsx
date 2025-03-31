import React, { useState } from "react";
import Property from "./Property";
import "../ResultScreens/Industryresult.css";

function Properties({ solutions, toggleModal }) {
    const [activeTab, setActiveTab] = useState(0);

    return (
        <div className="result-container flex flex-col w-full h-[94%] relative">
            {solutions.length > 0 && (
                <div className="tabs-container flex w-full rounded-t-lg gap-1">
                    {solutions.map((_, index) => (
                        <div
                            key={index}
                            className={`tab-item p-2 text-lg font-medium cursor-pointer border border-gray-300 rounded-t-md transition-all 
                            ${activeTab === index ? "bg-[#d3d3d3] text-blue-600 border-none" : "bg-white text-black hover:bg-gray-200"}`}
                            onClick={() => setActiveTab(index)}
                        >
                            Option {index + 1}
                        </div>
                    ))}
                </div>
            )}

            <div className="solutions-content h-[95%] border border-gray-300 rounded-b-lg bg-gray-100">
                {solutions.length > 0 && <Property solution={solutions[activeTab]} toggleModal={toggleModal} />}
            </div>
        </div>
    );
}

export default Properties;
