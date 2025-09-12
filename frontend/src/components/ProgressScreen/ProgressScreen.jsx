import React, { useState, useEffect, useContext } from 'react';
import { IoSearch } from "react-icons/io5";
import { PiCardsThreeBold } from "react-icons/pi";
import { FiDownload } from "react-icons/fi";
import { FaRegCircleCheck } from "react-icons/fa6";
import '../ProgressScreen/ProgressScreen.css';
import { FrappeContext, useFrappeEventListener,useFrappeCreateDoc, useFrappeGetDocList,useFrappeUpdateDoc } from 'frappe-react-sdk';
import { useSelector, useDispatch } from 'react-redux';
import { addAnalyticsResult } from '../../Redux/Store/Featuresilces/analyticsResult';
import { useNavigate, useParams } from "react-router-dom";
import LogoLoader from '../Responseloader/LogoLoader';
import FailureScreen from '../Failure/FailureScreen';

const ProgressScreen = () => {
  const { createDoc, isLoading, error } = useFrappeCreateDoc('');
  const [steps, setSteps] = useState([
    {
      id: 1,
      process_name: "Analyzing Your Query",
      process_value: 'Analyzing Your Query',
      color: "#3b82f6",
      bgColor: "#eff6ff",
      borderColor: "#bfdbfe",
      icon: (
        <IoSearch size={26} className='bg-[#eff6ff] text-[#3b82f6] ' />
      ),
      completed: false,
      processing: false,
      failed: false,
    },
    {
      id: 2,
      process_name: "Fetching Data",
      process_value: 'Fetching Data',
      color: "#ec4899",
      bgColor: "#fdf2f8",
      borderColor: "#fbcfe8",
      icon: (
        <FiDownload size={26} className='bg-[#fdf2f8] text-[#ec4899] ' />
      ),
      completed: false,
      processing: false,
      failed: false,
    },
    {
      id: 3,
      process_name: "Analyzing Data",
      process_value: 'Analyzing gathered Data',
      color: "#8b5cf6",
      bgColor: "#f5f3ff",
      borderColor: "#ddd6fe",
      icon: (
        <PiCardsThreeBold size={26} className='bg-[#f5f3ff] text-[#8b5cf6] ' />
      ),
      completed: false,
      processing: false,
      failed: false,
    },
    {
      id: 4,
      process_name: "Preparing Result",
      process_value: 'Preparing results',
      color: "#f59e0b",
      bgColor: "#fffbeb",
      borderColor: "#fde68a",
      icon: (
        <FaRegCircleCheck size={26} className='bg-[#fffbeb] text-[#f59e0b] ' />
      ),
      completed: false,
      processing: false,
      failed: false,
    }
  ]);

  const navigate = useNavigate();
  const { call } = useContext(FrappeContext);
  const aiResponse = useSelector((state) => state.ai.aiReponse);
  const confirmationMsg = useSelector((state)=> state.chat?.messages?.[state.chat.messages.length-1]?.text)
  const [messages, setMessages] = useState([]);
  const [showfailure, setShowfailure] = useState(false);
  const [allsuccess, setAllsuccess] = useState(false);
  const [result, setresult] = useState([]);
  const [loading, setLoading] = useState(true);
  const [failure, setFailure] = useState(false);
  const validationResult = useSelector((state) => state.validate.validation_result)
  const selectedOption = useSelector((state)=>state.ai.selectedOption)
  // console.log("validation Result", validationResult);
  // console.log("aiResponse", aiResponse);
  // console.log("confirmationMsg", confirmationMsg);
  const dispatch = useDispatch();
  const { updateDoc } = useFrappeUpdateDoc()
  const { sessionId } = useParams();
  const [isMounted, setIsMounted] = useState(false);
  
  useEffect(() => {
    if (aiResponse.length === 0) {
      navigate("/");
    }
  }, [aiResponse, navigate]); // Dependencies ensure effect runs when result changes

  if (aiResponse.length === 0) {
    return null; // Prevents rendering if navigation happens
  }

  // This part is added for updating the user intension based on the confirmation by user
  const updatedAiResponse = aiResponse?.map((item, index) => ({
  ...item,
  "User Intention": index === aiResponse.length - 1 ? confirmationMsg ?? item["User Intention"] : item["User Intention"]
}));

  const fetchAnalyticsResponse = async () => {
    // await clearProgressAndIntention(sessionId)
    try {
      // console.log("chat id in progress", sessionId); 
      const result = await call.get("frontend_app.Management_Class.Analytics_management.Analytics.analytics_module_call", { aiResponse: updatedAiResponse, chatId: sessionId, validationResult: validationResult, selectedOption: selectedOption });
      // console.log("analytics message result", result);
      setresult(result.message)
      dispatch(addAnalyticsResult(result.message))
    } catch (err) {
      let log = `Something went wrong while fetching the Analytics Response for ${JSON.stringify(updatedAiResponse)} ${JSON.stringify(selectedOption)}: ${JSON.stringify(err)}`
      await createDoc("AIX Diagnostics Hub", {
      type: "Analytics Error",
      note: log,
      session: sessionId,
      }).then ((res)=>{
        setLoading(false)
        setShowfailure(true)
      });
      // console.log("error occurred 😂", err);
      // throw err;  // Rethrow the error if you want to catch it in the caller function.
    }
  };


  const fetchData = async () => {
    try {
      // console.log("chatId", sessionId);

      const response = await fetch(`api/resource/Session?fields=["progress.process_name","progress.process_value","progress.name","progress.status","progress.modified"]&filters=[["name","=","${sessionId}"]]&order_by=modified asc`, {
        method: 'GET',
        headers: {
          // 'Authorization': 'token your_api_token', // Replace with actual token
          'Content-Type': 'application/json'
        }
      });
      // console.log("response is", response);

      // Check if the response is OK
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      // console.log("data is", data);
      setMessages(data.data)

      // Optionally, store it in your state or handle further logic
    } catch (error) {
      // console.error('Error fetching data:', error); // Handles errors
    }
  }

  const clearProgressAndIntention = async (chatId) => {
    try {
      await updateDoc('Session', chatId, {
        progress: [],
      });
    } catch (error) {
      // console.error("Error updating session:", error);
    }
  };



  useEffect(() => {
    // console.log("ai response is in progress", aiResponse);
    const analyticsResp = async ()=> {
      if (aiResponse && aiResponse.length > 0) {
        try {
          fetchAnalyticsResponse(aiResponse[0]);
        } catch (error) {
          // console.error("An error occurred:", error.message);
          let log = `Something went wrong while fetching the Analytics Response for ${JSON.stringify(updatedAiResponse)} ${JSON.stringify(selectedOption)}:  ${JSON.stringify(error.message)}`
          await createDoc("AIX Diagnostics Hub", {
          type: "Analytics Error",
          note: log,
          session: sessionId,
        });
          setLoading(true)
          setShowfailure(true)
        }
      } else {
        // console.error("aiResponse is either null or empty");
        let log = `Something went wrong while fetching the Analytics Response for ${JSON.stringify(updatedAiResponse)} ${JSON.stringify(selectedOption)}: Ai Response is either null or empty`
          await createDoc("AIX Diagnostics Hub", {
          type: "Analytics Error",
          note: log,
          session: sessionId,
        });
        setLoading(true)
        setShowfailure(true)
      }
    }
    analyticsResp()
  }, []);

  useEffect(() => {
    // console.log("message is", messages);

    if (messages) {
      const noPending = messages.some((msg) => msg.status == 'Processing')
      if (noPending) setLoading(false)
      const allSuccess = messages.every((msg) => msg.status === 'Complete');
      setAllsuccess(allSuccess);
      const hasFailure = messages.some((msg) => msg.status === 'Fail');
      setShowfailure(hasFailure);
    }
  }, [messages])

    useEffect(() => {
      const intervalId = setInterval(() => {
        // console.log("Interval running...");
        mutate();
        if (allsuccess) {
          clearInterval(intervalId);
          // console.log("Interval cleared!");
        }
      }, 3000);
      return () => clearInterval(intervalId); // cleanup on unmount
    }, [allsuccess]);

  useEffect(() => {
    let timer;

    if (allsuccess) {
      timer = setTimeout(() => {
        navigate('/solution')
      }, 2000);
    }
    return () => clearTimeout(timer);
  }, [allsuccess]);

  const { data, mutate } = useFrappeGetDocList("Session", {
    fields: ["progress.process_value", "progress.process_name", "progress.status", "progress.modified", "progress.is_completed", 'progress.name'],
    filters: [["name", "=", sessionId]],
    orderBy: { field: "modified", order: "asc" }
  });

  // // Timout will set the failure true if the progress takes more then n amount of time 
  // useEffect(() => {
  //   const timeout = setTimeout(() => {
  //     if(loading) {
  //       setLoading(false)
  //     }
      
  //     setFailure(true);
  //     setShowfailure(true)
  //   }, 30000);
  //   // Optional: Cleanup on unmount
  //   return () => clearTimeout(timeout);
  // }, []);
  useEffect(() => {
  const timeout = setTimeout(async () => {
    if (loading) {
      setLoading(false);
    }
    let log = `Process Timeout at Progress Screen for ${updatedAiResponse} ${selectedOption}`;
    await createDoc("AIX Diagnostics Hub", {
      type: "Process Timeout",
      note: log,
      session: sessionId,
    });
    setFailure(true);
    setShowfailure(true);
  }, 60000);
  
  return () => clearTimeout(timeout);
}, []);

useEffect(()=>{
  const method = async()=>{
    let log = `Some Error Occured In Analytics Module and it thrown Status Fail `;
    await createDoc("AIX Diagnostics Hub", {
      type: "Analytics Error",
      note: log,
      session: sessionId,
    });
  }
  if(showfailure) {
    method()
  }
},[showfailure])


  useFrappeEventListener("progress_update", async (eventData) => {
  // console.log("Event triggered, event data:", eventData);
  if (!failure) {
      // console.log('Refetching the DATA Again ........')
      await mutate();
  }
});

function areProcessArraysEqual(arr1, arr2) {
  if (arr1.length !== arr2.length) return false;

  const map1 = Object.fromEntries(arr1.map(item => [item.process_name, item]));
  const map2 = Object.fromEntries(arr2.map(item => [item.process_name, item]));

  return Object.keys(map1).every(name => {
    return JSON.stringify(map1[name]) === JSON.stringify(map2[name]);
  });
}

  useEffect(() => {
    // console.log('now the data is called', data)
    if(failure) return;
    if (data) {
      // console.log(data, messages, 'This is the dataaaa')
      const result =  areProcessArraysEqual(messages, data)
      // console.log('Result to compare is ',result)
      if(!result) {
        setMessages(data)
      }
      // console.log("Updated data after mutate:", data);
    }
  }, [data]);

  // useEffect(() => {
  //   // console.log('now the data is called', data)
  //   if(failure) return;
  //   if (data) {
  //     setMessages(data)
  //     // console.log("Updated data after mutate:", data);
  //   }
  // }, [data]);
  
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    if (failure) return;
    setIsMounted(true);
    const mergedSteps = steps.map((step) => {
      const msg = messages.slice(-4).find((m) => m.process_name === step.process_name);

      if (msg) {
        return {
          ...step, // ✅ keep static values like icon, color, etc.
          process_value: msg.process_value,
          completed: msg.status === 'Complete',
          processing: msg.status === 'Processing',
          failed: msg.status === 'Fail'
        };
      }
      return step;
    });
    setSteps(mergedSteps);
  }, [messages])


  // useEffect(()=>{
  //    console.log(showfailure,'ShoeFailure')
  // },[showfailure])

  // CSS animations
  const styles = `
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    
    .animate-fade-in-up {
      animation: fadeInUp 0.5s ease-out forwards;
    }
    
    .animate-fade-in {
      animation: fadeIn 0.5s ease-out forwards;
    }    
    
    .step-enter {
      opacity: 0;
      transform: translateY(20px);
    }
    
    .step-enter-active {
      opacity: 1;
      transform: translateY(0);
      transition: all 0.3s ease-out;
    }
    
    .step-exit {
      opacity: 1;
      transform: translateY(0);
    }
    
    .step-exit-active {
      opacity: 0;
      transform: translateY(-20px);
      transition: all 0.3s ease-out;
    }
    
    .title-animate {
      opacity: 0;
      transform: translateY(-20px);
      animation: fadeInUp 0.5s ease-out 0.2s forwards;
    }
  `;

  const ProcessingCard = ({ id, step }) => (
    <div
      key={id}
      className={`processing-card rounded-xl p-5 relative overflow-hidden ${isMounted ? 'animate-fade-in-up' : ''}`}
      style={{ borderColor: step.borderColor, color: step.color }}
    >
      <div className="flex items-center">
        <div
          className="icon-container mr-4 animate-pulse"
          style={{ backgroundColor: step.bgColor }}
        >

          <div className="flex flex-row gap-1 items-center">
            <span className=" h-2 dot w-2 rounded-full" style={{ backgroundColor: step.color }}></span>
            <span className="h-2 dot w-2 rounded-full" style={{ backgroundColor: step.color }}></span>
            <span className="h-2 dot w-2 rounded-full" style={{ backgroundColor: step.color }}></span>
          </div>
        </div>
        <div className="flex-grow">
          <h3 className="text-xl font-semibold mb-1" style={{ color: step.color }}>{step.process_value}</h3>
          <p className=" text-base text-gray-600">{step.process_name}...</p>
        </div>
        <div
          className="ml-4 px-3 py-1 rounded-full text-md font-medium animate-pulse"
          style={{ backgroundColor: step.bgColor, color: step.color }}
        >
          Processing
        </div>
      </div>
    </div>
  );

  const CompletedCard = ({ id, step }) => (
    <div
      key={id}
      className={`completed-step rounded-xl py-2 px-4 overflow-hidden ${isMounted ? '' : ''}`}
      style={{ borderColor: step.borderColor, animationDelay: `${step.id * 0.1}s` }}
    >
      <div className="flex items-center">
        <div
          className="icon-container rounded-full p-3 mr-4"
          style={{
            backgroundColor: step.bgColor,
            transform: isMounted ? 'scale(1)' : 'scale(0)',
            transition: 'transform 0.3s cubic-bezier(0.68, -0.55, 0.27, 1.55)'
          }}
        >
          {step.icon}
        </div>
        <div className="flex-grow">
          <h3 className="text-xl font-medium mb-0.5" style={{ color: step.color }}>{step.process_value}</h3>
          <p className="text-base text-gray-500">{step.process_name} - Complete</p>
        </div>
        <div
          className="ml-4 px-2.5 py-0.5 rounded-full text-md font-medium"
          style={{
            backgroundColor: step.bgColor,
            color: step.color,
            opacity: isMounted ? 1 : 0,
            transition: 'opacity 0.3s ease-out 0.2s'
          }}
        >
          Complete
        </div>
      </div>
    </div>
  );

  const CompletionCard = () => (
    <div
      className={`rounded-xl p-6 border border-green-200 text-center bg-green-50 shadow-sm ${isMounted ? 'animate-fade-in-up' : ''}`}
    // style={{ animationDelay: '0.3s' }}
    >
      <div className="flex flex-col items-center">
        <div
          className={`w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-3 ${isMounted ? '' : ''}`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-green-600 mb-2">All Steps Completed</h3>
        <p
          className="text-gray-600"
          style={{
            opacity: isMounted ? 1 : 0,
            transform: isMounted ? 'translateY(0)' : 'translateY(10px)',
            transition: 'all 0.3s ease-out 0.2s'
          }}
        >
          Your data has been successfully processed
        </p>
      </div>
    </div>
  );

  return (
    <>

      <style>{styles}</style>

      <div className="p-4 bg-white flex items-center justify-center h-screen w-screen">
        {loading ? (
          <LogoLoader text='Curating the Smart Sequence' />
        ) : showfailure ? (
          <FailureScreen /> // Render the Failure component if a message has a status of 'Fail'
        ) : (
          <div className="container relative p-8 w-[50%]">

            <div id="completed-steps-container" className="space-y-4 mb-4">
              {steps.filter(step => step.completed).map((step) => (
                <CompletedCard key={step.id} step={step} />
              ))}
            </div>

            <div id="current-step-container" className="mt-6">
              {allsuccess ? (
                <CompletionCard />
              ) : (
                steps.map((step) => (
                  step.processing && <ProcessingCard key={step.id} step={step} />
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default ProgressScreen;