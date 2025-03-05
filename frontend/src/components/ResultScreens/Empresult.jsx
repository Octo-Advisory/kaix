import React from 'react'
import Details from '../Details/Details'
import Backtochat from '../Backtochat/Backtochat';

function Empresult({ result }) {
  console.log("Emp resutl is", result);
  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
      <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        {/* Title Section */}
        <div className="top-header flex items-center justify-between">
          <div className="title w-full p-1 h-[10%] flex-1">
            <div className="text-3xl">Comprehensive Employment & Analytics Report</div>
          </div>
          <Backtochat/>
        </div>

        <div className="final-result flex justify-center items-center h-[95%]">
        {result['is_error'] ? (<div className='text-black font-bold'>{result['Analytics_response']}</div>) : (<img src={`data:image/png;base64,${result['chart_base64']}`} alt="Generated Chart" className='w-[90%] h-[90%] relative object-contain' />)}
        </div>
      </div>
      <Details />
    </div>
  )
}

export default Empresult
