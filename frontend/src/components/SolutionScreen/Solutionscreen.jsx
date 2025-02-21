import React, { useEffect, useState } from 'react'
import Industryresult from '../ResultScreens/Industryresult';
import Empresult from '../ResultScreens/Empresult';


function Solutionscreen({result}) {
  console.log("resultin solution scdeen",result);
  const user_intension = result["user_intension"]
  return (
    <div className='h-screen flex flex-col items-center'>
    {user_intension == "Query to build industry from Scratch"?(<Industryresult result = {result}/>):(user_intension == "Query to Get Employee Search" ? (<Empresult result = {result}/>):("Server Error"))}
    </div>
  )
}

export default Solutionscreen
