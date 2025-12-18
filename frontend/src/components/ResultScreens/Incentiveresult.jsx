import React, { useContext, useEffect, useRef, useState,useMemo } from "react";
import {  FaPlayCircle, FaStopCircle, FaArrowRight, FaClock, FaSync, FaCheckCircle, FaRunning } from 'react-icons/fa';
import Details from "../Details/Details";
import { HiMiniArrowPath } from "react-icons/hi2";
import Backtochat from "../Backtochat/Backtochat";
import DOMPurify from 'dompurify';
import "../ResultScreens/incentives.css"
import LogoLoader from "../Responseloader/LogoLoader";
import { useSelector } from "react-redux";
import { FrappeContext, useFrappeGetDoc, useFrappeUpdateDoc, useFrappeCreateDoc } from "frappe-react-sdk";
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import NoResultsFound from "../Failure/NoResultsFound";
import FailureScreen from "../Failure/FailureScreen";
import { AdditionalDetailIcon, BuildingIcon, ClipboardCheckIcon, DollarIcon, EligibilityIcon, FinancialSummaryIcon, IncentiveNameIcon, IncentiveTitleIcon, InfoIcon, ListCheckIcon, ScheduleIcon, SearchIcon, TriangleDownIcon, TriangleUpIcon } from "../../Icons/icon";

function Incentiveresult({ res, source, rerender }) {
  const { createDoc, isLoading, error } = useFrappeCreateDoc('');
    const lastChatId = useSelector((state) => state.chat.lastId);
  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Incentive")
  const configurations = uiData?.configurations || [];
  const uiConfig = configurations.reduce((acc, curr) => {
    acc[curr.key] = curr.value;
    return acc;
  }, {}); 

  const { data: adminToken } = useFrappeGetDoc("Mars Configurations", "admin_token")
  const ADMIN_TOKEN = adminToken?.admin_token
 
  const createDiagnostic = (errType, logMsg,chatId)=> {
      let log = ` ${logMsg}`
      createDoc("AIX Diagnostics Hub", {
      type: errType,
      note: log,
      chat_name: chatId
      });
  }

  function mapIncentivesToTypes(incentivesObj, typesObj,namesObj,scoreObj) {
  if(!incentivesObj || !typesObj) return []
    return Object.keys(incentivesObj).map(key => ({
        id: incentivesObj[key],
        name: namesObj[key],
        type: typesObj[key],  // Fallback in case type doesn't exist
        aggregated_score: scoreObj[key]
    }));
}

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
      // console.error("Error Storing Result json:", err);
      createDiagnostic("Land & Approvals", `Something went wrong while storing the result json ${JSON.stringify(err)} in Incentive screen`,lastChatId)
      return []; // Return empty for this batch on error
    }
  }

  let Analytics_response = rerender!==1 ?  res['Analytics_response'] : {}
  if ((
    typeof Analytics_response !== 'object' || 
    Analytics_response === null || 
    typeof Analytics_response === 'string') && rerender!== 1
  ) {
    // createDiagnostic("Data Error", `Invalid Data was passed that couldn't be rendered due to ${Analytics_response} in Incentives`,lastChatId)
    return <NoResultsFound diagnostics={true} type='Incentive' chatId={lastChatId} data={Analytics_response} module='Incentives'/>;
  }
  const result = rerender!==1 ?  JSON.parse(Analytics_response["Incentive Data"]) : {}
  // console.log(result)
  
  const { call } = useContext(FrappeContext)
  const [tempFailure, setTempFailure] = useState(false)
  const [someError, setSomeError] = useState(false)
  const [fetchedIncentive, setFetchedIncentive] = useState([]);
  const [selectedIncentive, setSelectedIncentive] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [incentives, setIncentives] = useState([]);
  const [loading, setLoading] = useState(true);
  const { updateDoc } = useFrappeUpdateDoc()
  const [activeContext, setActiveContext] = useState()
  const [incentivesMap, setIncentivesMap] = useState([])
  const [showFull, setShowFull] = useState(false);
  const [testJson, setTestJson] = useState({
    "Small": "## Incentives under Gujarat Industrial Policy 2020 for Small Businesses\n### Core Benefit Overview\nThe incentive provides assistance to Micro, Small, and Medium Enterprises (MSEs) for sheds developed by private developers. It offers a proportional benefit of **15%** of the total cost of land, building, other infrastructure facilities, Technical Consultancy fees, and TPQA charges.\n\n### Illustrative Financial Details\nAssuming a total investment of **\u20b95,00,00,000**, the benefit calculation is as follows:\n- Total Investment: **\u20b95,00,00,000**\n- Benefit: **15%** of **\u20b95,00,00,000** = **\u20b975,00,000**\n- Net Cost: **\u20b95,00,00,000** - **\u20b975,00,000** = **\u20b94,25,00,000**\n\n### Key Financial Insights\n- The benefit is calculated as **15%** of the total investment in eligible costs.\n- There is no explicit cap mentioned for this benefit.\n- This incentive is particularly beneficial for small businesses as it provides significant support for infrastructure development, reducing the net investment burden.\n\n### Conclusion\nThis incentive is highly beneficial for small businesses under the Gujarat Industrial Policy 2020, as it provides substantial financial assistance for infrastructure development, thereby reducing the overall investment burden and fostering business growth.",
    "Medium": "## Incentives under Gujarat Industrial Policy 2020 - Medium Scale\n### Core Benefit Overview\nThe incentive provides assistance to Medium Scale Enterprises (MSEs) for infrastructure development, specifically supporting costs related to land, building, other infrastructure facilities, technical consultancy fees, and TPQA charges. The support is structured as a proportional benefit, offering up to **15%** of the total investment in these areas.\n\n### Illustrative Financial Details\nFor a medium-scale investment of **\u20b930,00,00,000**, the benefit calculation is as follows:\n- Total Investment: **\u20b930,00,00,000**\n- Benefit: **15%** of **\u20b930,00,00,000** = **\u20b94,50,00,000**\n- Net Cost: **\u20b930,00,00,000** - **\u20b94,50,00,000** = **\u20b925,50,00,000**\n\nThis results in a significant reduction in the net cost of the project, making the investment more feasible for MSEs.\n\n### Key Financial Insights\n* The benefit is capped at **15%** of the total investment, ensuring alignment with the scale of the project.\n* The incentive is particularly advantageous for medium-scale businesses, as it provides a substantial proportion of the total investment cost, thereby reducing the financial burden on the enterprise.\n\n### Conclusion\nThe incentive under the Gujarat Industrial Policy 2020 is highly beneficial for medium-scale enterprises, offering significant financial support for infrastructure development. This makes it an attractive option for businesses looking to expand or establish their operations in the state."
  })



 
