import React, { useState, useContext } from "react";
import { FrappeContext } from "frappe-react-sdk";

function ChatScreen() {
  const { call } = useContext(FrappeContext);
  const [messages, setMessages] = useState([]); // Store chat messages
  const [userInput, setUserInput] = useState(""); // User input

  const handleSendMessage = async () => {
    if (!userInput.trim()) return; // Prevent sending empty messages

    const userMessage = { sender: "user", text: userInput };
    setMessages((prev) => [...prev, userMessage]); // Add user message to chat
    setUserInput("");

    try {
      
      const response = await call.get(
        "frontend_app.Management_Class.Ai_management.build.build_from_scratch",
        { input: userInput } // Pass user input to the call method
      );
      console.log("response is",response.message);
      
      const aiMessage = { sender: "ai", text: response.message['Ai_response'] || "No response" };
      setMessages((prev) => [...prev, aiMessage]); // Add AI response to chat
    } catch (err) {
      console.error("Error occurred:", err);
      const errorMessage = { sender: "ai", text: "Error processing your request." };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-screen bg-gray-100">
      <div className="flex flex-col w-[70%] h-[70%] bg-white shadow-lg rounded-lg overflow-hidden">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex my-2 ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`p-2 rounded-lg max-w-[50%] ${
                  message.sender === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-black"
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}
        </div>

        {/* Input and Send Button */}
        <div className="flex items-center p-4 border-t">
          <input
            type="text"
            className="flex-1 border rounded-lg px-4 py-2 mr-2 focus:outline-none"
            placeholder="Type your message..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          />
          <button
            onClick={handleSendMessage}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatScreen;