import React, { useEffect, useState } from 'react'
import Industryresult from '../ResultScreens/Industryresult';
import Empresult from '../ResultScreens/Empresult';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Approvalresult from '../ResultScreens/Approvalresult';
import Vendorresult from '../ResultScreens/Vendorresult';
import { useSelector } from 'react-redux';


function Solutionscreen() {
  const result = useSelector((state) => state.analytics.analyticsResult);
  console.log("resultin solution scdeen", result);
  const user_intension = result[0]["user_intension"]
  return (
    <div className='h-screen flex w-full items-center'>
      {user_intension === "Query to build industry from Scratch" ? (
        <Industryresult result={result[0]} />
      ) : user_intension === "Query to Get Employee Search" ? (
        <Empresult result={result[0]} />
      ) : user_intension === "Query to search Incentives" ? (
        <Incentiveresult result={result[0]} />
      ) : user_intension === "Query to Get Approvals" ? (
        <Approvalresult result={result[0]} />
      ) : user_intension === "Query to search Vendors" ? (
        <Vendorresult result={result[0]} />) : (
        "Server Error"
      )}

    </div>
  )
}

export default Solutionscreen
