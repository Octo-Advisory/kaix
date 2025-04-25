import React, { useEffect, useState } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import Details from '../Details/Details';
import {
    FaSearch, FaBuilding, FaFileAlt, FaClock, FaCheckCircle,
    FaInfoCircle, FaTag, FaLayerGroup, FaStar, FaSync
} from 'react-icons/fa';
import DOMPurify from 'dompurify';

// Parse stringified approval data


function Approvalresult({result}) {
    console.log("result in approvals",result);
    
    const approval_data = JSON.parse(result["Approval Data"]);
    const [viewMode, setViewMode] = useState("Pre-Operation");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedApproval, setSelectedApproval] = useState(null);
    const [approvalsData, setApprovalsDataData] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchApprovalsDetails = async () => {
        try {
            if (!approval_data || !approval_data["Approval ID"]) {
                setApprovalsDataData([]);
                setLoading(false);
                return;
            }

            const approvalIds = Object.values(approval_data["Approval ID"]);

            const fetchPromises = approvalIds.map((id, index) => {
                const filters = JSON.stringify([["name", "=", id]]);
                const fields = JSON.stringify(["*"]);

                const url = `/api/resource/Licenses and Approvals Type?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;

                return fetch(url, {
                    method: 'GET',
                    headers: {
                        'Authorization': 'token d3de1e0e4e25846:3d3be60aaa3b67c',
                        'Content-Type': 'application/json'
                    }
                }).then(res => res.ok ? res.json() : null);
            });

            const responses = await Promise.all(fetchPromises);
                
            const fetchedApprovals = responses
                .map((res, index) => {
                    const fallbackId = approval_data["Approval ID"][index];
                    const fallbackLevel = approval_data["Level"][index];
                    const fallbackScore = approval_data["aggregated_score"][index];

                    if (!res || !res.data || res.data.length === 0) {
                        return {
                            id: fallbackId,
                            approvalID: fallbackId,
                            name: fallbackId,
                            type: "N/A",
                            mode: "N/A",
                            level: fallbackLevel || "N/A",
                            stage: "Others",
                            land_type: "N/A",
                            business_location: "N/A",
                            details: "No description available",
                            aggregated_score: fallbackScore || 0,
                        };
                    }

                    const approval = res.data[0];
                    return {
                        id: approval.name,
                        approvalID: approval.name,
                        name: approval.approval_name || fallbackId,
                        type: approval.government_department || "N/A",
                        mode: approval.mode_of_application || "N/A",
                        level: approval.level || fallbackLevel || "N/A",
                        stage: approval.stage || "Others",
                        land_type: approval.land_type || "N/A",
                        business_location: approval.business_location || "N/A",
                        details: approval.description || "No description available",
                        aggregated_score: approval.aggregated_score || fallbackScore || 0
                    };
                });

            setApprovalsDataData(fetchedApprovals);
            setSelectedApproval(fetchedApprovals.length > 0 ? fetchedApprovals[0] : null);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching approvals:", error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchApprovalsDetails();
    }, []);

    const filteredApprovals = approvalsData.filter(
        (approval) => approval.stage === viewMode &&
            approval.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    useEffect(() => {
        if (filteredApprovals.length > 0) {
            setSelectedApproval(filteredApprovals[0]);
        } else {
            setSelectedApproval(null);
        }
    }, [viewMode, searchQuery]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen w-full">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading Approvals...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9] overflow-hidden">
            <div className="w-[95%] h-[95%] mx-auto my-0 p-6 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col">
                <div className="flex items-center justify-between pb-4 mb-4">
                    <div className="flex items-center">
                        <div className="p-3 mr-4 bg-blue-50 rounded-lg">
                            <FaFileAlt className="text-xl text-blue-600" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-semibold text-gray-800">Approvals Catalog</h1>
                            <p className="text-gray-500">Browse required approvals for your business</p>
                        </div>
                    </div>
                    <Backtochat />
                </div>

                <div className="flex items-center justify-between mb-4">
                    <div className="flex gap-2">
                        {["Pre-Operation", "Pre-Establishment", "Pre-Requisite", "Others"].map(mode => (
                            <button
                                key={mode}
                                className={`px-4 py-2 rounded-md text-sm font-medium ${viewMode === mode
                                    ? "bg-blue-100 text-blue-700 border border-blue-200"
                                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                                    }`}
                                onClick={() => setViewMode(mode)}
                            >
                                {mode}
                            </button>
                        ))}
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                        <div className="flex items-center gap-3 bg-blue-50/80 px-4 py-2.5 rounded-lg border border-blue-100">
                            <div className="p-2 bg-blue-100/50 rounded-full">
                                <FaClock className="text-blue-600 text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-gray-500 text-xs">TOTAL TIME</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-bold text-blue-700">{result["Total Effective Time"]}</span>
                                    <span className="text-xs text-gray-400">days</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 bg-green-50/80 px-4 py-2.5 rounded-lg border border-green-100">
                            <div className="p-2 bg-green-100/50 rounded-full">
                                <FaCheckCircle className="text-green-600 text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-gray-500 text-xs">ONLINE</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-bold text-green-700">{result["Online Percentage"]}</span>
                                    <span className="text-xs text-gray-400">%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="relative mb-4">
                    <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search by approval name or department..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-12 pr-4 py-3 w-full border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 placeholder-gray-400 text-gray-700"
                    />
                </div>

                <div className="flex flex-1 min-h-0 overflow-hidden bg-white rounded-lg border border-gray-200">
                    <div className="w-1/3 border-r border-gray-200 flex flex-col">
                        <div className="overflow-y-auto flex-1 list-view">
                            {filteredApprovals.length > 0 ? (
                                <div className="space-y-2 p-2">
                                    {filteredApprovals.map((approval) => (
                                        <div
                                            key={approval.id}
                                            className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${selectedApproval?.id === approval.id
                                                ? "bg-blue-50 border-l-4 border-blue-500"
                                                : "hover:bg-gray-50 border-l-4 border-transparent"
                                                }`}
                                            onClick={() => setSelectedApproval(approval)}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h3 className={`font-medium ${selectedApproval?.id === approval.id ? "text-blue-700" : "text-gray-700"
                                                    }`}>
                                                    {approval.name}
                                                </h3>
                                            </div>
                                            <div className="flex items-center mt-2 text-sm text-gray-500">
                                                <FaBuilding className="mr-2" />
                                                <span>{approval.type}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                                    <FaSearch className="text-gray-300 text-3xl mb-3" />
                                    <h3 className="text-lg font-medium text-gray-500">No approvals found</h3>
                                    <p className="text-gray-400">Try a different search term or view mode</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {selectedApproval && (
                        <div className="w-2/3 flex flex-col">
                            <div className="overflow-y-auto flex-1 p-6">
                                <div className="mb-8">
                                    <div className="flex items-center mb-2">
                                        <div className="p-2 mr-3 bg-blue-100 rounded-lg">
                                            <FaFileAlt className="text-blue-600" />
                                        </div>
                                        <h2 className="text-2xl font-semibold text-gray-800">{selectedApproval.name}</h2>
                                    </div>

                                    <div className="flex flex-wrap gap-2 mb-4">
                                        <span className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full flex items-center">
                                            <FaTag className="mr-1" /> {selectedApproval.type}
                                        </span>
                                        <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full flex items-center">
                                            <FaLayerGroup className="mr-1" /> {selectedApproval.level}
                                        </span>
                                        <span className="px-3 py-1 bg-green-50 text-green-700 text-sm rounded-full flex items-center">
                                            <FaStar className="mr-1" /> Score: {selectedApproval.aggregated_score.toFixed(1)}
                                        </span>
                                    </div>
                                </div>

                                <div className="mb-8">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                                        <FaInfoCircle className="mr-2 text-blue-500" />
                                        Approval Details
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                            <h4 className="font-medium text-gray-700 mb-2">Mode of Application</h4>
                                            <p className="text-gray-600">{selectedApproval.mode}</p>
                                        </div>
                                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                            <h4 className="font-medium text-gray-700 mb-2">Stage</h4>
                                            <p className="text-gray-600">{selectedApproval.stage}</p>
                                        </div>
                                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                            <h4 className="font-medium text-gray-700 mb-2">Land Type</h4>
                                            <p className="text-gray-600">{selectedApproval.land_type}</p>
                                        </div>
                                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                            <h4 className="font-medium text-gray-700 mb-2">Business Location</h4>
                                            <p className="text-gray-600">{selectedApproval.business_location}</p>
                                        </div>
                                    </div>
                                </div>

                                {selectedApproval.details !== "No description available" && (
                                    <div className="mb-8">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                                            <FaFileAlt className="mr-2 text-blue-500" />
                                            Description
                                        </h3>
                                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                            <div
                                                className="prose text-gray-700 max-w-none"
                                                dangerouslySetInnerHTML={{
                                                    __html: DOMPurify.sanitize(selectedApproval.details),
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="mb-8">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                                        <FaInfoCircle className="mr-2 text-blue-500" />
                                        Additional Information
                                    </h3>
                                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                        <p className="text-gray-600">
                                            Approval ID: <span className="font-medium">{selectedApproval.approvalID}</span>
                                        </p>
                                        <p className="text-gray-400 text-xs mt-2 flex items-center">
                                            <FaSync className="mr-1" />
                                            Data fetched from government sources
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <Details />
        </div>
    );
}

export default Approvalresult;
