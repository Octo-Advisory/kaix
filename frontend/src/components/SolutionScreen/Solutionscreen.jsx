import React, { useEffect, useState } from 'react'
import Industryresult from '../ResultScreens/Industryresult';
import Empresult from '../ResultScreens/Empresult';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Approvalresult from '../ResultScreens/Approvalresult';


function Solutionscreen({result}) {
  console.log("resultin solution scdeen",result);
  const user_intension = result["user_intension"]
  return (
    <div className='h-screen flex w-full items-center'>
    {user_intension === "Query to build industry from Scratch" ? (
  <Industryresult result={result} />
) : user_intension === "Query to Get Employee Search" ? (
  <Empresult result={result} />
) : user_intension === "Query to search Incentives" ? (
  <Incentiveresult result={result} />
) :user_intension === "Query to Get Approvals" ? (<Approvalresult result={result} />) : (
  "Server Error"
)}

    </div>
  )
}

export default Solutionscreen
