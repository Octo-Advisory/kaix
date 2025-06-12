import React, { useEffect, useRef,useState,useContext } from 'react';
import { Chart } from 'chart.js/auto';
import './Industryresult.css'
import {
  FaMapMarkerAlt,  FaRegQuestionCircle,  FaRoad,  FaTrain,  FaShip,  FaPlane,  FaHandHoldingUsd,  FaFileInvoice,  FaChartLine,  FaInfoCircle,FaCheckCircle,FaArrowLeft,FaArrowRight,FaIndustry,FaRuler,FaCity,FaBus,FaUsers,FaBoxes, FaTag,FaShieldAlt,FaCheck,FaExclamationTriangle,FaChevronRight,FaRegCheckCircle,FaRegDotCircle,FaTimesCircle
} from 'react-icons/fa';
import { IoIosArrowForward } from 'react-icons/io';
import { RiShipFill } from "react-icons/ri";
import { BsFillPencilFill,BsPatchCheckFill } from "react-icons/bs";
import { MdOfflineBolt, MdOutlineTypeSpecimen } from "react-icons/md";
import { FaCircleXmark, FaTriangleExclamation } from 'react-icons/fa6';
import { FaChevronDown, FaChevronUp } from "react-icons/fa";
import { FaXmark } from "react-icons/fa6";
import { FrappeContext } from 'frappe-react-sdk';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import MapComponent from '../MapComponent/MapComponent';
import Backtochat from '../Backtochat/Backtochat';
import Model from './Model';
import { useFrappeGetDoc } from 'frappe-react-sdk';
// import { result } from './data';
import Details from '../Details/Details';
import { isPlain } from '@reduxjs/toolkit';
import Approvalresult from './Approvalresult';
import GoogleMap from '../MapComponent/GoogleMap';
import LogoLoader from '../Responseloader/LogoLoader';
import Incentiveresult from './Incentiveresult';
import Vendorresult from './Vendorresult';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

