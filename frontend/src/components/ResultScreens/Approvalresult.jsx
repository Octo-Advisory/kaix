import React, { useEffect, useState, useRef, useContext } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import {
    FaSearch,FaClock, FaCheckCircle,
 FaLayerGroup, FaSync
} from 'react-icons/fa';
import DOMPurify from 'dompurify';
import LogoLoader from '../Responseloader/LogoLoader';
import { useSelector } from 'react-redux';
import { FrappeContext, useFrappeGetDoc, useFrappeUpdateDoc,useFrappeCreateDoc } from 'frappe-react-sdk';
import FailureScreen from '../Failure/FailureScreen';
import NoResultsFound from '../Failure/NoResultsFound';
import { AdditionalDetailIcon, ApprovalNameIcon, ApprovalTitleIcon, BuildingIcon, InfoIcon, SearchIcon } from '../../Icons/icon';

function Approvalresult({ result, source, rerender }) {
    const lastChatId = useSelector((state) => state.chat.lastId);
    const { createDoc } = useFrappeCreateDoc('');

    const createDiagnostic = async(errType, logMsg,chatId)=> {
      let log = ` ${logMsg}`
       createDoc("AIX Diagnostics Hub", {
      type: errType,
      note: log,
      chat_name: chatId
      });
    }

    const {call} = useContext(FrappeContext)
    const [tempFailure, setTempFailure] = useState(false)
    const [someError, setSomeError] = useState(false)
    // console.log("result in approvals", result);
    if (
    typeof result !== 'object' || 
    result === null || 
    typeof result === 'string'
  ) {
    // console.log('Invalid result:', result);
    // createDiagnostic("Data Error", `Invalid Data was passed that couldn't be rendered due to ${result} IN Approvals`,lastChatId)
    return <NoResultsFound diagnostics={true} type='Approvals' chatId={lastChatId} data={result} module='Approvals'/>;
  }
    let approval_data = result["Approval Data"];
    if (typeof approval_data === "string") {
        approval_data = JSON.parse(approval_data);
    }
    // console.log(approval_data, 'This is the approval Data')
    const [viewMode, setViewMode] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedApproval, setSelectedApproval] = useState(null);
    const [approvalsData, setApprovalsDataData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [approvalsMap, setApprovalsMap] = useState([])
    const [fetchedApproval, setFetchedApproval] = useState([])
    const [emptyStages, setEmptyStages] = useState([])
  
    const { updateDoc } = useFrappeUpdateDoc()
    const { data: uiData } = useFrappeGetDoc("UI Configuration", "Approvals")
      const configurations = uiData?.configurations || [];
      const uiConfig = configurations.reduce((acc, curr) => {
        acc[curr.key] = curr.value;
        return acc;
      }, {}); 

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

     function mapApprovalData(ApprovalsObj, nameObj,govtObj,scoreObj,stageObj) {
  if(!ApprovalsObj || !nameObj) return []
    return Object.keys(ApprovalsObj).map(key => ({
        id: ApprovalsObj[key],
        approval_name: nameObj[key],
        government_department: govtObj[key] || "Department of Industry & Health", // Fallback in case type doesn't exist
        aggregated_score: scoreObj[key],
        stage: stageObj[key]
    }));
}

const fetchApprovals = async()=>{
    if (!approval_data || !approval_data["Approval ID"]) {
        setApprovalsDataData([]);
        setApprovalsMap([])
        setTempFailure(true)
        setLoading(false);
        return;
    }
    let approvalsMapp = mapApprovalData(approval_data['Approval ID'], approval_data['Approval Name'], approval_data['Government Department'], approval_data["aggregated_score"], approval_data['Stages'])
    // console.log(approvalsMapp, 'This is the data we want tsee ')

    setLoading(false);
    const stages = [
    "Pre-Operation",
    "Pre-Establishment",
    "Pre-Requisite",
    "Others"
    ];

    // GROUP BY STAGE
    const grouped = approvalsMapp.reduce((acc, item) => {
    if (!acc[item.stage]) acc[item.stage] = [];
    acc[item.stage].push(item);
    return acc;
    }, {});

    // FIND EMPTY STAGES
    const empty_stages = stages.filter(
    stage => !grouped[stage] || grouped[stage].length === 0
    );
    setEmptyStages(empty_stages)
    setApprovalsMap(approvalsMapp)
    handleApprovalSelection(approvalsMapp[0])

    if (lastChatId && source != "FromScratch") {
        const no_of_approvals = approvalsMapp?.length
        const stageCounts = approvalsMapp?.reduce((acc, curr) => {
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
            "Approval Data": approvalsMapp,
            'no_of_approvals': no_of_approvals,
            'stagewise_no_of_approvals': stageCounts
        };
        
        await storeResultData(lastChatId, updatedResult, 'Query to Get Approvals')
        // console.log('Process Completed')
        // console.timeEnd()
    }
}

const handleApprovalSelection = async (approval) => {
    // console.time()
    // console.log('Fetching the Incentive')
    let aggregated_score = approval.aggregated_score
    let id = approval.id
    try {

        // 1️⃣ Check if we already have this incentive cached
        const existingApproval = fetchedApproval.find(
            (item) => item.id === id
        );

        if (existingApproval) {
            // console.log('Using cached Approval:', existingApproval);
            setSelectedApproval(existingApproval);
            return; // ✅ Skip API call
        }

        let fetchedApprovalsData = []
        const filters = JSON.stringify([["name", "=", id]]);
        const fields = JSON.stringify(["*"]);

        const url = `/api/resource/Licenses and Approvals Type?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
                'Content-Type': 'application/json'
            }
        })
        
        if(response.ok) {
            const data = await response.json();
            if (!data || !data.data || data.data.length === 0) {
                return {
                    id: id,
                    approvalID: id,
                    approval_name: id,
                    government_department: "N/A",
                    mode_of_application: "N/A",
                    level: "N/A",
                    stage: "Others",
                    time_taken: "N/A",
                    land_type: "N/A",
                    business_location: "N/A",
                    details: "No description available",
                };
            }
           
            const approval = data.data[0];
            let tempLevel = getLocationLevel(approval.city_level, approval.state_level, approval.country_level)
            fetchedApprovalsData.push({
                id: approval.name,
                approvalID: approval.name,
                approval_name: approval.license_approval || id,
                government_department: approval.government_department || "N/A",
                mode_of_application: approval.mode_of_application || "N/A",
                level: tempLevel || "N/A",
                time_taken: approval.delivery_schedule_in_working_days,
                stage: approval.stage || "Others",
                land_type: approval.land_type || "N/A",
                business_location: approval.business_location || "N/A",
                details: approval.description || "No description available",
                aggregated_score: approval.aggregated_score || aggregated_score || 0
            })
        }
        // 2️⃣ Add the newly fetched incentive to cache
        setFetchedApproval((prev) => [...prev, ...fetchedApprovalsData]);

        setSelectedApproval(fetchedApprovalsData.length > 0 ? fetchedApprovalsData[0] : null);
        setViewMode(viewMode!== 'All' && fetchedApprovalsData.length > 0 ? fetchedApprovalsData[0].stage : viewMode)
        setLoading(false);
        
    } catch (error) {
        // console.error("Error fetching approvals:", error);
        createDiagnostic("Approvals", `Something Went wrong while fetching the approvals ${JSON.stringify(error)} IN Approvals`,lastChatId)
        setSomeError(true)
        setLoading(false);
    }


  
};

// const fetchApprovalsDetails = async () => {
    //     try {

    //         if (!approval_data || !approval_data["Approval ID"]) {
    //             setApprovalsDataData([]);
    //             setTempFailure(true)
    //             setLoading(false);
    //             return;
    //         }

    //         const approvalIds = Object.values(approval_data["Approval ID"]);

    //         const fetchPromises = approvalIds.map((id, index) => {
    //             const filters = JSON.stringify([["name", "=", id]]);
    //             const fields = JSON.stringify(["*"]);

    //             const url = `/api/resource/Licenses and Approvals Type?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;

    //             return fetch(url, {
    //                 method: 'GET',
    //                 headers: {
    //                     'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
    //                     'Content-Type': 'application/json'
    //                 }
    //             }).then(res => res.ok ? res.json() : null);
    //         });

    //         const responses = await Promise.all(fetchPromises);

    //         const fetchedApprovals = responses
    //             .map((res, index) => {
    //                 const fallbackId = approval_data["Approval ID"][index];
    //                 // const fallbackLevel = approval_data["Level"][index];
    //                 const fallbackScore = approval_data["aggregated_score"][index];

    //                 if (!res || !res.data || res.data.length === 0) {
    //                     return {
    //                         id: fallbackId,
    //                         approvalID: fallbackId,
    //                         approval_name: fallbackId,
    //                         government_department: "N/A",
    //                         mode_of_application: "N/A",
    //                         level: "N/A",
    //                         stage: "Others",
    //                         time_taken: "N/A",
    //                         land_type: "N/A",
    //                         business_location: "N/A",
    //                         details: "No description available",
    //                         aggregated_score: fallbackScore || 0,
    //                     };
    //                 }

    //                 const approval = res.data[0];
    //                 let tempLevel = getLocationLevel(approval.city_level, approval.state_level, approval.country_level)
    //                 return {
    //                     id: approval.name,
    //                     approvalID: approval.name,
    //                     approval_name: approval.license_approval || fallbackId,
    //                     government_department: approval.government_department || "N/A",
    //                     mode_of_application: approval.mode_of_application || "N/A",
    //                     level: tempLevel || "N/A",
    //                     time_taken: approval.delivery_schedule_in_working_days,
    //                     stage: approval.stage || "Others",
    //                     land_type: approval.land_type || "N/A",
    //                     business_location: approval.business_location || "N/A",
    //                     details: approval.description || "No description available",
    //                     aggregated_score: approval.aggregated_score || fallbackScore || 0
    //                 };
    //             });

    //         setApprovalsDataData(fetchedApprovals);
    //         setSelectedApproval(fetchedApprovals.length > 0 ? fetchedApprovals[0] : null);
    //         setViewMode(fetchedApprovals.length > 0 ? fetchedApprovals[0].stage : 'Pre-Operation')
    //         setLoading(false);
    //         if (lastChatId && source != "FromScratch") {
    //             const no_of_approvals = fetchedApprovals?.length
    //             const stageCounts = fetchedApprovals?.reduce((acc, curr) => {
    //                 acc[curr.stage] = (acc[curr.stage] || 0) + 1;
    //                 return acc;
    //             }, {});
    //             const render_data = {
    //                 "Mode_Others": result["Mode_Others"],
    //                 "Mode_Pre-Establishment": result["Mode_Pre-Establishment"],
    //                 "Mode_Pre-Operation": result["Mode_Pre-Operation"],
    //                 "Mode_Pre-Requisite": result["Mode_Pre-Requisite"],
    //                 "Online Percentage": result["Online Percentage"],
    //                 "Others": result["Others"],
    //                 "Pre-Establishment": result["Pre-Establishment"],
    //                 "Pre-Operation": result["Pre-Operation"],
    //                 "Pre-Requisite": result["Pre-Requisite"],
    //                 "Total Effective Time": result["Total Effective Time"]
    //             };

    //             const updatedResult = {
    //                 ...render_data,
    //                 "Approval Data": fetchedApprovals,
    //                 'no_of_approvals': no_of_approvals,
    //                 'stagewise_no_of_approvals': stageCounts
    //             };
               
    //             await storeResultData(lastChatId, updatedResult, 'Query to Get Approvals')
    //         }
    //     } catch (error) {
    //         // console.error("Error fetching approvals:", error);
    //         createDiagnostic("Approvals", `Something Went wrong while fetching the approvals ${JSON.stringify(error)} IN Approvals`,lastChatId)
    //         setSomeError(true)
    //         setLoading(false);
    //     }
    // };

//     const storeResultData = async (lastChat,solutions,intension) => {
//   if(!lastChat || !solutions) return 

//   try {
//       const result = await call.post("frontend_app.Management_Class.helpers.utility.insert_solution_result", {
//       child_row_id: lastChat,
//       updated_solutions: solutions,
//       intension: intension
//       },
//     {
//     headers: {
//       'Expect': '' // 👈 Clear problematic header
//     }
//   });
      
//       return result.message || [];
//     } catch (err) {
//     //   console.error("Error Storing Result json:", err);
//       createDiagnostic("Approvals", `Something went wrong while storing the result json due to ${JSON.stringify(err)} IN Approvals`,lastChatId)
//       return []; // Return empty for this batch on error
//     }
// }

 const storeResultData = async (lastChat, solutions,intension) => {
    if (!lastChat || !solutions) return

    try {

      const convertJson = await call.post("frontend_app.Management_Class.helpers.utility.convert_json_to_binary", {
        child_row_id: lastChat,
        updated_solutions: solutions,
        intension: intension
      },
      {
          headers: {
            'Expect': '' // 👈 Clear problematic header
          }
      }
    )
    // console.log(convertJson, 'this is the msg');
    
    } catch (err) {
    //   console.error("Error Storing Result json:", err);
      createDiagnostic("Land & Approvals", `Something went wrong while storing the result json ${JSON.stringify(err)} in ApprovalResult`,lastChatId)
      return []; // Return empty for this batch on error
    }
  }

    useEffect(() => {
        
        if (rerender === 1 || source === 'FromScratch') {
            if(!approval_data) {
                createDiagnostic("Data Error", `Invalid Data was passed that couldn't be rendered due to ${JSON.stringify(approval_data)} in Approvals `,lastChatId)
                setTempFailure(true)
                return
            }
            const stages = [
            "Pre-Operation",
            "Pre-Establishment",
            "Pre-Requisite",
            "Others"
            ];

            // GROUP BY STAGE
            const grouped = approval_data.reduce((acc, item) => {
            if (!acc[item.stage]) acc[item.stage] = [];
            acc[item.stage].push(item);
            return acc;
            }, {});

            // FIND EMPTY STAGES
            const empty_stages = stages.filter(
            stage => !grouped[stage] || grouped[stage].length === 0
            );
            setEmptyStages(empty_stages)

            setApprovalsMap(approval_data)
            handleApprovalSelection(approval_data[0])
        } else {
            fetchApprovals();
        }
    }, []);

    
    // const filteredApprovals = approvalsMap.filter(
    //     (approval) => approval.stage === viewMode &&
    //         approval.approval_name.toLowerCase().includes(searchQuery.toLowerCase())
    // );
    const filteredApprovals = approvalsMap.filter((approval) => {
    const matchesStage = viewMode === "All" || approval.stage === viewMode;
    const matchesSearch = approval.approval_name
        .toLowerCase()
        .includes(searchQuery.toLowerCase());

    return matchesStage && matchesSearch;
});


    useEffect(() => {
        if (filteredApprovals.length > 0) {
            handleApprovalSelection(filteredApprovals[0]);

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
                        <div className="p-2 mr-4 rounded-lg h-[52px] w-[52px] flex items-center justify-center bg-gradient-to-r from-[#FF80AB] to-[#9575CD] text-white">
                            <ApprovalTitleIcon className="h-full w-full relative" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-semibold text-[#2C53A3]">{uiConfig?.['main_title'] || "Approvals Catalog"}</h1>
                            <p className="text-[#5A7EC7]">{uiConfig?.['sub_title'] || "Browse required approvals for your project"}</p>
                        </div>
                    </div>

                    <div className='relative flex-row flex items-center gap-6'>
                        <div className="relative flex flex-row items-center gap-4 text-sm">
                            <div className="flex items-center gap-3 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 px-4 py-0.5 rounded-lg border border-[#B8D1F3]">
                                <div className="p-2 bg-[#B8D1F3]/30 rounded-full">
                                    <FaClock className="text-[#2C53A3] text-sm" />
                                </div>
                                <div>
                                    <span className="font-medium text-[#5A7EC7] text-xs">{uiConfig?.['total_approval_time'] || 'Total Time'}</span>
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
                                    <span className="font-medium text-[#5A7EC7] text-xs">{uiConfig?.['total_online_percentage'] || 'Online'}</span>
                                    <div className="flex items-baseline gap-1.5">
                                        <span className="text-md font-bold text-[#2E7D32]">{result["Online Percentage"]}</span>
                                        <span className="text-xs text-[#5A7EC7]/70">%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {source === "SolutionScreen" && rerender!==1 &&  (
                            <Backtochat text='Back to Chat' />
                        )}
                    </div>
                </div>

                <div className="flex items-center justify-between mb-4">
                    <div className="flex gap-2">
                        {JSON.parse(uiConfig?.['view_mode'] || '[]').map(mode => (
                            <button
                                key={mode}
                                disabled = {emptyStages && emptyStages.length>0 && emptyStages.includes(mode)}
                                className={`px-4 py-2 rounded-md text-sm font-medium ${ emptyStages && emptyStages.length>0 && emptyStages.includes(mode) ? 'cursor-not-allowed line-through opacity-40 bg-white text-[#5A7EC7] border border-[#B8D1F3]/50' : viewMode === mode
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
                                <span className="font-medium text-[#5A7EC7] text-xs">{uiConfig?.['stagewise_total_time'] || 'Total Time'}</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-md font-bold text-[#2C53A3]">{viewMode==='All' ? result["Total Effective Time"] : result[viewMode]}</span>
                                    <span className="text-xs text-[#5A7EC7]/70">days</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 bg-gradient-to-r from-[#81C784]/20 to-[#4CAF50]/20 px-4 py-0.5 rounded-lg border border-[#81C784]">
                            <div className="p-2 bg-[#81C784]/30 rounded-full">
                                <FaCheckCircle className="text-[#2E7D32] text-sm" />
                            </div>
                            <div>
                                <span className="font-medium text-[#5A7EC7] text-xs">{uiConfig?.['stagewise_online_percentage'] || 'Online'}</span>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-md font-bold text-[#2E7D32]">{viewMode==='All' ? result["Online Percentage"] :  result[`Mode_${viewMode}`]}</span>
                                    <span className="text-xs text-[#5A7EC7]/70">%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>

                <div className="relative mb-4">
                    <SearchIcon strokeWidth={2} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5A7EC7]" />
                    <input
                        type="text"
                        placeholder="Search by approval name or department..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-12 pr-4 py-3 w-full border border-[#B8D1F3] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF80AB]/30 focus:border-[#7AA6DA] placeholder-[#5A7EC7]/70 text-[#2C53A3] bg-white bg-opacity-90"
                    />
                </div>

                <div className="flex flex-1 min-h-0 overflow-hidden bg-white rounded-lg border border-[#B8D1F3]">
                    <div className={`${filteredApprovals.length>0 ? 'w-1/3' : 'w-full items-center justify-center'} border-r border-[#B8D1F3] flex flex-col`}>
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
                                            onClick={() => handleApprovalSelection(approval)}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h3 className={`font-medium ${selectedApproval?.id === approval.id ? "text-black" : "text-[#3b69c5]"
                                                    }`}>
                                                    {approval.approval_name}
                                                </h3>
                                            </div>
                                            <div className="flex items-center mt-2 text-sm text-[#5A7EC7]">
                                                <BuildingIcon size={18} className="mr-2" />
                                                <span>{approval.government_department}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                                    <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB]/20 to-[#9575CD]/20">
                                        <FaSearch strokeWidth={2} className="text-2xl text-[#5A7EC7]" />
                                    </div>
                                    <h3 className="text-lg font-medium text-[#2C53A3]">{uiConfig?.['no_approvals_found'] || "No approvals found"}</h3>
                                    <p className="text-[#5A7EC7]">Try a different search term or view mode</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {selectedApproval && (
                        <div className={`${filteredApprovals.length >0 ? 'w-2/3' : 'w-0'} flex flex-col`}>
                            <div ref={containerRef} className="overflow-y-auto flex-1 p-6">
                                <div className="mb-8">
                                    <div className="flex items-center mb-2">
                                        <div className="p-2 mr-3 h-12 w-12 flex items-center justify-center rounded-lg bg-blue-100">
                                            <ApprovalNameIcon className="relative h-full w-full" />
                                        </div>
                                        <h2 className="text-2xl font-semibold text-[#2C53A3]">{selectedApproval.approval_name}</h2>
                                    </div>

                                    <div className="flex flex-wrap gap-2 mb-4">
                                        <span className="px-3 py-1 bg-gradient-to-r from-[#B8D1F3]/20 to-[#7AA6DA]/20 text-[#2C53A3] text-sm rounded-full flex items-center">
                                            <BuildingIcon size={12} className="mr-2" /> {selectedApproval.government_department}
                                        </span>
                                        <span className="px-3 py-1 bg-gradient-to-r from-[#E6F0FA]/30 to-[#B8D1F3]/20 text-[#2C53A3] text-sm rounded-full flex items-center">
                                            <FaLayerGroup className="mr-1" /> {selectedApproval.level}
                                        </span>
                                    </div>
                                </div>

                                <div className="mb-8">
                                    <h3 className="text-lg font-semibold text-black mb-3 flex items-center">
                                        <InfoIcon strokeWidth={1} className="mr-2 text-blue-700" />
                                        {uiConfig?.['approval_details'] || "Approval Details"}
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiConfig?.['mode_of_application'] || "Mode of Application"}</h4>
                                            <p className="text-[#5A7EC7]">{selectedApproval.mode_of_application}</p>
                                        </div>
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiConfig?.['stage'] || "Stage"}</h4>
                                            <p className="text-[#5A7EC7]">{selectedApproval.stage}</p>
                                        </div>
                                        {/* <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiConfig?.['land_type'] || "Land Type"}</h4> 
                                            <p className="text-[#5A7EC7]">{selectedApproval.land_type}</p>
                                        </div>
                                        <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                            <h4 className="font-medium text-[#2C53A3] mb-2">{uiConfig?.['project_location'] || "Project Location"}</h4> 
                                            <p className="text-[#5A7EC7]">{selectedApproval.business_location}</p>
                                        </div> */}
                                    </div>
                                </div>

                                {selectedApproval.details !== "No description available" && (
                                    <div className="mb-8">
                                        <h3 className="text-lg font-semibold text-black mb-3 flex items-center">
                                            <AdditionalDetailIcon strokeWidth={2} size={24} className="mr-2 text-[#7AA6DA]" />
                                            {uiConfig?.['approval_description'] || "Description"}
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
                                    <h3 className="text-lg font-semibold text-black mb-3 flex items-center">
                                        <InfoIcon strokeWidth={1} className="mr-2 text-blue-700" />
                                        {uiConfig?.['additional_information'] || "Additional Information"}
                                    </h3>
                                    <div className="p-4 rounded-lg border border-[#B8D1F3] bg-gradient-to-r from-[#E6F0FA]/10 to-white">
                                        <p className="text-[#5A7EC7]">
                                            Approval ID: <span className="font-medium text-[#2C53A3]">{selectedApproval.approvalID}</span>
                                        </p>
                                        <p className="text-[#5A7EC7]/70 text-xs mt-2 flex items-center">
                                            <FaSync className="mr-1" />
                                         {uiConfig?.['data_source'] || 'Data fetched from government sources'}
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
