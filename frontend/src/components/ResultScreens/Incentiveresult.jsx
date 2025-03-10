import React, { useState } from 'react';
import Details from '../Details/Details';
import Backtochat from '../Backtochat/Backtochat';
import * as Accordion from "@radix-ui/react-accordion";
import { ChevronDown, Info } from "lucide-react";

function Incentiveresult({ result }) {
    console.log("Result from incentive:", result);
    const [openItem, setOpenItem] = useState(null);
    // Safely parse JSON and handle errors
    let Analytics_response;
    try {
        Analytics_response = JSON.parse(result?.Analytics_response || '{}');
    } catch (error) {
        console.error("Error parsing Analytics_response:", error);
        Analytics_response = {};
    }

    // Convert data object into an array of incentive objects
    let incentivesArray = Object.keys(Analytics_response["Incentive Rank"]).map(key => ({
        id: Analytics_response["Incentive ID"][key],
        name: Analytics_response["Incentive Name"][key],
        type: Analytics_response["Incentive Type"][key],
        rank: Analytics_response["Incentive Rank"][key],
        details: Analytics_response["Incentive Details"][key],
        startDate: new Date(Analytics_response["Incentive Start Date"][key])
            .toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' }),

        endDate: new Date(Analytics_response["Incentive End Date"][key])
            .toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })
    }));

    // Ensure sorting by rank
    incentivesArray.sort((a, b) => b.rank - a.rank);

    console.log("incenitve array", incentivesArray);


    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
            <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
                {/* Title Section */}
                <div className="top-header flex items-center justify-between">
                    <div className="title w-full p-1 h-[10%] flex-1">
                        <div className="text-5xl">Incentives</div>
                    </div>
                    <Backtochat />
                </div>

                {/* Incentive Data */}
                <div className="p-3 h-[90%] overflow-auto">
                    <Accordion.Root type="single" collapsible className="space-y-2" value={openItem} onValueChange={setOpenItem}>
                        {incentivesArray.map((incentive, index) => (
                            <Accordion.Item key={index} value={`item-${index}`} className="border border-gray-300 rounded-lg overflow-hidden">
                                <Accordion.Header>
                                    <Accordion.Trigger className="w-full text-left px-4 py-3 bg-[#19a282] text-white font-semibold hover:bg-[#167d66] transition flex justify-between items-center">
                                        <span>{incentive.name} - {incentive.type}</span>
                                        <ChevronDown
                                            className={`transform transition-transform ${openItem === `item-${index}` ? 'rotate-180' : ''}`}
                                        />
                                    </Accordion.Trigger>
                                </Accordion.Header>
                                <Accordion.Content className="p-4 bg-white border-t border-gray-300">
                                    <div className="flex items-center gap-2 text-lg font-semibold text-gray-700 mb-2">
                                        <Info className="text-blue-500" />
                                        Incentive Details
                                    </div>
                                    <div className="bg-[#f8f9fa] p-3 rounded-md border border-gray-300 space-y-2">
                                        <p><span className="font-semibold">Type:</span> {incentive.type}</p>
                                        <p><span className="font-semibold">Description:</span> {incentive.details}</p>
                                        <p><span className="font-semibold">Effective Date:</span> {incentive.startDate} - {incentive.endDate}</p>
                                        {/* <p><span className="font-semibold">Rank:</span> {incentive.rank}</p> */}
                                    </div>
                                </Accordion.Content>
                            </Accordion.Item>
                        ))}
                    </Accordion.Root>
                </div>
            </div>
            <Details />
        </div>
    );
}

export default Incentiveresult;
