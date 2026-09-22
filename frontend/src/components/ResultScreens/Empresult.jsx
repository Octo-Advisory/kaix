import React, { useContext, useEffect, useState } from 'react';
import Backtochat from '../Backtochat/Backtochat';
import { Doughnut } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { useSelector } from 'react-redux';
import { FrappeContext, useFrappeUpdateDoc } from 'frappe-react-sdk';
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

  const { call } = useContext(FrappeContext)
  // Store result data function
  const storeResultData = async (lastChat, resultData) => {
    
    if (!lastChat || !resultData) return;
    const {chart_64, ...restAnalytics } = resultData;
    
    try {
      // Prepare the data to store
      // const dataToStore = {
      //   result: restAnalytics,  // Store the complete result object
      // };
  
      const convertJson = await call.post(
        "kaix.Management_Class.helpers.utility.convert_json_to_binary", 
        {
          child_row_id: lastChat,
          updated_solutions: restAnalytics,
          intension: "Query to Get Employee Search",
        },
        {
          headers: {
            'Expect': '' // 👈 Clear problematic header
          }
        }
      );
      
      // console.log("Result data stored successfully:", convertJson);
      return convertJson;
      
    } catch (err) {
      // console.error("Error Storing Result json:", err);
      // Note: You need to import createDiagnostic or handle this differently
      // createDiagnostic("Employment Search", `Something went wrong while storing the result json ${JSON.stringify(err)}`, lastChat)
      return null;
    }
  };
  const lastChatId = useSelector((state) => state.chat.lastId);
  const { updateDoc } = useFrappeUpdateDoc();

  const [employment, setEmployment] = useState({});
  const [comparison, setComparison] = useState({});
  const [comparisonPercentage, setComparisonPercentage] = useState({});
  const [showPercentage, setShowPercentage] = useState(false);
  const [isBarChart, setIsBarChart] = useState(false);
  const [hasSelectedData, setHasSelectedData] = useState(false);
  const [hasOtherData, setHasOtherData] = useState(false);
  const [debugInfo, setDebugInfo] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [chartTitle, setChartTitle] = useState('');
  const [isDataStored, setIsDataStored] = useState(false); // Track if data is stored

  // ---- DEBUG LOGGER ----
  const logDebug = (message, data = null) => {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    if (data) {
      // console.log(logMessage, data);
    } else {
      // console.log(logMessage);
    }
    setDebugInfo(prev => prev + logMessage + '\n');
  };

  // ---- SIMPLIFIED JSON PARSER ----
  const parseData = (str) => {
    if (!str) return {};
    
    // If it's already an object, return it
    if (typeof str === 'object') return str;
    
    // If it's not a string, return empty object
    if (typeof str !== 'string') return {};
    
    // Remove any extra quotes and backslashes
    let cleanStr = str.trim();
    
    // If it starts and ends with quotes, remove them
    if (cleanStr.startsWith('"') && cleanStr.endsWith('"')) {
      cleanStr = cleanStr.slice(1, -1);
    }
    
    // Replace escaped quotes
    cleanStr = cleanStr.replace(/\\"/g, '"');
    
    try {
      return JSON.parse(cleanStr);
    } catch (e) {
      // If still fails, try to extract JSON from string
      try {
        const jsonMatch = cleanStr.match(/\{.*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        }
      } catch (e2) {
        // console.error('Failed to parse JSON:', e2);
      }
      return {};
    }
  };

  // ----- FORMAT COMPARISON DATA FOR RE-CHARTS -----
  const formatComparisonData = (data) => {
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
      return {};
    }
    
    const allCities = new Set();
    Object.values(data).forEach(cityData => {
      if (cityData && typeof cityData === 'object') {
        Object.keys(cityData).forEach(city => allCities.add(city));
      }
    });
    
    const citiesArray = Array.from(allCities);
    
    const formattedData = {};
    
    citiesArray.forEach(city => {
      const cityEntry = {};
      
      Object.keys(data).forEach(employmentType => {
        const cityData = data[employmentType];
        if (cityData && cityData[city] !== undefined) {
          cityEntry[employmentType] = cityData[city];
        }
      });
      
      if (Object.keys(cityEntry).length > 0) {
        formattedData[city] = cityEntry;
      }
    });
    
    return formattedData;
  };

  // ----- CALCULATE PERCENTAGES FOR COMPARISON DATA -----
  const calculateComparisonPercentages = (data) => {
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
      return {};
    }
    
    const percentageData = {};
    
    Object.keys(data).forEach(city => {
      const cityData = data[city];
      const cityTotal = Object.values(cityData).reduce((sum, val) => sum + (Number(val) || 0), 0);
      
      const cityPercentages = {};
      
      Object.keys(cityData).forEach(employmentType => {
        const value = Number(cityData[employmentType]) || 0;
        cityPercentages[employmentType] = cityTotal > 0 ? (value / cityTotal) * 100 : 0;
      });
      
      percentageData[city] = cityPercentages;
    });
    
    return percentageData;
  };

  // ----- STORE RESULT IN DATABASE -----
  const storeResultInDB = async (resultData) => {
    if (!lastChatId || !resultData || isDataStored) return;
    
    try {
      logDebug('Storing result data in database...');
      // console.log(resultData, 'This is he result data')
      // Store the result using the function you provided
      const storeResult = await storeResultData(
        lastChatId, 
        resultData
      );
      
      if (storeResult) {
        setIsDataStored(true);
        logDebug('Result data successfully stored in database');
      } else {
        logDebug('Failed to store result data');
      }
    } catch (error) {
      console.error("Failed to store result:", error);
      logDebug('Error storing result data:', error);
    }
  };

  // ----- MAIN USE EFFECT -----
  useEffect(() => {
    const handleEmpData = async () => {
      setIsLoading(true);
      logDebug('=== START handleEmpData ===');
      logDebug('Raw result:', result);
      
      if (!result) {
        logDebug('No result provided');
        setIsLoading(false);
        return;
      }

      const resp = result?.Analytics_response || {};
      logDebug('Analytics_response:', resp);

      // Reset states (except storage flag)
      setEmployment({});
      setComparison({});
      setComparisonPercentage({});
      setIsBarChart(false);
      setHasSelectedData(false);
      setHasOtherData(false);
      setChartTitle('');

      // Store the result data in database
      // Only store if we have valid data and haven't stored it yet
      if (result && !result.Is_Error && !isDataStored) {
        storeResultInDB(result);
      }

      // Check which scenario we have
      if (result.intention === 'Comparison between cities, states, or areas' || 
          resp.comparison_data || resp.comparison_data_percentage || 
          resp.selected_comparison || resp.other_comparison) {
        logDebug('Processing as COMPARISON data');
        setIsBarChart(true);
        
        let compData = {};
        let percData = {};
        
        if (resp.comparison_data) {
          compData = parseData(resp.comparison_data);
          percData = parseData(resp.comparison_data_percentage || {});
          
          const formattedCompData = formatComparisonData(compData);
          const formattedPercData = formatComparisonData(percData);
          
          setComparison(formattedCompData);
          setComparisonPercentage(formattedPercData);
          setChartTitle('Employment Comparison Across Cities');
          
          logDebug('Comparison data formatted:', formattedCompData);
          
        } else if (resp.selected_comparison || resp.other_comparison) {
          const selected = parseData(resp.selected_comparison || {});
          const other = parseData(resp.other_comparison || {});
          
          logDebug('Selected data from backend:', selected);
          logDebug('Other data from backend:', other);
          
          const allData = {};
          
          Object.keys(selected).forEach(type => {
            allData[type] = selected[type];
          });
          
          Object.keys(other).forEach(type => {
            allData[type] = other[type];
          });
          
          logDebug('Combined data (selected + other):', allData);
          
          const formattedCompData = formatComparisonData(allData);
          const formattedPercData = calculateComparisonPercentages(formattedCompData);
          
          setComparison(formattedCompData);
          setComparisonPercentage(formattedPercData);
          
          setHasSelectedData(Object.keys(selected).length > 0);
          setHasOtherData(Object.keys(other).length > 0);
          setChartTitle('Employment Comparison (Selected vs Other Types)');
          
          logDebug('Formatted comparison data:', formattedCompData);
          logDebug('Calculated percentage data:', formattedPercData);
        }
        
      } else if (result.intention === 'Individual employment status' || 
                 resp.city_summary || resp.total_state_summary || 
                 resp.selected_data || resp.other_summary || resp.remaining_summary) {
        logDebug('Processing as INDIVIDUAL data');
        setIsBarChart(false);
        
        let data = {};
        
        if (resp.city_summary) {
          data = parseData(resp.city_summary);
          setChartTitle('City Employment Distribution');
        } else if (resp.total_state_summary) {
          data = parseData(resp.total_state_summary);
          setChartTitle('State Employment Distribution');
        }
        
        if (Object.keys(data).length === 0) {
          if (resp.selected_data) {
            const selected = parseData(resp.selected_data);
            Object.assign(data, selected);
            setHasSelectedData(Object.keys(selected).length > 0);
            setChartTitle('Selected Employment Types');
          }
          if (resp.other_summary || resp.remaining_summary) {
            const other = parseData(resp.other_summary || resp.remaining_summary);
            Object.assign(data, other);
            setHasOtherData(Object.keys(other).length > 0);
          }
        }
        
        logDebug('Final employment data to set:', data);
        setEmployment(data);
      }

      logDebug('=== END handleEmpData ===');
      setIsLoading(false);
    };

    handleEmpData();
  }, [result, rerender, lastChatId, updateDoc, isDataStored]);

  // ----- CALCULATE INDIVIDUAL PERCENTAGE -----
  const calculateIndividualPercentage = () => {
    if (!employment || typeof employment !== 'object') {
      return { skilled: 0, semi: 0, unskilled: 0 };
    }
    
    const skilled = Number(
      employment["Skilled"] || 
      employment["skilled"] || 
      0
    );
    
    const semi = Number(
      employment["Semi-skilled"] || 
      employment["semi-skilled"] || 
      employment["Semi-Skilled"] || 
      0
    );
    
    const unskilled = Number(
      employment["Unskilled"] || 
      employment["unskilled"] || 
      0
    );
    
    const total = Object.values(employment).reduce((sum, val) => sum + Number(val || 0), 0);

    if (total === 0) {
      return { skilled: 0, semi: 0, unskilled: 0 };
    }

    return {
      skilled: (skilled / total) * 100,
      semi: (semi / total) * 100,
      unskilled: (unskilled / total) * 100,
    };
  };

  // ---- Doughnut Chart Data ----
  const getDoughnutData = () => {
    const percentData = calculateIndividualPercentage();
    
    const skilled = employment["Skilled"] || employment["skilled"] || 0;
    const semi = employment["Semi-skilled"] || employment["semi-skilled"] || employment["Semi-Skilled"] || 0;
    const unskilled = employment["Unskilled"] || employment["unskilled"] || 0;
    
    let other = 0;
    Object.keys(employment).forEach(key => {
      const lowerKey = key.toLowerCase();
      if (!lowerKey.includes('skilled') && !lowerKey.includes('unskilled')) {
        other += Number(employment[key] || 0);
      }
    });
    
    const skilledNum = Number(skilled) || 0;
    const semiNum = Number(semi) || 0;
    const unskilledNum = Number(unskilled) || 0;
    const otherNum = Number(other) || 0;
    
    const labels = ["Skilled", "Semi-Skilled", "Unskilled"];
    const data = [skilledNum, semiNum, unskilledNum];
    const backgroundColor = ["#2563EB", "#16A34A", "#D97706"];
    
    if (otherNum > 0) {
      labels.push("Other");
      data.push(otherNum);
      backgroundColor.push("#DC2626");
    }
    
    const chartData = showPercentage ? 
      [percentData.skilled || 0, percentData.semi || 0, percentData.unskilled || 0] : 
      data;
    
    if (otherNum > 0 && showPercentage) {
      const total = Object.values(employment).reduce((sum, val) => sum + Number(val || 0), 0);
      const otherPercent = total > 0 ? (otherNum / total) * 100 : 0;
      chartData[3] = otherPercent;
    }
    
    return {
      labels: labels,
      datasets: [
        {
          data: chartData,
          backgroundColor: backgroundColor,
          borderWidth: 2,
        },
      ],
    };
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
            return `${label}: ${showPercentage ? `${value.toFixed(1)}%` : Math.round(value)}`;
          }
        }
      }
    },
  };

  // ---- BAR CHART FORMATTER ----
  // const formatBarData = (data) => {
  //   if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
  //     return [];
  //   }
    
  //   return Object.keys(data).map(city => {
  //     const cityData = data[city];
  //     const entry = { Category: city };
      
  //     Object.keys(cityData).forEach(type => {
  //       const value = cityData[type];
  //       entry[type] = value !== undefined && value !== null ? 
  //         (showPercentage ? Number(Number(value).toFixed(2)) : Math.round(Number(value))) : 
  //         0;
  //     });
      
  //     return entry;
  //   });
  // };

  const formatBarData = (data) => {
  if (!data || typeof data !== "object" || Object.keys(data).length === 0) {
    return [];
  }

  const skillOrder = ["Skilled", "Semi-skilled", "Unskilled"];

  return Object.keys(data).map(city => {
    const cityData = data[city];
    const entry = { Category: city };

    skillOrder.forEach(type => {
      const value = cityData[type];
      entry[type] =
        value !== undefined && value !== null
          ? showPercentage
            ? Number(Number(value).toFixed(2))
            : Math.round(Number(value))
          : 0;
    });

    return entry;
  });
};

  const SKILL_ORDER = ["Skilled", "Semi-skilled", "Unskilled"];
  const COLORS = {
  "Skilled": "#2563EB",
  "Semi-skilled": "#16A34A",
  "Unskilled": "#D97706"
};
  // Get the appropriate data for bar chart
  const getBarChartData = () => {
    return showPercentage ? comparisonPercentage : comparison;
  };

  const barChartData = getBarChartData();
  console.log(barChartData,'bbbbbbbaaarrrr');
  const CustomLegend = () => (
  <ul style={{ display: "flex", gap: 16, listStyle: "none", padding: 0, justifySelf:'center' }}>
    {SKILL_ORDER.map(skill => (
      <li key={skill} style={{ display: "flex", alignItems: "center" }}>
        <span
          style={{
            width: 12,
            height: 12,
            backgroundColor: COLORS[skill],
            marginRight: 8
          }}
        />
        {skill}
      </li>
    ))}
  </ul>
);

  const formattedBarData = formatBarData(barChartData);
  
  // Check what data we have
  const hasComparison = isBarChart && formattedBarData.length > 0;
  const hasIndividualData = !isBarChart && employment && typeof employment === 'object' && Object.keys(employment).length > 0;
  
  // Calculate percentages for individual view
  const percentData = calculateIndividualPercentage();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center w-screen h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655]">
        <div className="w-[98%] min-h-[95%] mx-auto my-5 p-5 flex flex-col bg-white rounded-lg shadow-md items-center justify-center">
          <div className="text-xl">Loading employment data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center w-screen h-screen bg-gradient-to-br from-[#0e2044] to-[#41b655] overflow-y-auto">
      <div className="w-[98%] min-h-[95%] mx-auto my-5 p-5 flex flex-col bg-white rounded-lg shadow-md">

        <div className="flex flex-row items-center justify-between mb-4">
          <div className="text-2xl font-medium">Comprehensive Employment & Analytics Report</div>
          <Backtochat text="Back to Chat" />
        </div>

        {/* {chartTitle && (
          <div className="mb-2 text-center">
            <h3 className="text-lg font-semibold text-gray-800">{chartTitle}</h3>
            <p className="text-sm text-gray-600">{result?.intention}</p>
          </div>
        )} */}

        <div className="flex flex-col items-center justify-center h-full space-y-10">

          {hasComparison ? (
            <>
              <div className="w-full max-w-4xl h-[400px] mt-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xl font-semibold text-gray-800">
                    {showPercentage ? "Percentage Distribution" : "Worker Count by City"}
                  </h3>

                  <button
                    onClick={() => setShowPercentage(!showPercentage)}
                    className="px-3 py-1 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    {showPercentage ? "Show Absolute Data" : "Show Percentage Data"}
                  </button>
                </div>

                {formattedBarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart 
                      data={formattedBarData}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="Category" />
                      <YAxis 
                        width={80}
                        label={{ 
                          value: showPercentage ? 'Percentage (%)' : 'Number of Workers', 
                          angle: -90, 
                          position: 'insideLeft' ,
                          offset: -10,
                        
                        }}
                        domain={showPercentage ? [0, 100] : [0, 'auto']}
                      />
                      <ReTooltip 
                        formatter={(value, name) => [
                          showPercentage ? `${Number(value).toFixed(1)}%` : value.toLocaleString(),
                          name
                        ]}
                        itemSorter={(item) => SKILL_ORDER.indexOf(item.name)}
                      />
                     <ReLegend content={<CustomLegend />} />

                      {formattedBarData.length > 0 &&
                        SKILL_ORDER.map((type, index) => {
                          const colors = ["#2563EB", "#16A34A", "#D97706"];
                          return (
                            <Bar
                              key={type}
                              dataKey={type}
                              name={type}
                              fill={colors[index]}
                              radius={[6, 6, 0, 0]}
                            />
                          );
                        })}

                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    No comparison data available
                  </div>
                )}

                
              </div>
            </>
          ) : hasIndividualData ? (
            <div className="flex flex-col items-center">
              <div className="w-full max-w-md h-80">
                <Doughnut data={getDoughnutData()} options={doughnutOptions} />
              </div>

              <button
                onClick={() => setShowPercentage(!showPercentage)}
                className="px-3 py-1 mt-5 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                {showPercentage ? "Show Absolute Data" : "Show Percentage Data"}
              </button>

              <div className="grid grid-cols-3 gap-4 mt-5 max-w-md w-full">
                <div className="text-center">
                  <div className="text-sm font-medium">Skilled</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {showPercentage ? 
                      `${percentData.skilled.toFixed(1)}% workers` : 
                      `${Math.round(employment["Skilled"] || employment["skilled"] || 0)} workers`}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-sm font-medium">Semi-Skilled</div>
                  <div className="text-lg font-semibold text-green-600">
                    {showPercentage ? 
                      `${percentData.semi.toFixed(1)}% workers` : 
                      `${Math.round(employment["Semi-skilled"] || employment["semi-skilled"] || employment["Semi-Skilled"] || 0)} workers`}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-sm font-medium">Unskilled</div>
                  <div className="text-lg font-semibold text-amber-600">
                    {showPercentage ? 
                      `${percentData.unskilled.toFixed(1)}% workers` : 
                      `${Math.round(employment["Unskilled"] || employment["unskilled"] || 0)} workers`}
                  </div>
                </div>
              </div>
              
              {Object.keys(employment).some(key => {
                const lowerKey = key.toLowerCase();
                return !lowerKey.includes('skilled') && !lowerKey.includes('unskilled');
              }) && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg w-full max-w-md">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Other Employment Types:</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.keys(employment)
                      .filter(key => {
                        const lowerKey = key.toLowerCase();
                        return !lowerKey.includes('skilled') && !lowerKey.includes('unskilled');
                      })
                      .map(type => (
                        <div key={type} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">{type}:</span>
                          <span className="text-sm font-semibold text-gray-800">
                            {showPercentage ? 
                              `${((Number(employment[type]) / Object.values(employment).reduce((sum, val) => sum + Number(val || 0), 0)) * 100).toFixed(1)}%` : 
                              Math.round(Number(employment[type]))
                            }
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
              
             
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="text-xl font-semibold text-gray-700 mb-3">
                No Employment Data Available
              </div>
              <p className="text-gray-600">
                Please check your query or try a different location/parameter.
              </p>
              <div className="mt-4 p-3 bg-gray-100 rounded-lg text-xs font-mono max-h-40 overflow-auto">
                <div className="font-bold mb-1">Debug Info:</div>
                <pre>{debugInfo}</pre>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default Empresult;