const IndustryResultScreen = ({ result,source }) => {
  const employmentChartRef = useRef(null);
  const [showEssentialMaterials, setShowEssentialMaterials] = useState(true);

  const [activeTab, setActiveTab] = useState('Property Details')
  const [activeProperty, setActiveProperty] = useState(0)
//   const selectedProperty = fullData.find(data=> data.rank === activeProperty)
const chartInstanceRef = useRef(null); // To destroy if needed later
const { call } = useContext(FrappeContext);
const [approvalsWindow,setApprovalWindow] = useState(false)
const [approvalsToSend, setApprovalsToSend] = useState()
const [incentivesWindow, setIncentivesWindow] = useState(false)
const [incentivesToSend, setIncentivesToSend] = useState()
const [vendorsWindow, setVendorsWindow] = useState(false)
const [vendorsToSend, setVendorsToSend] = useState()
const [propertyIndex, setPropertyIndex] = useState(1)
const [showLocalLaws,setShowLocalLaws] = useState(false)


ChartJS.register(ArcElement, Tooltip, Legend);
  const data = {
    labels: ['Skilled', 'Semi-Skilled', 'Unskilled'],
    datasets: [{
      data: [25, 40, 35],
      backgroundColor: ['#0e2044', '#41b655', '#f59e0b'],
      borderWidth: 1,
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false, // This matches your container styling
    plugins: {
      legend: {
        position: 'top', // or 'bottom', 'left', 'right'
      },
    },
  };
// useEffect(() => {
//   if (activeTab !== 'Property Details') return;

//   const canvas = employmentChartRef.current;
//   if (!canvas) return;

//   requestAnimationFrame(() => {
//     const ctx = canvas.getContext('2d');
//     if (!ctx) return;

//     if (chartInstanceRef.current) {
//       chartInstanceRef.current.destroy();
//     }

//     chartInstanceRef.current = new Chart(ctx, {
//       type: 'doughnut',
//       data: {
//         labels: ['Skilled', 'Semi-Skilled', 'Unskilled'],
//         datasets: [{
//           data: [25, 40, 35],
//           backgroundColor: ['#0e2044', '#41b655', '#f59e0b'],
//           borderWidth: 1,
//         }]
//       },
//       options: {
//         responsive: true,
//         maintainAspectRatio: false,
//       }
//     });
//   });

//   return () => {
//     if (chartInstanceRef.current) {
//       chartInstanceRef.current.destroy();
//       chartInstanceRef.current = null;
//     }
//   };
// }, [activeTab]);

  const [visibleTooltips, setVisibleTooltips] = useState({
    tooltip1: false,
      tooltip2: false,
      tooltip3: false,
      tooltip4: false,
      tooltip5: false,
      tooltip6: false,
    });
  
    const handleMouseEnter = (id) => {
      setVisibleTooltips(prev => ({ ...prev, [id]: true }));
    };
    
    const handleMouseLeave = (id) => {
      setVisibleTooltips(prev => ({ ...prev, [id]: false }));
    };
    
    const [activeButton, setActiveButton] = useState('Property Details')
    
    const analytics_response = source==="MapComponent" ? '' : result["Analytics_response"]
    console.log("analytics respon",analytics_response);
    // console.log("analytics responseee Final",JSON.parse(analytics_response['final_scoring_df']));
    const [isLoading, setIsLoading] = useState(true);
    const [selectedProperty,setSelectedProperty] = useState()
    const [solutions, setSolutions] = useState([])
  
    const fetchData = async (property) => {
      try {
        const response = await fetch(`/api/resource/Survey No?fields=["*"]&filters=[["name","=","${property}"]]&order_by=modified asc`, {
          method: 'GET',
          headers: {
            'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        const data = await response.json();
        return data.data
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    }

    const fetchAreaName = async(area)=> {
      try {
        const response = await fetch(`/api/resource/Area?fields=["area_name"]&filters=[["name","=","${area}"]]`, {
          method: 'GET',
          headers: {
            'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        const data = await response.json();
        console.log(data,'area data called')
        return data.data[0]
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    }

    const getApprovals = async (approvalList) => {
  try {
    const results = [];

    for (const approval of approvalList) {
      const response = await fetch(
        `/api/resource/Licenses and Approvals Type?fields=["license_approval", "government_department", "delivery_schedule_in_working_days", "name"]&filters=${encodeURIComponent(JSON.stringify([["name", "=", approval]]))}&order_by=modified asc`,
        {
          method: 'GET',
          headers: {
            'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) throw new Error(`Error: ${response.statusText}`);

      const data = await response.json();
      results.push(data.data[0]); // assuming it returns an array
    }

    return results;
  } catch (error) {
    console.error('Error fetching data:', error);
    return [];
  }
};

 const getIncentives = async (incentiveList) => {
  try {
    const results = [];

    for (const incentive of incentiveList) {
      const response = await fetch(
        `/api/resource/Incentive?fields=["incentive_name", "incentive_type", "incentive_rank", "name"]&filters=${encodeURIComponent(JSON.stringify([["name", "=", incentive]]))}&order_by=modified asc`,
        {
          method: 'GET',
          headers: {
            'Authorization': 'token d3de1e0e4e25846:51fd8e403a19045',
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
    console.error('Error fetching incentives:', error);
    return [];
  }
};

    const fetchPropertyData = async (analytics_response) => {
      let preaparedSolutions = [];
      const final_scoring_df = JSON.parse(analytics_response['final_scoring_df'])
      const property_id = final_scoring_df["Property_ID"]
      
      const Essential_supply_vendor_lookup_df = JSON.parse(analytics_response['Essential_supply_vendor_lookup_df'])
      const nonEssential_supply_vendor_lookup_df = JSON.parse(analytics_response['Non_essential_supply_vendor_lookup_df'])
      const Employment_lookup_df = JSON.parse(analytics_response['Employment_lookup_df'])
      const Solution_lookup_df = JSON.parse(analytics_response['Solution_lookup_df'])
      const Approval_lookup_df = JSON.parse(analytics_response['Approval_lookup_df'])
      console.log('This is Vendor Lookup for Essential', Essential_supply_vendor_lookup_df)
      console.log('This is Vendor Lookup for Non Essential', nonEssential_supply_vendor_lookup_df)
      console.log('This is Employment Lookup', Employment_lookup_df)
      console.log('This is Solution Lookup', Solution_lookup_df)
      console.log('This is Approval Lookup', Approval_lookup_df)
  
      const promises = Object.entries(property_id).map(async ([key, value]) => {
        try {
          
          const get_data = await fetchData(value)
          const data = get_data[0]
          const approval_data = await getApprovals(Approval_lookup_df['approval_id'][key])
          const incentive_data = await getIncentives(Solution_lookup_df['incentive_id'][key])

          if (data) {
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
  
            const essential_vendors_id = Essential_supply_vendor_lookup_df['vendor_id'] ? Essential_supply_vendor_lookup_df["vendor_id"][key] : ''
            const non_essential_vendors_id = nonEssential_supply_vendor_lookup_df['vendor_id'] ? nonEssential_supply_vendor_lookup_df["vendor_id"][key] :  ''
            if (Essential_supply_vendor_lookup_df["No_of_vendors_found"][key] && Array.isArray(Essential_supply_vendor_lookup_df["No_of_vendors_found"][key]) && Essential_supply_vendor_lookup_df["No_of_vendors_found"][key].length > 0) {
              const ess_supply_id = Essential_supply_vendor_lookup_df["supply_id"][key] || [];
              const ess_No_of_vendors_found = Essential_supply_vendor_lookup_df["No_of_vendors_found"][key] || [];
              const ess_Distance = Essential_supply_vendor_lookup_df["Distance"][key] || [];
              ess_supply_id.forEach((supply, index) => {
                if (ess_No_of_vendors_found[index] !== undefined && ess_Distance[index] !== undefined) {
                  const supply_vendor = {
                    supply: supply,
                    total_vendor: ess_No_of_vendors_found[index],
                    nearest_vendor_distance: ess_Distance[index],
                    status: get_status_for_distance(ess_Distance[index])
                  };
                  essential_supply_and_vendor.push(supply_vendor);
                }
              });
            }
  
            if (nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key] && Array.isArray(nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key]) && nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key].length > 0) {
              const noness_supply_id = nonEssential_supply_vendor_lookup_df["supply_id"][key] || [];
              const noness_No_of_vendors_found = nonEssential_supply_vendor_lookup_df["No_of_vendors_found"][key] || [];
              const noness_Distance = nonEssential_supply_vendor_lookup_df["Distance"][key] || [];
  
              noness_supply_id.forEach((supply, index) => {
                if (noness_No_of_vendors_found[index] !== undefined && noness_Distance[index] !== undefined) {
                  const supply_vendor = {
                    supply: supply,
                    total_vendor: noness_No_of_vendors_found[index],
                    nearest_vendor_distance: noness_Distance[index],
                    status: get_status_for_distance(noness_Distance[index])
                  };
                  nonessential_supply_and_vendor.push(supply_vendor);
                }
              });
            }
  
            const emp_skill_type = Employment_lookup_df['Skill_Type'][key]
            const count = Employment_lookup_df[`${emp_skill_type}`][key]
            const skilled_no = Employment_lookup_df['Skilled'][key] || 0
            const semiskilled_no = Employment_lookup_df['Semi-skilled'][key] || 0
            const unskilled_no = Employment_lookup_df['Unskilled'][key] || 0

            const incenetives = []
            // const incentive_name = Solution_lookup_df['incentive_name'][key]
            // const incentive_type = Solution_lookup_df['incentive_type'][key]
            // const incentive_rank = Solution_lookup_df['incentive_rank'][key]

            incentive_data.forEach((incentive,index)=>{
              const inc = { incentive_id:incentive.name, incentive_name: incentive.incentive_name, incentive_rank: incentive.incentive_rank, incentive_type: incentive.incentive_type }
              incenetives.push(inc)
            })
            // incentive_name.forEach((incentive, index) => {
            //   const inc = { incentive_name: incentive, incentive_rank: incentive_rank[index], incentive_type: incentive_type[index] }
            //   incenetives.push(inc)
            // })

            
            
            // const final_score = final_scoring_df['aggregated_score'][key]
            // const aggregated_score = final_scoring_df['Property-Wise Approval Score (PWAS)'][key]
            
            // const approval_name = Approval_lookup_df["approval_name"][key]
            // const government_department = Approval_lookup_df["government_department"][key]
            // const online_or_offline = Approval_lookup_df["online_or_offline"][key]
            // const stages = Approval_lookup_df["stages"][key]
            // const time_taken = Approval_lookup_df["time_taken"][key]
            const total_effective_time = Approval_lookup_df['Efficient Approval Time'][key]
            const online_percentage = Approval_lookup_df['Online Percentage'][key]
            const pre_requisite = Approval_lookup_df['Pre-Requisite'][key]
            const pre_establishment = Approval_lookup_df['Pre-Establishment'][key]
            const pre_operation = Approval_lookup_df['Pre-Operation'][key]
            const others = Approval_lookup_df['Others'][key]
            const mode_requisite = Approval_lookup_df['Mode_Pre-Requisite'][key]
            const mode_establishment = Approval_lookup_df['Mode_Pre-Establishment'][key]
            const mode_operation = Approval_lookup_df['Mode_Pre-Operation'][key]
            const mode_others = Approval_lookup_df['Mode_Others'][key]
            const approvals = []

            approval_data.forEach((approval,index)=> {
              const appr = {
                approval_id: approval.name,
                approval_name: approval.license_approval,
                government_department: approval.government_department,
                time_taken: approval.delivery_schedule_in_working_days
              }
              approvals.push(appr)
            })
  
            // approval_name.forEach((approval, index) => {
            //   const appr = {
            //     approval_name: approval_name[index],
            //     government_department: government_department[index],
            //     online_or_offline: online_or_offline[index],
            //     stages: stages[index],
            //     time_taken: time_taken[index]
            //   }
            //   approvals.push(appr)
            // })

            const road_transport = availability_of_local_transportation == 'Yes' ? 'good' : 'bad'
            const property_id = final_scoring_df['Property_ID'][key]
            const score = final_scoring_df['aggregated_score'][key]
            const areaName = await fetchAreaName(area)
            console.log(areaName,'his is areaname')
            const solution = {
            //   address: `${area || city}, ${district}, ${state}`,
              property_id: property_id,
              score: score,
              area:`${areaName.area_name}`,
              address:`${city}, ${state}`,
              property_type: property_type,
              total_area: area_acre,
              latitude_longitude: latLongArray,
              business_location_type: business_location_type || 'GIDC',
              availability_of_local_transportation: road_transport,
              seaport: { distance: distance_from_nearest_seaport, status: get_status_for_distance(distance_from_nearest_seaport) },
              airport: { distance: distance_from_nearest_airport, status: get_status_for_distance(distance_from_nearest_airport) },
              power: { distance: distance_from_power_source, status: get_status_for_distance(distance_from_power_source) },
              railway: { distance: distance_from_nearest_railway_station, status: get_status_for_distance(distance_from_nearest_railway_station) },
              essential_vendors: essential_supply_and_vendor,
              nonessential_vendors: nonessential_supply_and_vendor,
              essential_vendors_id:essential_vendors_id,
              non_essential_vendors_id:non_essential_vendors_id,
              employement: { type: emp_skill_type, count: count },
              skilled_no: skilled_no,
              semiskilled_no: semiskilled_no,
              unskilled_no: unskilled_no,
              incentives: incenetives,
              approvals: approvals,
              pre_requisite:pre_requisite,
              pre_establishment: pre_establishment,
              pre_operation:pre_operation,
              others:others,
              mode_establishment:mode_establishment,
              mode_operation:mode_operation,
              mode_requisite:mode_requisite,
              mode_others:mode_others,
              total_effective_time:total_effective_time,
              online_percentage:online_percentage,
              road_connectivity: { distance: road_connectivity, status: get_status_for_distance(road_connectivity) },
              boundary_coordinates: boundary_coordinates,
              result_type: "Industry_Result"
            }
            preaparedSolutions.push(solution)
          }
        } catch (error) {
          console.log("error is ❌", error);
        }
      });
  
      await Promise.all(promises);
      setSolutions(preaparedSolutions);
    };

     useEffect(() => {
      if(source==="SolutionScreen"){
        const loadPropertyData = async () => {
          await fetchPropertyData(analytics_response);
          setIsLoading(false);
        };
        loadPropertyData();
      }
      }, []);
  
useEffect(() => {
  console.log(solutions, selectedProperty);
  if (solutions) {
    let tempsolutions = solutions.sort((a,b)=> b.score - a.score)
    setSelectedProperty(tempsolutions[0])
  }
}, [solutions]);

useEffect(()=>{
  console.log(result,'this is the result')
  if(source==="MapComponent") {
    setSelectedProperty(result)
  }
},[result])

useEffect(()=>{
  console.log( selectedProperty, 'this are the approvals');
},[selectedProperty])

const gridPart  = useRef(null)
   useEffect(() => {
    if (gridPart.current) {
      gridPart.current.scrollTop = 0;
    }
  }, [selectedProperty]);

function createVendorData(essential, nonessential) {
  if(!essential && !nonessential){return}
  const allVendors = [...essential, ...nonessential];
  const vendorData = {
    vendor_id: {},
  };


  allVendors.forEach((item, index) => {
    const idx = index.toString();
    vendorData.vendor_id[idx] = item;
  });

  return {
    Analytics_response: {
      "Unfiltered All Supplier": JSON.stringify(vendorData)
    },
    latitude_longitude: {}
  };
}

const handleShowVendor = () => {
   const data = createVendorData(selectedProperty?.essential_vendors_id, selectedProperty?.non_essential_vendors_id);
  setVendorsToSend(data);
  setVendorsWindow(true)
}
function createIncentiveData(incentives) {
  const incentiveData = {
    "Incentive ID": {},
    "Level": {},
  };

  incentives.forEach((item, index) => {
    const idx = index.toString();
    incentiveData["Incentive ID"][idx] = item.incentive_id;
    incentiveData["Level"][idx] = ''  
  });

  return incentiveData

}
const handleShowIncentive = () => {
   const data = createIncentiveData(selectedProperty?.incentives);
  setIncentivesToSend(data);
  setIncentivesWindow(true)
}
function createApprovalData(approval) {
  const approvalData = {
    "Approval ID": {},
    "Level": {},
    "aggregated_score": {},
    
  };

  approval.approvals.forEach((item, index) => {
    const idx = index.toString();
    approvalData["Approval ID"][idx] = item.approval_id;
    approvalData["Level"][idx] = ''  
    approvalData["aggregated_score"][idx] = ''
  });

  return {
    "Approval Data": JSON.stringify(approvalData),
    "Pre-Requisite": approval.pre_requisite,
    "Pre-Operation":approval.pre_operation,
    "Pre-Establishment":approval.pre_establishment,
    "Others":approval.others,
    "Online Percentage": approval.online_percentage,
    "Total Effective Time": approval.total_effective_time,
    "Mode_Pre-Requisite":approval.mode_requisite,
    "Mode_Pre-Operation":approval.mode_operation,
    "Mode_Pre-Establishment": approval.mode_establishment,
    "Mode_Others":approval.mode_others
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

      const defaultIcon = L.icon({
            iconUrl: markerIconPng,
            iconSize: [25, 41],
            iconAnchor: [12, 41]
        });

      const handleLocalLaws = ()=> {
        if(showLocalLaws) {
          setShowLocalLaws(false)
        }
        else {
          setShowLocalLaws(true)
        }
      }
      
      const gridRef = useRef(null)
      useEffect(()=>{
        if(showLocalLaws) {
          if (gridRef.current) {
            gridRef.current.scrollTop = gridRef.current.scrollHeight;
          }
        }
      },[showLocalLaws])
      
      const mapRef = useRef(null);
  
      useEffect(() => {
          if (mapRef.current && selectedProperty.latitude_longitude) {
              mapRef.current.setView(selectedProperty.latitude_longitude, 13);
          }
      }, [selectedProperty]);

      useEffect(()=>{
        if(showLocalLaws){
          setShowLocalLaws(false)
        }
        if(gridRef.current) {
          gridRef.current.scrollTop = 0;
        }
      },[selectedProperty])
      
     

      useEffect(()=>{
        console.log(solutions,'this is the solutions prepared')
      },[solutions])

      const shouldRender = source === "SolutionScreen" ? solutions && selectedProperty : source === "MapComponent"? selectedProperty: false; // fallback if needed


  return (
    <>
    {shouldRender ? (
        <div className='relative flex flex-col w-screen h-screen'>
      {source==='SolutionScreen' && (<div className='sticky top-0 left-0 w-full h-fit flex flex-col z-99  bg-white border-b border-gray-300'>
        <div className='relative w-full h-12 p-4 flex flex-row justify-between mb-4'>
          <div className='relative flex flex-row gap-2 items-center'>
            <h2 className='relative text-2xl font-semibold'>Industrial Property Solutions</h2>
            <div className='max-h-fit max-w-fit h-fit w-fit relative text-xs bg-blue-200 bg-opacity-20 text-blue-500 py-2 px-4 flex flex-row gap-2 rounded-full items-center hover:cursor-default'><span className = 'rounded-full h-2 w-2 bg-blue-500'></span> Want the best property to build a Cement Industry</div>
          </div>
          <Backtochat />
        </div>

        <div className='relative flex flex-row gap-6 w-full h-10 px-4 pb-3 justify-start items-center border-b border-gray-300'>
          <div  className={` relative h-full flex items-center justify-center px-2 rounded-md border border-gray-200 hover:cursor-pointer ${activeButton === 'Property Details' ? 'bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 text-[#2C53A3]' : 'text-black bg-white'}`} onClick={()=> {setActiveButton('Property Details'), setActiveTab('Property Details')}}>Property Details</div>
          <div className={` relative h-full flex items-center justify-center px-2 rounded-md border border-gray-200 hover:cursor-pointer ${activeButton === 'Map View' ? 'bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 text-[#2C53A3]' : 'text-black bg-white'}`} onClick={()=> {setActiveButton('Map View'), setActiveTab('Map View')}}>Map view</div>
          <div className={` relative h-full flex items-center justify-center px-2 rounded-md border border-gray-200 hover:cursor-pointer ${activeButton === 'Analytics' ? 'bg-gradient-to-r from-[#FF80AB]/10 to-[#9575CD]/10 text-[#2C53A3]' : 'text-black bg-white'}`} onClick={()=> {setActiveButton('Analytics'), setActiveTab('Analytics')}}>Analytics</div>
        </div>

        {activeTab==='Property Details' && (<div className='relative w-full min-h-36 h-36 flex flex-row p-3 gap-4 overflow-x-auto overflow-y-hidden hide-scrollbar'>

          {solutions && solutions.sort((a,b)=> b.score - a.score).map((data,index) =>{
            const isSelected = selectedProperty.property_id === data.property_id;
            return (<div key={index} onClick={()=> {setSelectedProperty(solutions[index]),setPropertyIndex(index+1)}} className={`relative cursor-pointer min-h-28 h-28 min-w-[200px] w-[200px] border border-gray-400 flex flex-col rounded-md hover:cursor-pointer overflow-hidden transform transition duration-300  shadow-lg ${isSelected ? '-translate-y-1 border-2 border-gray-700': 'hover:shadow-lg hover:-translate-y-1 '}`} >
              <div className='relative min-h-8 h-8 max-h-8 bg-gradient-to-r from-[#0e2044] to-[#41b655] w-full opacity-80'></div>
              <div className='relative min-h-20 h-20 max-h-24 bg-white-500 w-full flex flex-col gap-1 pt-4 pb-2 px-2'>
                <div className='absolute rounded-full h-6 w-6 bg-white flex items-center -top-3.5 left-2 justify-center text-sm shadow-md'>{index+1}</div>
                <h1 className='relative font-semibold text-sm'>{data.area}</h1>
                <h2 className='relative text-gray-600 text-xs'>{data.address}</h2>
              </div>
          </div>)
        })}          
        </div>)}

      </div>)}

      <div ref={gridRef} className={`${source==="MapComponent" ? 'overflow-y-hidden' : 'overflow-y-auto'}  bg-gray-50 h-full w-full relative`}>
    {activeTab === 'Map View' && (
      <div className='relative h-full w-full overflow-hidden'>
        <MapComponent solutions={solutions} toggleModal={toggleModal} />
      </div>
    )}
    {activeTab === 'Analytics' && (
      <div className='relative h-screen w-screen overflow-hidden flex items-center justify-center'>
        <p className='text-green-400 font-semibold text-2xl'>Analytics View coming Soon.....</p>
      </div>
    )}

    { activeTab === "Property Details" && (
      <>
    {selectedProperty ? (
      <div className="relative flex-1 mx-auto w-full p-2  font-sans bg-gray-50 flex flex-col gap-3 overflow-x-hidden">

      {/* Top Row */}
      <div className="grid grid-cols-1 md:grid-cols-8 gap-4">
        {/* Location Map Card */}
        <div className="card p-4 bg-white rounded shadow-sm gap-4 flex flex-col items-start col-span-2">
          <div className="flex justify-start items-center  flex-row  w-full">
           {/* <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">Location Map <div className="relative inline-block"><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={() => handleMouseEnter('tooltip1')} onMouseLeave={() => handleMouseLeave('tooltip1')}/><div className={`${visibleTooltips.tooltip1 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Shows the exact location of the property/project on the map</div></div></h2> */}
            <span className="text-sm font-bold text-black flex flex-row items-center gap-2"><span className='h-6 w-6 p-2 rounded-full flex items-center font-semibold shadow-md justify-center border-2 border-black text-black bg-transparent'>{propertyIndex}</span> {selectedProperty.area}</span>
          </div>
          <div className="bg-gray-100 h-48 w-full rounded relative overflow-hidden ">
            {/* Map SVG Placeholder */}
            {/* <MapContainer
                key={selectedProperty.address}
                center={selectedProperty.latitude_longitude || [0, 0]}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
                className='z-1'
                attributionControl={false}
                zoomControl={false}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                />
                <Marker position={selectedProperty.latitude_longitude || [0, 0]} icon={defaultIcon}>
                    <Popup className="font-medium">{selectedProperty.property_type}</Popup>
                </Marker>
            </MapContainer> */}
            <GoogleMap lat={selectedProperty?.latitude_longitude[0]} lng={selectedProperty?.latitude_longitude[1]} tooltipText={selectedProperty?.address}/>
            <div className="absolute bottom-2 right-2 flex flex-row gap-1 items-center bg-white px-2 py-1 rounded text-xs font-medium shadow-sm">
              <FaMapMarkerAlt className="text-red-500" size={16} />
             <p>{selectedProperty.latitude_longitude.length > 0? `${selectedProperty.latitude_longitude[0]}, ${selectedProperty.latitude_longitude[1] || ''}`: ''}</p>
            </div>
          </div>
          <div className="text-xs text-gray-600 flex justify-between relative w-full flex-row">
            <span>{selectedProperty.address}</span>
            <button className="text-primary hover:underline flex flex-row items-center cursor-pointer" onClick={()=>{setActiveTab('Map View'), setActiveButton('Map View')}}>View Full Map <IoIosArrowForward /></button>
          </div>
          <div className='flex flex-col gap-3 relative w-full'>
          <div className="flex justify-between items-center border-b border-gray-100">
              <span className="text-sm text-gray-600">Land Type</span>
              <span className="text-sm font-medium">{selectedProperty.property_type}</span>
            </div>
            <div className="flex justify-between items-center border-b border-gray-100">
              <span className="text-sm text-gray-600">Total Area</span>
              <span className="text-sm font-medium">{selectedProperty.total_area} Acres</span>
            </div>
            <div className="flex justify-between items-center border-b border-gray-100">
              <span className="text-sm text-gray-600">Zoning Status</span>
              <span className="text-sm font-medium">{selectedProperty.business_location_type}</span>
            </div>
            </div>
        </div>
          
        {/* Vendor Proximity */}
        <div className="card p-4 bg-white rounded shadow-sm gap-6 relative flex flex-col items-start col-span-3">
          <div className="flex gap-2 items-center relative flex-row">
            <h2 className="text-base font-semibold text-primary relative">Vendor Proximity</h2>
            <div className="tooltip relative inline-block">
              <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={()=>{handleMouseEnter('tooltip2')}} onMouseLeave={()=>{handleMouseLeave('tooltip2')}}/>
              <div className={`${visibleTooltips.tooltip2 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Nearby vendors sorted by distance and relevance to the selected property</div>
            </div>
          </div>
          <div className="flex space-x-2 justify-between items-center relative w-full">
            <div className='relative flex flex-row gap-2'>
              <div className='relative flex flex-col gap-1 items-center'>
                <button 
                  onClick={()=> {setShowEssentialMaterials(true)}}
                  className={`px-3 py-1 text-xs cursor-pointer text-black font-semibold transition-all`}
                >
                  Essential Supplies
                </button>
                <div className={`${showEssentialMaterials ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
              </div>
              <div className='relative flex flex-col gap-1 items-center'>
                <button 
                  onClick={()=> {setShowEssentialMaterials(false)}}
                  className={`px-3 py-1 text-xs font-medium rounded-full cursor-pointer`}>
                  Non-Essential Supplies
                </button>
                <div className={`${!showEssentialMaterials ? 'bg-blue-500 w-full' : 'bg-transparent w-0'} ' h-[2px] bg-blue-500 rounded-full transition-width duration-300`}></div>
              </div>
            </div>
            
            {/* <div className='relative py-1 px-2 text-xs text-orange-800 bg-orange-100 rounded-full font-semibold'>{showEssentialMaterials ? `${selectedProperty.essential_vendors.reduce((sum, item) => sum + item.total_vendor, 0)}`: `${selectedProperty.nonessential_vendors.reduce((sum,item) => sum + item.total_vendor, 0)}`} Found</div> */}
            </div>
          {showEssentialMaterials ? (
            <div className="gap-3 w-full relative grid grid-cols-2">
              {selectedProperty.essential_vendors.length === 0 ? (
                <p className="text-sm text-gray-500 italic col-span-2 h-28 justify-self-center self-center">
                  No vendors available
                </p>
              ) : (
                selectedProperty.essential_vendors.slice(0, 5).map((essentials, index) => (
                  <div key={index} className="grid grid-cols-2 gap-2 col-span-2">
                    <div className="flex flex-row gap-2 items-start">
                      <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div>
                      <div className='flex flex-col'>
                        <span className="text-sm font-medium">{essentials.supply}</span>
                        <span className='text-xs font-light text-gray-600'>No.of Vendors: {essentials.total_vendor}</span>
                      </div>
                    </div>
                    <div className='flex flex-row gap-2 justify-self-end'>
                      <span className="text-xs text-gray-600 ">
                        Nearest Vendor: <span className='font-semibold text-gray-700'>{essentials.nearest_vendor_distance.toFixed(2)} km</span>
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
              {selectedProperty.nonessential_vendors.length === 0 ? (
                <p className="text-sm text-gray-500 italic col-span-2 h-28 justify-self-center self-center">
                  No vendors available
                </p>
              ) : (
                selectedProperty.nonessential_vendors.slice(0, 5).map((essential, idx) => (
                  <div key={idx} className="grid grid-cols-2 gap-2 col-span-2">
                    <div className="flex flex-row gap-2 items-start">
                      <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div>
                      <div className='flex flex-col'>
                        <span className="text-sm font-medium">{essential.supply}</span>
                        <span className='text-xs font-light text-gray-600'>No.of Vendors: {essential.total_vendor}</span>
                      </div>
                    </div>
                    <div className='flex flex-row gap-2 justify-self-end'>
                      <span className="text-xs text-gray-600 ">
                        Nearest Vendor: <span className='font-semibold text-gray-700'>{essential.nearest_vendor_distance.toFixed(2)} km</span>
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

            {selectedProperty.essential_vendors.reduce((sum, item) => sum + item.total_vendor, 0) > 5 || selectedProperty.nonessential_vendors.reduce((sum, item) => sum + item.total_vendor, 0) > 5 && (
              <div className=" flex items-center justify-center w-full absolute bottom-3 self-center">
                <button className="py-2 text-black rounded text-sm flex flex-row gap-2 items-center font-medium cursor-pointer" onClick={handleShowVendor}>
                  Explore Vendor List <FaArrowRight />
                </button>
              </div>
            )}
          </div>
            
        {/* Approvals List */}
        <div className="card p-4 bg-white rounded shadow-sm relative flex flex-col col-span-3 items-start gap-6">
        
          <div className='flex relative flex-row items-center justify-between w-full'>
            <div className='relative gap-2 flex flex-row items-center'>
            <h2 className="text-base relative font-semibold text-primary">Required Approvals</h2>
            <div className="tooltip relative inline-block">
              <FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={()=>{handleMouseEnter('tooltip3')}} onMouseLeave={()=>{handleMouseLeave('tooltip3')}}/>
              <div className={`${visibleTooltips.tooltip3 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Govt. clearances required for the project</div>
            </div>
            </div>
            <div className='relative rounded-full bg-orange-100 py-1 px-2 text-orange-800 text-xs font-semibold'>{selectedProperty.approvals.length} Needed</div>
          </div>

          <div className=" relative w-full grid grid-cols-4 gap-3">
           
           {selectedProperty.approvals.slice(0,5).map((approval, index)=> 
              <>
                <div key={index} className="relative flex flex-row items-start w-full gap-2 col-span-3">
                  <div className="w-2 h-2 rounded-full flex-shrink-0 bg-purple-500 mt-2"></div>
                  <div className='relative flex flex-col'>
                    <span className="text-sm font-medium">{approval.approval_name}</span>
                    <span className='text-xs text-gray-500'>{approval.government_department}</span>
                  </div>
                </div>
                <div key={index} className="relative flex flex-row items-center gap-2 whitespace-nowrap col-span-1 justify-self-end">
                  <div className='relative flex flex-col'>
                    <p className='relative text-gray-600 text-xs'>Est. Duration</p>
                    <span className="text-sm text-black">{approval.time_taken} days</span>
                  </div>
                </div>
              </>
          )}
          </div>

          <div className='absolute flex flex-row gap-2 items-center text-sm justify-center p-2 bottom-3 self-center cursor-pointer' onClick={handleShowApprovals}>
            View Approvals <FaArrowRight />
          </div>

        </div>

      </div>

      {/* Middle Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        {/* Geo & Utility Snapshots Panel */}
        <div className="card p-4 bg-white rounded shadow-sm col-span-1 gap-6 flex flex-col items-start">
          <div className="flex justify-between items-center">
            <h2 className="text-base font-semibold text-primary flex flex-row items-center gap-2">Geo & Utility Snapshots <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={()=>{handleMouseEnter('tooltip4')}} onMouseLeave={()=>{handleMouseLeave('tooltip4')}}/><div className={`${visibleTooltips.tooltip4 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Nearby Transport & Connectivity Distances</div></div></h2>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center col-span-1 flex-row gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                <FaRoad className="text-indigo-600" />
              </div>
              <div className='flex flex-col gap-1'>
                <p className="text-sm font-medium">Highway</p>
                <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.road_connectivity.distance} km {selectedProperty.road_connectivity.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500'/>) : selectedProperty.road_connectivity.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500'/>) : (<FaCircleXmark size={12} className='text-red-500'/>)}</p>
              </div>
            </div>
            <div className="flex items-center col-span-1 flex-row gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                <FaTrain className="text-indigo-600" />
              </div>
              <div className='flex flex-col gap-1'>
                <p className="text-sm font-medium">Railway Station</p>
                <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.railway.distance} km {selectedProperty.railway.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500'/>) : selectedProperty.railway.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500'/>) : (<FaCircleXmark size={12} className='text-red-500'/>)}</p>
              </div>
            </div>
            <div className="flex items-center col-span-1 flex-row gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                <RiShipFill className="text-indigo-600" />
              </div>
              <div className='flex flex-col gap-1'>
                <p className="text-sm font-medium">Seaport</p>
                <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.seaport.distance} km {selectedProperty.seaport.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500'/>) : selectedProperty.seaport.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500'/>) : (<FaCircleXmark size={12} className='text-red-500'/>)}</p>
              </div>
            </div>
            <div className="flex items-center col-span-1 flex-row gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                <FaPlane className="text-indigo-600" />
              </div>
              <div className='flex flex-col gap-1'>
                <p className="text-sm font-medium">Airport</p>
                <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.airport.distance} km {selectedProperty.airport.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500'/>) : selectedProperty.airport.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500'/>) : (<FaCircleXmark size={12} className='text-red-500'/>)}</p>
              </div>
            </div>
            <div className="flex items-center col-span-2 flex-row gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                <MdOfflineBolt className="text-indigo-600 text-md" />
              </div>
              <div className='flex flex-col gap-1'>
                <p className="text-sm font-medium">Power Source</p>
                <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.power.distance} km {selectedProperty.power.status === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500'/>) : selectedProperty.power.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500'/>) : (<FaCircleXmark size={12} className='text-red-500'/>)}</p>
              </div>
            </div>
            <div className="flex items-center col-span-2 flex-row gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2">
                <FaBus className="text-indigo-600 text-md" />
              </div>
              <div className='flex flex-col gap-1'>
                <p className="text-sm font-medium">Availability of Local Transportation</p>
                <p className="text-xs text-gray-600 flex flex-row gap-1 items-center">{selectedProperty.availability_of_local_transportation} {selectedProperty.availability_of_local_transportation === 'good' ? (<BsPatchCheckFill size={12} className='text-green-500'/>) : selectedProperty.power.status === 'warning' ? (<FaTriangleExclamation size={12} className='text-yellow-500'/>) : (<FaCircleXmark size={12} className='text-red-500'/>)}</p>
              </div>
            </div>
          </div>        
          
        </div>

        {/* Employment Data Section */}
       <div className="card p-4 bg-white rounded shadow-sm col-span-1">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">Employment Data <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={()=>{handleMouseEnter('tooltip5')}} onMouseLeave={()=>{handleMouseLeave('tooltip5')}} />
            <div className={`${visibleTooltips.tooltip5 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Local Workforce Skill Levels Overview</div>
          </div>
            </h2>
          </div>
           
            <div className="h-48 relative w-full">
              <Doughnut data={{
                        labels: ['Skilled', 'Semi-Skilled', 'Unskilled'],
                        datasets: [{
                          data: [selectedProperty.skilled_no, selectedProperty.semiskilled_no, selectedProperty.unskilled_no],
                          backgroundColor: ['#0e2044', '#41b655', '#f59e0b'],
                          borderWidth: 1,
                        }]
                      }} 
                        options={{
                        responsive: true,
                        maintainAspectRatio: false, // This matches your container styling
                        plugins: {
                          legend: {
                            position: 'top', // or 'bottom', 'left', 'right'
                          },
                        },
                      }}
        className="w-full h-full" // This will make the chart fill its container
      />
              {/* <canvas ref={employmentChartRef} className="w-full h-full" /> */}
            </div>
          <div className="mt-2 grid grid-cols-3 gap-2">
            <div className="text-center">
              <div className="text-sm font-medium">Skilled</div>
              <div className="text-xs text-gray-600">{selectedProperty.skilled_no} workers</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium">Semi-skilled</div>
              <div className="text-xs text-gray-600">{selectedProperty.semiskilled_no} workers</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium">Unskilled</div>
              <div className="text-xs text-gray-600">{selectedProperty.unskilled_no} workers</div>
            </div>
          </div>
          
        </div>

         {/* Government Incentives Overview */}
         <div className="card p-4 bg-white rounded col-span-2 pb-12 shadow-sm gap-6 relative flex flex-col items-start">
          <div className="flex flex-row justify-between items-center w-full">
            <h2 className="text-base font-semibold text-primary flex flex-row gap-2 items-center">Regional Incentives <div className='relative inline-block'><FaRegQuestionCircle size={15} className="text-gray-400" onMouseEnter={()=>{handleMouseEnter('tooltip6')}} onMouseLeave={()=>{handleMouseLeave('tooltip6')}}/><div className={`${visibleTooltips.tooltip6 ? 'block' : 'hidden'} absolute top-6 left-1/2 transform -translate-x-1/2 text-xs text-white bg-black rounded-md p-2 min-w-fit whitespace-nowrap z-[333]`}>Applicable Government Incentives & Schemes</div></div></h2>
            <div className='relative py-1 px-2 rounded-full text-xs text-orange-800 bg-orange-100 font-semibold'>{selectedProperty.incentives.length} Found</div>
          </div>
          <div className="flex flex-col gap-3 relative w-full h-full">
            {selectedProperty.incentives.sort((a,b)=>a.incentive_rank - b.incentive_rank).slice(0,5).map((incentive,index)=>
              <div key={index} className="flex items-start relative flex-row gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div>
                  <div className='relative flex flex-col items-start'>
                    <h3 className="text-sm font-medium">{incentive.incentive_type}</h3>
                    <p className="text-xs text-gray-600">{incentive.incentive_name}</p>
                </div>
              </div>
            )}
          </div>
          {selectedProperty.incentives.length > 5 && (
            <div className='flex flex-row gap-2 items-center text-sm justify-center p-2 absolute bottom-3 self-center cursor-pointer' onClick={handleShowIncentive}>
              View Incentives <FaArrowRight />
            </div>
          )}
          
        </div>
       
      </div>     
      
      {/* Bottom row */}
      <div className={`relative w-full p-4 bg-white transition-all duration-300 ${showLocalLaws ? 'h-fit' : 'h-fit'}`} >
        <div className='h-fit w-full flex flex-row items-center justify-start gap-4 p-2' onClick={handleLocalLaws}>
          <h1 className='font-semibold text-base text-black '>Local Laws & Taxes</h1>
          {showLocalLaws ? (<FaChevronUp />) : (<FaChevronDown />)}
        </div>
 
        {showLocalLaws && (<div className='relative flex flex-col p-2 gap-3'>

            <div className='relative grid grid-cols-2 gap-4 w-full'>
              <div className='relative flex flex-col gap-2 p-4 col-span-1 border-l-4 border-[#2c53a3] bg-[#2c53a3]/10'>
                <h1 className="font-semibold text-md">Factories Act, 1948</h1>
                <ul className="list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1">
                  <li>Governs health, safety, and working hours in manufacturing units.</li>
                  <li>Mandatory for factories with 10+ workers (with power).</li>
                </ul>
              </div>
              <div className='relative flex flex-col gap-2 p-4 col-span-1 border-l-4 border-[#e91e63] bg-[#e91e63]/10'>
                <h1 className='font-semibold text-md'>Environment Protection Act, 1986</h1>
              <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                <li>Requires environmental clearance for polluting industries.</li>
                <li>Enforced by Pollution Control Boards.</li>
              </ul>
              </div>
              <div className='relative flex flex-col gap-2 p-4 col-span-1 border-l-4 border-[#673AB7] bg-[#673ab7]/10'>
                 <h1 className='font-semibold text-md'> Shops and Establishments Act (State-specific)</h1>
              <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                <li>Mandatory registration for all businesses like shops/offices.</li>
                <li>Regulates working hours, holidays, and employee rights.</li>
              </ul>
              </div>
              <div className='relative flex flex-col gap-2 p-4 col-span-1 border-l-4 border-[#4caf50] bg-[#4caf50]/10'>
                <h1 className='font-semibold text-md'>Building Bye-Laws</h1>
              <ul className='list-disc text-xs marker:text-purple-500 ml-5 mt-1 space-y-1'>
                <li>Local rules for construction (height, setbacks, FSI).</li>
                <li>Need approval before starting any building work.</li>
              </ul>
              </div>
            </div>

        </div>)}
      </div>
    </div>
    ) : (
      <LogoLoader />
      // <div className='relative flex justify-center h-full w-full items-center'>
      //   <p>Loading property...</p>
      // </div>
    )}
    </>)}
    </div>
    </div>

    ) : (<LogoLoader />)}

    {approvalsWindow && approvalsToSend && (
      <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
        <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={()=>{setApprovalWindow(false),setApprovalsToSend()}} >
          <FaXmark size={22}/>
        </div>
          <Approvalresult result={approvalsToSend} source="FromScratch" />
      </div>
    )}
    {incentivesWindow && incentivesToSend && (
      <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
        <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={()=>{setIncentivesWindow(false),setIncentivesToSend()}}>
       <FaXmark size={28}/>
        </div>
          <Incentiveresult result={incentivesToSend} source="FromScratch"/>
          
      </div>
    )}
    {vendorsWindow && vendorsToSend && (
      <div className='absolute top-0 left-0 h-screen w-screen backdrop-blur-2xl z-[340]'>
        <div className='absolute top-6 right-6 h-8 w-8 cursor-pointer rounded-full bg-white shadow-md p-2 flex flex-row items-center justify-end z-[345] text-black' onClick={()=>{setVendorsWindow(false),setVendorsToSend()}}>
       <FaXmark size={28}/>
        </div>
          <Vendorresult result={vendorsToSend} source="FromScratch" />
      </div>
    )}
    </>
  );
};

export default IndustryResultScreen;