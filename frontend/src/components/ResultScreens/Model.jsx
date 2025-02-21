import React from 'react'
import { FaCheckCircle } from 'react-icons/fa';
import { FaTimesCircle } from 'react-icons/fa';
import { GoAlertFill } from "react-icons/go";

function Model({ isOpen, onClose, title, data }) {
  if (!isOpen) return null;

   const statusIcon = {
          good: <FaCheckCircle size={20} color="green" />,
          bad: <FaTimesCircle size={20} color="red" />,
          warning: <GoAlertFill size={20} color="yellow" />,
          danger: <GoAlertFill size={20} color="red" />,
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg w-11/12 md:w-1/2 lg:w-1/3 max-h-[80vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4">
          {data.map((item, index) => (
            <div key={index} className="flex items-center gap-3 mb-3">
              <div className="text-green-500">
                {statusIcon[item.status] ? (statusIcon[item.status]):(<FaCheckCircle size={20} />) }
              </div>
              <div className="text-gray-700">
                {item.total_vendor
                  ? `${item.total_vendor} suppliers for ${item.supply} with the top choice ${item.nearest_venodor_distance} km away`
                  : item.incentive_name || item.approval_name}
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 focus:outline-none"
          >
            Close
          </button>
        </div>
      </div>
    </div>

  )
}

export default Model
