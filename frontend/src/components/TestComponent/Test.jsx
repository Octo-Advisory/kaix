import React, { useState } from 'react';
import { FaList, FaStar, FaClipboardList, FaEllipsisH } from "react-icons/fa";
function Test() {
  const incentives = [
    {
      name: "Performance Bonus",
      type: "Monetary",
      description: "Reward for outstanding performance in Q1.",
      startDate: "2025-03-01",
      endDate: "2025-06-30",
    },
    {
      name: "Employee of the Month",
      type: "Recognition",
      description: "Awarded to the best performer of the month.",
      startDate: "2025-03-01",
      endDate: "2025-03-31",
    },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">Incentives</h1>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {incentives.map((incentive, index) => (
          <IncentiveCard key={index} incentive={incentive} />
        ))}
      </div>
    </div>
  );
}

const IncentiveCard = ({ incentive }) => {
  return (
    <div className="bg-white shadow-lg rounded-2xl p-6 border border-gray-200 transition hover:shadow-xl">
      <h2 className="text-xl font-semibold text-gray-800">{incentive.name}</h2>
      <span className="text-sm text-gray-500 bg-blue-100 px-3 py-1 rounded-full">
        {incentive.type}
      </span>
      <p className="text-gray-600 mt-3">{incentive.description}</p>
      <div className="mt-4 flex justify-between text-sm text-gray-500">
        <span>📅 {incentive.startDate} - {incentive.endDate}</span>
        <button className="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-600 transition">
          View Details
        </button>
      </div>
    </div>
  );
};

export default Test;
