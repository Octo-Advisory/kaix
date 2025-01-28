import React, { useState, useEffect } from "react";
import { useFrappeEventListener, useFrappeGetDocList } from "frappe-react-sdk";

function TestComponent() {
  const [first, setFirst] = useState(false);
  // const [data, setData] = useState(null); // Store data in local state
  const [error, setError] = useState(null);

  const {data,mutate} = useFrappeGetDocList("Session",{
     fields : ["progress.process_value","progress.status"],
     filters : [["name","=","s10t518787"]]
   })

  // const fetchData = async () => {
  //   try {
  //     const response = await fetch('/api/resource/Session?fields=["progress.process_name","progress.process_value","progress.status"]', {
  //       method: 'GET',
  //       headers: {
  //         // 'Authorization': 'token your_api_token', // Replace with actual token
  //         'Content-Type': 'application/json'
  //       }
  //     });
  
  //     // Check if the response is OK
  //     if (!response.ok) {
  //       throw new Error(`Error: ${response.statusText}`);
  //     }
  
  //     const data = await response.json();
  //     console.log("data is",data);
  //     // Optionally, store it in your state or handle further logic
  //   } catch (error) {
  //     console.error('Error fetching data:', error); // Handles errors
  //   }
  // }

  useFrappeEventListener("progress_update",(eventData)=>{
    console.log(eventData);
    mutate()
  })

  console.log("data is",data);
  
    // useEffect(()=>{
    //   fetchData()
    //   const interval = setInterval(fetchData, 1000);

    // // Cleanup interval on component unmount
    // return () => clearInterval(interval);
    // })
  return (
    <div>
      <h1>Chat Screen</h1>
      {/* <p>First state value (toggled every second): {first.toString()}</p>
      <p>Data: {JSON.stringify(data)}</p>
      {error && <p>Error: {error.message}</p>} */}
    </div>
  );
}

export default TestComponent;