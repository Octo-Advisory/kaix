import React from 'react'

function Vendorcards({supplier}) {
    console.log("supplier is",supplier);
    
  return (
    <div className="flex justify-center items-center h-full bg-gray-100">
    <div className="bg-white shadow-lg rounded-2xl p-6 h-[90%] w-[90%]">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">{supplier.vendor_id}</h2>
      <p className="text-gray-600"><strong>Supply :</strong> {supplier.supply_id}</p>
      <p className="text-gray-600"><strong>Supply Capacity:</strong> {supplier.vendor_supply_capacity}</p>
      <p className="text-gray-600"><strong>Experience:</strong> {supplier.years_of_experience} years</p>
      <p className="text-gray-600"><strong>Past Clients:</strong> {supplier.no_of_past_clients}</p>
      <p className="text-gray-600"><strong>Services:</strong> {supplier.no_of_servieces}</p>
      <p className="text-gray-600"><strong>Employees:</strong> {supplier.no_of_employees}</p>
      <p className="text-gray-600"><strong>Distance:</strong> {supplier.Dist ? Number(supplier.Dist).toFixed(2) : "N/A"} km</p>
    </div>
  </div>
  )
}

export default Vendorcards