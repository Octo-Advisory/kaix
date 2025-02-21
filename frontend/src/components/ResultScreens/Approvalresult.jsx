import React from 'react'

function Approvalresult({ result }) {
    console.log("resulkt from approval screen", result);
    const Analytics_response = result["Analytics_response"];
    // console.log("Analytics_response", Analytics_response);
    const total_effective_time = Analytics_response["Total Effective Time"]
    const online_percentage = Analytics_response["Online Percentage"]
    const approval_data = JSON.parse(Analytics_response["Approval Data"])
    // console.log("approval_dataa", approval_data);
    const approval_name = approval_data["Approval Name"]
    const stages = approval_data["Stages"]
    const approvals = Object.values(approval_name)
    // console.log("approvals", approvals);
    // Convert the JSON data into an array of objects for easier manipulation
    const items = Object.keys(approval_name).map(key => ({
        approvalName: approval_name[key],
        stage: stages[key]
      }));

      console.log("stages",items);

    const finalData = items.reduce((acc,item)=>{
        if(!acc[item.stage]){
            acc[item.stage] = [];
        }
        acc[item.stage].push(item.approvalName);
        return acc
    },{})
    
    console.log("finalData",finalData);
    
      
    return (
        <div className='h-screen w-full flex flex-col items-center justify-center bg-[#242f6a] p-6'>
            {/* Title */}
            <div className="text-2xl font-bold text-white mb-4">Approvals</div>

            {/* Table Container */}
            <div className="w-full bg-white rounded-lg shadow-lg flex-1 flex flex-col overflow-hidden">
                <div className="overflow-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#166d5b] text-white text-center">
                                <th colSpan={2} className="p-4 text-lg font-semibold">
                                    Total Effective Time: <span className="font-normal">{total_effective_time} Days</span> | Online Percentage: <span className="font-normal">{online_percentage} %</span>
                                </th>
                            </tr>
                            <tr className="bg-[#19a282] text-white sticky top-0">
                                <th className="p-4 text-lg font-semibold">No.</th>
                                <th className="p-4 text-lg font-semibold">Approval Name</th>
                            </tr>
                        </thead>
                        <tbody>
                            {approvals.map((approval, index) => (
                                <tr
                                    key={index}
                                    className={`${index % 2 === 0 ? "bg-gray-100" : "bg-white"} hover:bg-[#19a282]/20 transition-all`}
                                >
                                    <td className="p-4 text-gray-800">{index + 1}</td>
                                    <td className="p-4 text-gray-800">{approval}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Approvalresult
