import React, { useEffect, useState } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { useSelector } from 'react-redux';
import { useFrappeUpdateDoc } from 'frappe-react-sdk';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ReTooltip,
  Legend as ReLegend,
  ResponsiveContainer,
} from "recharts";

ChartJS.register(ArcElement, Tooltip, Legend);

function Empresult({ result, rerender }) {
  const lastChatId = useSelector((state) => state.chat.lastId);
  const { updateDoc } = useFrappeUpdateDoc();

  const [employment, setEmployment] = useState({});
  const [comparison, setComparison] = useState({});
  const [comparisonPercentage, setComparisonPercentage] = useState({});
  const [showPercentage, setShowPercentage] = useState(false);

  useEffect(() => {
    const handleEmpData = async () => {
      const parsedEmployment = JSON.parse(result?.Analytics_response?.city_summary || '{}');
      const parsedComparison = JSON.parse(result?.Analytics_response?.comparison_data || '{}');
      const parsedComparisonPercentage = JSON.parse(result?.Analytics_response?.comparison_data_percentage || '{}');

      setEmployment(parsedEmployment);
      setComparison(parsedComparison);
      setComparisonPercentage(parsedComparisonPercentage);

      if (rerender !== 1) {
        await updateDoc("Chat history", lastChatId, {
          result: JSON.stringify({ result }),
          intension: "Query to Get Employee Search",
        });
      }
    };

    handleEmpData();
  }, [result, rerender, lastChatId, updateDoc]);

  // Format comparison data for Recharts — DYNAMIC version
const formatData = (obj) => {
  if (!obj || Object.keys(obj).length === 0) return [];

  const allCities = Array.from(
    new Set(
      Object.values(obj)
        .map((cityObj) => Object.keys(cityObj))
        .flat()
    )
  );

  return Object.keys(obj).map((category) => {
    const entry = { Category: category };
    allCities.forEach((city) => {
      const val = obj[category]?.[city] || 0;
      entry[city] = Number(val.toFixed ? val.toFixed(2) : parseFloat(val).toFixed(2));
    });
    return entry;
  });
};

  const chartData = showPercentage
    ? formatData(comparisonPercentage)
    : formatData(comparison);

  // Doughnut chart data
  const doughnutData = {
    labels: ["Skilled", "Semi-Skilled", "Unskilled"],
    datasets: [
      {
        data: [
          employment?.["Skilled"]?.toFixed(2) || 0,
          employment?.["Semi-skilled"]?.toFixed(2) || 0,
          employment?.["Unskilled"]?.toFixed(2) || 0,
        ],
        backgroundColor: ["#2563EB", "#16A34A", "#D97706"],
        borderWidth: 2,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
  };

  // Detect whether to show comparison or single city
  const hasComparison =
    comparison && Object.keys(comparison).length > 0 && Object.keys(comparison[Object.keys(comparison)[0]] || {}).length > 1;

  return (
    <div className="flex flex-col items-center justify-center w-screen h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655] overflow-y-auto">
      <div className="w-[98%] min-h-[95%] mx-auto my-5 p-5 flex flex-col bg-white rounded-lg shadow-md">
        
        {/* Header */}
        <div className="flex flex-row items-center justify-between mb-4">
          <div className="w-fit p-1">
            <div className="text-2xl font-medium">Comprehensive Employment & Analytics Report</div>
          </div>
          <Backtochat text="Back to Chat" />
        </div>

        {/* Main Section */}
        <div className="flex flex-col items-center justify-center h-full space-y-10">
          {result?.is_error ? (
            <div className="text-black font-bold text-center">
              {result?.Analytics_response}
            </div>
          ) : hasComparison ? (
            // 🟩 When multiple cities → Bar Chart comparison
            <div className="w-full max-w-4xl h-[400px] mt-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xl font-semibold text-gray-800">
                  City-wise Comparison ({showPercentage ? "Percentage" : "Absolute"})
                </h3>
                <button
                  onClick={() => setShowPercentage(!showPercentage)}
                  className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition"
                >
                  {showPercentage ? "Show Absolute Data" : "Show Percentage Data"}
                </button>
              </div>

<ResponsiveContainer width="100%" height="100%">
  <BarChart
    data={chartData}
    margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
  >
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="Category" />
    <YAxis domain={showPercentage ? [0, 100] : ["auto", "auto"]} />
    <ReTooltip />
    <ReLegend />

    {chartData.length > 0 && (() => {
      const cityKeys = Object.keys(chartData[0]).filter((key) => key !== "Category");

      // 🎨 Generate consistent color for each city name
      const getColorForCity = (city) => {
        const hash = [...city].reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const hue = hash % 360; // map hash to color wheel
        return `hsl(${hue}, 70%, 50%)`;
      };

      return cityKeys.map((city) => (
        <Bar
          key={city}
          dataKey={city}
          fill={getColorForCity(city)}
          radius={[6, 6, 0, 0]}
        />
      ));
    })()}
  </BarChart>
</ResponsiveContainer>


            </div>
          ) : (
            // 🟦 When single city → Doughnut Chart
            <div className='relative flex flex-col items-center w-full h-fit'>
              <div className="w-full max-w-md h-80 relative mb-6">
                <Doughnut data={doughnutData} options={doughnutOptions} />
              </div>

              <div className="mt-2 grid grid-cols-3 gap-4 w-full max-w-md">
                <div className="text-center flex flex-col gap-1">
                  <div className="text-sm font-medium">Skilled</div>
                  <div className="text-lg text-blue-600 font-semibold">
                    {employment?.["Skilled"] || 0} workers
                  </div>
                </div>
                <div className="text-center flex flex-col gap-1">
                  <div className="text-sm font-medium">Semi-skilled</div>
                  <div className="text-lg text-green-600 font-semibold">
                    {employment?.["Semi-skilled"] || 0} workers
                  </div>
                </div>
                <div className="text-center flex flex-col gap-1">
                  <div className="text-sm font-medium">Unskilled</div>
                  <div className="text-lg text-amber-600 font-semibold">
                    {employment?.["Unskilled"] || 0} workers
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Empresult;
