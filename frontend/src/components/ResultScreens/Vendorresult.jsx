import React, { useEffect, useState, useRef, useTransition, useContext } from 'react';
import { FaLocationDot } from "react-icons/fa6";
import { FrappeContext, useFrappeGetDoc, useFrappeGetDocList,useFrappeCreateDoc } from 'frappe-react-sdk';
import Backtochat from '../Backtochat/Backtochat';
import MapComponent from '../MapComponent/MapComponent';
import {
 FaCheckCircle, FaList, FaAward, FaInfoCircle, FaChartBar, FaShieldAlt, FaStoreAlt, FaFileAlt, FaSearch
} from 'react-icons/fa';
import { AiFillProduct } from "react-icons/ai";
import { MdPeopleAlt } from "react-icons/md";
import LogoLoader from '../Responseloader/LogoLoader';
import { all } from 'axios';
import MapBoxMap from '../MapComponent/MapBoxMap';
import { useSelector } from 'react-redux';
import { useFrappeUpdateDoc} from 'frappe-react-sdk';
import { current } from '@reduxjs/toolkit';
import NoResultsFound from '../Failure/NoResultsFound';
import SingleMap from '../MapComponent/SingleMap';
import { CertificateIcon, CheckIcon } from '../../Icons/icon';
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";


const useClickOutside = (ref, handler) => {
    useEffect(() => {
      const maybeHandler = (event) => {
        if (ref.current && !ref.current.contains(event.target)) {
          handler();
        }
      };
      document.addEventListener("mousedown", maybeHandler);
      return () => {
        document.removeEventListener("mousedown", maybeHandler);
      };
    }, [ref, handler]);
  };

