import React, { useEffect, useState } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import Details from '../Details/Details';
import { FaSearch } from 'react-icons/fa';
import DOMPurify from 'dompurify';

function Approvalresult({result}) {
    const [viewMode, setViewMode] = useState("Pre-Operation");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedApproval, setSelectedApproval] = useState(null);
    const Analytics_response = result["Analytics_response"];
    
    const approval_data = JSON.parse(Analytics_response["Approval Data"]);

    const approvals = Object.keys(approval_data["Approval ID"]).map((key) => ({
        approvalID: approval_data["Approval ID"][key],
        approval_name: approval_data["Approval Name"][key] || "N/A",
        department: approval_data["Government Department"][key] || "N/A",
        mode: approval_data["Mode of Application"][key] || "N/A",
        level: approval_data["Level"][key] || "N/A",
        stage: approval_data["Stages"][key] || "N/A",
        land_type: approval_data["Land_type"][key] || "N/A",
        business_location: approval_data["Business_location"][key] || "N/A",
        description: approval_data["description"][key] || "No description available",
    }));

    const filteredApprovals = approvals.filter(
        (approval) => approval.stage === viewMode &&
            approval.approval_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Set the first item by default when viewMode changes or component mounts
    useEffect(() => {
        if (filteredApprovals.length > 0) {
            setSelectedApproval(filteredApprovals[0]);
        } else {
            setSelectedApproval(null);
        }
    }, [viewMode]);

    // Handle search query change
    const handleSearchChange = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        
        if (query === "") {
            // Reset to the first item when search is cleared
            if (filteredApprovals.length > 0) {
                setSelectedApproval(filteredApprovals[0]);
            } else {
                setSelectedApproval(null);
            }
        } else {
            // Clear selection when searching
            setSelectedApproval(null);
        }
    };

    // Set first result in search if found
    useEffect(() => {
        if (searchQuery && filteredApprovals.length > 0) {
            setSelectedApproval(filteredApprovals[0]);
        }
    }, [searchQuery, filteredApprovals]);

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
                                className={`bg-gradient-to-r text-white px-3 py-2 rounded-md ${viewMode === mode ? "from-green-400 to-green-600" : "from-gray-400 to-gray-600"}`}
                                onClick={() => setViewMode(mode)}
                            >
                                {mode}
                            </button>
                        ))}
                    </div>
                    <div className="flex gap-4 text-gray-700 text-lg">
                        <span><strong>Total Effective Time:</strong> {Analytics_response["Total Effective Time"]} Days</span>
                        <span><strong>Online Percentage:</strong> {Analytics_response["Online Percentage"]}%</span>
                    </div>
                </div>

                <div className="bg-white shadow p-4 flex items-center my-4 rounded-lg">
                    <div className="relative w-full">
                        <input
                            type="text"
                            placeholder="Search approvals..."
                            value={searchQuery}
                            onChange={handleSearchChange}
                            className="px-3 py-2 border rounded-lg pl-10 w-full"
                        />
                        <FaSearch className="absolute left-3 top-3 text-gray-500" />
                    </div>
                </div>

                <div className="flex h-[70%] overflow-y-auto bg-white shadow">
                    <div className="w-2/3">
                        {filteredApprovals.length > 0 ? (
                            filteredApprovals.map((item) => (
                                <div
                                    key={item.approvalID}
                                    className={`p-4 border cursor-pointer shadow-sm ${selectedApproval?.approvalID === item.approvalID ? "bg-[#242f6a] text-white border-none" : "bg-white"}`}
                                    onClick={() => setSelectedApproval(item)}
                                >
                                    <span className="font-semibold">{item.approval_name} ({item.department})</span>
                                </div>
                            ))
                        ) : (
                            <p className="text-gray-500">No approvals found.</p>
                        )}
                    </div>

                    {selectedApproval && (
                        <div className="w-1/3 bg-[#242f6a] shadow p-4 text-white h-[65vh] overflow-y-auto top-0 sticky">
                            <h2 className="text-xl font-bold">{selectedApproval.approval_name}</h2>
                            <p className="mt-2 text-sm"><strong>Government Department:</strong> {selectedApproval.department}</p>
                            <p className="mt-2 text-sm"><strong>Mode of Application:</strong> {selectedApproval.mode}</p>
                            <p className="mt-2 text-sm"><strong>Level:</strong> {selectedApproval.level}</p>
                            <p className="mt-2 text-sm"><strong>Stage:</strong> {selectedApproval.stage}</p>
                            <p className="mt-2 text-sm"><strong>Land Type:</strong> {selectedApproval.land_type}</p>
                            <p className="mt-2 text-sm"><strong>Business Location:</strong> {selectedApproval.business_location}</p>
                            <p className="mt-2 text-sm">
                                <strong>Description:</strong> <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(selectedApproval.description) }} />
                            </p>
                        </div>
                    )}
                </div>
            </div>
            <Details />
        </div>
    );
}

export default Approvalresult;
