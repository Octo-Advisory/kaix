import React, { useState,useEffect } from 'react';
import { FiSend } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo from '../../assets/favicon.png'

function Searchbar() {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const [loading,setLoading] = useState(false)

  const fetchAIResponse = async (userMessage) => {
      const API_URL =
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyA0re42NbCbdFuTIsPnvreArTxRJvjkMUA";
  
      const requestBody = {
        contents: [
          {
            parts: [{ text: userMessage }],
          },
        ],
      };
  
      try {
        const response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });
  
        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }
  
        const data = await response.json();
        console.log("data is", data);
        console.log("res is", data.candidates);
  
        const aiMessage = data?.candidates[0]?.content?.parts[0].text.trim() || "I'm sorry, I couldn't process that.";
        return aiMessage;
      } catch (error) {
        console.error('Error fetching AI response:', error);
        return "Something went wrong. Please try again.";
      }
    };
  
    const handleSendbtn = async () => {
      if (message.trim()) {
        const newUserMessage = {
          sender: 'user',
          text: message,
          timestamp: new Date().toISOString(),
        };
        dispatch(addMessage(newUserMessage));
        setMessage('');
  
        setLoading(true)
  
        const aiResponse = await fetchAIResponse(message);
  
        const newAIMessage = {
          sender: 'ai',
          text: aiResponse,
          timestamp: new Date().toISOString(),
        };
        dispatch(addMessage(newAIMessage));
        setLoading(false)
      }
    }

  return (
    <div className="flex flex-col items-center justify-center space-y-6 w-full">
      {/* Title */}
      <div className="first-text">
        <h1 className="text-4xl font-semibold text-[#242f6a]">What can I help with?</h1>
      </div>

      {/* Input Box */}
      <div className="input-container flex items-center border-2 border-[#19a282] rounded-full p-3 gap-3 bg-white shadow-lg w-[70%]">
        <div className="input-box flex-grow w-full">
          <input
            type="text"
            placeholder="Message Mars 2.0"
            className="w-full border-none outline-none bg-transparent text-black placeholder-[#242f6a] opacity-60 px-4 py-2"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
        </div>
        <div className="send-btn cursor-pointer bg-[#19a282] hover:bg-[#217964] p-3 rounded-full transition" onClick={handleSendbtn}>
          <FiSend size={28} className="text-white" />
        </div>
      </div>
    </div>
  );
}

export default Searchbar;
