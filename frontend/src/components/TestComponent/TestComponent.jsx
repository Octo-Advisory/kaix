import React, { useContext, useState } from "react";
import { FrappeContext } from "frappe-react-sdk";

function TestComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false); // Local loading state for the button
  const [error, setError] = useState(null); // Local error state

  const {call} = useContext(FrappeContext)

  const handleResponse = async () => {
    if (!input.trim()) return;

    // Add the user's message to the chat
    setMessages((prev) => [...prev, { sender: "user", text: input }]);

    try {
      // setIsLoading(true); // Set loading to true while waiting for the response

      // Example of using 'frappe-client' to call a custom method
      const searchParams = {
        method: 'frontend_app.Management_Class.AI.ai_module_call', // Replace with your actual method
        args: { input: input.trim() }, // Pass user input as an argument
      };

      // Perform the custom API call using frappe-client
      call.post("frontend_app.Management_Class.AI.ai_module_call", searchParams.args).then((res)=>{
        console.log(res);
        
        setMessages((prev) => [...prev, { sender: "bot", text: JSON.stringify(res.message) }]);
      })
      
      // console.log("call is",JSON.stringify(call));
      
      // Handle the bot's response
      

      // setIsLoading(false); // Set loading to false after receiving the response
    } catch (err) {
      console.error("Error:", err);
      setError(err); // Set the error if the API call fails
      setMessages((prev) => [...prev, { sender: "bot", text: "Error fetching response." }]);
      setIsLoading(false); // Set loading to false even if an error occurs
    }

    setInput(""); // Clear the input field after sending
  };

  return (
    <div>
      <h1>Chat Screen</h1>
      <div
        style={{
          border: "1px solid #ccc",
          padding: "10px",
          height: "300px",
          overflowY: "scroll",
          marginBottom: "10px",
        }}
      >
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              textAlign: message.sender === "user" ? "right" : "left",
              margin: "5px 0",
            }}
          >
            <strong>{message.sender === "user" ? "You" : "Bot"}:</strong> {message.text}
          </div>
        ))}
      </div>
      <div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          style={{ width: "80%", padding: "5px" }}
        />
        <button onClick={handleResponse} disabled={isLoading} style={{ padding: "5px 10px" }}>
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
      {error && <p style={{ color: "red" }}>Error: {error.message}</p>}
    </div>
  );
}

export default TestComponent;
