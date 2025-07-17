import React, { useEffect, useState, useRef } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import {
    FaSearch, FaBuilding, FaFileAlt, FaClock, FaCheckCircle,
    FaInfoCircle, FaTag, FaLayerGroup, FaStar, FaSync
} from 'react-icons/fa';
import DOMPurify from 'dompurify';
import LogoLoader from '../Responseloader/LogoLoader';
import { useSelector } from 'react-redux';
import { useFrappeGetDoc, useFrappeUpdateDoc } from 'frappe-react-sdk';
import FailureScreen from '../Failure/FailureScreen';
import NoResultsFound from '../Failure/NoResultsFound';

// Parse stringified approval data


function Approvalresult({ result, source, rerender }) {
    const [tempFailure, setTempFailure] = useState(false)
    const [someError, setSomeError] = useState(false)
    console.log("result in approvals", result);
    let approval_data = result["Approval Data"];
    if (typeof approval_data === "string") {
        approval_data = JSON.parse(approval_data);
    }
    const [viewMode, setViewMode] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedApproval, setSelectedApproval] = useState(null);
    const [approvalsData, setApprovalsDataData] = useState([]);
    const [loading, setLoading] = useState(true);
    const lastChatId = useSelector((state) => state.chat.lastId);
    const { updateDoc } = useFrappeUpdateDoc()
    const { data: uiData } = useFrappeGetDoc("UI Configuration", "UI Configuration")

    const getLocationLevel = (city, state, country) => {
        if (city === 1) {
            return "City";
        } else if (state === 1) {
            return "State";
        } else if (country === 1) {
            return "Country";
        } else {
            return "N/A";
        }
    }

    const fetchApprovalsDetails = async () => {
        try {

            if (!approval_data || !approval_data["Approval ID"]) {
                setApprovalsDataData([]);
                setTempFailure(true)
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
                        'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
                        'Content-Type': 'application/json'
                    }
                }).then(res => res.ok ? res.json() : null);
            });

            const responses = await Promise.all(fetchPromises);

            const fetchedApprovals = responses
                .map((res, index) => {
                    const fallbackId = approval_data["Approval ID"][index];
                    // const fallbackLevel = approval_data["Level"][index];
                    const fallbackScore = approval_data["aggregated_score"][index];

                    if (!res || !res.data || res.data.length === 0) {
                        return {
                            id: fallbackId,
                            approvalID: fallbackId,
                            approval_name: fallbackId,
                            government_department: "N/A",
                            mode_of_application: "N/A",
                            level: "N/A",
                            stage: "Others",
                            time_taken: "N/A",
                            land_type: "N/A",
                            business_location: "N/A",
                            details: "No description available",
                            aggregated_score: fallbackScore || 0,
                        };
                    }

                    const approval = res.data[0];
                    let tempLevel = getLocationLevel(approval.city_level, approval.state_level, approval.country_level)
                    return {
                        id: approval.name,
                        approvalID: approval.name,
                        approval_name: approval.license_approval || fallbackId,
                        government_department: approval.government_department || "N/A",
                        mode_of_application: approval.mode_of_application || "N/A",
                        level: tempLevel || "N/A",
                        time_taken: approval.delivery_schedule_in_working_days,
                        stage: approval.stage || "Others",
                        land_type: approval.land_type || "N/A",
                        business_location: approval.business_location || "N/A",
                        details: approval.description || "No description available",
                        aggregated_score: approval.aggregated_score || fallbackScore || 0
                    };
                });

            setApprovalsDataData(fetchedApprovals);
            setSelectedApproval(fetchedApprovals.length > 0 ? fetchedApprovals[0] : null);
            setViewMode(fetchedApprovals.length > 0 ? fetchedApprovals[0].stage : 'Pre-Operation')
            setLoading(false);
            if (lastChatId && source != "FromScratch") {
                const no_of_approvals = fetchedApprovals?.length
                const stageCounts = fetchedApprovals?.reduce((acc, curr) => {
                    acc[curr.stage] = (acc[curr.stage] || 0) + 1;
                    return acc;
                }, {});
                const render_data = {
                    "Mode_Others": result["Mode_Others"],
                    "Mode_Pre-Establishment": result["Mode_Pre-Establishment"],
                    "Mode_Pre-Operation": result["Mode_Pre-Operation"],
                    "Mode_Pre-Requisite": result["Mode_Pre-Requisite"],
                    "Online Percentage": result["Online Percentage"],
                    "Others": result["Others"],
                    "Pre-Establishment": result["Pre-Establishment"],
                    "Pre-Operation": result["Pre-Operation"],
                    "Pre-Requisite": result["Pre-Requisite"],
                    "Total Effective Time": result["Total Effective Time"]
                };

                const updatedResult = {
                    ...render_data,
                    "Approval Data": fetchedApprovals,
                    'no_of_approvals': no_of_approvals,
                    'stagewise_no_of_approvals': stageCounts
                };
                console.log(updatedResult, 'This are the results after prepared....', updatedResult)
                await updateDoc("Chat history", lastChatId, {
                    result: JSON.stringify({ "result": updatedResult }),
                    intension: "Query to Get Approvals"
                });
            }
        } catch (error) {
            console.error("Error fetching approvals:", error);
            setSomeError(true)
            setLoading(false);
        }
    };

    useEffect(() => {
        console.log('Entered the new log ...', rerender, result)
        if (rerender === 1 || source === 'FromScratch') {
            console.log('Entered the OKKKKK', source, result)
            if(!approval_data) {
                setTempFailure(true)
                return
            }
            setApprovalsDataData(approval_data)
            setViewMode(approval_data?.[0].stage)
            setSelectedApproval(approval_data?.[0])
            setLoading(false)
        } else {
            fetchApprovalsDetails();
        }
    }, []);

    const filteredApprovals = approvalsData.filter(
        (approval) => approval.stage === viewMode &&
            approval.approval_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    useEffect(() => {
        if (filteredApprovals.length > 0) {
            setSelectedApproval(filteredApprovals[0]);

        } else {
            setSelectedApproval(null);
        }
    }, [viewMode, searchQuery]);

    const containerRef = useRef(null)

    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = 0;
        }
    }, [selectedApproval])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen w-screen">
                <LogoLoader text='Rolling Out the Final Compliance View' />
            </div>
        );
    }

    if (someError) {
        return (
            <FailureScreen />
        )
    }

    if (tempFailure) {
        return (
            <NoResultsFound />
        )
    }

    return (
        <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655] overflow-hidden">
            <div className="w-[98%] h-[95%] mx-auto my-0 p-6 bg-white rounded-xl shadow-sm border border-white border-opacity-40 flex flex-col backdrop-blur-sm">
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#B8D1F3]">
                    <div className="flex items-center">
                        <div className="p-3 mr-4 rounded-lg bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10">
                            <FaFileAlt className="text-xl text-[#7AA6DA]" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-semibold text-[#2C53A3]">{uiData?.approval_main_title || "Approvals Catalog"}</h1>
                            <p className="text-[#5A7EC7]">{uiData?.approval_sub_title || "Browse required approvals for your project"}</p>
                        </div>
                    </div>

                    <div className='relative flex-row flex items-center gap-6'>
                        <div className="relative flex flex-row items-center gap-4 text-sm">
                            <div className="flex items-center gap-3 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 px-4 py-0.5 rounded-lg border border-[#B8D1F3]">
                                <div className="p-2 bg-[#B8D1F3]/30 rounded-full">
                                    <FaClock className="text-[#2C53A3] text-sm" />
                                </div>
                                <div>
                                    <span className="font-medium text-[#5A7EC7] text-xs">TOTAL TIME</span>
                                    <div className="flex items-baseline gap-1.5">
                                        <span className="text-md font-bold text-[#2C53A3]">{result["Total Effective Time"]}</span>
                                        <span className="text-xs text-[#5A7EC7]/70">days</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-3 bg-gradient-to-r from-[#81C784]/20 to-[#4CAF50]/20 px-4 py-0.5 rounded-lg border border-[#81C784]">
                                <div className="p-2 bg-[#81C784]/30 rounded-full">
                                    <FaCheckCircle className="text-[#2E7D32] text-sm" />
                                </div>
                                <div>
                                    <span className="font-medium text-[#5A7EC7] text-xs">ONLINE</span>
                                    <div className="flex items-baseline gap-1.5">
                                        <span className="text-md font-bold text-[#2E7D32]">{result["Online Percentage"]}</span>
                                        <span className="text-xs text-[#5A7EC7]/70">%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {source === "SolutionScreen" && (
                            <Backtochat text='Back to Chat' />
                        )}
                    </div>
                </div>

                <div className="flex items-center justify-between mb-4">
                    <div className="flex gap-2">
                        {/* below line changed by jenith on 14/05/25 13:25 */}
                        {["Pre-Requisite", "Pre-Establishment", "Pre-Operation", "Others"].map(mode => (
                            <button
                                key={mode}
                                className={`px-4 py-2 rounded-md text-sm font-medium ${viewMode === mode
                                    ? "bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 text-[#2C53A3] border border-[#B8D1F3]"
                                    : "bg-white text-[#5A7EC7] hover:bg-[#E6F0FA] border border-[#B8D1F3]/50"
                                    }`}
                                onClick={() => setViewMode(mode)}
                            >
                                {mode}
                            </button>
                        ))}
                    </div>

                    <div className='flex relative flex-row gap-4 text-sm'>
                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 px-4 py-0.5 rounded-lg border border-[#B8D1F3]">
                            <div className="p-2 bg-[#B8D1F3]/30 rounded-full">
                                <FaClock className="text-[#2C53A3] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">TOTAL TIME</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-md font-bold text-[#2C53A3]">{result[viewMode]}</span>
                                    <span className="text-xs text-[#5A7EC7]/70">days</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#81C784]/20 to-[#4CAF50]/20 px-4 py-0.5 rounded-lg border border-[#81C784]">
                            <div className="p-2 bg-[#81C784]/30 rounded-full">
                                <FaCheckCircle className="text-[#2E7D32] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">ONLINE</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-md font-bold text-[#2E7D32]">{result[`Mode_${viewMode}`]}</span>
                                    <span className="text-xs text-[#5A7EC7]/70">%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>

                <div className="relative mb-4">
                    <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5A7EC7]" />
                    <input
                        type="text"
                        placeholder="Search by approval name or department..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-12 pr-4 py-3 w-full border border-[#B8D1F3] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF80AB]/30 focus:border-[#7AA6DA] placeholder-[#5A7EC7]/70 text-[#2C53A3] bg-white bg-opacity-90"
                    />
                </div>

                <div className="flex flex-1 min-h-0 overflow-hidden bg-white rounded-lg border border-[#B8D1F3]">
                    <div className="w-1/3 border-r border-[#B8D1F3] flex flex-col">
                        <div className="overflow-y-auto flex-1 list-view bg-gradient-to-b from-[#E6F0FA]/10 to-transparent">
                            {filteredApprovals.length > 0 ? (
                                <div className="space-y-2 p-2">
                                    {filteredApprovals.map((approval) => (
                                        <div
                                            key={approval.id}
                                            className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${selectedApproval?.id === approval.id
                                                ? "bg-[#41b655] bg-opacity-20 border-l-4 border-[#41b655] "
                                                : "bg-[#41b655] bg-opacity-10 border-none"
                                                }`}
                                            // style={{
                                            //     background: selectedApproval?.id === approval.id
                                            //     ? 'linear-gradient(to right, rgba(255, 128, 171, 0.08), rgba(255, 255, 255, 0.9))'
                                            //     : 'transparent',
                                            //     borderLeftColor: selectedApproval?.id === approval.id ? '#FF80AB' : 'transparent'
                                            // }}
                                            onClick={() => setSelectedApproval(approval)}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h3 className={`font-medium ${selectedApproval?.id === approval.id ? "text-black" : "text-[#3b69c5]"
                                                    }`}>
                                                    {approval.approval_name}
                                                </h3>
                                            </div>
                                            <div className="flex items-center mt-2 text-sm text-[#5A7EC7]">
                                                <FaBuilding className="mr-2" />
                                                <span>{approval.government_department}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                                    <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB]/20 to-[#9575CD]/20">
                                        <FaSearch className="text-2xl text-[#5A7EC7]" />
                                    </div>
                                    <h3 className="text-lg font-medium text-[#2C53A3]">{uiData?.no_approvals_found || "No approvals found"}</h3>
                                    <p className="text-[#5A7EC7]">Try a different search term or view mode</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {selectedApproval && (
                        <div className="w-2/3 flex flex-col">
                            <div ref={containerRef} className="overflow-y-auto flex-1 p-6">
                                <div className="mb-8">
                                    <div className="flex items-center mb-2">
                                        <div className="p-3 mr-3 rounded-lg bg-blue-100">
                                            <FaFileAlt className="text-blue-800" />
                                        </div>
                                        <h2 className="text-2xl font-semibold text-[#2C53A3]">{selectedApproval.approval_name}</h2>
                                    </div>

                                    <div className="flex flex-wrap gap-2 mb-4">
                                        <span className="px-3 py-1 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 text-[#2C53A3] text-sm rounded-full flex items-center">
                                            <FaBuilding className="mr-2" /> {selectedApproval.government_department}
                                        </span>
                                        <span className="px-3 py-1 bg-gradient-to-r from-[#E6F0FA]/30 to-[#B8D1F3]/20 text-[#2C53A3] text-sm rounded-full flex items-center">
                                            <FaLayerGroup className="mr-1" /> {selectedApproval.level}
                                        </span>
                                        {/* <span className="px-3 py-1 bg-gradient-to-r from-[#81C784]/20 to-[#4CAF50]/20 text-[#2E7D32] text-sm rounded-full flex items-center">
                                            <FaStar className="mr-1" /> Score: {selectedApproval.aggregated_score.toFixed(1)}
                                        </span> */}
                                    </div>
                                </div>

                                <div className="mb-8">
                                    <h3 className="text-lg font-semibold text-[#2C53A3] mb-3 flex items-center">
                                        <FaInfoCircle className="mr-2 text-[#FF80AB]" />
                                        {uiData?.approval_details || "Approval Details"}
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiData?.approval_mode_of_application || "Mode of Application"}</h4>
                                            <p className="text-[#5A7EC7]">{selectedApproval.mode_of_application}</p>
                                        </div>
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiData?.approval_stage || "Stage"}</h4>
                                            <p className="text-[#5A7EC7]">{selectedApproval.stage}</p>
                                        </div>
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiData?.approval_land_type || "Land Type"}</h4> {/* changed by jenith on 14/05/25 13:26 */}
                                            <p className="text-[#5A7EC7]">{selectedApproval.land_type}</p>
                                        </div>
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiData?.approval_project_location || "Project Location"}</h4> {/* changed by jenith on 14/05/25 13:27 */}
                                            <p className="text-[#5A7EC7]">{selectedApproval.business_location}</p>
                                        </div>
                                    </div>
                                </div>

                                {selectedApproval.details !== "No description available" && (
                                    <div className="mb-8">
                                        <h3 className="text-lg font-semibold text-[#2C53A3] mb-3 flex items-center">
                                            <FaFileAlt className="mr-2 text-[#7AA6DA]" />
                                            {uiData?.approval_description || "Description"}
                                        </h3>
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <div
                                                className="prose text-[#5A7EC7] max-w-none"
                                                dangerouslySetInnerHTML={{
                                                    __html: DOMPurify.sanitize(selectedApproval.details),
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="mb-8">
                                    <h3 className="text-lg font-semibold text-[#2C53A3] mb-3 flex items-center">
                                        <FaInfoCircle className="mr-2 text-[#9575CD]" />
                                        {uiData?.approval_additional_information || "Additional Information"}
                                    </h3>
                                    <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                        <p className="text-[#5A7EC7]">
                                            Approval ID: <span className="font-medium text-[#2C53A3]">{selectedApproval.approvalID}</span>
                                        </p>
                                        <p className="text-[#5A7EC7]/70 text-xs mt-2 flex items-center">
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
        </div>
    );
}

export default Approvalresult;
