import React, { useEffect,useState } from 'react';
import { AiOutlineClear, AiOutlineSend } from 'react-icons/ai'; // React Icons
import '../ProgressScreen/ProgressScreen.css';
import check from '../../assets/check.png';
import Confirmation from '../Confirmation/Confirmation';
import Failure from '../Failure/Failure';

function ProgressScreen() {
  const messages = [
    { text: "Finding best lands", status: "Success" },
    { text: "Finding nearest locations", status: "Success" },
    { text: "Searching vendors nearby", status: "Success" },
    { text: "Finding zones", status: "Success" },
    { text: "Merging matches", status: "Success" }
  ];
  
  const [showFailure, setShowFailure] = useState(false);

  useEffect(() => {
    // Check if any message has a status of 'Fail'
    
    if (hasFailure) {
      // Set a timeout to show the Failure component
      const timeout = setTimeout(() => {
        setShowFailure(true);
      }, 3000); // 3 seconds delay
      
      // Cleanup timeout on component unmount or dependency change
      return () => clearTimeout(timeout);
    }
  }, [messages]);
  const hasFailure = messages.some((msg) => msg.status === 'Fail');
  const allSuccess = messages.every((msg) => msg.status === 'Success');

  return (
    <div className="overflow-auto bg-white rounded-lg shadow-inner flex justify-center items-center h-[90%] w-[80%] relative shadow-mg">
      {showFailure ? (
        <Failure /> // Render the Failure component if a message has a status of 'Fail'
      ) : allSuccess ? (
        <Confirmation />
      ) :(
        <div className="progress-container flex flex-col items-start w-[80%] self-center justify-self-center mb-2 gap-8 h-auto sm:w-[60%] sm:pl-10 md:pl-32 lg:pl-36 md:w-[60%]  p-5 relative custom-top">
          {messages.map((msg, index) => (
            <div
              className={`progress-step ${
                msg.status === 'Success'
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
    ${
      msg.status === 'Success'
        ? 'completed'
        : msg.status === 'Processing'
        ? 'loading'
        : msg.status === 'Fail'
        ? 'failed'
        : ''
    }`}
                >
                  {msg.status === 'Success' ? (
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
                    className={`step-text text-base sm:text-md md:text-xl lg:text-2xl xl:text-3xl ${
                      msg.status === 'Success'
                        ? 'completed-text'
                        : msg.status === 'Processing'
                        ? 'active-text'
                        : ''
                    }`}
                  >
                    {msg.text}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProgressScreen;
