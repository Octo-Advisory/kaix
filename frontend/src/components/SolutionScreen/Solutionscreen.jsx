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


function Solutionscreen() {
  const navigate = useNavigate();
  const result = useSelector((state) => state.analytics.analyticsResult);
  // console.log("resultr",result);
  
  useEffect(() => {
    if (result.length === 0) {
      navigate("/");
    }
  }, [result, navigate]); // Dependencies ensure effect runs when result changes

  if (result.length === 0) {
    return null; // Prevents rendering if navigation happens
  }
  // console.log("resultin solution scdeen", result);
  const user_intension = result[0]["user_intension"]
  const Analytics_response = result[0]?.["Analytics_response"]

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

    </div>
  )
}
 
export default Solutionscreen
