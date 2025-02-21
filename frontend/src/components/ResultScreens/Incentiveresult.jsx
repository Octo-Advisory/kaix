import React from 'react';

function Incentiveresult({ result }) {
    console.log("result from incentive ", result);
    const Analytics_response = JSON.parse(result["Analytics_response"]);
    // console.lo g("Analytics_response", Analytics_response);
    const incentive_name = Analytics_response["Incentive Name"];
    const incentive_type = Analytics_response["Incentive Type"];

    const incentives = Object.values(incentive_name);
    const incentive_types = Object.values(incentive_type);

    return (
        <div className='h-screen w-full flex flex-col items-center justify-center bg-[#242f6a] p-6'>
            {/* Title */}
            <div className="text-2xl font-bold text-white mb-4">Incentives</div>
            
            {/* Table Container */}
            <div className="w-full bg-white rounded-lg shadow-lg flex-1 flex flex-col overflow-hidden">
                <div className="overflow-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#19a282] text-white sticky top-0">
                                <th className="p-4 text-lg font-semibold">No.</th>
                                <th className="p-4 text-lg font-semibold">Incentive Name</th>
                                <th className="p-4 text-lg font-semibold">Incentive Type</th>
                            </tr>
                        </thead>
                        <tbody>
                            {incentives.map((incentive, index) => (
                                <tr
                                    key={index}
                                    className={`${index % 2 === 0 ? "bg-gray-100" : "bg-white"} hover:bg-[#19a282]/20 transition-all`}
                                >
                                    <td className="p-4 text-gray-800">{index + 1}</td>
                                    <td className="p-4 text-gray-800">{incentive}</td>
                                    <td className="p-4 text-gray-800">{incentive_types[index]}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default Incentiveresult;