//    if (typeof result === 'object' && result !== null) {
 
//     console.log('All good')
//   // safely use `essential` here
//   } else {
//     let msg = result;
//     console.log(msg, 'Setting the result fail...')
//     setTempFailure(true)
//     // fallback or ignore
// }
// const analytics_response = result['Analytics_response']

  // const incentivesMap = mapIncentivesToTypes(result['Incentive ID'], result['Incentive Type'], result['Incentive Name'])
  // useEffect(() => {
  //   const initializeFirstIncentive = async () => {
  //     if (incentivesMap && loading && incentivesMap.length > 0) {
  //       if (lastChatId) {
  //         if (source !== "FromScratch") {
  //           const updatedResult = {
  //             ...incentivesMap,
  //             "no_of_incentives": incentivesMap?.length
  //           }
  //           if(!isResultStored) {
  //             await storeResultData(lastChatId, incentivesMap, 'Query to search Incentives')
  //           }
  //           setIsResultStored(true)
  //           console.log('Storedd...')
  //         } 
  //       }
  //       await handleIncentiveSelection(incentivesMap[0].id);
  //       setLoading(false);
  //     }
  //   };

  //   initializeFirstIncentive();
  // }, [incentivesMap]); 


const handleIncentiveSelection = async (incentiveName) => {
  // console.log(incentiveName, 'this is the incentive');

  // 1️⃣ Check if we already have this incentive cached
  const existingIncentive = fetchedIncentive.find(
    (item) => item.id === incentiveName
  );

  if (existingIncentive) {
    // console.log('Using cached incentive:', existingIncentive);
    setSelectedIncentive(existingIncentive);
    setLoading(false)
    return; // ✅ Skip API call
  }

  // If not cached, fetch it from API
  let fetchedIncentives = [];
  let fetchedIndustryIncentives = [];

  const filters = JSON.stringify([["name", "=", incentiveName]]);
  const fields = JSON.stringify(["*"]);

  // -------------------------
  // API CALL 1: Incentive Industry Mapping
  // -------------------------
  const url = `/api/resource/Incentive Industry Mapping?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `token ${ADMIN_TOKEN}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.ok) {
    const data = await response.json();
    if (data.data?.length > 0) {
      const incentive = data.data[0];
      fetchedIndustryIncentives.push({
        incentive_name: incentive.incentive,
        state_level: incentive.state_level,
        country_level: incentive.country_level,
        city_level: incentive.city_level,
      });
    }
  }

  // -------------------------
  // API CALL 2: Incentive Details
  // -------------------------
  const url2 = `/api/resource/Incentive?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;
  const response2 = await fetch(url2, {
    method: 'GET',
    headers: {
      'Authorization': `token ${ADMIN_TOKEN}`,
      'Content-Type': 'application/json'
    }
  });

  if (response2.ok) {
    const data = await response2.json();
    if (data.data?.length > 0) {
      const incentive = data.data[0];
      let parsedContext = safeJsonParse(incentive.contextual_analysis);

      fetchedIncentives.push({
        id: incentive.name,
        name: incentive.incentive_name,
        type: incentive.incentive_type || "N/A",
        quantum_of_assistance: incentive.quantum_of_assistance,
        description: incentive.description,
        incentive_rank: incentive.incentive_rank || "N/A",
        contextual_analysis: parsedContext?.final_markdown || '',
        startDate: incentive.incentive_operation_start_date || "N/A",
        endDate: incentive.incentive_operation_end_date || "N/A",
        status: getProgramStatus(incentive.incentive_operation_start_date, incentive.incentive_operation_end_date),
        category_description: JSON.parse(incentive.category_description) || {}
      });
    }
  }

  // -------------------------
  // Merge industry data and compute level
  // -------------------------
  fetchedIncentives = fetchedIncentives.map(incentive => {
    const matchingIndustry = fetchedIndustryIncentives.find(
      industry => industry.incentive_name === incentive.id
    );
    if (matchingIndustry) {
      let tempLevel = getLocationLevel(
        matchingIndustry.city_level,
        matchingIndustry.state_level,
        matchingIndustry.country_level
      );
      return {
        ...incentive,
        level: tempLevel,
      };
    }
    return incentive;
  });

  // 2️⃣ Add the newly fetched incentive to cache
  setFetchedIncentive((prev) => [...prev, ...fetchedIncentives]);

  // 3️⃣ Set as selected
  setSelectedIncentive(fetchedIncentives[0]);
  setLoading(false)
  // console.log(fetchedIncentives, 'This is what we need to set now');
};


 useEffect(() => {
  const checkData = async()=> {
    try {
        if (rerender === 1 || source==='FromScratch') {
        let tempResult = res?.['result'] ? res.result : res
        // setIncentives(tempResult)
        setIncentivesMap(tempResult)
        await handleIncentiveSelection(tempResult[0].id)
        setLoading(false);
      }
      else {
        fetchIncentives()
      }
      // else {
      //   fetchIncentivesDetails();
      // }
    }
    catch(err) {
      createDiagnostic("Incentive", `Something went wrong while rendering the data. Rerender = ${JSON.stringify(rerender)}, Source = ${JSON.stringify(source)}  ${JSON.stringify(err)} in Incentives`, lastChatId)
      setSomeError(true)
    }
  }
  checkData()
  }, [res]);

  const fetchIncentives = async()=>{
    if (!result || !result["Incentive ID"]) {
        setIncentives([]);
        setTempFailure(true)
        setLoading(false);
        return;
    }
    let incentiveData = mapIncentivesToTypes(result['Incentive ID'], result['Incentive Type'], result['Incentive Name'],result["aggregated_score"])
    // setLoading(false);
    setIncentivesMap(incentiveData)
    handleIncentiveSelection(incentiveData[0].id)
    if (lastChatId) {
      if (source !== "FromScratch") {
        const updatedResult = {
          ...incentiveData,
          "no_of_incentives": incentiveData?.length
        }
        await storeResultData(lastChatId, incentiveData, 'Query to search Incentives')
      } 
    }
    
    
  }



  function safeJsonParse(input) {
  try {
    if (typeof input === 'object') return input; // already parsed
    return JSON.parse(input);
  } catch (e) {
    // console.error("❌ JSON parse error:", e.message);
    // console.warn("Raw input:", input);
    return {};
  }
}

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
  const fetchIncentivesDetails = async () => {

    try {
      if (!result || !result["Incentive ID"]) {
        setIncentives([]);
        setTempFailure(true)
        setLoading(false);
        return;
      }
      const incentiveIds = Object.values(result["Incentive ID"]);

      let fetchedIncentives = [];
      let fetchedIndustryIncentives= []

      for(const[index,id] of incentiveIds.entries()) {
        const filters = JSON.stringify([["name", "=", id]]);
        const fields = JSON.stringify(["*"]);

        const url = `/api/resource/Incentive Industry Mapping?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `token ${ADMIN_TOKEN}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.data && data.data.length > 0) {
            const incentive = data.data[0];
            fetchedIndustryIncentives.push({
              incentive_name: incentive.incentive,
              state_level: incentive.state_level,
              country_level: incentive.country_level,
              city_level: incentive.city_level,
            });
          }
        }
      }
      for (const [index, id] of incentiveIds.entries()) {
        const filters = JSON.stringify([["name", "=", id]]);
        const fields = JSON.stringify(["*"]);

        const url = `/api/resource/Incentive?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `token ${ADMIN_TOKEN}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          
          const data = await response.json();
          if (data.data && data.data.length > 0) {
            
            const incentive = data.data[0];
            
            let parsedContext = safeJsonParse(incentive.contextual_analysis);

            fetchedIncentives.push({
              id: incentive.name,
              name: incentive.incentive_name,
              type: incentive.incentive_type || "N/A",
              quantum_of_assistance: incentive.quantum_of_assistance,
              description: incentive.description,
              // rank: result["Incentive Rank"]?.[index] ?? "N/A",
              incentive_rank: incentive.incentive_rank || "N/A",              
              contextual_analysis: parsedContext?.final_markdown || '',
              // contextual_analysis: JSON.parse(incentive.contextual_analysis)?.["final_markdown"] || '',
              aggregated_score: result?.["aggregated_score"]?.[index] ?? 0,
              startDate: incentive.incentive_operation_start_date || "N/A",
              endDate: incentive.incentive_operation_end_date || "N/A",
              status: getProgramStatus(incentive.incentive_operation_start_date, incentive.incentive_operation_end_date),
              // level: result["Level"]?.[index] ?? "N/A",
              category_description: JSON.parse(incentive.category_description) || {}
            });
          }
        }
      }
      fetchedIncentives = fetchedIncentives.map(incentive => {
      const matchingIndustry = fetchedIndustryIncentives.find(
        industry => industry.incentive_name === incentive.id
      );
     

      if (matchingIndustry) {
        let tempLevel = getLocationLevel(matchingIndustry.city_level, matchingIndustry.state_level, matchingIndustry.country_level)
        return {
          ...incentive,
          level: tempLevel,
        };
      }

      return incentive; // No match, keep as is
    });

      setIncentives(fetchedIncentives);

      setSelectedIncentive(fetchedIncentives.length > 0 ? fetchedIncentives[0] : null);
      setLoading(false);

      if (lastChatId) {
        if (source !== "FromScratch") {
          const updatedResult = {
            ...fetchedIncentives,
            "no_of_incentives": fetchedIncentives?.length
          }
          await storeResultData(lastChatId, fetchedIncentives, 'Query to search Incentives')
        } 
      }

    } catch (error) {
      // console.error("Error fetching incentives:", error);
      createDiagnostic("Incentive", `API call failed to get response due to  ${JSON.stringify(error)} in Incentives`, lastChatId)
      setSomeError(true)
      setLoading(false);
    }
  };
  
  // useEffect(()=>{
  //   if(incentives.length>0) {
  //     setSelectedIncentive(incentives[0])
  //   }
  // },[incentives])

 

  const displayedIncentives = incentivesMap?.filter(
    (incentive) =>
      incentive.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incentive.type?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    const checkSearch = async()=>{
      if (searchQuery === "") {
        incentivesMap.length > 0 ? await handleIncentiveSelection(incentivesMap[0].id) : null
      } else {
        setSelectedIncentive(displayedIncentives.length > 0 ? displayedIncentives[0] : null);
      }
    }
    checkSearch()
  }, [searchQuery]);

  const formatDate = (dateString) => {
    if (!dateString || dateString === "N/A") return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateDuration = (startDate, endDate) => {
    if (startDate === "N/A" || endDate === "N/A") return "N/A";

    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 30) return `${diffDays} days`;
    if (diffDays < 365) return `${Math.round(diffDays / 30)} months`;
    return `${Math.round(diffDays / 365)} years`;
  };

  const getProgramStatusIcon = (startDate, endDate) => {
    const now = new Date();
    const start = new Date(startDate);
    const end = new Date(endDate);

    if (now < start) return <FaClock className="text-yellow-500 mr-1" />;
    if (now >= start && now <= end) return <FaRunning className="text-green-500 mr-1" />;
    return <FaCheckCircle className="text-gray-500 mr-1" />;
  };

  const getProgramStatus = (startDate, endDate) => {
    if (startDate === "N/A" || endDate === "N/A") return "Status unavailable";

    const today = new Date();
    const start = new Date(startDate);
    const end = new Date(endDate);

    if (today < start) return "Upcoming";
    if (today > end) return "Closed";
    return "Active";
  };

  const containerRef = useRef(null)
  const contextualRef = useRef(null)

  // const [fetchedIncentive, setFetchedIncentive] = useState([])
  // const handleIncentiveSelection = async(incentive)=> {
  //   console.log(incentive, 'this is the incentive')
  //   let fetchedIncentives = []
  //   let fetchedIndustryIncentives = []
  //   const filters = JSON.stringify([["name", "=", incentive]]);
  //   const fields = JSON.stringify(["*"]);
    
  //   const url = `/api/resource/Incentive Industry Mapping?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;
  //   const response = await fetch(url, {
  //     method: 'GET',
  //     headers: {
  //       'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
  //       'Content-Type': 'application/json'
  //     }
  //   });
  //   if (response.ok) {
  //     const data = await response.json();
  //     if (data.data && data.data.length > 0) {
  //       const incentive = data.data[0];
  //       fetchedIndustryIncentives.push({
  //         incentive_name: incentive.incentive,
  //         state_level: incentive.state_level,
  //         country_level: incentive.country_level,
  //         city_level: incentive.city_level,
  //       });
  //     }
  //   }

  //   const url2 = `/api/resource/Incentive?fields=${encodeURIComponent(fields)}&filters=${encodeURIComponent(filters)}`;
  //   const response2 = await fetch(url2, {
  //     method: 'GET',
  //     headers: {
  //       'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
  //       'Content-Type': 'application/json'
  //     }
  //   });

  //   if (response2.ok) {
  //     const data = await response2.json();
  //     if (data.data && data.data.length > 0) {
        
  //       const incentive = data.data[0];
        
  //       let parsedContext = safeJsonParse(incentive.contextual_analysis);

  //       fetchedIncentives.push({
  //         id: incentive.name,
  //         name: incentive.incentive_name,
  //         type: incentive.incentive_type || "N/A",
  //         quantum_of_assistance: incentive.quantum_of_assistance,
  //         description: incentive.description,
  //         // rank: result["Incentive Rank"]?.[index] ?? "N/A",
  //         incentive_rank: incentive.incentive_rank || "N/A",              
  //         contextual_analysis: parsedContext?.final_markdown || '',
  //         // contextual_analysis: JSON.parse(incentive.contextual_analysis)?.["final_markdown"] || '',
  //         // aggregated_score: result?.["aggregated_score"]?.[index] ?? 0,
  //         startDate: incentive.incentive_operation_start_date || "N/A",
  //         endDate: incentive.incentive_operation_end_date || "N/A",
  //         status: getProgramStatus(incentive.incentive_operation_start_date, incentive.incentive_operation_end_date),
  //         // level: result["Level"]?.[index] ?? "N/A",
  //         category_description: JSON.parse(incentive.category_description) || {}
  //       });
  //     }
  //   }
  //   fetchedIncentives = fetchedIncentives.map(incentive => {
  //       const matchingIndustry = fetchedIndustryIncentives.find(
  //         industry => industry.incentive_name === incentive.id
  //       );
  //       if (matchingIndustry) {
  //         let tempLevel = getLocationLevel(matchingIndustry.city_level, matchingIndustry.state_level, matchingIndustry.country_level)
  //         return {
  //           ...incentive,
  //           level: tempLevel,
  //         };
  //       }

  //     return incentive; // No match, keep as is
  //   });
  //   setSelectedIncentive(fetchedIncentives[0])
  //   console.log(fetchedIncentives, 'This is what we need to set now')
  // }
  


  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
    if (selectedIncentive?.contextual_analysis) {
    const keys = Object.keys(selectedIncentive.contextual_analysis);
    setActiveContext(keys.includes("Default") ? "Default" : keys[0]);
  }

  if(showFull) {
    setShowFull(false)
  }
  }, [selectedIncentive])

  useEffect(() => {
    if (contextualRef.current) {
      contextualRef.current.scrollTop = 0;
    }
  }, [showFull, activeContext])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen w-screen">
        <LogoLoader text="Just a Moment - Mapping the Money-Savers" />
      </div>
    );
  }

  if(tempFailure) {
    return (
      <NoResultsFound />
    )
  }
  if(someError) {
    return(
      <FailureScreen />
    )
  }

  const getIconForCategory = (category) => {
    switch (category) {
      case 'Eligibility':
        return <EligibilityIcon strokeWidth={2} size={24} className="text-blue-700" />;
      case 'Benefits':
        return <DollarIcon strokeWidth={2} size={24} className="text-blue-700" />;
      case 'Process':
        return <HiMiniArrowPath className="text-blue-700" />;
      case 'Requirements':
        return <ListCheckIcon className="text-blue-700" />;
      default:
        return <InfoIcon strokeWidth={1} className="text-blue-700" />;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655]">
      <div className="w-[98%] h-[95%] mx-auto my-0 p-4 rounded-xl shadow-lg flex flex-col bg-white backdrop-blur-sm border border-white border-opacity-40">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#B8D1F3]">
          <div className="flex items-center">
            <div className="p-3 mr-4 rounded-lg h-12 w-12 flex items-center justify-center bg-gradient-to-r from-[#FF80AB] to-[#9575CD] text-white">
              <IncentiveTitleIcon className="h-full w-full relative" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-[#2C53A3]">{uiConfig?.['main_title'] || "Incentives Catalog"}</h1>
              <p className="text-[#5A7EC7]">{uiConfig?.['sub_title'] || "Browse available incentive programs"}</p>
            </div>
          </div>

          {source === 'SolutionScreen' && rerender!==1 && (
            <Backtochat text='Back to Chat' />
          )}
        </div>

        {/* Search Bar */}
        <div className="relative mb-2">
          <SearchIcon strokeWidth={2} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5A7EC7]" />
          <input
            type="text"
            placeholder="Search by program name or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-12 pr-4 py-2 w-full rounded-lg focus:outline-none focus:ring-2 placeholder-[#9CB3D9] border border-[#B8D1F3] bg-white bg-opacity-90 text-[#2C53A3] focus:ring-[#FF80AB]"
          />
        </div>

        {/* Main Content Area */}
        <div className="flex flex-1 min-h-0 overflow-hidden rounded-lg border border-[#B8D1F3] bg-white bg-opacity-90">
          {/* Incentive List - Scrollable */}
          <div className="w-1/3 border-r border-[#B8D1F3] flex flex-col">
            <div className="overflow-y-auto flex-1 list-view p-2 bg-gradient-to-b from-[#E6F0FA]/20 to-transparent">
              {incentivesMap.length > 0 ? (
                <div className="space-y-2">
                  {incentivesMap.map((incentive) => (
                    <div
                      key={incentive.id}
                      className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${selectedIncentive?.id === incentive.id
                        ? "bg-[#41b655] bg-opacity-20 border-l-4 border-[#41b655] "
                        : "bg-[#41b655] bg-opacity-10 border-none"
                        }`}

                      // onClick={() => setSelectedIncentive(incentive)}
                      onClick={() => {handleIncentiveSelection(incentive.id)}}
                    >
                      <div className="flex justify-between items-start">
                        <h3 className={`font-medium ${selectedIncentive?.id === incentive.id ? "text-black" : "text-[#3b69c5]"}`}>
                          {incentive.type}
                        </h3>
                      </div>
                      <div className="flex items-center mt-2 text-sm text-[#5A7EC7]">
                        <BuildingIcon size={18} className="mr-2 text-[#5A7EC7]" />
                        <span>{incentive.name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                  <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB] to-[#9575CD] text-white">
                    <SearchIcon strokeWidth={2} className="text-2xl" />
                  </div>
                  <h3 className="text-lg font-medium text-[#2C53A3]">{uiConfig?.['no_program_found'] || "No programs found"}</h3>
                  <p className="text-[#5A7EC7]">Try a different search term</p>
                </div>
              )}
            </div>
          </div>

          {/* Detailed View - Scrollable Content */}
          {selectedIncentive && (
            <div className="w-2/3 flex flex-col">
              <div ref={containerRef} className="overflow-y-auto flex-1 p-6">
                <div className="mb-8">
                  <div className="flex items-center mb-4">
                           <div className="p-2 mr-3 h-12 w-12 flex items-center justify-center rounded-lg bg-blue-100">
                      <IncentiveNameIcon className="h-full w-full relative" />
                    </div>
                    <h2 className="text-2xl font-semibold text-[#2C53A3]">{selectedIncentive.type}</h2>
                  </div>

                  <div className="flex flex-wrap gap-3 mb-6">
                    <span className="px-3 py-1 text-sm rounded-full flex items-center text-white bg-[#7AA6DA]">
                      {/* <FaTag className="mr-1" /> {selectedIncentive.name} */}
                      {selectedIncentive.name}
                    </span>
                    {/* <span className="px-3 py-1 text-sm rounded-full flex items-center text-white bg-[#FF80AB]">
                  <FaLayerGroup className="mr-1" /> {selectedIncentive.level}
                </span> */}
                    {/* <span className="px-3 py-1 text-sm rounded-full flex items-center text-white bg-gradient-to-r from-[#81C784] to-[#4CAF50]">
                  <FaStar className="mr-1" /> Score: {selectedIncentive.aggregated_score.toFixed(1)}
                </span> */}
                  </div>
                </div>

                {/* Key Dates - Improved Date Display */}
                <div className="mb-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      {/* text-[#2C53A3] */}
                      <h3 className="text-lg font-semibold mb-3 flex items-center  text-black">
                        <ScheduleIcon strokeWidth={2} className="mr-2 text-blue-700" />
                       {uiConfig?.['program_period'] || "Program Period"}
                      </h3>
                      <div className="p-4 rounded-lg border border-[#B8D1F3]" style={{
                        background: 'linear-gradient(to right, rgba(184, 209, 243, 0.1), rgba(255, 255, 255, 0.9))'
                      }}>
                        <div className="font-medium flex items-center text-[#2C53A3]">
                          <FaPlayCircle className="mr-2 text-[#81C784]" />
                          {formatDate(selectedIncentive.startDate)}
                          <FaArrowRight className="mx-2 text-[#9575CD]" />
                          <FaStopCircle className="mr-2 text-[#FF80AB]" />
                          {formatDate(selectedIncentive.endDate)}
                        </div>
                        {selectedIncentive.startDate !== "N/A" && selectedIncentive.endDate !== "N/A" && (
                          <div className="text-xs mt-1 flex items-center text-[#5A7EC7]">
                            <FaClock className="mr-1" />
                            Duration: {calculateDuration(selectedIncentive.startDate, selectedIncentive.endDate)}
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center text-black">
                        <ClipboardCheckIcon strokeWidth={2} className="mr-2 text-blue-700" />
                        {uiConfig?.['program_status'] || "Program Status"}
                      </h3>
                      <div className="p-4 rounded-lg border border-[#B8D1F3]" style={{
                        background: 'linear-gradient(to right, rgba(255, 128, 171, 0.08), rgba(255, 255, 255, 0.9))'
                      }}>
                        <div className="font-medium flex items-center text-[#2C53A3]">
                          {getProgramStatusIcon(selectedIncentive.startDate, selectedIncentive.endDate)}
                          <span className="ml-2">
                            {getProgramStatus(selectedIncentive.startDate, selectedIncentive.endDate)}
                          </span>
                        </div>
                        <div className="text-xs mt-1 flex items-center text-[#5A7EC7]">
                          <FaSync className="mr-1" />
                          Last updated: {formatDate(new Date().toISOString())}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Additional Details Section */}
                {selectedIncentive.quantum_of_assistance !== "N/A" && selectedIncentive.quantum_of_assistance && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold mb-3 flex items-center text-black">
                      <AdditionalDetailIcon strokeWidth={2} size={24} className="mr-2 text-blue-700" />
                      {uiConfig?.['additional_details'] || "Additional Details"}
                    </h3>
                    <div className="p-4 rounded-lg border border-[#B8D1F3]" style={{
                      background: 'linear-gradient(to right, rgba(129, 199, 132, 0.1), rgba(255, 255, 255, 0.9))'
                    }}>
                      <div
                        className="prose max-w-none text-[#2C53A3]"
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(selectedIncentive.quantum_of_assistance),
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Features Grid */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold mb-4 flex items-center text-black">
                    <InfoIcon strokeWidth={1} className="mr-2 text-blue-700" />
                    {uiConfig?.['program_details'] || "Program Details"}
                  </h3>

                  {selectedIncentive.category_description && Object.keys(selectedIncentive.category_description).length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(selectedIncentive.category_description).map(([key, value]) => (
                        <div key={key} className="p-4 rounded-lg border border-[#B8D1F3]" style={{
                          background: 'linear-gradient(to right, rgba(149, 117, 205, 0.08), rgba(255, 255, 255, 0.9))'
                        }}>
                          <h3 className="text-lg font-semibold mb-3 flex items-center text-black">
                            {getIconForCategory(key)}
                            <span className="ml-2">{key}</span>
                          </h3>
                          {Array.isArray(value) ? (
                            <ul className="space-y-2">
                              {value.map((item, index) => (
                                <li key={index} className="flex flex-row gap-2 items-start justify-start text-md">
                                  <span className=" rounded-full h-2 w-2  relative top-2 bg-blue-700 flex-shrink-0"></span>
                                  <span className="text-[#2C53A3]">{item}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div className="text-[#2C53A3]">{value}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg border border-[#B8D1F3] flex items-center text-[#5A7EC7]" style={{
                      background: 'linear-gradient(to right, rgba(184, 209, 243, 0.1), rgba(255, 255, 255, 0.9))'
                    }}>
                      <InfoIcon strokeWidth={1} className="mr-2" />
                      {uiConfig?.['no_additional_details_available'] || "No additional details available"}
                    </div>
                  )}
                </div>

                <div className={`relative max-w-full ${showFull ? 'h-[80vh]' : 'h-[60vh]'} border border-gray-200 rounded-lg shadow-lg flex flex-col overflow-hidden`}>

                  {/* Sticky Header */}
                  <div className="sticky top-0 z-10 bg-white flex flex-col gap-2 p-4 border-b border-gray-200 shadow-sm  h-fit flex-shrink-0">
                    <h2 className="text-lg font-semibold text-black gap-2 flex flex-row items-center"> <span className="relative h-7 w-7 flex"><FinancialSummaryIcon className='text-blue-700 mr-2 h-full w-full' /></span>{uiConfig?.['financial_benefit_summary'] || "Financial Benefit Summary"}</h2>

                    <div className="flex gap-4 overflow-x-auto h-fit">
                      {selectedIncentive.contextual_analysis &&
                        Object.entries(selectedIncentive.contextual_analysis).map(([key]) => {
                          if (key === 'Default') return null; // 👈 Hide "Default" button

                          return (
                            <div key={key} className="flex flex-col items-center min-w-fit">
                              <button
                                className={`text-base font-medium ${
                                  activeContext === key ? 'text-blue-600' : 'text-gray-600 hover:text-gray-800'
                                }`}
                                onClick={() => setActiveContext(key)}
                              >
                                {key}
                              </button>
                              <div
                                className={`${
                                  activeContext === key ? 'w-full' : 'w-0'
                                } h-0.5 bg-blue-500 rounded-full transition-all duration-300`}
                              ></div>
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Scrollable Content Area */}
                  <div ref={contextualRef} className={`flex-grow px-6 py-4 ${showFull ? 'overflow-y-auto' : 'overflow-hidden'}`}>
                    {selectedIncentive.contextual_analysis && Object.entries(selectedIncentive.contextual_analysis)
                      .filter(([key]) => key === activeContext)
                      .map(([key, value]) => (
                        <div key={key} className="prose max-w-none pb-8">
                          <ReactMarkdown
                            rehypePlugins={[rehypeRaw]}
                            remarkPlugins={[remarkBreaks, remarkGfm]}
                            components={{
                              h2: ({node, ...props}) => <h2 className="text-base font-bold text-gray-800 mt-3 mb-2 pb-1" {...props} />,
                              h3: ({node, ...props}) => <h3 className="text-md font-semibold text-gray-700 mt-3 mb-2" {...props} />,
                              p: ({node, ...props}) => <p className="text-gray-700 mb-2 text-sm" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-semibold text-sm text-gray-900" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />,
                              ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-1" {...props} />,
                              li: ({node, ...props}) => <li className="text-gray-700 text-sm mb-1" {...props} />,
                            }}
                          >
                            {value || testJson['Medium']}
                          </ReactMarkdown>
                        </div>
                      ))}
                  </div>

                  {/* Sticky Footer */}
                  <div className="sticky bottom-0 bg-white border-t border-gray-200 p-3 flex justify-center h-[60px] flex-shrink-0">
                    <button
                      onClick={() => setShowFull(!showFull)}
                      className="flex flex-row items-center gap-2 text-blue-600 font-medium hover:text-blue-800 transition-colors px-4 py-1 rounded-full hover:bg-blue-50"
                    >
                      {showFull ? 'Show Less' : 'Show More '} {showFull ? (<TriangleUpIcon size={8} />) : (<TriangleDownIcon size={8} />)}
                    </button>
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

export default Incentiveresult;