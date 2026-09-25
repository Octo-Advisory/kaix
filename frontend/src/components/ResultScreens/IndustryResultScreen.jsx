import React, { useEffect, useRef, useState, useContext, useTransition } from 'react';
import { Chart } from 'chart.js/auto';
import './Industryresult.css'
import {
  FaRegQuestionCircle, FaRoad, FaTrain, FaPlane, FaChartLine, FaArrowRight, FaBus, 
} from 'react-icons/fa';
import { IoIosArrowForward } from 'react-icons/io';
import { ImHammer2 } from "react-icons/im";
import { RiShipFill } from "react-icons/ri";
import { BsCashCoin, BsCurrencyExchange, BsPatchCheckFill } from "react-icons/bs";
import { MdOfflineBolt } from "react-icons/md";
import { FaCircleXmark, FaTriangleExclamation } from 'react-icons/fa6';
import { FaXmark } from "react-icons/fa6";
import { FrappeContext, useFrappePostCall, useFrappeUpdateDoc,useFrappeCreateDoc, useFrappeAuth } from 'frappe-react-sdk';
import MapComponent from '../MapComponent/MapComponent';
import Backtochat from '../Backtochat/Backtochat';
import { useFrappeGetDoc } from 'frappe-react-sdk';
import { isPlain } from '@reduxjs/toolkit';
import Approvalresult from './Approvalresult';
import LogoLoader from '../Responseloader/LogoLoader';
import Incentiveresult from './Incentiveresult';
import Vendorresult from './Vendorresult';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import Comparison from '../Comparison/Comparison';
import FailureScreen from '../Failure/FailureScreen'
import Spider from '../Spider/Spider';
import { useSelector } from 'react-redux';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import { IoWifi } from 'react-icons/io5';
import MapBoxMap from '../MapComponent/MapBoxMap';
import SingleMap from '../MapComponent/SingleMap';
import NoResultsFound from '../Failure/NoResultsFound';
import { CiCoinInsert } from 'react-icons/ci';
import NewIndustryScreen from './Test/NewIndustryScreen';
import LogoIcon from '../../assets/New Symbol.png'
import LogoIcon2 from '../../assets/New MarsAIX White - Edited.png'
import FollowUpChat from '../FollowUp/FollowUpChat';


