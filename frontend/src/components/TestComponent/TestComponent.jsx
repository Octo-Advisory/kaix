import React, { useState, useEffect } from "react";
import { useFrappeGetCall } from "frappe-react-sdk";

function TestComponent() {
  const [count, setCount] = useState(null);

  const { data, error, isLoading } = useFrappeGetCall("mars.mars.testing");

  useEffect(() => {
    if (data) {
      console.log("API Data:", data);
      setCount(data.message); // Update only with the correct data
    }
  }, [data]);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Frappe Get Call Results</h1>
      {count !== null ? (
        <pre>{JSON.stringify(count)}</pre>
      ) : (
        <div>No data available</div>
      )}
    </div>
  );
}

export default TestComponent;