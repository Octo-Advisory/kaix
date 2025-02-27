import React, { useState } from 'react';
import { FaList, FaStar, FaClipboardList, FaEllipsisH } from "react-icons/fa";
const approvalsData = {
  "Pre-Operation": [
    "Application for E-waste (Management and Handling)",
    "Approval of Electrical Installation",
    "Biomedical Waste Authorization (under Biomedical Waste Management Rules, 2016)",
    "Electrical Installation Certification",
    "Factory License Application",
    "GPCB - Consolidated Consent and Authorisation",
    "GPCB - Plastic Waste Registration",
    "License for contractors under provision of The Contracts Labour",
    "License for Principal Employer - under Contract Labour Act",
    "New HT Connection for DGVCL, MGVCL, PGVCL, UGVCL",
    "Profession Tax (Enrollment Certificate) - authority as per location chosen above",
    "Solid Waste Authorization Module (under Solid Waste Management Rules, 2016)"
  ],
  "Pre-Establishment": [
    "Approval for Boiler manufacturer",
    "Building and Other Construction Workers Permission",
    "Building Plan Approval - GIDC",
    "Certificate of non forest land/ NOC from forest dept.",
    "Encumbrance certificate",
    "GIDC - Land Application",
    "GPCB - Consent To Establish",
    "Industrial Entrepreneur Memorandum (IEM) Registration",
    "Land 65 NA Application (Online Revenue)",
    "MSME Intent Registration",
    "NOC for Fire Department",
    "Permission for Restricted Tree Cutting",
    "Property Registration",
    "Registration of Partnership Firms",
    "Tree Cutting Application Under Forest Dept"
  ]
};

function Test() {
  const [viewMode, setViewMode] = useState("Pre-Operation");

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-[#f4f4f9]">
      <div className="w-[95%] h-[95%] mx-auto my-5 p-5 bg-white rounded-lg shadow-md">
        <div className="title w-full p-1 h-[10%]">
          <div className="text-5xl text-center">Approvals</div>
        </div>
        <div className="select-sections py-2 h-[10%] flex items-center gap-2 justify-center">
        <button 
  className="bg-gradient-to-r from-green-400 to-green-600 text-white px-3 py-2 rounded-md"
  onClick={() => setViewMode("Pre-Operation")}
>
  <FaList size={22} /> Pre-Operation
</button>

<button 
  className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-white px-3 py-2 rounded-md"
  onClick={() => setViewMode("Pre-Establishment")}
>
  <FaStar size={22} /> Pre-Establishment
</button>

<button 
  className="bg-gradient-to-r from-blue-400 to-blue-600 text-white px-3 py-2 rounded-md"
  onClick={() => setViewMode("Pre-Requisite")}
>
  <FaClipboardList size={22} /> Pre-Requisite
</button>

<button 
  className="bg-gradient-to-r from-gray-400 to-gray-600 text-white px-3 py-2 rounded-md"
  onClick={() => setViewMode("Others")}
>
  <FaEllipsisH size={22} /> Others
</button>
        </div>
        <div className="py-5 h-[80%] overflow-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-200">
                <th className="p-3 border">Approval Name</th>
              </tr>
            </thead>
            <tbody>
              {approvalsData[viewMode].map((item, index) => (
                <tr key={index} className="border text-center hover:bg-gray-100">
                  <td className="p-3 border">{item}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Test;
