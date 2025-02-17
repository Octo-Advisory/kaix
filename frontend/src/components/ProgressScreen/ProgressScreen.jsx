import React, { useContext, useEffect, useState } from 'react';
import { AiOutlineClear, AiOutlineSend } from 'react-icons/ai';
import '../ProgressScreen/ProgressScreen.css';
import check from '../../assets/check.png';
import Confirmation from '../Confirmation/Confirmation';
import Failure from '../Failure/Failure';
import { FrappeContext, useFrappeDocTypeEventListener, useFrappeDocumentEventListener, useFrappeEventListener, useFrappeGetDoc, useFrappeGetDocList, useSWRConfig } from 'frappe-react-sdk';
import { useDispatch, useSelector } from 'react-redux';

function ProgressScreen() {

  const { call } = useContext(FrappeContext);
  const aiResponse = useSelector((state) => state.ai.aiReponse);
  const chatId = useSelector((state) => state.chat.chatID);
  const [messages, setMessages] = useState([]);
  const [showfailure, setShowfailure] = useState(false);
  const [allsuccess, setAllsuccess] = useState(false);
  const [result, setresult] = useState([]);
  const [loading, setLoading] = useState(true);
  const [intervalId, setIntervalId] = useState(null);

  const fetchAnalyticsResponse = async () => {
    try {
      console.log("chat id in progress", chatId);

      const result = await call.get("frontend_app.Management_Class.Analytics_management.Analytics.analytics_module_call", { aiReponse: aiResponse, chatId: chatId });
      console.log("analytics message", result);
      setresult(result.message)
      // return result.message;  // Return the result so that the calling function gets it.
    } catch (err) {
      console.log("error occurred 😂", err);
      throw err;  // Rethrow the error if you want to catch it in the caller function.
    }
  };

  const fetchData = async () => {
    try {
      const response = await fetch(`api/resource/Session?fields=["progress.process_name","progress.process_value","progress.status","progress.modified"]&filters=[["name","=","${chatId}"]]&order_by=modified asc`, {
        method: 'GET',
        headers: {
          // 'Authorization': 'token your_api_token', // Replace with actual token
          'Content-Type': 'application/json'
        }
      });

      // Check if the response is OK
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("data is", data);
      setMessages(data.data)
      // Optionally, store it in your state or handle further logic
    } catch (error) {
      console.error('Error fetching data:', error); // Handles errors
    }
  }

  useEffect(() => {
    // Start the interval only if no failures and not all are complete
    if (!showfailure && !allsuccess) {
      const interval = setInterval(() => {
        fetchData(); // Fetch data every second
      }, 1000);

      // Cleanup the interval when conditions change or component unmounts
      return () => clearInterval(interval);
    }
  }, [showfailure, allsuccess, messages]);

  useEffect(() => {
    console.log("new use effect call");
    fetchData()
  }, [])

  useEffect(() => {
    console.log("ai response is in progress", aiResponse);
    if (aiResponse && aiResponse.length > 0) {
      try {
        fetchAnalyticsResponse(aiResponse[0]);
      } catch (error) {
        console.error("An error occurred:", error.message);
      }
    } else {
      console.error("aiResponse is either null or empty");
    }
  }, []);

  useEffect(() => {
    console.log("message is", messages);

    if (messages) {
      const noPending = messages.some((msg) => msg.status !== 'Pending')
      if (noPending) setLoading(false)
      const allSuccess = messages.every((msg) => msg.status === 'Complete');
      setAllsuccess(allSuccess);
      const hasFailure = messages.some((msg) => msg.status === 'Fail');
      setShowfailure(hasFailure);
    }
  }, [messages])

  const { data, mutate } = useFrappeGetDocList("Session", {
    fields: ["progress.process_value", "progress.status", "progress.modified"],
    filters: [["name", "=", chatId]],
    orderBy: { field: "modified", order: "asc" }
  });

  useFrappeEventListener("progress_update", async (eventData) => {
    console.log("Event triggered, event data:", eventData);
    await mutate()
    console.log("Data refetched after event trigger.");
  });

  useEffect(() => {
    if (data) {
      setMessages(data)
      console.log("Updated data after mutate:", data);
    }
  }, [data]);

  return (
    <div className="overflow-auto bg-white shadow-inner flex justify-center items-center h-full w-full relative shadow-mg">
      {loading ? (
        <div className="loading-indicator">Loading...</div> // Add a loading indicator here
      ) : showfailure ? (
        <Failure /> // Render the Failure component if a message has a status of 'Fail'
      ) : allsuccess ? (
        <Confirmation result={result} />
      ) : (
        <div className="progress-container flex flex-col items-start w-[80%] self-center justify-self-center mb-2 gap-8 h-auto sm:w-[60%] sm:pl-10 md:pl-32 lg:pl-36 md:w-[60%]  p-5 relative custom-top">
          {messages?.map((msg, index) => (
            <div
              className={`progress-step ${msg.status === 'Complete'
                  ? 'toshow'
                  : msg.status === 'Processing'
                    ? 'toshow'
                    : msg.status === 'Fail'
                      ? 'toshow'
                      : ''
                }`}
              key={index}
            >
              <div className="circleMessage relative flex flex-row gap-6 w-[80%] min-w-fit flex-nowrap justify-between sm:gap-4 md:gap-6 lg:gap-8 sm:w-[90%] md:w-[85%] lg:w-[80%]">
                <div
                  className={`circle w-8 h-8 sm:w-10 sm:h-10 md:w-10 md:h-10 lg:w-10 lg:h-10 rounded-full border-2 border-gray-300 
    bg-white flex justify-center items-center 
    relative transition-all duration-300 ease-in-out 
    shrink-0 
    ${msg.status === 'Complete'
                      ? 'completed'
                      : msg.status === 'Processing'
                        ? 'loading'
                        : msg.status === 'Fail'
                          ? 'failed'
                          : ''
                    }`}
                >
                  {msg.status === 'Complete' ? (
                    <span className="tick">
                      <img src={check} className="check" />
                    </span>
                  ) : msg.status === 'Processing' ? (
                    <div className="spinner"></div> // Loading spinner
                  ) : msg.status === 'Fail' ? (
                    <span className="fail-icon">❌</span> // Custom fail icon or text
                  ) : null}
                </div>

                <div className="step-text-container">
                  <span
                    className={`step-text text-base sm:text-md md:text-xl lg:text-2xl xl:text-3xl ${msg.status === 'Complete'
                        ? 'completed-text'
                        : msg.status === 'Processing'
                          ? 'active-text'
                          : ''
                      }`}
                  >
                    {msg.process_value}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {/* {loading ? (<div className="loading-indicator">Loading...</div>):(<Solutionscreen result={messages}/>)} */}
    </div>
  );
}

export default ProgressScreen;
