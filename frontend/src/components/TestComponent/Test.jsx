import React from 'react'

const approvalsData = {
  "Pre-Operation": [
    "Application for E-waste (Management and Handling)",
    "Approval of Electrical Installation",
    "Biomedical Waste Authorization (under Biomedical Waste Management Rules, 2016)",
    "Electrical Installation Certification",
    "Factory License Application",
    "GPCB - Consolidated Consent and Authorisation",
    "GPCB - Plastic Waste Registration",
    "New HT Connection for DGVCL, MGVCL, PGVCL, UGVCL",
    "Profession Tax (Enrollment Certificate)",
    "Renewal of Consent to Operate"
  ],
  "Pre-Establishment": [
    "Approval for Boiler manufacturer",
    "Building Plan Approval - GIDC",
    "Development Permission - DSIRDA",
    "Encumbrance certificate",
    "GPCB - Consent To Establish",
    "Incorporation of Company under Companies Act (SPICe+ Forms)",
    "Land 65 NA Application (Online Revenue)",
    "MSME Intent Registration",
    "Property Registration",
    "Udyam Registration for MSME"
  ],
  "Pre-Operation1": [
    "Application for E-waste (Management and Handling)",
    "Approval of Electrical Installation",
    "Biomedical Waste Authorization (under Biomedical Waste Management Rules, 2016)",
    "Electrical Installation Certification",
    "Factory License Application",
    "GPCB - Consolidated Consent and Authorisation",
    "GPCB - Plastic Waste Registration",
    "New HT Connection for DGVCL, MGVCL, PGVCL, UGVCL",
    "Profession Tax (Enrollment Certificate)",
    "Renewal of Consent to Operate"
  ],
};

function Test() {   
  return (
    <div className="w-full bg-white rounded-lg shadow-lg flex-1 h-screen flex flex-col overflow-hidden">
    <div className="overflow-auto">
        <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-white z-10">
                <tr className="bg-[#166d5b] text-white text-center">
                    <th colSpan={2} className="p-4 text-lg font-semibold">
                        Total Effective Time: <span className="font-normal">80 Days</span> | Online Percentage: <span className="font-normal">92 %</span>
                    </th>
                </tr>
                <tr className="bg-[#19a282] text-white sticky top-0">
                    <th className="p-4 text-lg font-semibold">Stage</th>
                    <th className="p-4 text-lg font-semibold">Approvals</th>
                </tr>
            </thead>
            <tbody>
                {Object.entries(approvalsData).map(([stage, approvals], index) => (
                    <tr key={index} className={`${index % 2 === 0 ? "bg-gray-100" : "bg-white"} hover:bg-[#19a282]/20 transition-all`}>
                        <td className="p-4 text-gray-800">{stage}</td>
                        <td className="p-4 text-gray-800">
                            {approvals.map((item, idx) => (
                                <div key={idx} className='p-1'>{item}</div>
                            ))}
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
</div>
  )
}

export default Test