const IndustryResultScreen = ({ result, source, rerender }) => {
  const { createDoc } = useFrappeCreateDoc('');
  const lastChatId = useSelector((state) => state.chat.lastId);
  const createDiagnostic = (errType, logMsg,chatId)=> {
      let log = ` ${logMsg}`
      createDoc("AIX Diagnostics Hub", {
      type: errType,
      note: log,
      chat_name: chatId
      });
  }

  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Build From Scratch")
  const configurations = uiData?.configurations || [];
  const uiConfig = configurations.reduce((acc, curr) => {
    acc[curr.key] = curr.value;
    return acc;
  }, {});

  const { data: adminToken } = useFrappeGetDoc("Mars Configurations", "admin_token")
  const ADMIN_TOKEN = adminToken?.admin_token

  const [showEssentialMaterials, setShowEssentialMaterials] = useState(true);

  const [activeTab, setActiveTab] = useState('Property Details')
  const { call } = useContext(FrappeContext);
  const [approvalsWindow, setApprovalWindow] = useState(false)
  const [approvalsToSend, setApprovalsToSend] = useState()
  const [incentivesWindow, setIncentivesWindow] = useState(false)
  const [incentivesToSend, setIncentivesToSend] = useState()
  const [vendorsWindow, setVendorsWindow] = useState(false)
  const [vendorsToSend, setVendorsToSend] = useState()
  const [marketAndLaws, setMarketAndLaws] = useState('Local Laws')
  const [showLocalLaws, setShowLocalLaws] = useState(true)
  const [showtaxes, setShowTaxes] = useState(false)
  const [showMarketTrends, setShowMarketTrends] = useState(false)
  const [someError, setSomeError] = useState(false)
  const [tempFailure, setTempFailure] = useState(false)
  const [SingleMapWindow, setSingleMapWindow] = useState(false) 
  const [activeButton, setActiveButton] = useState('Property Details')
  const [isLoading, setIsLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState()
  const [solutions, setSolutions] = useState([])
 

  ChartJS.register(ArcElement, Tooltip, Legend);

  const [visibleTooltips, setVisibleTooltips] = useState({
    tooltip1: false,
    tooltip2: false,
    tooltip3: false,
    tooltip4: false,
    tooltip5: false,
    tooltip6: false,
    tooltip7: false,
  });

  const handleMouseEnter = (id) => {
    setVisibleTooltips(prev => ({ ...prev, [id]: true }));
  };

  const handleMouseLeave = (id) => {
    setVisibleTooltips(prev => ({ ...prev, [id]: false }));
  };
  // console.log(result, 'first check')
  const analytics_response = source === "MapComponent" ? '' : result["Analytics_response"]

  if(source!== "MapComponent") {

    if (
      typeof analytics_response !== 'object' || 
      analytics_response === null || 
      typeof analytics_response === 'string'
    ) {
      // console.log('Invalid analytics_response:', analytics_response);
      // createDiagnostic("Data Error", `Invalid Data was passed that couldn't be rendered due to ${analytics_response} in Build From Scratch`,lastChatId)
      return <NoResultsFound diagnostics={true} type='Land & Approvals' chatId={lastChatId} data={analytics_response} module='Build From Scratch'/>;
    }
  }
  // if ((typeof analytics_response === 'object' && analytics_response !== null) || source === "MapComponent") {
  //   console.log('All good')
  // } else {
  //   let msg = analytics_response;
  //   console.log(msg, 'Setting the result fail...')
  //   setTempFailure(true)
  // }

  // This part is for showing the Query Title in the Solutions Screen 
  const aiResponse = useSelector((state) => state.ai.aiReponse);
  const industryTitle = aiResponse?.[aiResponse.length - 1]?.["state"]?.['Main-Industry']
  const tempIndustry = rerender !== 1 && source === 'SolutionScreen' ? industryTitle : analytics_response?.[0]?.industryTitle
  const titles = [
    `for your ${tempIndustry} industry setup`,
    `tailored to ${tempIndustry} industry needs`,
    `that fit your ${tempIndustry} industry vision`,
  ];
  const [randomTitle, setRandomTitle] = useState(null);
  useEffect(() => {
    if (tempIndustry) {
      const newTitle = titles[Math.floor(Math.random() * titles.length)].toLowerCase();
      setRandomTitle(newTitle);
    }
  }, [tempIndustry]);


  const fetchData = async (property) => {
    try {
      const response = await fetch(`/api/resource/Survey No?fields=["*"]&filters=[["name","=","${property}"]]&order_by=modified asc`, {
        method: 'GET',
        headers: {
          'Authorization': `token ${ADMIN_TOKEN}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`Error: ${response.statusText}`);
      const data = await response.json();
      return data.data
    } catch (error) {
      // console.error('Error fetching data:', error);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching Survey Data ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
      setSomeError(true)
    }
  }

  const fetchAreaName = async (area) => {
    try {
      const response = await fetch(`/api/resource/Area?fields=["area_name"]&filters=[["name","=","${area}"]]`, {
        method: 'GET',
        headers: {
          'Authorization': `token ${ADMIN_TOKEN}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error(`Error: ${response.statusText}`);
      const data = await response.json();
      return data.data[0]
    } catch (error) {
      // console.error('Error fetching data:', error);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching Area Name ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
      setSomeError(true)
    }
  }

  const getApprovals = async (approvalList) => {
    try {
      const results = [];
      for (const approval of approvalList) {
        const response = await fetch(
          `/api/resource/Licenses and Approvals Type?fields=["license_approval","business_location_type","description", "government_department","city_level", "state_level", "country_level", "mode_of_application", "delivery_schedule_in_working_days", "name", "stage","land_type"]&filters=${encodeURIComponent(JSON.stringify([["name", "=", approval]]))}&order_by=modified asc`,
          {
            method: 'GET',
            headers: {
              'Authorization': `token ${ADMIN_TOKEN}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) throw new Error(`Errorr: ${response.statusText}`);

        const data = await response.json();
        results.push(data.data[0]); // assuming it returns an array
      }

      return results;
    } catch (error) {
      // console.error('Error fetching data:', error);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching Approvals Data ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
      setSomeError(true)
      return [];
    }
  };

  const storeResultData = async (lastChat, solutions) => {
    if (!lastChat || !solutions) return

    try {

      const convertJson = await call.post("kaix.Management_Class.helpers.utility.convert_json_to_binary", {
        child_row_id: lastChat,
        updated_solutions: solutions,
        intension: "Query to build industry from Scratch" 
      },
      {
          headers: {
            'Expect': '' // 👈 Clear problematic header
          }
      }
    )
    
    } catch (err) {
      console.error("Error Storing Result json:", err);
      createDiagnostic("Land & Approvals", `Something went wrong while storing the result json ${JSON.stringify(err)} in Build From Scratch`,lastChatId)
      return []; // Return empty for this batch on error
    }
  }

  const getVendorData = async (doc, records) => {
    if (!records) return [];
    const uniqueRecords = [...new Set(records)];
    const BATCH_SIZE = 100; // Max 100 records per API call

    // Helper to call API for a batch
    const fetchBatch = async (batch) => {
      try {
        const result = await call.get("kaix.Management_Class.helpers.utility.get_docs_with_children", {
          doctype: doc,
          names: JSON.stringify(batch)
        });
        return result.message || [];
      } catch (err) {
        // console.error("Error fetching child records for batch:", err);
        createDiagnostic("Land & Approvals", `Something went wrong while fetching child records for batch  ${JSON.stringify(err)} in Build From Scratch`,lastChatId)
        return []; // Return empty for this batch on error
      }
    };

    try {
      if (uniqueRecords.length <= BATCH_SIZE) {
        // Normal flow for <= 100 records
        return await fetchBatch(uniqueRecords);
      } else {
        // Split records into batches of 100
        const batches = [];
        for (let i = 0; i < uniqueRecords.length; i += BATCH_SIZE) {
          const chunk = uniqueRecords.slice(i, i + BATCH_SIZE);
          batches.push(chunk);
        }

        // Call all batches in parallel
        const batchResults = await Promise.all(batches.map(fetchBatch));

        // Flatten results into a single array
        const mergedResults = batchResults.flat();

        return mergedResults;
      }
    } catch (err) {
      console.error("Error fetching child records:", err);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching child records  ${JSON.stringify(err)} in Build From Scratch`,lastChatId)
      return []; // Return empty array on failure
    }
  };

  const getAllVendorsData = async (vendorType, vendorList) => {
    try {
      // Handle empty cases
      if (!vendorList || (Array.isArray(vendorList) && vendorList.length === 0)) {
        return [];
      }

      // Handle string case
      if (typeof vendorList === "string") {
        return await getVendorData(vendorType, [vendorList]);
      }

      // Handle array case
      if (Array.isArray(vendorList)) {
        // First flatten the array in case some elements are arrays themselves
        const flatList = vendorList.flat();

        // Remove any empty/null/undefined values
        const cleanList = flatList.filter(v => v);

        if (cleanList.length === 0) return [];

        // Get all vendor data at once (more efficient than individual calls)
        return await getVendorData(vendorType, cleanList);
      }

      // If we get here, the input was invalid
      // console.warn("Invalid vendorList type:", typeof vendorList);
      return [];
    } catch (err) {
      // console.error("❌ Error in getAllVendorsData:", err);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching All Vendors Data ${JSON.stringify(err)} in Build From Scratch`,lastChatId)
      setSomeError(true)
      return [];
    }
  };
  const getIncentives = async (incentiveList) => {
    try {
      const results = [];

      for (const incentive of incentiveList) {
        const response = await fetch(
          `/api/resource/Incentive?fields=["incentive_name", "incentive_type","incentive_operation_start_date", "incentive_operation_end_date", "incentive_rank", "name","quantum_of_assistance", "description", "category_description", "contextual_analysis"]&filters=${encodeURIComponent(JSON.stringify([["name", "=", incentive]]))}&order_by=modified asc`,
          {
            method: 'GET',
            headers: {
              'Authorization': `token ${ADMIN_TOKEN}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) throw new Error(`Error: ${response.statusText}`);

        const data = await response.json();
        results.push(data.data[0]); // assuming response.data is an array with one object
      }

      return results;
    } catch (error) {
      // console.error('Error fetching incentives:', error);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching Incentives Data ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
      setSomeError(true)
      return [];
    }
  };
  const getIndustryIncentives = async (incentiveList) => {
    try {
      const results = [];

      for (const incentive of incentiveList) {
        const response = await fetch(
          `/api/resource/Incentive Industry Mapping?fields=["incentive","state_level", "city_level", "country_level"]&filters=${encodeURIComponent(JSON.stringify([["name", "=", incentive]]))}&order_by=modified asc`,
          {
            method: 'GET',
            headers: {
              'Authorization': `token ${ADMIN_TOKEN}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) throw new Error(`Error: ${response.statusText}`);

        const data = await response.json();
        results.push(data.data[0]); // assuming response.data is an array with one object
      }

      return results;
    } catch (error) {
      // console.error('Error fetching incentives:', error);
      createDiagnostic("Land & Approvals", `Something went wrong while fetching Industry Incentives Data ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
      setSomeError(true)
      return [];
    }
  };
  const findIndexByPropertyId = (propertyId, lookupDF) => {
    const entries = Object.entries(lookupDF["Property_ID"]);
    const found = entries.find(([idx, val]) => val === propertyId);
    return found ? Number(found[0]) : null; // returns index like "0", "1", etc.
  };
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
  const renameKey = (obj, oldKey, newKey) => {
    if (obj && oldKey in obj) {
      obj[newKey] = obj[oldKey];
      delete obj[oldKey];
    }
    return obj; // (Optional: return the modified object)
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

  function parseLegalText(rawText) {
    // Split into blocks starting with number.
    const parts = rawText.split(/(?=\d+\.)/g).filter(Boolean);

    return parts.map((block) => {
      // Normalize line breaks and trim
      const cleaned = block.replace(/\r/g, '').trim();

      // Try to match:
      const match = cleaned.match(/^(\d+)\.(.+?)(?:\s*[–-]\s*|\n)([\s\S]*)$/);

      if (match) {
        return {
          number: parseInt(match[1]),
          title: match[2].trim(),
          description: match[3].trim().replace(/\n+/g, ' ')  // remove extra newlines
        };
      }

      // Fallback: try to split by first line (title), rest (desc)
      const fallbackLines = cleaned.split('\n');
      if (fallbackLines.length >= 2) {
        const fallbackMatch = fallbackLines[0].match(/^(\d+)\.(.*)$/);
        if (fallbackMatch) {
          return {
            number: parseInt(fallbackMatch[1]),
            title: fallbackMatch[2].trim(),
            description: fallbackLines.slice(1).join(' ').trim()
          };
        }
      }

      return null; // Skip if nothing matched
    }).filter(Boolean);
  }

// const parseSuppliers = (supplierData) => {
//   console.log("Thsi is in parseSuuppliers", supplierData);
  
//     if (!supplierData?.vendor_id) return [];

//     // Create a Map to handle duplicates (last entry wins)
//     const vendorMap = new Map();

//     Object.keys(supplierData.vendor_id).forEach(key => {
//       const vendorId = supplierData.vendor_id[key];
//       const vendorData = {
//         supply_id: supplierData.supply_id?.[key],
//         Final_Score_With_Features: supplierData.Final_Score_With_Features?.[key],
//         vendor_id: vendorId,
//         // aggregated_score: supplierData.aggregated_score?.[key],
//         // Add all other properties dynamically
//         ...Object.fromEntries(
//           Object.entries(supplierData)
//             .filter(([k]) => !['vendor_id', 'supply_id', 'Final_Score_With_Features'].includes(k))
//             .map(([k, v]) => [k, v[key]])
//         )
//       };

//       // This will automatically override previous entries with same vendor_id
//       vendorMap.set(vendorId, vendorData);
//     });

//     return Array.from(vendorMap.values());
//   };

const parseSinglePropertySuppliers = (supplyIds, vendorIds) => {
  const vendorMap = new Map(); // Store vendors as keys and their associated supplies as values

  // For each supply in the given property
  supplyIds.forEach((supply, supplyIndex) => {
    // Handle vendor(s) for this supply index
    const currentVendors = vendorIds[supplyIndex];

    // If vendor(s) is an array, loop through each vendor
    if (Array.isArray(currentVendors)) {
      currentVendors.forEach(vendor => {
        // If vendor already exists in the map, add the supply_id to its best_supply
        if (vendorMap.has(vendor)) {
          vendorMap.get(vendor).best_supply.push(supply);
        } else {
          // If vendor doesn't exist, create a new entry with the current supply
          vendorMap.set(vendor, { vendor_id: vendor, best_supply: [supply] });
        }
      });
    } else if (typeof currentVendors === 'string') {
      // If vendor(s) is a single string, push it directly to the best_suppliers list
      if (vendorMap.has(currentVendors)) {
        vendorMap.get(currentVendors).best_supply.push(supply);
      } else {
        vendorMap.set(currentVendors, { vendor_id: currentVendors, best_supply: [supply] });
      }
    }
  });

  // Convert the map to an array and remove duplicates by using Set
  const result = Array.from(vendorMap.values()).map(vendor => {
    // Convert best_supply array to Set to remove duplicates and then back to an array
    vendor.best_supply = [...new Set(vendor.best_supply)];
    return vendor;
  });

  return result;
};
  
  const parseAllSupplies = (supplies) => {
    const allsupplies = []
    Object.keys(supplies.supply_id).forEach(key=> {
      const supply = supplies.supply_id[key]
      allsupplies.push(supply)
    })

    return allsupplies
  }
  function parseLegalOrTaxText(rawText) {
  // Normalize line breaks
  rawText = rawText.replace(/\r/g, "").trim();

  // First, split into blocks — either numbered sections or by line
  let parts;

  if (/^\d+\./m.test(rawText)) {
    // If it contains numbered items, split by number pattern
    parts = rawText.split(/(?=\d+\.)/g).filter(Boolean);
  } else {
    // Else split each entry into its own "block"
    parts = rawText.split(/\n+/).filter(Boolean);
  }

  return parts.map((block, index) => {
    const cleaned = block.trim().replace(/\s+/g, " ");

    // Match patterns like "1.Title – Description" or "Title – Description"
    const match = cleaned.match(/^(?:\d+\.)?\s*(.+?)\s*[–-]\s*(.+)$/);

    if (match) {
      return {
        number: /^\d+\./.test(cleaned)
          ? parseInt(cleaned.match(/^(\d+)\./)[1])
          : index + 1,
        title: match[1].trim(),
        description: match[2].trim()
      };
    }

    // Fallback: no dash found
    return {
      number: /^\d+\./.test(cleaned)
        ? parseInt(cleaned.match(/^(\d+)\./)[1])
        : index + 1,
      title: cleaned,
      description: ""
    };
  });
}

function mapVendorsToSupply(supplies, vendors) {
  // console.log(supplies, vendors, "This is in the function");
  let result = [];

  supplies.forEach((supply, index) => {
    const currentVendor = vendors[index];

    if (Array.isArray(currentVendor)) {
      // case: array of vendors
      currentVendor.forEach(vendor => {
        result.push({
          vendor_id: vendor,
          supply_id: supply
        });
      });
    } else if (typeof currentVendor === "string") {
      // case: single vendor string
      result.push({
        vendor_id: currentVendor,
        supply_id: supply
      });
    }
    // else do nothing (null/undefined)
  });

  return result;
}

const attachBestSuppliesToVendorData = (vendorData, parsedSuppliersData) => {
  // console.log(vendorData, parsedSuppliersData, 'Okay this is last second data');
  return vendorData.map(vendor => {
    // Find the supplier data with matching vendor_id
    const supplier = parsedSuppliersData.find(s => s.vendor_id === vendor.name);
    
    // If supplier exists, add best_supply to vendor data, else return the vendor as is
    // return supplier 
    //   ? { ...vendor, best_supply: supplier.best_supply, vendor_id: supplier.vendor_id, supply_id: supplier.supply_id }
    //   : vendor;
    return supplier 
  ? (() => {
      const { supplies,record_status, exclusion,business_type,certifications,creation,docstatus,idx,modified,modified_by,no_of_employees,no_of_location,no_of_past_clients,no_of_services,owner,years_of_experience,
google_cid, ...rest } = {
        ...vendor,
        best_supply: supplier.best_supply,
        vendor_id: supplier.vendor_id,
        supply_id: supplier.supply_id,
      };
      return rest;
    })()
  : (() => {
      const { supplies,record_status, exclusion,business_type,certifications,creation,docstatus,idx,modified,modified_by,no_of_employees,no_of_location,no_of_past_clients,no_of_services,owner,google_cid,years_of_experience
, ...rest } = vendor;
      return rest;
    })();

  });
};

const fallBackMarketTrend = `## **India’s Economy Sustains Strong Growth at ~6.5% Real GDP**

- Real GDP growth clocked in at **6.5%** for fiscal year 2024–25, making India the fastest-growing major economy. :contentReference[oaicite:1]{index=1}

- The economy's nominal GDP expanded by **9.9%** in the same period, with real GVA rising **6.4%**. :contentReference[oaicite:2]{index=2}

- Growth was underpinned by robust private consumption, improving private investment (with gross fixed capital formation rising), strong public capex, and resilient exports. :contentReference[oaicite:3]{index=3}
 
## **Inflation Moderates to Multi-Year Lows**

- Retail inflation averaged **~4.6%** in 2024–25—the lowest since 2018–19. :contentReference[oaicite:4]{index=4}

- In July 2025, inflation dropped sharply to **1.55%**, its lowest in eight years, driven mainly by falling food prices. :contentReference[oaicite:5]{index=5}

- Core inflation remained moderate (~4–4.1%), signaling maintained consumer demand. :contentReference[oaicite:6]{index=6}
 
## **Exports and Foreign Investment Surge**

- Total exports reached a record **USD 825 billion** in 2024–25, up **76%** over the past decade. Services exports alone grew to **USD 387 billion**—more than double since 2013–14. :contentReference[oaicite:7]{index=7}

- Cumulative FDI inflows exceeded **USD 1.05 trillion**, with equity inflows jumping **27%** in the first nine months of FY 25. :contentReference[oaicite:8]{index=8}

- Digital transactions grew nine-fold from FY18 to FY24, with UPI processing **172 billion transactions** in 2024. :contentReference[oaicite:9]{index=9}
 
## **Monetary Policy and Outlook**

- The RBI cut interest rates sharply—its largest cuts in five years—to lend support to growth; the target is an “aspirational” **7–8% growth**. :contentReference[oaicite:10]{index=10}

- The full year FY 2024–25 fiscal deficit was brought down to **4.8%** of GDP, with early FY 2025–26 indicators showing further improvement. :contentReference[oaicite:11]{index=11}

- OECD projects real GDP to grow at **6.3% in FY 2025–26** and **6.4% in FY 2026–27**, with inflation contained around **4%**. :contentReference[oaicite:12]{index=12}

- A Reuters poll similarly forecasts **6.4% growth** for FY 2025–26 and **6.7% in FY 2026–27**, with inflation averaging **3.6%**, rising to **4.3%** next year. :contentReference[oaicite:13]{index=13}
 
## **Risks: Trade Tensions and Currency**

- New U.S. tariffs on Indian goods—approaching **50%**—could dent GDP growth by approximately **0.6 percentage points**, threatening key sectors like textiles and jewelry. :contentReference[oaicite:14]{index=14}

- The rupee weakened, trading near **₹87.66/USD**, with RBI intervention aiming to stabilize it. Bond yields rose (~6.41% on the 10-year). :contentReference[oaicite:15]{index=15}

- Despite these headwinds, government support (e.g. credit guarantees, export relief) and ongoing structural reforms may mitigate the impact. :contentReference[oaicite:16]{index=16}

 
## **India’s Economy Sustains Strong Growth at ~6.5% Real GDP**

- Real GDP growth clocked in at **6.5%** for fiscal year 2024–25, making India the fastest-growing major economy

- The economy's nominal GDP expanded by **9.9%** in the same period, with real GVA rising **6.4%**

- Growth was underpinned by robust private consumption, improving private investment, strong public capex, and resilient exports
 
## **Inflation Moderates to Multi-Year Lows**

- Retail inflation averaged **~4.6%** in 2024–25—the lowest since 2018–19

- In July 2025, inflation dropped sharply to **1.55%**, its lowest in eight years, driven mainly by falling food prices

- Core inflation remained moderate (~4–4.1%), signaling maintained consumer demand
 
## **Exports and Foreign Investment Surge**

- Total exports reached a record **USD 825 billion** in 2024–25, up **76%** over the past decade

- Services exports alone grew to **USD 387 billion**—more than double since 2013–14

- Cumulative FDI inflows exceeded **USD 1.05 trillion**, with equity inflows jumping **27%** in the first nine months of FY 25
 
## **Monetary Policy and Outlook**

- The RBI cut interest rates sharply—its largest cuts in five years—to lend support to growth; the target is an “aspirational” **7–8% growth**

- The full year FY 2024–25 fiscal deficit was brought down to **4.8%** of GDP, with early FY 2025–26 indicators showing further improvement

- Forecasts project real GDP to grow at **6.3% in FY 2025–26** and **6.4% in FY 2026–27**, with inflation contained around **4%**
 
## **Risks: Trade Tensions and Currency**

- New U.S. tariffs on Indian goods—approaching **50%**—could dent GDP growth by approximately **0.6 percentage points**, threatening key sectors like textiles and jewelry

- The rupee weakened, trading near **₹87.66/USD**, with RBI intervention aiming to stabilize it; bond yields rose to ~6.41% on the 10-year

- Despite these headwinds, government support and ongoing structural reforms may mitigate the impact

 `

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

function mapIncentivesToTypes(incentivesObj, typesObj,namesObj) {
  if(!incentivesObj || !typesObj) return []
    return Object.keys(incentivesObj).map(key => ({
        id: incentivesObj[key],
        name: namesObj[key],
        type: typesObj[key],  // Fallback in case type doesn't exist
    }));
}

function mapApprovalData(ApprovalsObj, nameObj,govtObj,stageObj,timeObj) {
  if(!ApprovalsObj || !nameObj) return []
    return Object.keys(ApprovalsObj).map(key => ({
        id: ApprovalsObj[key],
        approval_name: nameObj[key],
        government_department: govtObj[key] || "Department of Industry & Health", // Fallback in case type doesn't exist
        stage: stageObj[key],
        time_taken: timeObj[key]
    }));
}

  const fetchPropertyData = async (analytics_response) => {
    let preaparedSolutions = [];
    const final_scoring_df = JSON.parse(analytics_response?.['final_scoring_df'])
    const property_id = final_scoring_df["Property_ID"]
    if (!property_id) {
      setTempFailure(true)
    }

    const Essential_supply_vendor_lookup_df = JSON.parse(analytics_response['Essential_supply_vendor_lookup_df'])
    const Essential_supply_all_vendor_lookup_df = JSON.parse(analytics_response['Essential_supply_all_vendor_lookup_df'])
    const nonEssential_supply_vendor_lookup_df = JSON.parse(analytics_response['Non_essential_supply_vendor_lookup_df'])
    const nonEssential_supply_all_vendor_lookup_df = JSON.parse(analytics_response['Non_essential_supply_all_vendor_lookup_df'])
    const Employment_lookup_df = JSON.parse(analytics_response['Employment_lookup_df'])
    const Solution_lookup_df = JSON.parse(analytics_response['Solution_lookup_df'])
    const Approval_lookup_df = JSON.parse(analytics_response['Approval_lookup_df'])
    console.log('This is Vendor Lookup for Essential', Essential_supply_vendor_lookup_df)
    console.log('This is Vendor Lookup All for Essential', Essential_supply_all_vendor_lookup_df)
    console.log('This is Vendor Lookup for Non Essential', nonEssential_supply_vendor_lookup_df)
    console.log('This is Vendor Lookup All for Non Essential', nonEssential_supply_all_vendor_lookup_df)
    console.log('This is Employment Lookup', Employment_lookup_df)
    console.log('This is Solution Lookup', Solution_lookup_df)
    console.log('This is Approval Lookup', Approval_lookup_df)
    console.log('This is Final DF ', final_scoring_df)


    const promises = Object.entries(property_id).map(async ([key, value]) => {
      try {
        const get_data = await fetchData(value)

        //Added by jenith for matching the property id in every DF
        const approval_index = findIndexByPropertyId(value, Approval_lookup_df)
        const incentive_index = findIndexByPropertyId(value, Solution_lookup_df)
        console.log("incentive_index",incentive_index)
        const essential_index = findIndexByPropertyId(value, Essential_supply_vendor_lookup_df)
        const essential_all_index = findIndexByPropertyId(value, Essential_supply_all_vendor_lookup_df)
        const non_essential_index = findIndexByPropertyId(value, nonEssential_supply_vendor_lookup_df)
        const non_essential_all_index = findIndexByPropertyId(value, nonEssential_supply_all_vendor_lookup_df)
        const employment_index = findIndexByPropertyId(value, Employment_lookup_df)

        const data = get_data[0]
        // const approval_data = await getApprovals(Approval_lookup_df['approval_id'][approval_index])
        const approval_data = mapApprovalData(Approval_lookup_df['approval_id'][approval_index], Approval_lookup_df['approval_name'][approval_index],Approval_lookup_df['government_department'][approval_index],Approval_lookup_df['stages'][approval_index],Approval_lookup_df['time_taken'][approval_index])
        // const incentive_data = await getIncentives(Solution_lookup_df['incentive_id'][incentive_index])
        const incenetives = mapIncentivesToTypes(Solution_lookup_df['incentive_id'][incentive_index],Solution_lookup_df['incentive_type'][incentive_index],Solution_lookup_df['incentive_name'][incentive_index]  )
        // console.log(nonEssential_supply_all_vendor_lookup_df?.['vendor_id']?.[non_essential_all_index],'Okay This ones new')
        // const industry_incentive_data = await getIndustryIncentives(Solution_lookup_df['incentive_id'][incentive_index])
        const essential_vendor_id_data = Essential_supply_vendor_lookup_df?.['vendor_id']?.[essential_index] ? await getAllVendorsData("Vendor", Essential_supply_vendor_lookup_df?.['vendor_id']?.[essential_index]) : []
        const essential_vendor_all_id_data = Essential_supply_all_vendor_lookup_df?.['vendor_id']?.[essential_all_index] ? await getAllVendorsData("Vendor", Essential_supply_all_vendor_lookup_df?.['vendor_id']?.[essential_all_index]) : []
        const non_essential_vendor_id_data = nonEssential_supply_vendor_lookup_df?.['vendor_id']?.[non_essential_index] ? await getAllVendorsData("Vendor", nonEssential_supply_vendor_lookup_df?.['vendor_id']?.[non_essential_index]) : []
        const non_essential_vendor_all_id_data = nonEssential_supply_all_vendor_lookup_df?.['vendor_id']?.[non_essential_all_index] ? await getAllVendorsData("Vendor", nonEssential_supply_all_vendor_lookup_df?.['vendor_id']?.[non_essential_all_index]) : []
        
        const parsed_essential_all = parseSinglePropertySuppliers(Essential_supply_all_vendor_lookup_df.supply_id[essential_all_index], Essential_supply_all_vendor_lookup_df.vendor_id[essential_all_index])
        const parsed_essential = parseSinglePropertySuppliers(Essential_supply_vendor_lookup_df.supply_id[essential_index],Essential_supply_vendor_lookup_df.vendor_id[essential_index])
        const parsed_nonessential_all = parseSinglePropertySuppliers(nonEssential_supply_all_vendor_lookup_df.supply_id[non_essential_all_index],nonEssential_supply_all_vendor_lookup_df.vendor_id[non_essential_all_index])
        const parsed_nonessential = parseSinglePropertySuppliers(nonEssential_supply_vendor_lookup_df.supply_id[non_essential_index],nonEssential_supply_vendor_lookup_df.vendor_id[non_essential_index])

        // const mapped_essential_supply_all = parseSuppliersAndBestSupplies(parsed_essential_all[essential_all_index])
        // console.log(mapped_essential_supply_all, 'This is okay mapped essential')
        // const mapped_essential_supply = parseSuppliersAndBestSupplies(parsed_essential[essential_index])
        // const mapped_non_essential_supply = parseSuppliersAndBestSupplies(parsed_nonessential[non_essential_index])
        // const mapped_non_essential_supply_all = parseSuppliersAndBestSupplies(parsed_nonessential_all[non_essential_all_index])
        // const mapped_essential_supply_all = mapVendorsToSupply(parsed_essential_all[essential_all_index]?.supply_id, parsed_essential_all[essential_all_index]?.vendor_id)
        // console.log(mapped_essential_supply_all, 'This is okay mapped essential')
        // const mapped_essential_supply = mapVendorsToSupply(parsed_essential[essential_index]?.supply_id, parsed_essential[essential_index]?.vendor_id)
        // const mapped_non_essential_supply = mapVendorsToSupply(parsed_nonessential[non_essential_index]?.supply_id, parsed_nonessential[non_essential_index]?.vendor_id)
        // const mapped_non_essential_supply_all = mapVendorsToSupply(parsed_nonessential_all[non_essential_all_index]?.supply_id, parsed_nonessential_all[non_essential_all_index]?.vendor_id)
    
        essential_vendor_id_data.forEach(v => renameKey(v, "table_podq", "supplies"));
        essential_vendor_all_id_data.forEach(v => renameKey(v, "table_podq", "supplies"));
        non_essential_vendor_id_data.forEach(v => renameKey(v, "table_podq", "supplies"));
        non_essential_vendor_all_id_data.forEach(v => renameKey(v, "table_podq", "supplies"));

        // Remove duplicates function
        const removeDuplicates = (arr, key = 'vendor_name') => {
          if (!Array.isArray(arr)) return [];
          const seen = new Set();
          return arr.filter(obj => {
            if (!obj || typeof obj !== 'object') return false;
            const value = obj[key];
            if (value === undefined || seen.has(value)) {
              return false;
            }
            seen.add(value);
            return true;
          });
        };

        // const temp_essential_data = removeDuplicates(essential_vendor_id_data)
        // const temp_essential_data_all = removeDuplicates(essential_vendor_all_id_data)
        // const temp_non_essential_data = removeDuplicates(non_essential_vendor_id_data)
        // const temp_non_essential_data_all = removeDuplicates(non_essential_vendor_all_id_data)

        // Create deduplicated versions
        const unique_essential_vendor_id_data = attachBestSuppliesToVendorData(essential_vendor_id_data,parsed_essential);
        const unique_essential_vendor_all_id_data = attachBestSuppliesToVendorData(essential_vendor_all_id_data, parsed_essential_all);
        const unique_non_essential_vendor_id_data = attachBestSuppliesToVendorData(non_essential_vendor_id_data, parsed_nonessential);
        const unique_non_essential_vendor_all_id_data = attachBestSuppliesToVendorData(non_essential_vendor_all_id_data, parsed_nonessential_all);
        // const unique_essential_vendor_id_data = removeDuplicates(essential_vendor_id_data);
        // const unique_essential_vendor_all_id_data = removeDuplicates(essential_vendor_all_id_data);
        // const unique_non_essential_vendor_id_data = removeDuplicates(non_essential_vendor_id_data);
        // const unique_non_essential_vendor_all_id_data = removeDuplicates(non_essential_vendor_all_id_data);

        if (data) {
          const nearest_airport_coord = data.nearest_airport_coord;
          const nearest_power_source_coord = data.nearest_power_source_coord;
          const nearest_seaport_coord = data.nearest_seaport_coord;
          const nearest_railway_station_coord = data.nearest_railway_station_coord;
          const nearest_highway_coord = data.nearest_highway_coord;
          const nearest_power_source = data.nearest_power_source;
          const nearest_railway_station = data.nearest_railway_station;
          const nearest_airport = data.nearest_airport;
          const nearest_seaport = data.nearest_seaport;
          const boundary_coordinates = data.boundary_coordinates
          const latLong = data.latitude_longitude
          const latLongArray = latLong ? latLong.split(',').map(coord => parseFloat(coord)) : []
          const area = data.area
          const city = data.city
          const district = data.district
          const availability_of_local_transportation = data.availability_of_local_transportation
          const road_connectivity = data.road_connectivity
          const area_acre = data.area_acre
          const state = data.state
          const property_type = data.property_type
          const business_location_type = data.business_location_type
          const distance_from_power_source = data.distance_from_power_source
          const distance_from_nearest_railway_station = data.distance_from_nearest_railway_station
          const distance_from_nearest_airport = data.distance_from_nearest_airport
          const distance_from_nearest_seaport = data.distance_from_nearest_seaport

          const essential_supply_and_vendor = []
          const nonessential_supply_and_vendor = []

          const essential_vendors_id = Essential_supply_vendor_lookup_df?.['vendor_id'] ? Essential_supply_vendor_lookup_df?.["vendor_id"]?.[essential_index] : ''
          const non_essential_vendors_id = nonEssential_supply_vendor_lookup_df?.['vendor_id'] ? nonEssential_supply_vendor_lookup_df?.["vendor_id"]?.[non_essential_index] : ''
          if (Essential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[essential_index] && Array.isArray(Essential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[essential_index]) && Essential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[essential_index]?.length > 0) {
            const ess_supply_id = Essential_supply_vendor_lookup_df?.["supply_id"]?.[essential_index] || [];
            const ess_vendor_id = Essential_supply_vendor_lookup_df?.["vendor_id"]?.[essential_index] || [];
            const ess_No_of_vendors_found = Essential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[essential_index] || [];
            const ess_Distance = Essential_supply_vendor_lookup_df?.["Distance"]?.[essential_index] || [];
            ess_supply_id.forEach((supply, index) => {
              if (ess_No_of_vendors_found[index] !== undefined && ess_Distance[index] !== undefined) {
                const supply_vendor = {
                  supply: supply,
                  total_vendor: ess_No_of_vendors_found[index],
                  vendor_name: ess_vendor_id[index],
                  nearest_vendor_distance: ess_Distance[index],
                  status: get_status_for_distance(ess_Distance[index])
                };
                essential_supply_and_vendor.push(supply_vendor);
              }
            });
          }

          if (nonEssential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[non_essential_index] && Array.isArray(nonEssential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[non_essential_index]) && nonEssential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[non_essential_index].length > 0) {
            const noness_supply_id = nonEssential_supply_vendor_lookup_df?.["supply_id"]?.[non_essential_index] || [];
            const noness_vendor_id = nonEssential_supply_vendor_lookup_df?.["vendor_id"]?.[non_essential_index] || [];
            const noness_No_of_vendors_found = nonEssential_supply_vendor_lookup_df?.["No_of_vendors_found"]?.[non_essential_index] || [];
            const noness_Distance = nonEssential_supply_vendor_lookup_df?.["Distance"]?.[non_essential_index] || [];

            noness_supply_id.forEach((supply, index) => {
              if (noness_No_of_vendors_found[index] !== undefined && noness_Distance[index] !== undefined) {
                const supply_vendor = {
                  supply: supply,
                  total_vendor: noness_No_of_vendors_found[index],
                  vendor_name: noness_vendor_id[index],
                  nearest_vendor_distance: noness_Distance[index],
                  status: get_status_for_distance(noness_Distance[index])
                };
                nonessential_supply_and_vendor.push(supply_vendor);
              }
            });
          }

          const vendor_summary = {
            "total_vendors": (Essential_supply_all_vendor_lookup_df?.['vendor_id']?.[essential_all_index]?.length || 0) + (nonEssential_supply_all_vendor_lookup_df?.['vendor_id']?.[non_essential_all_index]?.length || 0),
            "essential_vendors": Essential_supply_all_vendor_lookup_df?.['vendor_id']?.[essential_all_index]?.length || 0,
            "non_essential_vendors": nonEssential_supply_all_vendor_lookup_df?.['vendor_id']?.[non_essential_all_index]?.length || 0
          }

          const emp_skill_type = Employment_lookup_df['Skill_Type']?.[employment_index]
const count = Employment_lookup_df?.[emp_skill_type]?.[employment_index] ?? 0
const skilled_no = Employment_lookup_df['Skilled']?.[employment_index] || 0
const semiskilled_no = Employment_lookup_df['Semi-Skilled']?.[employment_index] || 0  // fixed casing
const unskilled_no = Employment_lookup_df['Unskilled']?.[employment_index] || 0

          // let incenetives = incentive_data.map(incentive => {
          //   // let parsedContext = safeJsonParse(incentive.contextual_analysis);
          //   let inc = {
          //     id: incentive.name,
          //     name: incentive.incentive_name,
          //     // endDate: incentive.incentive_operation_end_date,
          //     // startDate: incentive.incentive_operation_start_date,
          //     // incentive_rank: incentive.incentive_rank,
          //     type: incentive.incentive_type,
          //     // quantum_of_assistance: incentive.quantum_of_assistance,
          //     // contextual_analysis: parsedContext?.final_markdown || '',
          //     // description: incentive.description,
          //     // category_description: JSON.parse(incentive.category_description)
          //   };

          //   // Always calculate status
          //   // inc.status = getProgramStatus(inc.startDate, inc.endDate);

          //   // Add level only if industry match found
          //   // const matchingIndustry = industry_incentive_data.find(
          //   //   industry => industry.incentive === inc.id // or inc.name if needed
          //   // );

          //   // if (matchingIndustry) {
          //   //   inc.level = getLocationLevel(
          //   //     matchingIndustry.city_level,
          //   //     matchingIndustry.state_level,
          //   //     matchingIndustry.country_level
          //   //   );
          //   // }

          //   return inc;
          // });

          const total_effective_time = Approval_lookup_df['Efficient Approval Time'][approval_index]
          const online_percentage = Approval_lookup_df['Online Percentage'][approval_index]
          const pre_requisite = Approval_lookup_df['Pre-Requisite'][approval_index]
          const pre_establishment = Approval_lookup_df['Pre-Establishment'][approval_index]
          const pre_operation = Approval_lookup_df['Pre-Operation'][approval_index]
          const others = Approval_lookup_df['Others'][approval_index]
          const mode_requisite = Approval_lookup_df['Mode_Pre-Requisite'][approval_index]
          const mode_establishment = Approval_lookup_df['Mode_Pre-Establishment'][approval_index]
          const mode_operation = Approval_lookup_df['Mode_Pre-Operation'][approval_index]
          const mode_others = Approval_lookup_df['Mode_Others'][approval_index]
          // const approvals = []

          // approval_data.forEach((approval, index) => {
          //   // let tempLevel = getLocationLevel(approval.city_level, approval.state_level, approval.country_level)
          //   const appr = {
          //     id: approval.name,
          //     // approvalID: approval.name,
          //     approval_name: approval.license_approval,
          //     government_department: approval.government_department,
          //     time_taken: approval.delivery_schedule_in_working_days,
          //     // land_type: approval.land_type,
          //     // level: tempLevel,
          //     stage: approval.stage || "N/A",
          //     // mode_of_application: approval.mode_of_application || "N/A",
          //     // business_location: approval.business_location || "N/A",
          //     // details: approval.description || "No Description Available",
          //   }
          //   approvals.push(appr)
          // })

          const stageCounts = approval_data?.reduce((acc, curr) => {
            acc[curr.stage] = (acc[curr.stage] || 0) + 1;
            return acc;
          }, {});

          const suitability_score = final_scoring_df["Property-Wise Suitability Score (PWSS)"][key]
          const employment_score = final_scoring_df["Property-Wise Employment Score (PWES)"][key]
          const incentive_score = final_scoring_df["Property-Wise Incentive Score (PWIS)"][key]
          const approvals_score = final_scoring_df["Property-Wise Approval Score (PWAS)"][key]
          const vendors_score = final_scoring_df["Property-Wise Vendor Score (PWVS)"][key]

          const scores = [suitability_score, employment_score, incentive_score, approvals_score, vendors_score]
          const network_availability = final_scoring_df['Network Connectivity'][key] || "Not available"

          const road_transport = availability_of_local_transportation == 'Yes' ? 'good' : 'bad'
          const property_id = final_scoring_df['Property_ID'][key]
          // const score = final_scoring_df['aggregated_score'][key]
          const score = final_scoring_df['Aggregate Property Performance Score (APPS)'][key]  
          // const score = final_scoring_df['Reranked_Aggregate_Property_Performance_Score_(RAPPS)'][key]

          const local_laws = final_scoring_df['local_laws'][key]
          const parsedLocalLaws = local_laws ? parseLegalText(local_laws) : []
          const taxes = final_scoring_df['taxes'][key]
          const parsedTaxes = taxes ? parseLegalOrTaxText(taxes) : []
          const market_trends = final_scoring_df['market_trends'][key] ? final_scoring_df['market_trends'][key] : fallBackMarketTrend;

          const temp_power_source = Math.floor(Math.random() * (20 - 2 + 1)) + 2;

          const areaName = await fetchAreaName(area)
          const solution = {
            //   address: `${area || city}, ${district}, ${state}`,
            property_id: property_id,
            score: score,
            area: `${areaName.area_name}`,
            tempAddress: `${areaName.area_name}-${city}-${state}`,
            address: `${city}, ${state}`,
            property_type: property_type,
            total_area: area_acre,
            latitude_longitude: latLongArray,
            business_location_type: business_location_type || 'GIDC',
            availability_of_local_transportation: road_transport,
            seaport: { distance: distance_from_nearest_seaport, status: get_status_for_distance(distance_from_nearest_seaport) },
            airport: { distance: distance_from_nearest_airport, status: get_status_for_distance(distance_from_nearest_airport) },
            // power: { distance: distance_from_power_source, status: get_status_for_distance(distance_from_power_source) },
            power: { distance: temp_power_source, status: get_status_for_distance(temp_power_source) },
            railway: { distance: distance_from_nearest_railway_station, status: get_status_for_distance(distance_from_nearest_railway_station) },
            essential_vendors: essential_supply_and_vendor,
            nonessential_vendors: nonessential_supply_and_vendor,
            essential_vendor_details: unique_essential_vendor_id_data,
            essential_vendor_all_details: unique_essential_vendor_all_id_data,
            non_essential_vendor_details: unique_non_essential_vendor_id_data,
            non_essential_vendor_all_details: unique_non_essential_vendor_all_id_data,
            vendor_summary: vendor_summary,
            employement: { type: emp_skill_type, count: count },
            skilled_no: skilled_no,
            semiskilled_no: semiskilled_no,
            unskilled_no: unskilled_no,
            incentives: incenetives,
            no_of_incentives: incenetives.length,
            approvals: approval_data,
            no_of_approvals: approval_data.length,
            stagewise_no_of_approvals: stageCounts,
            pre_requisite: pre_requisite,
            pre_establishment: pre_establishment,
            pre_operation: pre_operation,
            others: others,
            mode_establishment: mode_establishment,
            mode_operation: mode_operation,
            mode_requisite: mode_requisite,
            mode_others: mode_others,
            total_effective_time: total_effective_time,
            online_percentage: online_percentage,
            road_connectivity: { distance: road_connectivity, status: get_status_for_distance(road_connectivity) },
            boundary_coordinates: boundary_coordinates,
            result_type: "Industry_Result",
            network_availability: network_availability,
            local_laws: parsedLocalLaws,
            taxes: parsedTaxes,
            market_trends: market_trends,
            industryTitle: industryTitle,
            scores: scores,
            nearest_airport_coord: nearest_airport_coord,
            nearest_power_source_coord: nearest_power_source_coord,
            nearest_seaport_coord: nearest_seaport_coord,
            nearest_railway_station_coord: nearest_railway_station_coord,
            nearest_highway_coord: nearest_highway_coord,
            nearest_power_source: data.nearest_power_source,
            nearest_railway_station: data.nearest_railway_station,
            nearest_airport: data.nearest_airport,
            nearest_seaport: data.nearest_seaport,
            nearest_highway: data.nearest_highway
          }
          preaparedSolutions.push(solution)
          // console.log(solution, 'This is the solution printed ......')

        }
      } catch (error) {
        console.log("error is ❌", error);
        createDiagnostic("Land & Approvals", `Something went wrong while preparing Full Data for Rendering ${JSON.stringify(error)} in Build From Scratch`,lastChatId)
        // setSomeError(true)
      }
    });

    await Promise.all(promises);
    // console.log(preaparedSolutions, 'okay ')
    const updatedSolutions = preaparedSolutions
    .sort((a, b) => b.score - a.score) // Sort descending by score
    .map((solution, index) => ({
      ...solution,
      propertyIndex: index + 1 // Start from 1
    }));
    
    // console.log(updatedSolutions, 'this are the updated Solutions ')
    setSolutions(updatedSolutions);

    if (lastChatId) {
      let temp = {
        'Analytics_response': updatedSolutions
      }
      await storeResultData(lastChatId, temp)
    }
  };

  useEffect(() => {
    if (source === "SolutionScreen" && rerender != 1) {
      const loadPropertyData = async () => {
        await fetchPropertyData(analytics_response);
        setIsLoading(false);
      };
      loadPropertyData();
    }
    else if (source === 'MapComponent') {
      setSelectedProperty(result)
    }
    else {
      if (source === 'SolutionScreen' && rerender == 1) {
        // console.log(analytics_response, 'This ist he Solutions')
        setSolutions(analytics_response)
        setIsLoading(false);
      }
    }

  }, []);

  useEffect(() => {
    // console.log(solutions, selectedProperty);
    if (solutions && solutions.length > 0) {
      let tempsolutions = solutions.sort((a, b) => b.score - a.score)
      setSelectedProperty(tempsolutions[0])
    }
  }, [solutions]);

  useEffect(() => {
    // console.log(selectedProperty, 'this are the Property Solutions');
    if(selectedProperty) {
      if(selectedProperty.essential_vendors.length===0) {
        setShowEssentialMaterials(false)
      }
      else if(selectedProperty.nonessential_vendors.length===0) {
        setShowEssentialMaterials(true)
      }
      else if (selectedProperty.essential_vendors.length===0 && nonessential_vendors.length===0) {
        setShowEssentialMaterials(true)
      }
    }
  }, [selectedProperty])

  const gridPart = useRef(null)
  useEffect(() => {
    if (gridPart.current) {
      gridPart.current.scrollTop = 0;
    }
  }, [selectedProperty]);

  function createVendorData(essential, essential_all, nonessential, nonessential_all, latitude_longitude) {
    let result = {
      Analytics_response: {
        "Unfiltered All IS Supplier": null,
        "Best IS Supplier": null,
        "Unfiltered Essential Supplier": essential_all,
        "Best Essential Supplier": essential,
        "Better Supplier": null,
        "Unfiltered Non-Essential Supplier": nonessential_all,
        "Best Non-Essential Supplier": nonessential
      },
      latitude_longitude: latitude_longitude,
      propertyData: selectedProperty
    };
    return result
  }
  const handleShowVendor = () => {
    const data = createVendorData(selectedProperty?.essential_vendor_details, selectedProperty?.essential_vendor_all_details, selectedProperty?.non_essential_vendor_details, selectedProperty?.non_essential_vendor_all_details, selectedProperty?.latitude_longitude);
    setVendorsToSend(data);
    setVendorsWindow(true)
  }
  function createIncentiveData(incentives) {
    // const incentiveData = {
    //   "Incentive ID": {},
    //   "Level": {},
    // };

    // incentives.forEach((item, index) => {
    //   const idx = index.toString();
    //   incentiveData["Incentive ID"][idx] = item.incentive_id;
    //   incentiveData["Level"][idx] = ''  
    // });

    // return incentiveData
    return incentives
  }
  const handleShowIncentive = () => {
    const data = createIncentiveData(selectedProperty?.incentives);
    setIncentivesToSend(data);
    setIncentivesWindow(true)
  }
  function createApprovalData(approval) {

    return {
      // "Approval Data": JSON.stringify(approvalData),
      "Approval Data": approval.approvals,
      "Pre-Requisite": approval.pre_requisite,
      "Pre-Operation": approval.pre_operation,
      "Pre-Establishment": approval.pre_establishment,
      "Others": approval.others,
      "Online Percentage": approval.online_percentage,
      "Total Effective Time": approval.total_effective_time,
      "Mode_Pre-Requisite": approval.mode_requisite,
      "Mode_Pre-Operation": approval.mode_operation,
      "Mode_Pre-Establishment": approval.mode_establishment,
      "Mode_Others": approval.mode_others
    };
  }
  const handleShowApprovals = () => {
    const data = createApprovalData(selectedProperty);
    setApprovalsToSend(data);
    setApprovalWindow(true)
  }
  const get_status_for_distance = (distance) => {
    if (distance < 100) return "good";
    else if (distance >= 100 && distance < 200) return "warning";
    else if (distance >= 200 && distance < 300) return "danger";
    else return "bad";
  }

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalData, setModalData] = useState([]);
  const [modalTitle, setModalTitle] = useState('');

  const toggleModal = (data, title) => {
    setModalData(data);
    setModalTitle(title);
    setIsModalOpen(!isModalOpen);
  };

  const gridRef = useRef(null)
  const handleLocalLawsClick = () => {
    if (gridRef.current) {
      gridRef.current.scrollTop = gridRef.current.scrollHeight;
    }
  }

  useEffect(() => {
    if (!showLocalLaws) {
      setShowLocalLaws(true)
      setMarketAndLaws('Local Laws')
      setShowMarketTrends(false)
      if (gridRef.current) {
        gridRef.current.scrollTop = 0;
      }
    }
    else {
      if (gridRef.current) {
        gridRef.current.scrollTop = 0;
      }
    }
  }, [selectedProperty, activeTab, activeButton])

  // for local laws containers 
  const bgMap = [
    'border-[#2c53a3] bg-[#2c53a3]/10',
    'border-[#e91e63] bg-[#e91e63]/10',
    'border-[#673AB7] bg-[#673ab7]/10',
    'border-[#4caf50] bg-[#4caf50]/10',
    'border-indigo-500 bg-[#4338ca]/10'
  ];


  const shouldRender = source === "SolutionScreen" ? solutions && selectedProperty : source === "MapComponent" ? selectedProperty : false; // fallback if needed
  
  const { currentUser } = useFrappeAuth()
  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');

  const renderUserAvatar = (sender) => {
      const isCurrentUser = sender === 'user';
  
      if (sender !== 'user') {
        return (
          <img
            src={LogoIcon}
            alt="Bot"
            className="h-8 w-8 relative rounded-full flex-shrink-0"
          />
        );
      }
  
      if (isCurrentUser && currentUser) {
        if (userDoc?.user_image) {
          return (
            <img
              src={userDoc.user_image}
              alt="User"
              className="h-8 w-8 relative rounded-full object-cover flex-shrink-0"
            />
          );
        } else {
          return (
            <div className="h-8 w-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold flex-shrink-0">
              {currentUser?.charAt(0).toUpperCase()}
            </div>
          );
        }
      }
  
      return (
        <img
          src={userIcon}
          alt="User"
          className="h-8 w-8 relative rounded-full flex-shrink-0"
        />
      );
    };
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const [message, setMessage] = useState("");

  const handleMouseEnterr = () => {
    if (!isClicked) setIsHovered(true);
  };

  const handleMouseLeavee = () => {
    if (!isClicked) setIsHovered(false);
  };

  const handleClick = () => {
    setIsClicked((prev) => !prev);
  };

  const handleSend = () => {
    alert(`Message sent: ${message}`);
    setMessage("");
  };

  const expanded = isHovered || isClicked;
  const [isExpanded, setIsExpanded] = useState(false) 
  return (
    <>
      {shouldRender ? (
        <div className='relative flex flex-col w-screen h-screen'>
          
          {/* <FollowUpChat solutions={solutions} seletedProperty={selectedProperty} /> */}

          {source === 'SolutionScreen' && (<div className='sticky top-0 left-0 w-full h-fit flex flex-col z-[11]  bg-white border-b border-gray-300'>
            <div className='relative w-full h-12 p-4 flex flex-row justify-between mb-4'>
              <div className='relative flex flex-row gap-2 items-center'>
                <h1 className="text-2xl font-bold text-[#0e2044]"> {uiConfig["main_title"] || "Industrial property solutions"}<span className="bg-gradient-to-br from-[#3CB35B] via-[#2E8C4A] to-[#152F4F] font-bold bg-clip-text text-transparent ml-2">{randomTitle}</span></h1>
              </div>
              {rerender!==1 && source==="SolutionScreen" && (<Backtochat text='Back to Chat' />)}
            </div>

            <div className='relative flex flex-row gap-6 w-full h-fit px-4 justify-start items-center border-b border-gray-300'>
              <div className='relative flex flex-col gap-1 items-center'><div className={` relative h-full flex items-center justify-center px-2 hover:cursor-pointer hover:text-[#2C53A3] ${activeButton === 'Property Details' ? 'text-[#0B2152]' : 'text-gray-500 '}`} onClick={() => { setActiveButton('Property Details'), setActiveTab('Property Details') }}>{uiConfig?.['property_tab'] || "Property Details"}</div><span className={`${activeButton === 'Property Details' ? 'w-full' : 'w-0'} h-0.5 bg-[#0B2152] rounded-full relative transition-all duration-300`}></span></div>
              <div className='relative flex flex-col gap-1 items-center'><div className={` relative h-full flex items-center justify-center px-2 hover:cursor-pointer hover:text-[#2C53A3]  ${activeButton === 'Map View' ? 'text-[#0B2152]' : 'text-gray-500 '}`} onClick={() => { setActiveButton('Map View'), setActiveTab('Map View') }}>{uiConfig?.['map_tab'] || "Map view"}</div><span className={`${activeButton === 'Map View' ? 'w-full' : 'w-0'} h-0.5 relative transition-all rounded-full duration-300 bg-[#0B2152]`}></span></div>
              {solutions.length>1 && (<div className='relative flex flex-col gap-1 items-center'><div className={` relative h-full flex items-center justify-center px-2 hover:cursor-pointer hover:text-[#2C53A3] ${activeButton === 'Analytics' ? 'text-[#0B2152]' : 'text-gray-500 '}`} onClick={() => { setActiveButton('Analytics'), setActiveTab('Analytics') }}>{uiConfig?.['analytics_tab'] || "Analytics"}</div><span className={`${activeButton === 'Analytics' ? 'w-full' : 'w-0'} h-0.5 relative rounded-full transition-all duration-300 bg-[#0B2152]`}></span></div>)}
              {/* <div className='relative flex flex-col gap-1 items-center'><div className={` relative h-full flex items-center justify-center px-2 hover:cursor-pointer hover:text-[#2C53A3] ${activeButton === 'newUI' ? 'text-[#0B2152]' : 'text-gray-500 '}`} onClick={() => { setActiveButton('newUI'), setActiveTab('newUI') }}>{uiConfig?.['newUI_tab'] || "newUI"}</div><span className={`${activeButton === 'newUI' ? 'w-full' : 'w-0'} h-0.5 relative rounded-full transition-all duration-300 bg-[#0B2152]`}></span></div> */}
            </div>

            {activeTab === 'Property Details' && (<div className='relative w-full min-h-36 h-36 flex flex-row p-3 gap-4 overflow-x-auto overflow-y-hidden hide-scrollbar'>

              {solutions && solutions.map((data, index) => {
                const isSelected = selectedProperty.property_id === data.property_id;
                return (<div key={index} onClick={() => { setSelectedProperty(solutions[index]) }} className={`relative cursor-pointer min-h-28 h-28 min-w-[200px] w-[200px] border border-gray-400 flex flex-col rounded-md hover:cursor-pointer overflow-hidden transform transition duration-300  shadow-lg ${isSelected ? '-translate-y-1 border-2 border-gray-700' : 'hover:shadow-xl hover:-translate-y-1 '}`} >
                  <div className={`relative min-h-8 h-8 flex flex-row px-2 items-center justify-end max-h-8 bg-gradient-to-r from-[#0e2044] to-[#41b655] ${isSelected ? 'opacity-100' : 'opacity-80'} w-full`}>
                    <span className='bg-white py-0.5 px-2 rounded-full font-semibold text-xs text-black flex items-center justify-center'>{data.score.toFixed(2)}&nbsp;/&nbsp;10</span>
                  </div>
                  <div className='relative min-h-20 h-20 max-h-24 bg-white-500 w-full flex flex-col gap-1 pt-4 pb-2 px-2'>
                    <div className='absolute rounded-full h-6 w-6 bg-white flex items-center -top-3.5 left-2 justify-center text-sm shadow-md'>{data.propertyIndex}</div>
                    <h1 className='relative font-semibold text-sm'>{data.area}</h1>
                    <h2 className='relative text-gray-600 text-xs'>{data.address}</h2>
                  </div>
                </div>)
              })}
            </div>)}

          </div>)}

          <div ref={gridRef} className={`${activeTab === "Analytics" ? 'overflow-y-hidden' : 'overflow-y-auto'}  bg-gray-50 h-full w-full relative`}>
            {activeTab === 'Map View' && (
              <div className='relative h-full w-full overflow-hidden'>
                <MapComponent intension="For All Propert Listing" solutions={solutions} toggleModal={toggleModal} />
              </div>
            )}
            {activeTab === 'Analytics' && (
              <div className='relative h-screen w-screen overflow-hidden flex items-center justify-center'>
                <Comparison solutions={solutions} />
              </div>
            )}

            {/* {activeTab === 'newUI' && (
              <div className='relative h-full w-full overflow-hidden flex flex-1'>
                <NewIndustryScreen solutions={solutions} />
              </div>
            )} */}

            {activeTab === "Property Details" && (
              <>
                {selectedProperty ? (
                  <div className="relative flex-1 w-full p-2  font-sans bg-gray-50 flex flex-col gap-3 overflow-x-hidden">

                    {/* Top Row */}
                    <div className="grid grid-cols-1 md:grid-cols-8 w-full gap-4">

                      {/* Location Map Card */}
                      <div className="card p-4 bg-white rounded shadow-md gap-4 flex flex-col items-start col-span-2">
                        <div className="flex justify-start items-center  flex-row  w-full">
                          {/* <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">Location Map <div className="relative inline-block"><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter('tooltip1')} onMouseLeave={() => handleMouseLeave('tooltip1')}/><div className={`${visibleTooltips.tooltip1 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Shows the exact location of the property/project on the map</div></div></h2> */}
                          <span className="text-sm font-bold text-black flex flex-row items-center gap-2"><span className='h-6 w-6 p-2 rounded-full flex items-center font-semibold shadow-md justify-center border-2 border-black text-black bg-transparent'>{selectedProperty?.propertyIndex}</span> {uiConfig?.['property_title']} {selectedProperty.area}</span>
                        </div>
                        <div className="bg-gray-100 h-48 w-full rounded relative overflow-hidden ">
                          <MapBoxMap lat={selectedProperty?.latitude_longitude[0]} lng={selectedProperty?.latitude_longitude[1]} source='FromProperty' solutions={solutions} />
                        </div>
                        <div className="text-xs text-gray-600 flex justify-between relative w-full flex-row">
                          <span>{selectedProperty.address}</span>
                          {source === "SolutionScreen" && (<button className="text-primary hover:underline flex flex-row items-center cursor-pointer" onClick={() => { setSingleMapWindow(true) }} >View Full Map <IoIosArrowForward /></button>)}
                        </div>
                        <div className='flex flex-col gap-3 relative w-full'>
                          <div className="flex justify-between items-center border-b border-gray-100">
                            <span className="text-sm text-gray-600">{uiConfig?.['property_card_detail_1'] || "Property Type"}</span>
                            <span className="text-sm font-medium">{selectedProperty.property_type}</span>
                          </div>
                          <div className="flex justify-between items-center border-b border-gray-100">
                            <span className="text-sm text-gray-600">{uiConfig?.['property_card_detail_2'] || "Total Area"}</span>
                            <span className="text-sm font-medium">{selectedProperty.total_area} Acres</span>
                          </div>
                          <div className="flex justify-between items-center border-b border-gray-100">
                            <span className="text-sm text-gray-600">{uiConfig?.['property_card_detail_3'] || "Business Location Type"}</span>
                            <span className="text-sm font-medium">{selectedProperty.business_location_type}</span>
                          </div>

                        </div>
                      </div>

                      {/* Vendor Proximity */}
                      <div className="card p-4 bg-white rounded  shadow-md gap-6 relative flex flex-col items-start col-span-3">
                        <div className='relative flex flex-row items-center justify-between'>
                          <div className="flex gap-2 items-center relative flex-row">
                            <h2 className="text-base font-semibold text-primary relative">{uiConfig?.['vendor_card_title'] || "Supply Chain Accessibility"}</h2>
                            <div className="tooltip relative inline-block">
                              <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => { handleMouseEnter('tooltip2') }} onMouseLeave={() => { handleMouseLeave('tooltip2') }} />
                              <div className={`${visibleTooltips.tooltip2 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>{uiConfig?.['vendor_card_tooltip'] || "Nearby vendors sorted by distance and relevance to the selected property"}</div>
                            </div>
                            <span title={`${uiConfig?.['vendor_score_hover_title'] || 'Property-Wise Vendor Score'}`} className='py-1 cursor-default px-4 relative flex items-center  justify-center rounded-full text-white font-semibold text-xs bg-gradient-to-r from-[#70A1D9] to-[#5b96d8]'>{selectedProperty?.scores[4].toFixed(2)} &nbsp;/&nbsp;10</span>
                          </div>
                          <div className='relative p-2 text-sm text'></div>
                        </div>
                        <div className="flex space-x-2 justify-between items-center relative w-full">
                          <div className='relative flex flex-row gap-2'>
                            <div className='relative flex flex-col gap-1 items-center'>
                              <button
                                onClick={() => { setShowEssentialMaterials(true) }}
                                className={`px-3 py-1 text-xs cursor-pointer text-black font-semibold transition-all`}
                              >
                                {uiConfig?.['essential_supplies_title'] || "Essential Supplies"}
                              </button>
                              <div className={`${showEssentialMaterials ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                            </div>
                            <div className='relative flex flex-col gap-1 items-center'>
                              <button
                                onClick={() => { setShowEssentialMaterials(false) }}
                                className={`px-3 py-1 text-xs font-medium rounded-full cursor-pointer`}>
                                {uiConfig?.['non_essential_supplies_title'] || "Non-Essential Supplies"}
                              </button>
                              <div className={`${!showEssentialMaterials ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                            </div>
                          </div>

                          {/* <div className='relative py-1 px-2 text-xs text-orange-800 bg-orange-100 rounded-full font-semibold'>{showEssentialMaterials ? `${selectedProperty.essential_vendors.reduce((sum, item) => sum + item.total_vendor, 0)}`: `${selectedProperty.nonessential_vendors.reduce((sum,item) => sum + item.total_vendor, 0)}`} Found</div> */}
                        </div>
                        {showEssentialMaterials ? (
                          <div className="gap-3 w-full relative grid grid-cols-2">
                            {selectedProperty.essential_vendors?.length === 0 ? (
                              <p className="text-sm text-gray-500 italic col-span-2 h-28 justify-self-center self-center">
                                No vendors available
                              </p>
                            ) : (
                              selectedProperty.essential_vendors?.slice(0, 5)?.map((essentials, index) => (
                                <div key={index} className="grid grid-cols-2 gap-2 col-span-2">
                                  <div className="flex flex-row gap-2 items-start">
                                    <div className="w-2 h-2 rounded-full bg-[#70A1D9] mt-2"></div>
                                    <div className='flex flex-col'>
                                      <span className="text-sm font-medium">{essentials.supply}</span>
                                      <span className='text-xs font-light text-gray-600'>{uiConfig?.['no_of_vendors'] || 'No of Vendors:'} {essentials.total_vendor}</span>
                                    </div>
                                  </div>
                                  <div className='flex flex-row gap-2 justify-self-end'>
                                    <span className="text-xs text-gray-600 ">
                                      {uiConfig?.['nearest_vendor'] || 'Nearest Vendor:'} <span className='font-semibold text-gray-700'>{essentials.nearest_vendor_distance.toFixed(2)} km</span>
                                    </span>
                                    {essentials.status === 'good' ? (
                                      <BsPatchCheckFill className="text-green-500" />
                                    ) : essentials.status === 'warning' ? (
                                      <FaTriangleExclamation className="text-yellow-500" />
                                    ) : (
                                      <FaCircleXmark className="text-red-500" />
                                    )}

                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        ) : (
                          <div className="gap-3 w-full relative grid grid-cols-2">
                            {selectedProperty.nonessential_vendors?.length === 0 ? (
                              <p className="text-sm text-gray-500 italic col-span-2 h-28 justify-self-center self-center">
                                No vendors available
                              </p>
                            ) : (
                              selectedProperty.nonessential_vendors?.slice(0, 5)?.map((essential, idx) => (
                                <div key={idx} className="grid grid-cols-2 gap-2 col-span-2">
                                  <div className="flex flex-row gap-2 items-start">
                                    <div className="w-2 h-2 rounded-full bg-[#70A1D9] mt-2"></div>
                                    <div className='flex flex-col'>
                                      <span className="text-sm font-medium">{essential.supply}</span>
                                      <span className='text-xs font-light text-gray-600'>{uiConfig?.['no_of_vendors'] || 'No of Vendors:'} {essential.total_vendor}</span>
                                    </div>
                                  </div>
                                  <div className='flex flex-row gap-2 justify-self-end'>
                                    <span className="text-xs text-gray-600 ">
                                       {uiConfig?.['nearest_vendor'] || 'Nearest Vendor:'} <span className='font-semibold text-gray-700'>{essential.nearest_vendor_distance.toFixed(2)} km</span>
                                    </span>
                                    {essential.status === 'good' ? (
                                      <BsPatchCheckFill className="text-green-500" />
                                    ) : essential.status === 'warning' ? (
                                      <FaTriangleExclamation className="text-yellow-500" />
                                    ) : (
                                      <FaCircleXmark className="text-red-500" />
                                    )}
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        )}

                        {/* {selectedProperty.essential_vendors.reduce((sum, item) => sum + item.total_vendor, 0) > 5 || selectedProperty.nonessential_vendors.reduce((sum, item) => sum + item.total_vendor, 0) > 5 && ( */}
                        {(selectedProperty.essential_vendors?.length > 0 || selectedProperty.nonessential_vendors?.length > 0) && (
                          <div className=" flex items-center justify-center w-full absolute bottom-3 self-center">
                            <button className="py-2 text-black rounded text-sm flex flex-row gap-2 items-center font-medium cursor-pointer" onClick={handleShowVendor}>
                              {uiConfig?.['vendor_list_button_title'] || "Explore Vendor List"} <FaArrowRight />
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Approvals List */}
                      <div className="card p-4 bg-white rounded shadow-md relative flex flex-col col-span-3 items-start gap-6">

                        <div className='flex relative flex-row items-center justify-between w-full'>
                          <div className='relative gap-2 flex flex-row items-center'>
                            <h2 className="text-base relative font-semibold text-primary">{uiConfig?.['approval_card_title'] || "Compliance & Regulatory Checklist"}</h2>
                            <div className="tooltip relative inline-block">
                              <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => { handleMouseEnter('tooltip3') }} onMouseLeave={() => { handleMouseLeave('tooltip3') }} />
                              <div className={`${visibleTooltips.tooltip3 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>  {uiConfig?.['approval_card_tooltip'] || "Govt. clearances required for the project"}</div>
                            </div>
                            <span title={`${uiConfig?.['approvals_score_hover_title'] || 'Property-Wise Approval Score'}`} className='py-1 cursor-default px-4 relative flex items-center justify-center rounded-full text-xs tex-white text-white font-semibold bg-gradient-to-r from-[#E91E63] to-[#ec135c]'>{selectedProperty?.scores[3].toFixed(2)} &nbsp;/&nbsp;10</span>
                          </div>
                          <div className='relative rounded-full bg-orange-100 py-1 px-2 text-orange-800 text-xs font-semibold'>{selectedProperty.approvals.length} Needed</div>
                        </div>

                        <div className=" relative w-full grid grid-cols-4 gap-3">

                          {selectedProperty.approvals.slice(0, 5).map((approval, index) =>
                            <>
                              <div key={index} className="relative flex flex-row items-start w-full gap-2 col-span-3">
                                <div className="w-2 h-2 rounded-full flex-shrink-0 bg-[#E91E63] mt-2"></div>
                                <div className='relative flex flex-col'>
                                  <span className="text-sm font-medium">{approval.approval_name}</span>
                                  <span className='text-xs text-gray-500'>{approval.government_department}</span>
                                </div>
                              </div>
                              <div key={index} className="relative flex flex-row items-center gap-2 whitespace-nowrap col-span-1 justify-self-end">
                                <div className='relative flex flex-col'>
                                  <p className='relative text-gray-600 text-xs'>{uiConfig?.['approval_duration'] || 'Est. Duration'}</p>
                                  <span className="text-sm text-black">{approval.time_taken} days</span>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                        {selectedProperty.approvals.length > 0 && (
                        <div className='absolute flex flex-row gap-2 items-center text-sm justify-center p-2 bottom-3 self-center cursor-pointer' onClick={handleShowApprovals}>
                          {uiConfig?.['approval_list_button_title'] || "View Approvals"} <FaArrowRight />
                        </div>
                        )}
                      </div>

                    </div>

                    {/* Middle Row */}
                    <div className="grid grid-cols-1 md:grid-cols-8 gap-4">

                      {/* Geo & Utility Snapshots Panel */}
                      <div className="card p-4 bg-white rounded shadow-md col-span-2 gap-6 flex flex-col items-start">
                        <div className='relative gap-2 flex flex-row items-center'>
                          <h2 className="text-base relative font-semibold text-primary"> {uiConfig?.['location_summary_card_title'] || "Location Intelligence Summary"}</h2>
                          <div className="tooltip relative inline-block">
                            <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => { handleMouseEnter('tooltip4') }} onMouseLeave={() => { handleMouseLeave('tooltip4') }} />
                            <div className={`${visibleTooltips.tooltip4 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}> {uiConfig?.['location_summary_card_tooltip'] || "Nearby Transport & Connectivity Distances"}</div>
                          </div>
                          <span title={`${uiConfig?.['location_score_hover_title'] || 'Property-Wise Suitability Score'}`} className='py-1 cursor-default px-4 relative flex items-center justify-center rounded-full text-xs text-white font-semibold  bg-gradient-to-r from-[#673AB7] to-[#5f2abb]'>{selectedProperty?.scores[0].toFixed(2)}&nbsp;/&nbsp;10</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex items-center col-span-1 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <FaRoad className="text-indigo-600" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_highway_title'] || "Highway"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.road_connectivity.distance.toFixed(2)} km {selectedProperty.road_connectivity.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.road_connectivity.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                          <div className="flex items-center col-span-1 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <FaTrain className="text-indigo-600" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_railway_title'] || "Railway"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.railway.distance.toFixed(2)} km {selectedProperty.railway.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.railway.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                          <div className="flex items-center col-span-1 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <RiShipFill className="text-indigo-600" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_seaport_title'] || "Seaport"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.seaport.distance.toFixed(2)} km {selectedProperty.seaport.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.seaport.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                          <div className="flex items-center col-span-1 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <FaPlane className="text-indigo-600" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_airport_title'] || "Airport"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.airport.distance.toFixed(2)} km {selectedProperty.airport.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.airport.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                          <div className="flex items-center col-span-2 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <MdOfflineBolt className="text-indigo-600 text-md" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_power_source_title'] || "Power Source"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.power.distance.toFixed(2)} km {selectedProperty.power.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.power.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                          <div className="flex items-center col-span-2 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <FaBus className="text-indigo-600 text-md" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_transportation_title'] || "Availability of Local Transportation"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.availability_of_local_transportation} {selectedProperty.availability_of_local_transportation === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.power.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                          <div className="flex items-center col-span-2 flex-row gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                              <IoWifi className="text-indigo-600 text-md" />
                            </div>
                            <div className='flex flex-col gap-1'>
                              <p className="text-sm font-medium">{uiConfig?.['location_summary_network_title'] || "Network Availability"}</p>
                              <p className="text-xs text-gray-600 flex flex-row gap-1 items-center"> {selectedProperty.network_availability} {selectedProperty.network_availability === '4G & 5G' ? (<BsPatchCheckFill size={12} className='text-green-500' />) : selectedProperty.network_availability === '4G' ? (<FaTriangleExclamation size={12} className='text-yellow-500' />) : (<FaCircleXmark size={12} className='text-red-500' />)}</p>
                            </div>
                          </div>
                        </div>

                      </div>

                      {/* Spider Map */}
                      <div className="w-full flex flex-col col-span-2 p-4 bg-white rounded shadow-md">
                        <div className="flex flex-row justify-start self-start items-center w-full">
                          <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">{uiConfig?.['spider_map_card_title'] || "Decision Support Radar"} <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => { handleMouseEnter('tooltip7') }} onMouseLeave={() => { handleMouseLeave('tooltip7') }} /><div className={`${visibleTooltips.tooltip7 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>{uiConfig?.['spider_map_card_tooltip'] || "Summarizes core property suitability factors."}</div></div></h2>
                        </div>
                        <div className='relative flex items-center justify-center h-[320px]'>
                          <Spider label={selectedProperty.tempAddress} scores={selectedProperty.scores} />
                        </div>
                      </div>

                      {/* Government Incentives Overview */}
                      <div className="card p-4 bg-white rounded col-span-4 pb-12 shadow-md gap-6 relative flex flex-col items-start">
                        <div className="flex flex-row justify-between items-center w-full">
                          <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center"> {uiConfig?.['incentives_card_title'] || "Subsidy & Support Matrix"} <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => { handleMouseEnter('tooltip6') }} onMouseLeave={() => { handleMouseLeave('tooltip6') }} /><div className={`${visibleTooltips.tooltip6 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>{uiConfig?.['incentives_card_tooltip'] || "Applicable Government Incentives & Schemes"}</div></div>
                            <span  title={`${uiConfig?.['incentives_score_hover_title'] || 'Property-Wise Incentive Score'}`} className='py-1 px-4 relative cursor-default flex items-center justify-center rounded-full text-xs  text-white font-semibold bg-gradient-to-r from-[#4CAF50] to-[#3cb340]'>{selectedProperty?.scores[2].toFixed(2)} &nbsp;/&nbsp;10</span>
                          </h2>
                          <div className='relative py-1 px-2 rounded-full text-xs text-orange-800 bg-orange-100 font-semibold'>{selectedProperty.incentives.length} Found</div>
                        </div>
                        <div className="flex flex-col gap-3 relative w-full h-full">
                          {selectedProperty.incentives.sort((a, b) => a.incentive_rank - b.incentive_rank).slice(0, 5).map((incentive, index) =>
                            <div key={index} className="flex items-start relative flex-row gap-2">
                              <div className="w-2 h-2 rounded-full bg-[#4CAF50] mt-2"></div>
                              {/* <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div> */}
                              <div className='relative flex flex-col items-start'>
                                <h3 className="text-sm font-medium">{incentive.type}</h3>
                                <p className="text-xs text-gray-600">{incentive.name}</p>
                              </div>
                            </div>
                          )}
                        </div>
                        {selectedProperty.incentives.length > 0 && (
                          <div className='flex flex-row gap-2 items-center text-sm justify-center p-2 absolute bottom-3 self-center cursor-pointer' onClick={handleShowIncentive}>
                            {uiConfig?.['incentives_list_button_title'] || "View Incentives"} <FaArrowRight />
                          </div>
                        )}

                      </div>

                    </div>

                    {/* Bottom row */}
                    <div className='relative grid grid-cols-8 gap-4'>

                      {/* Employment Data Section */}
                      <div className="card p-4 bg-white max-h-[350px] min-h-[350px] flex flex-col gap-2 h-full rounded shadow-md col-span-2">
                        <div className="flex justify-between h-fit items-center mb-3">
                          <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">{uiConfig?.['employement_card_title'] || "Workforce Availability Insights"} <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => { handleMouseEnter('tooltip5') }} onMouseLeave={() => { handleMouseLeave('tooltip5') }} />
                            <div className={`${visibleTooltips.tooltip5 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>{uiConfig?.['employement_card_tooltip'] || "Local Workforce Skill Levels Overview"}</div>
                          </div>
                            <span  title={`${uiConfig?.['employment_score_hover_title'] || 'Property-Wise Employment Score'}`} className='py-1 px-4 relative cursor-default flex items-center justify-center rounded-full text-xs  text-white font-semibold  bg-gradient-to-r from-[#2C53A3] to-[#234ea4]'>{selectedProperty?.scores[1].toFixed(2)} &nbsp;/&nbsp;10</span>
                          </h2>
                        </div>

                        <div className="h-full relative w-full">
                          <Doughnut data={{
                            labels: ['Skilled', 'Semi-Skilled', 'Unskilled'],
                            datasets: [{
                              data: [selectedProperty.skilled_no, selectedProperty.semiskilled_no, selectedProperty.unskilled_no],
                              backgroundColor: ['#2563EB', '#16A34A', '#D97706'],
                              borderWidth: 1,
                            }]
                          }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              cutout: '60%', // thinner ring (default is ~50%)
                              plugins: {
                                legend: {
                                  display: false // hide legend
                                },
                              },
                            }}
                            className="w-ful  l h-full" // This will make the chart fill its container
                          />
                        </div>
                        <div className="mt-2 h-fit grid grid-cols-3 gap-2">
                          <div className="text-center flex flex-col gap-2">
                            <div className="text-xs font-medium">Skilled</div>
                            <div className="text-sm text-blue-600 font-semibold">{selectedProperty.skilled_no} workers</div>
                          </div>
                          <div className="text-center flex flex-col gap-2">
                            <div className="text-xs font-medium">Semi-skilled</div>
                            <div className="text-sm text-green-600 font-semibold">{selectedProperty.semiskilled_no} workers</div>
                          </div>
                          <div className="text-center flex flex-col gap-2">
                            <div className="text-xs font-medium">Unskilled</div>
                            <div className="text-sm text-amber-600 font-semibold">{selectedProperty.unskilled_no} workers</div>
                          </div>
                        </div>

                      </div>

                      {/* Market Trends and Local Laws */}
                      <div className={`relative col-span-6 w-full rounded p-4 max-h-[350px] bg-white transition-all shadow-md duration-300 overflow-hidden`}>
                        <div className='h-fit w-full flex flex-row border-b  items-center justify-start gap-8'>
                          <div className='relative flex flex-col gap-1 w-fit bg-white cursor-pointer select-none' onClick={() => { setMarketAndLaws('Local Laws'), setShowMarketTrends(false), setShowLocalLaws(true),setShowTaxes(false), handleLocalLawsClick() }}>
                            <h1 className='font-semibold text-base text-black flex flex-row gap-2 items-center'><ImHammer2 className='text-blue-600 font-semibold' /> {uiConfig?.['local_laws_card_title'] || "Local Laws"}</h1>
                            <div className={`${marketAndLaws === 'Local Laws' ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                          </div>
                          <div className='relative flex flex-col gap-1 w-fit bg-white cursor-pointer select-none' onClick={() => { setMarketAndLaws('Taxes'), setShowMarketTrends(false), setShowLocalLaws(false),setShowTaxes(true), handleLocalLawsClick() }}>
                            <h1 className='font-semibold text-base text-black flex flex-row gap-2 items-center'><BsCurrencyExchange className='text-blue-600 text-2xl font-bold' /> {uiConfig?.['taxes_card_title'] || "Taxes"}</h1>
                            <div className={`${marketAndLaws === 'Taxes' ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                          </div>

                          <div className='relative flex flex-col gap-1 w-fit bg-white cursor-pointer select-none' onClick={() => { setMarketAndLaws('Market Trends'), setShowMarketTrends(true), setShowLocalLaws(false),setShowTaxes(false), handleLocalLawsClick() }}>
                            <h1 className='font-semibold text-base text-black flex flex-row gap-2 items-center'><FaChartLine className='text-purple-600' /> {uiConfig?.['market_trends_card_title'] || "Market Trends"}</h1>
                            <div className={`${marketAndLaws === 'Market Trends' ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
                          </div>
                        </div>

                        <div className='relative h-[calc(100%-50px)] overflow-y-auto'>
                          {showLocalLaws && (
                            (selectedProperty?.local_laws && selectedProperty?.local_laws.length > 0) ? (
                              <div className='w-full p-4 grid grid-cols-2 gap-4'>
                                {selectedProperty?.local_laws && selectedProperty?.local_laws.length > 0 && selectedProperty.local_laws.map((law, index) => (
                                  <div className={`relative flex flex-col gap-2 p-4 border-l-4 ${bgMap[index]}`} >
                                    <h1 className='font-semibold text-md'>{law.title}</h1>
                                    <p className='text-sm font-normal '>{law.description}</p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className='w-full p-4 grid grid-cols-2 gap-4'>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#2c53a3] bg-[#2c53a3]/10'>
                                  <h1 className="font-semibold text-md">Factories Act, 1948</h1>
                                  <ul className="list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1">
                                    <li>Governs health, safety, and working hours in manufacturing units.</li>
                                    <li>Mandatory for factories with 10+ workers (with power).</li>
                                  </ul>
                                </div>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#e91e63] bg-[#e91e63]/10'>
                                  <h1 className='font-semibold text-md'>Environment Protection Act, 1986</h1>
                                  <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                                    <li>Requires environmental clearance for polluting industries.</li>
                                    <li>Enforced by Pollution Control Boards.</li>
                                  </ul>
                                </div>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#673AB7] bg-[#673ab7]/10'>
                                  <h1 className='font-semibold text-md'> Shops and Establishments Act (State-specific)</h1>
                                  <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                                    <li>Mandatory registration for all businesses like shops/offices.</li>
                                    <li>Regulates working hours, holidays, and employee rights.</li>
                                  </ul>
                                </div>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#4caf50] bg-[#4caf50]/10'>
                                  <h1 className='font-semibold text-md'>Building Bye-Laws</h1>
                                  <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                                    <li>Local rules for construction (height, setbacks, FSI).</li>
                                    <li>Need approval before starting any building work.</li>
                                  </ul>
                                </div>
                              </div>
                            )
                          )}
                          {showtaxes && (
                            (selectedProperty?.taxes && selectedProperty?.taxes.length > 0) ? (
                              <div className='w-full p-4 grid grid-cols-2 gap-4'>
                                {selectedProperty?.taxes && selectedProperty?.taxes.length > 0 && selectedProperty.taxes.map((law, index) => (
                                  <div className={`relative flex flex-col gap-2 p-4 border-l-4 ${bgMap[index]}`} >
                                    <h1 className='font-semibold text-md'>{law.title}</h1>
                                    <p className='text-sm font-normal '>{law.description}</p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className='w-full p-4 grid grid-cols-2 gap-4'>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#2c53a3] bg-[#2c53a3]/10'>
                                  <h1 className="font-semibold text-md">GST Act, 2017</h1>
                                  <ul className="list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1">
                                    <li>Applies to yarn, fabric, and garments (5%-12%).</li>
                                   
                                  </ul>
                                </div>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#e91e63] bg-[#e91e63]/10'>
                                  <h1 className='font-semibold text-md'>Income Tax Act, 1961</h1>
                                  <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                                    <li>Deductions on power, wages, and technology upgradation.</li>
                              
                                  </ul>
                                </div>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#673AB7] bg-[#673ab7]/10'>
                                  <h1 className='font-semibold text-md'>Customs Act, 1962</h1>
                                  <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                                    <li>On imported machines and raw materials.</li>
                                 
                                  </ul>
                                </div>
                                <div className='relative flex flex-col gap-2 p-4 border-l-4 border-[#4caf50] bg-[#4caf50]/10'>
                                  <h1 className='font-semibold text-md'>TDS (Section 194C, 194H)</h1>
                                  <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                                    <li>On processing contracts, agent commissions.</li>
                                  </ul>
                                </div>
                              </div>
                            )
                          )}

                          {showMarketTrends && (
                            <div className='p-2'>
                              <ReactMarkdown
                                rehypePlugins={[rehypeRaw]}
                                remarkPlugins={[remarkBreaks, remarkGfm]}
                                components={{
                                  h2: ({ node, ...props }) => <h2 className="text-base font-bold text-gray-800 mt-3 mb-2 pb-1" {...props} />,
                                  h3: ({ node, ...props }) => <h3 className="text-md font-semibold text-gray-700 mt-3 mb-2" {...props} />,
                                  p: ({ node, ...props }) => <p className="text-gray-700 mb-2 text-sm" {...props} />,
                                  strong: ({ node, ...props }) => <strong className="font-semibold text-sm text-gray-900" {...props} />,
                                  ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />,
                                  ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-4 space-y-1" {...props} />,
                                  li: ({ node, ...props }) => <li className="text-gray-700 text-sm mb-1" {...props} />,
                                }}
                              >
                                {selectedProperty?.market_trends}
                              </ReactMarkdown>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>



                  </div>
                ) : (
                  <LogoLoader text='Just a Moment!' />
                )}
              </>)}
          </div>
        </div>

      )
        : someError ?
          (<FailureScreen />) : tempFailure ? (<NoResultsFound />)
            : (<LogoLoader text="Just a sec - We're drawing the full picture!" />)}

      {approvalsWindow && approvalsToSend && (
        <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setApprovalWindow(false), setApprovalsToSend() }} >
            <FaXmark size={22} />
          </div>
          <Approvalresult result={approvalsToSend} source="FromScratch" rerender={1} />
        </div>
      )}
      {incentivesWindow && incentivesToSend && (
        <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setIncentivesWindow(false), setIncentivesToSend() }}>
            <FaXmark size={28} />
          </div>
          <Incentiveresult res={incentivesToSend} source="FromScratch" rerender={1} />
        </div>
      )}
      {vendorsWindow && vendorsToSend && (
        <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setVendorsWindow(false), setVendorsToSend() }}>
            <FaXmark size={28} />
          </div>
          <Vendorresult result={vendorsToSend} source="FromScratch" />
        </div>
      )}
      {SingleMapWindow && (
        <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
          <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={() => { setSingleMapWindow(false) }}>
            <FaXmark size={28} />
          </div>
          <SingleMap selectedProperty={selectedProperty} intension="From Industry Result Screen" />
        </div>
      )}
    </>
  );
};

export default IndustryResultScreen;