function Vendorresult({ result, source, rerender }) {
  const { createDoc } = useFrappeCreateDoc('');
  const lastChatId = useSelector((state) => state.chat.lastId);
  const createDiagnostic = (errType, logMsg,chatId)=> {
      let log = `${logMsg}`
      createDoc("AIX Diagnostics Hub", {
      type: errType,
      note: log,
      chat_name: chatId
      });
  }
  const {call} = useContext(FrappeContext)
  const [tempFailure, setTempFailure] = useState(false)
  const [forcedFail, setForcedFail]= useState(false)
  // First check in the code should be ::::  Unfiltered All IS Supplier
  // console.log(result, source, 'This is the result screen from Vendor Screen')
  const analytics_response = (source === "SolutionScreen" || source === 'FromScratch') ? result["Analytics_response"] : ''
  // if ((typeof analytics_response === 'object' && analytics_response !== null && typeof analytics_response !== 'string') ) {
  //   console.log('All good')
  //   // safely use `essential` here
  // } else {
  //   let msg = analytics_response;
  //   console.log(msg, 'Setting the result fail...')
  //   setTempFailure(true)
  //   // fallback or ignore
  // }
  if(source!=='MapComponent') {
    if (
     typeof analytics_response !== 'object' || 
     analytics_response === null || 
     typeof analytics_response === 'string' 
   ) {
      // console.log('Invalid analytics_response:', analytics_response,source, rerender);
      // createDiagnostic("Data Error", `Invalid Data was passed that couldn't be rendered due to ${analytics_response} in Vendors`,lastChatId)
      return <NoResultsFound diagnostics={true} type='Suppliers' chatId={lastChatId} data={analytics_response} module='Vendors'/>;
    }
  }
  
  

  const IndividualQuery = analytics_response?.['Unfiltered All IS Supplier'] ? true : false
  // console.log(IndividualQuery, analytics_response, 'This is the first check ')
  
  if(!IndividualQuery && source!=='MapComponent') {
    let essential_all = analytics_response?.['Unfiltered Essential Supplier']
    let essential_best = analytics_response?.['Best Essential Supplier']
    let non_essential_all = analytics_response?.['Unfiltered Non-Essential Supplier']
    let non_essential_best = analytics_response?.['Best Non-Essential Supplier']
    let check_all = [essential_all, essential_best, non_essential_all, non_essential_best]
    // console.log(check_all, essential_all, essential_best, non_essential_all, non_essential_best)
    let allNull = check_all.every(item=> !item)
    if(allNull) {
      // createDiagnostic("Data Error", `Invalid Data was passed that couldn't be rendered due to ${analytics_response} in Vendors`,lastChatId)
      return <NoResultsFound diagnostics={true} type='Suppliers' chatId={lastChatId} data={analytics_response} module='Vendors'/>;
    }
  }
  // console.log(IndividualQuery, 'This is the Individual Query')
  const user_lat_long = result["latitude_longitude"]
  const propertyData = (source === "FromScratch") ? result['propertyData'] : ''
  // console.log(result, rerender, user_lat_long, analytics_response, 'This is the result in vendors Screen')
  const [viewMode, setViewMode] = useState('Suppliers')
  const [currentData, setCurrentData] = useState("All Suppliers");
  const [supplierType, setSupplierType] = useState('Essential')
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [supplierList, setSupplierList] = useState()
  const [groupedData, setGroupedData] = useState()
  const [loading, setLoading] = useState(true)

  const [essentialAllSuppliers, setEssentialAllSuppliers] = useState([])
  const [essentialBestSuppliers, setEssentialBestSuppliers] = useState([])
  const [nonEssentialAllSuppliers, setNonEssentialAllSuppliers] = useState([])
  const [nonEssentialBestSuppliers, setNonEssentialBestSuppliers] = useState([])

  const [allIndividualSuppliers, setAllIndividualSuppliers] = useState([])
  const [bestIndividualSuppliers, setBestIndividualSuppliers] = useState([])
  const [betterIndividualSuppliers, setBetterIndividualSuppliers] = useState([])

  const [updatedAllIndividualSupplier, setUpdatedAllIndividualSupplier] = useState([])
  const [updatedBestIndividualSupplier, setUpdatedBestIndividualSupplier] = useState([])
  const [updatedBetterSupplier, setUpdatedBetterSupplier] = useState([])

  const [updEssentialAllSupplier, setUpdEssentialAllSupplier] = useState([])
  const [updEssentialBestSupplier, setUpdEssentialBestSupplier] = useState([])
  const [updNonEssentialAllSupplier, setUpdNonEssentialAllSupplier] = useState([])
  const [updNonEssentialBestSupplier, setUpdNonEssentialBestSupplier] = useState([])

  const [individualAllSupply, setIndividualAllSupply] = useState([])
  const [essentialAllSupply, setEssentialAllSupply] = useState([])
  const [nonessentialAllSupply, setNonEssentialAllSupply] = useState([])
  const supplyNode = useRef(null)
  const [supplydropdownopen, setSupplyDropdownOpen] = useState(false)
  const [supplyname, setSupplyName] = useState()
  const [supplyList, setSupplyList] = useState([])
  useClickOutside(supplyNode, ()=> setSupplyDropdownOpen(false));

  const { data: uiData } = useFrappeGetDoc("UI Configuration", "Vendors")
    const configurations = uiData?.configurations || [];
    const uiConfig = configurations.reduce((acc, curr) => {
      acc[curr.key] = curr.value;
      return acc;
    }, {});

  const mapRef = useRef(null);

  
  const { updateDoc } = useFrappeUpdateDoc()

  // const parseSuppliers = (supplierData) => {
  //   if (!supplierData?.vendor_id) return [];

  //   // Create a Map to handle duplicates (last entry wins)
  //   const vendorMap = new Map();

  //   Object.keys(supplierData.vendor_id).forEach(key => {
  //     const vendorId = supplierData.vendor_id[key];
  //     const vendorData = {
  //       supply_id: supplierData.supply_id?.[key],
  //       Final_Score_With_Features: supplierData.Final_Score_With_Features?.[key],
  //       vendor_id: vendorId,
  //       // aggregated_score: supplierData.aggregated_score?.[key],
  //       // Add all other properties dynamically
  //       ...Object.fromEntries(
  //         Object.entries(supplierData)
  //           .filter(([k]) => !['vendor_id', 'supply_id', 'Final_Score_With_Features'].includes(k))
  //           .map(([k, v]) => [k, v[key]])
  //       )
  //     };

  //     // This will automatically override previous entries with same vendor_id
  //     vendorMap.set(vendorId, vendorData);
  //   });

  //   return Array.from(vendorMap.values());
  // };
  
const parseAllSupplies = (supplies) => {
  // console.log('this are the supplies', supplies)
  if (!supplies || supplies.length===0) return []
    const allsupplies = [] 
    Object.keys(supplies.supply_id).forEach(key=> { 
      const supply = supplies.supply_id[key] 
      allsupplies.push(supply) 
    }) 
    return allsupplies 
  }

const parseAllTempSupplies = (vendors) => {
  // console.log(vendors,'This are the vendors Supplies')
  if (!vendors || vendors.length===0) return []
  const allsupplies = [];
  // Iterate over each vendor in the input data
  vendors.forEach(vendor => {
    // Iterate over the best_supply array for each vendor
    vendor.best_supply.forEach(supply => {
      allsupplies.push(supply);
    });
  });

  return allsupplies;
};


   const parseSuppliers = (supplierData) => {
    // console.log("Here comes the suplyData", supplierData)
    if (!supplierData) return [];
  if (!supplierData?.vendor_id) return [];
   
  const vendorMap = new Map();

  Object.keys(supplierData.vendor_id).forEach(key => {
    const vendorId = supplierData.vendor_id[key];

    const vendorData = {
      supply_id: supplierData.supply_id?.[key],
      Final_Score_With_Features: supplierData.Final_Score_With_Features?.[key],
      vendor_id: vendorId,
      // Add all other properties dynamically
      ...Object.fromEntries(
        Object.entries(supplierData)
          .filter(([k]) => !['vendor_id', 'supply_id', 'Final_Score_With_Features'].includes(k))
          .map(([k, v]) => [k, v[key]])
      )
    };

    if (!vendorMap.has(vendorId)) {
      // First time: create entry with best_supply Set
      vendorMap.set(vendorId, {
        ...vendorData,
        best_supply: new Set([vendorData.supply_id])
      });
    } else {
      // Already exists: add supply_id into best_supply Set
      const existing = vendorMap.get(vendorId);
      existing.best_supply.add(vendorData.supply_id);

      vendorMap.set(vendorId, { ...existing, ...vendorData, best_supply: existing.best_supply });
    }
  });

  // Convert Sets to arrays before returning
  return Array.from(vendorMap.values()).map(v => ({
    ...v,
    best_supply: Array.from(v.best_supply)
  }))
};

  useEffect(() => {
    if (source !== "MapComponent") {
      if (IndividualQuery) {
        
        setBestIndividualSuppliers(((source === "SolutionScreen") && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Best IS Supplier"] || "{}")) : analytics_response?.["Best IS Supplier"] || "{}")
        setBetterIndividualSuppliers(((source === "SolutionScreen") && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Better Supplier"] || "{}")) : analytics_response?.["Better Supplier"] || "{}")
        setAllIndividualSuppliers(((source === "SolutionScreen") && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Unfiltered All IS Supplier"] || "{}")) : analytics_response?.["Unfiltered All IS Supplier"] || "{}")
        let temp_supply = ((source=== "SolutionScreen") && rerender !==1) ? JSON.parse(analytics_response["Unfiltered All IS Supplier"] || "{}") : analytics_response?.["Unfiltered All IS Supplier"] || "{}"
        let all_supply = parseAllSupplies(temp_supply)
        let uniqueSupplies = [...new Set(all_supply)];
        setIndividualAllSupply(uniqueSupplies)
        setSupplyName(uniqueSupplies[0])
      }

      if (!IndividualQuery) {
        setEssentialBestSuppliers((source === 'SolutionScreen' && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Best Essential Supplier"] || "[]")) : analytics_response["Best Essential Supplier"] || "[]");
        setEssentialAllSuppliers((source === 'SolutionScreen' && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Unfiltered Essential Supplier"] || "[]")) : analytics_response["Unfiltered Essential Supplier"] || "[]");
        // console.log(parseSuppliers(JSON.parse(analytics_response["Unfiltered Essential Supplier"] || "[]")),' Okay this is something new ')
        let temp_essential_supply = (source === 'SolutionScreen' && rerender !== 1) ? JSON.parse(analytics_response["Unfiltered Essential Supplier"] || "[]") : analytics_response["Unfiltered Essential Supplier"] || "[]"
        let all_supply = (source === 'SolutionScreen' && rerender !== 1) ? parseAllSupplies(temp_essential_supply) : parseAllTempSupplies(temp_essential_supply)
        let uniqueEssentialSupplies = [...new Set(all_supply)]
        // console.log(uniqueEssentialSupplies, 'This are all the supplies that are essential')
        setEssentialAllSupply(uniqueEssentialSupplies)
        
        setNonEssentialBestSuppliers((source === 'SolutionScreen' && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Best Non-Essential Supplier"] || "[]")) : analytics_response["Best Non-Essential Supplier"] || "[]");
        setNonEssentialAllSuppliers((source === 'SolutionScreen' && rerender !== 1) ? parseSuppliers(JSON.parse(analytics_response["Unfiltered Non-Essential Supplier"] || "[]")) : analytics_response["Unfiltered Non-Essential Supplier"] || "[]");
        let temp_nonEssential_supply = (source === 'SolutionScreen' && rerender !== 1) ? JSON.parse(analytics_response["Unfiltered Non-Essential Supplier"] || "[]") : analytics_response["Unfiltered Non-Essential Supplier"] || "[]"
        let all_non_essential_supply = (source === 'SolutionScreen' && rerender !== 1) ? parseAllSupplies(temp_nonEssential_supply) : parseAllTempSupplies(temp_nonEssential_supply)
        let uniquenonEssentialSupplies = [...new Set(all_non_essential_supply)]
        setNonEssentialAllSupply(uniquenonEssentialSupplies)

      }
    }
  }, [analytics_response])


  const allVendorNames = [...(nonEssentialAllSuppliers || []).map(f => f?.vendor_id), ...(essentialAllSuppliers || []).map(f => f?.vendor_id), ...(nonEssentialBestSuppliers || []).map(f => f?.vendor_id), ...(essentialBestSuppliers || []).map(f => f?.vendor_id)];
  const allSupplyNames = [...(nonEssentialAllSuppliers || []).map(f => f?.supply_id), ...(essentialAllSuppliers || []).map(f => f?.supply_id)];
  const vendorNames = ((source === "SolutionScreen") && rerender !== 1) ? IndividualQuery ? allIndividualSuppliers?.map(f => f.vendor_id) : allVendorNames : []
  const supplyNames = ((source === "SolutionScreen") && rerender !== 1) ? IndividualQuery ? allIndividualSuppliers?.map(f => f.supply_id) : allSupplyNames : []
  // console.log(vendorNames, 'This are the Vendor Names', supplyNames)
  const ShouldRender = rerender === 1 ? false : true

  const { data: vendorData, error, isLoading } = useFrappeGetDocList('Vendor', ShouldRender ? {
    filters: [['name', 'in', vendorNames]],
    fields: [
      'no_of_services', 'no_of_past_clients', 'portfolio', 'category', 'certifications', 'state', 'website_url', 'email_id', 'years_of_experience', 'no_of_employees', 'latitude_longitude', 'vendor_name', 'name'
    ],
    limit: 50000
  } : null);

  const { data: supplies, isLoading: supplyLoading } = useFrappeGetDocList('Vendor', ShouldRender ? {
    filters: [['name', 'in', vendorNames]],
    fields: ['table_podq.supply', 'table_podq.maximum_supply_capacity', 'table_podq.uom', 'table_podq.parent'],
    limit: 500000,
  } : null);

  function groupSuppliesWithVendors(vendors, supplies) {
    // Step 1: Group supplies by parent
    const grouped = supplies.reduce((acc, item) => {
      if (!acc[item.parent]) acc[item.parent] = [];
      acc[item.parent].push(item);
      return acc;
    }, {});

    // Step 2: Map vendors and attach grouped supplies
    return vendors.map(vendor => {
      return {
        ...vendor,
        supplies: grouped[vendor.vendor_name] || []
      };
    });
  }

  useEffect(() => {
    if ((source === "SolutionScreen") && rerender !== 1) {
      if (vendorData && supplies && !supplyLoading && !isLoading && vendorData.length > 0 && supplies.length > 0) {
        // console.log('Data Before Mapping ', vendorData, supplies)
        let d = groupSuppliesWithVendors(vendorData, supplies)
        // console.log(d, 'this is data grouped');
        setGroupedData(d)
      }
    }
  }, [vendorData, supplies])

  // Assuming the analytics response passes only the Ids ... and we have all data called from db in vendorData so match the names
  const updateData = (suppliers) => {
    // console.log('Came here', suppliers)
    if (!suppliers || suppliers.length < 1) return []
    const updatedSet = new Set();

    return suppliers.map(supplier => {
      if (rerender === 1) return supplier;

      const match = groupedData?.find(
        vendor => vendor.vendor_name === supplier.vendor_id
      );
      if (match) {
        updatedSet.add(supplier.vendor_id);
        return { ...supplier, ...match };
      }

      return supplier;
    });
  };

  function generateAnalyticsResponse(bestIndividualSuppliers, unfilteredSuppliers) {
    // console.log(bestIndividualSuppliers, unfilteredSuppliers, 'This is before conversion...')
    const Analytics_response = {
      "Best IS Supplier": bestIndividualSuppliers,
      "Unfiltered All IS Supplier": unfilteredSuppliers,
      "Best Essential Supplier": null,
      "Unfiltered Essential Supplier": null,
      "Best Non-Essential Supplier": null,
      "Unfiltered Non-Essential Supplier": null,
    };
    return Analytics_response;  // 🔥 Ready to store
  }
  function generateAnotherAnalyticsResponse(bestEssentialSuppliers, unfilteredEssentialSuppliers, bestNonEssentialSuppliers, unfilteredNonEssentialsuppliers) {
    // console.log(bestEssentialSuppliers, unfilteredEssentialSuppliers, unfilteredNonEssentialsuppliers, bestNonEssentialSuppliers, 'This is before conversion...')
    const Analytics_response = {
      "Best IS Supplier": null,
      "Unfiltered All IS Supplier": null,
      "Best Essential Supplier": bestEssentialSuppliers,
      "Unfiltered Essential Supplier": unfilteredEssentialSuppliers,
      "Best Non-Essential Supplier": bestNonEssentialSuppliers,
      "Unfiltered Non-Essential Supplier": unfilteredNonEssentialsuppliers,
    };
    return Analytics_response;  // 🔥 Ready to store
  }

  const storeResultData = async (lastChat,solutions,intension) => {
  if(!lastChat || !solutions) return 

  try {
    // console.log(lastChat, solutions?.[0], 'Method Called')
      const result = await call.post("frontend_app.Management_Class.helpers.utility.insert_solution_result", {
      child_row_id: lastChat,
      updated_solutions: solutions,
      intension: intension
      },
    {
    headers: {
      'Expect': '' // 👈 Clear problematic header
    }
  });
      // console.log('This is the result we want ot store.... ', result.message)
      return result.message || [];
    } catch (err) {
      // console.error("Error Storing Result json:", err);
      createDiagnostic("Suppliers", `Error storing Result Json due to ${JSON.stringify(err)} in Vendors`,lastChatId)
      return []; // Return empty for this batch on error
    }
}

  useEffect(() => {
    if (groupedData && !isLoading && !supplyLoading) {
      if (source !== 'MapComponent') {
        if (IndividualQuery) {
          if (allIndividualSuppliers && allIndividualSuppliers.length > 0) setUpdatedAllIndividualSupplier(((source === "SolutionScreen") && rerender !== 1) ? updateData(allIndividualSuppliers) : [])
          if (bestIndividualSuppliers && bestIndividualSuppliers.length > 0) setUpdatedBestIndividualSupplier(((source === "SolutionScreen") && rerender !== 1) ? updateData(bestIndividualSuppliers) : [])
        }
        if (!IndividualQuery) {
          if (essentialAllSuppliers && essentialAllSuppliers.length > 0) setUpdEssentialAllSupplier(((source === "SolutionScreen") && rerender !== 1) ? updateData(essentialAllSuppliers) : [])
          if (essentialBestSuppliers && essentialBestSuppliers.length > 0) setUpdEssentialBestSupplier(((source === "SolutionScreen") && rerender !== 1) ? updateData(essentialBestSuppliers) : [])
          if (nonEssentialAllSuppliers && nonEssentialAllSuppliers.length > 0) setUpdNonEssentialAllSupplier(((source === "SolutionScreen") && rerender !== 1) ? updateData(nonEssentialAllSuppliers) : [])
          if (nonEssentialBestSuppliers && nonEssentialBestSuppliers.length > 0) setUpdNonEssentialBestSupplier(((source === "SolutionScreen") && rerender !== 1) ? updateData(nonEssentialBestSuppliers) : [])
        }
      }
    }

    if (rerender === 1 || source === "FromScratch") {
      if (source !== "MapComponent") {
        if (IndividualQuery) {
          if (allIndividualSuppliers && allIndividualSuppliers.length > 0) setUpdatedAllIndividualSupplier((source === "SolutionScreen") ? allIndividualSuppliers : [])
          if (bestIndividualSuppliers && bestIndividualSuppliers.length > 0) setUpdatedBestIndividualSupplier((source === "SolutionScreen") ? bestIndividualSuppliers : [])
        }
        if (!IndividualQuery) {
          if (essentialAllSuppliers && essentialAllSuppliers.length > 0) setUpdEssentialAllSupplier(((source === "SolutionScreen" || source === "FromScratch")) ? essentialAllSuppliers : [])
          if (essentialBestSuppliers && essentialBestSuppliers.length > 0) setUpdEssentialBestSupplier(((source === "SolutionScreen" || source === "FromScratch")) ? essentialBestSuppliers : [])
          if (nonEssentialAllSuppliers && nonEssentialAllSuppliers.length > 0) setUpdNonEssentialAllSupplier(((source === "SolutionScreen" || source === "FromScratch")) ? nonEssentialAllSuppliers : [])
          if (nonEssentialAllSuppliers && nonEssentialBestSuppliers.length > 0) setUpdNonEssentialBestSupplier(((source === "SolutionScreen" || source === "FromScratch")) ? nonEssentialBestSuppliers : [])
        }
      }
    }

  }, [groupedData, allIndividualSuppliers, bestIndividualSuppliers, essentialAllSuppliers, essentialBestSuppliers, nonEssentialAllSuppliers, nonEssentialBestSuppliers])

  useEffect(() => {
    if ((source === "SolutionScreen" || source === 'FromScratch')) {
      let currentypeAll = supplierType === "Essential" ? updEssentialAllSupplier : updNonEssentialAllSupplier
      let currentypeBest = supplierType === "Essential" ? updEssentialBestSupplier : updNonEssentialBestSupplier
      setSupplyList(IndividualQuery ? individualAllSupply : (supplierType === "Essential" ? essentialAllSupply : nonessentialAllSupply))
      let all = IndividualQuery ? updatedAllIndividualSupplier : currentypeAll
      let best = IndividualQuery ? updatedBestIndividualSupplier : currentypeBest
      // const filteredSuppliers = currentData==='All Suppliers' ? all.filter((s) => s.supply_id === supplyname) : best.filter((s) => s.supply_id === supplyname)
      const filteredSuppliers = currentData==='All Suppliers' ? all.filter((s) => s.best_supply.includes(supplyname)) : best.filter((s) => s.best_supply.includes(supplyname))
      // const sourceList = currentData === 'All Suppliers' ? all : best
      const sourceList = filteredSuppliers

      if (!sourceList || sourceList.length === 0) {
        setSupplierList([]);
        setLoading(false)
        return;
      }

      const query = (searchQuery || "").toLowerCase();
      const filtered = query
        ? sourceList?.filter(s => (s.name || "").toLowerCase().includes(query))
        : sourceList;

      setSupplierList(filtered);
      setLoading(false)
    }
  }, [currentData, supplierType, groupedData,supplyname, searchQuery, updEssentialAllSupplier, updEssentialBestSupplier, updNonEssentialAllSupplier, updNonEssentialBestSupplier, updatedAllIndividualSupplier, updatedBestIndividualSupplier]);

  useEffect(()=>{
    if(supplyList.length>0) {
      setSupplyName(supplyList[0])
    }
    else {
      setSupplyName('No Supplies Found')
    }
  },[supplyList])

  useEffect(()=>{
    if(!IndividualQuery) {
     
      if(updEssentialAllSupplier.length> 0) {
        setSupplierType('Essential')
        setCurrentData('All Suppliers')
      }
      else {
        setSupplierType('Non-Essential')
        setCurrentData('All Suppliers')
      }
    }
  },[updEssentialAllSupplier, updNonEssentialAllSupplier])

  useEffect(() => {
    // Prevents rerun if rerender flag is set
    if (rerender === 1) return;
  
    if (source == 'FromScratch' || source == 'MapComponent') return;

    // Proceed only if suppliers are ready
    if (IndividualQuery) {
      if (updatedAllIndividualSupplier && updatedAllIndividualSupplier.length > 0) {
        // console.log(updatedAllIndividualSupplier, updatedBestIndividualSupplier, 'This is the log we want to see')
        const analyticsJSON = generateAnalyticsResponse(updatedBestIndividualSupplier, updatedAllIndividualSupplier);
        const updatedResult = {
          'Analytics_response': analyticsJSON,
          'latitude_longitude': user_lat_long,
          "vendor_summary": {
            "total_vendors_count": updatedAllIndividualSupplier.length,
            "best_vendors_count": updatedBestIndividualSupplier.length,
            "all_vendors_count": updatedAllIndividualSupplier.length
          }

        };

        // Call the async function correctly
        (async () => {
          try {
            if(lastChatId) {
              await storeResultData(lastChatId,updatedResult,'Query to Search Vendors')
            }
            // console.log("✅ Analytics saved to chat history");
          } catch (err) {
            createDiagnostic("Suppliers", `Failed to Update Doc due to ${JSON.stringify(err)} in Vendors`,lastChatId)
            // console.error("❌ Failed to update doc:", err);
          }
        })();
      }
    }
    if (!IndividualQuery) {
      if (updNonEssentialAllSupplier && updNonEssentialAllSupplier.length > 0 || updEssentialAllSupplier && updEssentialAllSupplier.length > 0) {
        // console.log(updNonEssentialAllSupplier, updNonEssentialAllSupplier, 'This is the log we want to see')
        const analyticsJSON = generateAnotherAnalyticsResponse(updEssentialBestSupplier, updEssentialAllSupplier, updNonEssentialBestSupplier, updNonEssentialAllSupplier);
        const updatedResult = {
          'Analytics_response': analyticsJSON,
          'latitude_longitude': user_lat_long,
          "vendor_summary": {
            "total_vendors_count": updEssentialAllSupplier.length + updNonEssentialAllSupplier.length,
            "essential_vendors_count": updEssentialAllSupplier.length,
            "non_essential_vendors_count": updNonEssentialAllSupplier.length
          }
        };

        // Call the async function correctly
        (async () => {
          try {
            if(lastChatId) {
              await storeResultData(lastChatId,updatedResult,'Query to Search Vendors')
            }
            // console.log("✅ Analytics saved to chat history");
          } catch (err) {
            createDiagnostic("Suppliers", `Failed to Update Doc due to ${JSON.stringify(err)} in Vendors`,lastChatId)
            // console.error("❌ Failed to update doc:", err);
          }
        })();
      }

    }
  }, [updatedBestIndividualSupplier, updatedAllIndividualSupplier, updEssentialAllSupplier, updEssentialBestSupplier, updNonEssentialAllSupplier, updNonEssentialBestSupplier]);

  useEffect(() => {
    if ((source === "SolutionScreen" || source === 'FromScratch')) {
      if (supplierList && supplierList.length > 0) {
        const newVendor = supplierList[0];
        setSelectedVendor(newVendor);
      } else {
        setSelectedVendor(null);
      }
    }
  }, [supplierList]);

  const [map_bestSuppliers, setMapBestSuppliers] = useState([]);
  const [map_allSuppliers, setMapAllSuppliers] = useState([]);
  const [map_result, setMapResult] = useState([]);

  // Helper function to safely parse coordinates
  const parseCoordinates = (coordStr) => {
    if (!coordStr) return null;

    // Handle array case
    if (Array.isArray(coordStr)) {
      return coordStr.length === 2 &&
        !isNaN(coordStr[0]) &&
        !isNaN(coordStr[1])
        ? coordStr
        : null;
    }

    // Handle string case
    if (typeof coordStr === 'string' && coordStr.includes(',')) {
      const [latStr, lngStr] = coordStr.split(',');
      const lat = parseFloat(latStr.trim());
      const lng = parseFloat(lngStr.trim());
      return !isNaN(lat) && !isNaN(lng) ? [lat, lng] : null;
    }

    return null;
  };

  useEffect(() => {
    const transformSupplier = (supplier, category) => {
      const coords = parseCoordinates(supplier.latitude_longitude);
      return {
        ...supplier,
        category,
        result_type: "Vendor",
        latitude_longitude: coords,  // Will be null if invalid
        user_lat_long: user_lat_long
      };
    };

    const shouldTransform = source === "SolutionScreen" || source === 'FromScratch';

    let tempall = IndividualQuery
      ? updatedAllIndividualSupplier
      : [...(updEssentialAllSupplier || []), ...(updNonEssentialAllSupplier || [])];

    let tempbest = IndividualQuery
      ? updatedBestIndividualSupplier
      : [...(updEssentialBestSupplier || []), ...(updNonEssentialBestSupplier || [])];

    setMapBestSuppliers(
      shouldTransform
        ? tempbest?.map(s => transformSupplier(s, "Best")) || []
        : []
    );

    setMapAllSuppliers(
      shouldTransform
        ? tempall?.map(s => transformSupplier(s, "General")) || []
        : []
    );
  }, [updatedAllIndividualSupplier, updEssentialAllSupplier, updEssentialBestSupplier, updNonEssentialAllSupplier, updNonEssentialBestSupplier, updatedBestIndividualSupplier, source, user_lat_long]);

  useEffect(() => {
    // Filter out suppliers with invalid coordinates before combining
    const validSuppliers = [
      ...map_allSuppliers?.filter(s => s?.latitude_longitude !== null),
      ...map_bestSuppliers?.filter(s => s?.latitude_longitude !== null)
    ];
    setMapResult(validSuppliers);
  }, [map_allSuppliers, map_bestSuppliers]);


  const handleVendorClick = (vendor) => {
    setSelectedVendor((prev) => {
      if (prev?.name === vendor.name) return prev; // same vendor, avoid unnecessary state update
      return vendor;
    });
  };

  const getLatLng = (latlngStr) => {
    if (!latlngStr) return [0, 0];
    const parts = latlngStr.split(",");
    const lat = parseFloat(parts[0]);
    const lng = parseFloat(parts[1]);
    if (isNaN(lat) || isNaN(lng)) return [0, 0];
    return [lat, lng];
  };

  const getLatLng2 = (latlngStr) => {
    if (!latlngStr) return [0, 0];
    const lat = parseFloat(latlngStr[0])
    const lng = parseFloat(latlngStr[1])
    if (isNaN(lat) || isNaN(lng)) return [0, 0];
    return [lat, lng];
  }

  useEffect(() => {
    if (source === 'MapComponent') {
      // console.log(result, 'This is the result passed from the map component....')
      setSelectedVendor(result)
      setLoading(false)
    }
  }, [result])

  const detailRef = useRef(null);
  useEffect(() => {
    if (detailRef.current) {
      detailRef.current.scrollTop = 0;
    }
  }, [selectedVendor]);

  const vendorLatLng = (source === "SolutionScreen" || source === 'FromScratch') ? getLatLng(selectedVendor?.latitude_longitude) : getLatLng2(selectedVendor?.latitude_longitude)

  const tempSource = rerender !== 1 ? source : 'FromScratch'
  // console.log(tempSource, source, ' okay from vendor')

  const coord = user_lat_long;
  // console.log(coord, 'This is the coordinates passed')
  const fixedCoord = source === "SolutionScreen" ? coord[0].split(',').map(Number).reverse() : source === "FromScratch" ? coord.slice().reverse() : null
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen w-screen">
        <LogoLoader text="Let's See Who's Got What You Need" />
      </div>
    );
  }

  if (tempFailure) {
    return (
      <NoResultsFound />
    )
  }

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655] overflow-hidden">
      <div className="w-[98%] h-[95%] mx-auto my-0 p-6 bg-white rounded-xl shadow-sm border border-white border-opacity-40 flex flex-col backdrop-blur-sm">
        {(source === "SolutionScreen" || source === 'FromScratch') && (<div className="flex items-center justify-between pb-4 mb-2 border-b border-[#B8D1F3]">
          <div className="flex items-center">
            <div className="p-3 mr-4 rounded-lg bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10">
              <FaFileAlt className="text-xl text-[#7AA6DA]" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-[#2C53A3]">{uiConfig?.['main_title'] || "Vendors List"}</h1>
              <p className="text-[#5A7EC7]">{uiConfig?.['sub_title'] || "Browse required supplies for your business"}</p>
            </div>
          </div>

          <div className='flex relative flex-row items-center gap-4 mr-4'>
            <div className="flex flex-row items-center bg-white border border-[#41b655] rounded-full overflow-hidden p-1 relative w-fit h-fit">
              <div
                onClick={() => setViewMode("Suppliers")}
                className={`p-1 px-3 text-sm  flex flex-row items-center justify-center font-semibold cursor-pointer transition-all duration-300 ${viewMode === "Suppliers"
                  ? "bg-[#0e2044] text-white"
                  : "text-[#0e2044] bg-white"
                  } rounded-l-full`}
              >
                {uiConfig?.['view_mode_suppliers'] || "Suppliers"}
              </div>
              <div
                onClick={() => setViewMode("Map")}
                className={`p-1 px-3 text-sm font-semibold flex flex-row items-center justify-center cursor-pointer transition-all duration-300 ${viewMode === "Map"
                  ? "bg-[#0e2044] text-white"
                  : "text-[#0e2044] bg-white"
                  } rounded-r-full`}
              >   
              {uiConfig?.['view_mode_map'] || "Map"} 
              </div>
            </div>
            {source === 'SolutionScreen' && rerender!==1 && (
              <Backtochat text='Back to Chat' />
            )}
          </div>
        </div>)}

        {(source === "SolutionScreen" || source === 'FromScratch') && viewMode === 'Suppliers' && (<div className="relative mb-2 flex flex-row gap-2 w-full">
          <div className='relative flex w-full flex-row gap-4'>
            <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#5A7EC7]" />
            <input type="text" placeholder="Search by Vendor name..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-12 pr-4 py-2 w-full border border-[#B8D1F3] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF80AB]/30 focus:border-[#7AA6DA] placeholder-[#5A7EC7]/70 text-[#2C53A3] bg-white bg-opacity-90" />
          </div>
        </div>)}

        {viewMode === 'Suppliers' && (<div className="flex flex-1 h-full w-full overflow-hidden bg-white rounded-lg border border-[#B8D1F3]">
          {(source === "SolutionScreen" || source === 'FromScratch') && (<div className="w-1/3 border-r border-[#B8D1F3] flex flex-col">
            {!IndividualQuery && (<div className='relative flex flex-row border-b border-gray-200 pt-2 w-full'>
              <div className='relative flex flex-col gap-1 cursor-pointer items-center w-full' onClick={() => { setSupplierType('Essential') }}>
                <button
                  onClick={() => { setSupplierType('Essential') }}
                  className={`px-3 py-1 text-xs cursor-pointer text-black font-semibold transition-all`}
                >
                  {uiConfig?.['vendor_essential_tab'] || "Essential Suppliers"}

                </button>
                <div className={`${supplierType === "Essential" ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
              </div>
              <div className='relative flex flex-col gap-1 cursor-pointer items-center w-full' onClick={() => { setSupplierType('Non-Essential') }}>
                <button
                  onClick={() => { setSupplierType('Non-Essential') }}
                  className={`px-3 py-1 text-xs cursor-pointer text-black font-semibold transition-all`}
                >
                  {uiConfig?.['vendor_non_essential_tab'] || "Non Essential Suppliers"}
                </button>
                <div className={`${supplierType === "Non-Essential" ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
              </div>
            </div>)}
            <div className='relative inline-block border-b p-2' ref={supplyNode}>
                <div onClick={() => setSupplyDropdownOpen(!supplydropdownopen)} className={` ${supplyList.length>0 ? "" : "pointer-events-none opacity-50"} flex rounded-md  justify-center items-center gap-3 py-1  w-full`}><span className='text-sm select-none font-semibold'>{supplyname}</span><span className='text-md font-bold absolute top-4 right-2'>{!supplydropdownopen ? (<IoIosArrowDown/>) : (<IoIosArrowUp/>)}</span></div>
                <div className={`absolute border overflow-y-auto max-h-[350px] border-black p-2 flex flex-col gap-2 left-0 z-40 mt-1  w-full rounded-md bg-white  transition-all ${supplydropdownopen ? 'top-full opacity-100 visible': 'top-[110%] invisible opacity-0'}`}>
                    {supplyList.map((supply, index) => (
                        <div key={`supply${index}`}  className={`rounded-lg  py-2 px-5 flex items-center text justify-center transition-all text-xs md:text-md col-span-1 border border-black text-center font-semibold tracking-wide whitespace-nowrap hover:bg-[#0e2044] cursor-pointer hover:text-white ${supplyname === supply ? "bg-[#0e2044] text-white" : "bg-[#f2f2f2]"}`} onClick={(e)=> {setSupplyName(e.currentTarget.textContent), setSupplyDropdownOpen(false)}}>{supply}</div>
                    ))}                    
                </div>
            </div>
            <div className="relative flex justify-center border-b border-gray-200 flex-row gap-2 pt-2 w-full">
              <div className='relative flex flex-col gap-1 cursor-pointer items-center w-full' onClick={() => { setCurrentData('Best Suppliers') }}>
                <button
                  onClick={() => { setCurrentData('Best Suppliers') }}
                  className={`px-3 py-1 text-xs select-none cursor-pointer flex flex-row gap-2 items-center text-green-500 font-semibold transition-all`}
                >
                  <FaAward size={20} />{uiConfig?.['vendor_best_suppliers_tab'] || "Best Suppliers"}
                </button>
                <div className={`${currentData === "Best Suppliers" ? 'bg-green-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-green-500 rounded-full transition-width duration-300`}></div>
              </div>
              <div className='relative flex flex-col gap-1 cursor-pointer items-center w-full' onClick={() => { setCurrentData('All Suppliers') }}>
                <button
                  onClick={() => { setCurrentData('All Suppliers') }}
                  className={`px-3 py-1 text-xs select-none cursor-pointer flex flex-row gap-2 items-center text-orange-500 font-semibold transition-all`}
                >
                  <FaList size={20} />{uiConfig?.['vendor_all_suppliers_tab'] || "All Suppliers"}
                </button>
                <div className={`${currentData === "All Suppliers" ? 'bg-orange-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-orange-500 rounded-full transition-width duration-300`}></div>
              </div>
            </div>
            <div className="overflow-y-auto flex-1 list-view bg-gradient-to-b from-[#E6F0FA]/10 to-transparent">
              {supplierList && supplierList.length > 0 ? (
                <div className="space-y-2 p-2">
                  {supplierList?.map((vendor, idx) => (
                    <div
                      key={idx}
                      className={`p-4 cursor-pointer rounded-lg transition-all duration-200 ${selectedVendor?.name === vendor.name
                        ? "bg-[#41b655] bg-opacity-20 border-l-4 border-[#41b655] "
                        : "bg-[#41b655] bg-opacity-10 border-none"
                        }`}
                      onClick={() => { handleVendorClick(vendor) }}
                    >
                      <div className="flex justify-between items-start">
                        <h3 className={`font-medium ${selectedVendor?.name === vendor.name ? "text-black" : "text-[#3b69c5]"
                          }`}>
                          {vendor.name}
                        </h3>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6">
                  <div className="p-4 rounded-full mb-3 bg-gradient-to-r from-[#FF80AB]/20 to-[#9575CD]/20">
                    <FaSearch className="text-2xl text-[#5A7EC7]" />
                  </div>
                  <h3 className="text-lg font-medium text-[#2C53A3]">{uiConfig?.['no_vendors_found'] || "No Vendors found"}</h3>
                  <p className="text-[#5A7EC7]">Try a different search term or view mode</p>
                </div>
              )}
            </div>
          </div>)}

          {selectedVendor && (
            <div className={`${source === "MapComponent" ? 'w-full' : 'w-2/3'} flex flex-col`}>
              <div ref={detailRef} className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6 full flex-1 overflow-y-auto scrollbar-hide">
                {selectedVendor ? (

                  <div className='relative flex flex-col gap-8'>
                    <div className='relative flex flex-row gap-2 justify-start items-center'>
                      <div className='relative flex flex-row gap-2'>
                        <span className='p-3 rounded-lg flex items-center justify-center relative bg-blue-100'><FaStoreAlt className='text-blue-800' /></span>
                        <div className='relative flex flex-col justify-center gap-0.5'>
                          <h2 className="text-xl font-bold text-blue-700">{selectedVendor.name}</h2>
                          {/* {selectedVendor.category && (<h3 className='relative text-md'>{selectedVendor.category}</h3>)} */}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col flex-1 gap-4">
                      <h2 className="text-xl font-bold text-gray-800 flex gap-3 flex-row items-center">
                        <FaChartBar className="text-blue-700" />
                        {uiConfig?.['vendor_statistics'] || "Company Statistics"}
                      </h2>
                      <div className="grid grid-cols-4 gap-4">
                        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                          <div className="text-3xl font-bold text-blue-700">{selectedVendor.years_of_experience}</div>
                          <p className="text-gray-600 mt-1">{uiConfig?.['years_of_experience_label'] || 'Years Experience'}</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                          <div className="text-3xl font-bold text-blue-700">{selectedVendor.no_of_services}</div>
                          <p className="text-gray-600 mt-1">{ uiConfig?.['services_offered_label'] || 'Services Offered'}</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                          <div className="text-3xl font-bold text-blue-700">{selectedVendor.no_of_employees}</div>
                          <p className="text-gray-600 mt-1">{uiConfig?.['employees_label'] || 'Employees'}</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm text-center">
                          <div className="text-3xl font-bold text-blue-700">500</div>
                          <p className="text-gray-600 mt-1">{uiConfig?.['projects_completed_label'] || 'Projects Completed'}</p>
                        </div>
                      </div>
                    </div>

                    {selectedVendor && selectedVendor.portfolio && (<div className="relative flex flex-col gap-4">
                      <h2 className="text-xl font-bold text-gray-800 flex flex-row gap-3 items-center">
                        <FaInfoCircle className="text-blue-700" />
                        Overview
                      </h2>
                      <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                        <p className="text-gray-700 leading-relaxed">
                          {selectedVendor.portfolio}
                        </p>
                      </div>
                    </div>)}

                    <div className="relative flex flex-col gap-4">
                      <h2 className="text-xl font-bold text-gray-800 flex flex-row gap-3 items-center">
                        <MdPeopleAlt className="text-blue-700" />
                        {uiConfig?.['past_clients_label'] || "Past Clients"}
                      </h2>
                      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="bg-blue-50 p-3 border-b border-gray-200">
                          {selectedVendor.no_of_past_clients}
                        </div>
                      </div>
                    </div>


                    {selectedVendor && selectedVendor.supplies && (<div className="relative flex flex-col gap-2">
                      <h2 className="text-xl font-bold text-gray-800 mb-4 flex flex-row gap-3 items-center">
                        <AiFillProduct className='text-blue-700' />
                        {uiConfig?.['supplies_and_capacities_label'] || "Supplies & Capacities"}
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedVendor.supplies && selectedVendor.supplies.map((data, index) => (
                          <div key={index} className={`bg-white rounded-lg border border-gray-200 overflow-hidden ${data.supply===supplyname ? 'shadow-[0px_0px_10px_0px_rgba(0,0,0,0.98)] transform scale-[1.03]' : ''}`}>
                            <div className="bg-blue-50 p-3 border-b border-gray-200">
                              <div className="flex justify-between items-center">
                                <span className="font-medium text-gray-800">{data.supply}</span>
                                <span className="bg-[#0e2044] text-white text-xs px-2 py-0.5 rounded-full flex flex-row gap-1 items-center">{data.maximum_supply_capacity} {data.uom}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>)}

                    {selectedVendor && selectedVendor.certifications && (<div className='relative flex flex-col gap-4'>
                      <h2 className="text-xl font-bold text-gray-800 flex items-center flex-row gap-3">
                        <CertificateIcon strokeWidth={2} className="text-blue-700" />
                        {uiConfig?.['certifications_label'] || "Certifications"}
                      </h2>
                      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm flex flex-col">
                        <div className="relative grid grid-cols-2 gap-4">
                          {selectedVendor.certifications.split(',').filter(opt => opt.trim() !== "").map((opt, i) => (
                            <div key={i} className="flex flex-row gap-1 items-center col-span-1">
                              {/* <div className="bg-green-100 p-1 rounded-full"> */}
                                <CheckIcon size={20} className="text-green-700" />
                              {/* </div> */}
                              <span className="text-gray-700 font-semibold">{opt}</span>
                            </div>))}
                        </div>
                      </div>
                    </div>)}

                    {source !== "MapComponent" && (<div className="relative flex flex-col gap-2">
                      <h4 className="text-xl font-semibold text-gray-800 flex flex-row gap-2 items-center">
                        <FaLocationDot className='text-blue-700' size={20} />
                        {uiConfig?.['vendor_location_label'] || "Location"}
                      </h4>
                      <div className="relative h-[250px] w-full p-4">
                        {source !== "MapComponent" && (<MapBoxMap
                          lat={vendorLatLng[0]}  // Vendor lat
                          lng={vendorLatLng[1]}  // Vendor lng
                          source="FromVendor"
                          vendorCoord={fixedCoord} // Property coord [lng, lat]
                          vendorName={selectedVendor?.name}
                        />)}
                      </div>
                    </div>)}
                  </div>
                ) : (
                  <div>
                    <h1>Please Select a Vendor</h1>
                  </div>
                )
                }
              </div>
            </div>
          )}
        </div>)}

        {viewMode === 'Map' && (
          <div className='relative h-full w-full flex items-center justify-center overflow-hidden'>
            {source === "FromScratch" && (
              <SingleMap selectedProperty={propertyData} intension="From Vendor Screen" />
            )}
            {source !== "FromScratch" && (
              <MapComponent solutions={map_result} source="SolutionScreen" intension={source === "FromScratch"? "For All Vendor Listing" :"For Property to Vendor" }/>
            )}            
            {/* <MapComponent solutions={map_result} source={tempSource} intension={source == "FromScratch"? "For All Vendor Listing" :"For Property to Vendor" }/> */}
          </div>
        )}
      </div>

    </div>
  );
}

export default Vendorresult;