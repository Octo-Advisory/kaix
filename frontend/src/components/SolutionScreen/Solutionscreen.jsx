import React, { useEffect, useState } from 'react'
import Industryresult from '../ResultScreens/Industryresult';
import Empresult from '../ResultScreens/Empresult';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Approvalresult from '../ResultScreens/Approvalresult';
import Vendorresult from '../ResultScreens/Vendorresult';
import { useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";


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
  console.log("resultin solution scdeen", result);
  const user_intension = result[0]["user_intension"]
  const Analytics_response = result[0]?.["Analytics_response"]
  return (
    <div className='h-screen flex w-full items-center'>
      {user_intension === "Query to build industry from Scratch" ? (
        <Industryresult result={result[0]} />
      ) : user_intension === "Query to Get Employee Search" ? (
        <Empresult result={result[0]} />
      ) : user_intension === "Query to search Incentives" ? (
        <Incentiveresult result={JSON.parse(Analytics_response["Incentive Data"])} />
      ) : user_intension === "Query to Get Approvals" ? (
        <Approvalresult result={Analytics_response} />
      ) : user_intension === "Query to search Vendors" ? (
        <Vendorresult result={result[0]} />) : (
        "Server Error"
      )}

    </div>
  )
}

export default Solutionscreen
