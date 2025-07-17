import React, { useEffect, useState } from 'react';
import Details from '../Details/Details';
import Backtochat from '../Backtochat/Backtochat';
import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { useSelector } from 'react-redux';
import { useFrappeUpdateDoc } from 'frappe-react-sdk';

ChartJS.register(ArcElement, Tooltip, Legend);

function Empresult({ result, rerender }) {
  console.log("Emp result is", result);
  const lastChatId = useSelector((state) => state.chat.lastId);
  const { updateDoc } = useFrappeUpdateDoc()
  const [employment, setEmployment] = useState({});

  // const employment = JSON.parse(result?.Analytics_response?.city_summary || '{}');
  // console.log("Parsed Employment Data:", employment);

  useEffect(() => {
    const handleEmpData = async () => {
      const parsedEmployment = JSON.parse(result?.Analytics_response?.city_summary || '{}');
      console.log("employment is", parsedEmployment);
      setEmployment(parsedEmployment);
      
      if (rerender != 1) {
        await updateDoc("Chat history", lastChatId, {
            result: JSON.stringify({ "result": result }),
            intension: "Query to Get Employee Search"
          });
    }}

    handleEmpData()

  }, [result, rerender, lastChatId, updateDoc])
  // Chart Data
  const pieData = {
    labels: ["Skilled", "Semi-Skilled", "Unskilled"],
    datasets: [
      {
        data: [
          employment?.['Skilled'] || 0,
          employment?.['Semi-skilled'] || 0,
          employment?.['Unskilled'] || 0,
        ],
        backgroundColor: ["#2563EB", "#16A34A", "#D97706"],
        borderWidth: 1,
      },
    ],
  };

  // Chart Options
  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false // hide legend
      },
    },
  };

  return (
    <div className="flex flex-col items-center justify-center w-screen h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655] overflow-hidden">
      <div className="w-[98%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        {/* Title Section */}
        <div className="top-header flex flex-row  items-center justify-between mb-4">
          <div className="title w-fit p-1">
            <div className="text-2xl font-medium">Comprehensive Employment & Analytics Report</div>
          </div>
          <Backtochat text="Back to Chat" />
        </div>

        <div className="final-result flex flex-col items-center justify-center h-[85%]">
          {result?.is_error ? (
            <div className="text-black font-bold text-center">
              {result?.Analytics_response}
            </div>
          ) : (
            <>
              <div className="w-full max-w-md h-64 relative mb-6">
                <Pie data={pieData} options={pieOptions} />
              </div>

              <div className="mt-2 h-fit grid grid-cols-3 gap-4 w-full max-w-md">
                <div className="text-center flex flex-col gap-1">
                  <div className="text-sm font-medium">Skilled</div>
                  <div className="text-lg text-blue-600 font-semibold">
                    {employment?.['Skilled'] || 0} workers
                  </div>
                </div>
                <div className="text-center flex flex-col gap-1">
                  <div className="text-sm font-medium">Semi-skilled</div>
                  <div className="text-lg text-green-600 font-semibold">
                    {employment?.['Semi-skilled'] || 0} workers
                  </div>
                </div>
                <div className="text-center flex flex-col gap-1">
                  <div className="text-sm font-medium">Unskilled</div>
                  <div className="text-lg text-amber-600 font-semibold">
                    {employment?.['Unskilled'] || 0} workers
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Empresult;