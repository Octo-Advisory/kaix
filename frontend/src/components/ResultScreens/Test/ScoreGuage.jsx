import GaugeChart from "react-gauge-chart";

const ScoreGauge = ({ value }) => {
  return (
    <div className="w-[250px]">
      <GaugeChart
        id="gauge-chart"
        nrOfLevels={20}
        colors={["#FF5F6D", "#FFC371", "#4CAF50"]}
        arcWidth={0.3}
        percent={value / 100}
        textColor="#0B2152"
      />
    </div>
  );
};

export default ScoreGauge
