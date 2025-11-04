import React, { useEffect, useState } from 'react'
import Empresult from '../ResultScreens/Empresult';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Approvalresult from '../ResultScreens/Approvalresult';
import Vendorresult from '../ResultScreens/Vendorresult';
import IndustryResultScreen from '../ResultScreens/IndustryResultScreen';
import { useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
import FailureScreen from '../Failure/FailureScreen';
import NoResultsFound from '../Failure/NoResultsFound';
import LogoLoader from '../Responseloader/LogoLoader';
import NavigationPrompt from '../Chatscreen/NavigationPrompt';


function Solutionscreen() {
  const navigate = useNavigate();
  const result = useSelector((state) => state.analytics.analyticsResult);
  // console.log("resultr",result);

  const [timeoutReached, setTimeoutReached] = useState(false);
  const [confirmationPending, setConfirmationPending] = useState(false);

  useEffect(() => {
  const beforeUnloadHandler = (e) => {
    e.preventDefault();
    e.returnValue = "";
  };
  window.addEventListener("beforeunload", beforeUnloadHandler);
  return () => window.removeEventListener("beforeunload", beforeUnloadHandler);
}, []);


  useEffect(() => {
    // If result is empty, start a timeout
    let timeoutId;

    if (result.length === 0) {
      // Set the timeout to check after 5 seconds
      timeoutId = setTimeout(() => {
        setTimeoutReached(true); // Set the timeoutReached state to true after 5 seconds
      }, 5000);
    } else {
      // If result is not empty, clear any previous timeout and reset timeoutReached
      clearTimeout(timeoutId);
      setTimeoutReached(false);
    }

    // Cleanup function to clear the timeout if the component unmounts or result changes
    return () => {
      clearTimeout(timeoutId);
    };
  }, [result]);


  if (timeoutReached) {
    return <NoResultsFound />; // Return "No Results" if the timeout is reached
  }

  if (result.length === 0) {
    return <LogoLoader/>; // Optional: show a loading message until the timeout
  }

  
  // useEffect(() => {
  //   if (result.length === 0) {
  //     navigate("/");
  //   }
  // }, [result, navigate]); // Dependencies ensure effect runs when result changes

  // if (result.length === 0) {
  //   return null; // Prevents rendering if navigation happens
  // }
  // console.log("resultin solution scdeen", result);
  const user_intension = result[0]["user_intension"]
  const Analytics_response = result[0]?.["Analytics_response"]
  // console.log(Analytics_response, 'Okay its Analytics Response')

//Check if the incentive Stringis valid json after pasrsing .. if not show now result .. Reminain 
  return (
    <div className='h-screen flex w-full items-center'>
      {user_intension === "Query to build industry from Scratch" ? (
        <IndustryResultScreen result={result[0]} source="SolutionScreen"/>
      ) : user_intension === "Query to Get Employee Search" ? (
        <Empresult result={result[0]} />
      ) : user_intension === "Query to search Incentives" ? (
        // <Incentiveresult result={JSON.parse(Analytics_response["Incentive Data"])} source="SolutionScreen" />
        <Incentiveresult res={result[0]} source="SolutionScreen" />
      ) : user_intension === "Query to Get Approvals" ? (
        <Approvalresult result={Analytics_response} source="SolutionScreen" />
      ) : user_intension === "Query to search Vendors" ? (
        <Vendorresult result={result[0]} source="SolutionScreen" rerender={0} />
      ) : (
        <FailureScreen />
      )}

      <NavigationPrompt
        when={true}
        message="Confirmation is pending. You can’t leave this chat — if you leave, the confirmation will be lost."
        // onConfirm={() => setConfirmationPending(false)}
      />
      

    </div>
  )
}
 
export default Solutionscreen
