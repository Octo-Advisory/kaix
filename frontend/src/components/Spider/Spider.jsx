import React from "react";
import { Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

function Spider({ label, scores }) {
  const labels = ["Property Suitability", "Employment", "Incentive", "Approvals", "Vendors"];

  const factorColors = {
    'Property Suitability': "#673AB7", // Purple
    Employment: "#2C53A3",  // Medium Blue
    Incentive: "#4CAF50",   // Green
    Approvals: "#E91E63",   // Magenta
    Vendors: "#70A1D9",     // Light Blue
  };

  const pointColors = labels.map(label => factorColors[label]);

  const data = {
    labels,
    datasets: [
      {
        label,
        data: scores,
        fill: true,
        backgroundColor: "rgba(11, 33, 82, 0.1)",
        borderColor: "#0B2152",
        pointBackgroundColor: pointColors,
        pointBorderColor: "#fff",
        pointHoverRadius: 7,
        pointRadius: 5,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 10,
        ticks: {
          stepSize: 2,
          color: "#4b5563",
          font: {
            weight: "bold",
            size: 12,
          },
          backdropColor: "rgba(255,255,255,0.8)",
        },
        angleLines: {
          color: "rgba(200, 200, 200, 0.5)",
        },
        grid: {
          color: "rgba(200, 200, 200, 0.3)",
        },
        pointLabels: {
          font: {
            size: 14,
            weight: "600",
            // family: "Inter, sans-serif",
          },
          color: (context) => {
            return factorColors[labels[context.index]] || '#000';
          }
        },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(31, 41, 55, 0.9)",
        titleColor: "#fff",
        bodyColor: "#fff",
        padding: 12,
        cornerRadius: 8,
        titleFont: {
          size: 14,
          weight: "bold",
        },
        bodyFont: {
          size: 12,
          weight: "500",
        },
      },
    },
  };

  return <Radar data={data} options={options} />;
}

export default Spider;