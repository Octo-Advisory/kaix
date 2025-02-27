import React, { useState } from "react";
import "./App.css"; // Import your CSS file for styling

const App = () => {
  const [showAllData, setShowAllData] = useState(false);

  const data = {
    final: {
      supply_id: { 0: "Boxes", 1: "Packaging Materials" },
      supply_score: { 0: 6.8412660905, 1: 6.4206700697 },
      vendor_id: {
        0: "MS Paper and Engineering Works",
        1: "Kirti Paper Bag Sales Agency",
      },
      vendor_supply_capacity: { 0: 5000.0, 1: 10000.0 },
      Distance: { 0: 6.0944684397, 1: 2.1778887862 },
    },
    all: {
      supply_id: {
        10: "Boxes",
        17: "Boxes",
        11: "Boxes",
        0: "Boxes",
        14: "Boxes",
        5: "Boxes",
        1: "Boxes",
        8: "Boxes",
        7: "Packaging Materials",
        12: "Packaging Materials",
        4: "Packaging Materials",
        15: "Packaging Materials",
        9: "Packaging Materials",
        6: "Packaging Materials",
        16: "Packaging Materials",
        13: "Packaging Materials",
      },
      Final_Score_With_Features: {
        10: 6.8412660905,
        17: 6.3371416989,
        11: 6.3005847329,
        0: 6.0748820598,
        14: 5.761257,
        5: 5.720548918,
        1: 5.3872648652,
        8: 3.770007,
        7: 6.4206700697,
        12: 6.3927746883,
        4: 6.0167521182,
        15: 5.840007,
        9: 5.8229517319,
        6: 5.8083592357,
        16: 5.210007,
        13: 4.5945604255,
      },
      vendor_id: {
        10: "MS Paper and Engineering Works",
        17: "Swiss Pac Pvt Ltd",
        11: "Nagdev Plastic Industries Manufacturers of Garbage bags Trash Bags BioHazard Bags Polythene sheet Construction Sheet",
        0: "A1 Enterprise",
        14: "RSTRADERS",
        5: "Himja Vacuum Packaging Best For Food and Clothes Vacuum Packaging",
        1: "Aaaka Plastics",
        8: "Krishna Plastic and Packaging Industries",
        7: "Kirti Paper Bag Sales Agency",
        12: "Nagdev Plastic Industries Manufacturers of Garbage bags Trash Bags BioHazard Bags Polythene sheet Construction Sheet",
        4: "Expert kraft",
        15: "RSTRADERS",
        9: "Mahalaxmi Plastic",
        6: "Himja Vacuum Packaging Best For Food and Clothes Vacuum Packaging",
        16: "Securement Packaging Pvt Ltd",
        13: "Pramukh Packaging",
      },
      vendor_supply_capacity: {
        10: 5000.0,
        17: 5000.0,
        11: 5000.0,
        0: 100000.0,
        14: 5000.0,
        5: 5000.0,
        1: 5000.0,
        8: 5000.0,
        7: 10000.0,
        12: 10000.0,
        4: 10000.0,
        15: 10000.0,
        9: 10000.0,
        6: 10000.0,
        16: 10000.0,
        13: 10000.0,
      },
      Dist: {
        10: 6.0944684397,
        17: 15.4609997884,
        11: 5.5379435832,
        0: 3.7981020303,
        14: 1.948120047,
        5: 3.4993273135,
        1: 2.6849195853,
        8: 101.4719699684,
        7: 2.1778887862,
        12: 5.5379435832,
        4: 6.8887243915,
        15: 1.948120047,
        9: 2.3497891653,
        6: 3.4993273135,
        16: 102.0795237123,
        13: 87.0040031208,
      },
    },
  };

  const toggleAllData = () => {
    setShowAllData(!showAllData);
  };

  return (
    <div className="container">
      <h1>Supply and Vendor Data</h1>

      {/* Final Data Table */}
      <div className="section">
        <h2>Final Data</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Supply ID</th>
              <th>Supply Score</th>
              <th>Vendor ID</th>
              <th>Vendor Supply Capacity</th>
              <th>Distance</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(data.final.supply_id).map((key) => (
              <tr key={key}>
                <td>{data.final.supply_id[key]}</td>
                <td>{data.final.supply_score[key].toFixed(2)}</td>
                <td>{data.final.vendor_id[key]}</td>
                <td>{data.final.vendor_supply_capacity[key]}</td>
                <td>{data.final.Distance[key].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* All Data Section */}
      <div className="section">
        <h2 onClick={toggleAllData} className="toggle-header">
          All Data {showAllData ? "▲" : "▼"}
        </h2>
        {showAllData && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Supply ID</th>
                <th>Final Score</th>
                <th>Vendor ID</th>
                <th>Vendor Supply Capacity</th>
                <th>Distance</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(data.all.supply_id).map((key) => (
                <tr key={key}>
                  <td>{data.all.supply_id[key]}</td>
                  <td>{data.all.Final_Score_With_Features[key].toFixed(2)}</td>
                  <td>{data.all.vendor_id[key]}</td>
                  <td>{data.all.vendor_supply_capacity[key]}</td>
                  <td>{data.all.Dist[key].toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default App;