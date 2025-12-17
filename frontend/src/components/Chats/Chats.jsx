import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { FiSend } from 'react-icons/fi';
import { AiOutlineClear } from 'react-icons/ai';
import { addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo from '../../assets/favicon.png'
import botLogo1 from '../../assets/favicon.jpeg'

function Chats() {
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
    <div className="w-full flex flex-col h-full items-center">
      {/* Chat Messages */}
      <div className="w-full h-full overflow-y-auto p-1 flex flex-col space-y-4 flex-grow">
        <div className="chats flex flex-col space-y-3">
          {/* Render all messages */}
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-2 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender != 'user' && <img src={botLogo1} alt="" className='h-8 w-8 relative rounded-full' />}
              <div
                className={`p-2 rounded-lg ${msg.sender === 'user' ? 'max-w-[70%] bg-[#19a282] text-white' : 'bg-gray-200 text-[#242f6a]'}`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-2 justify-start">
              <img src={botLogo1} alt="" className='h-8 w-8 relative rounded-full' />
              <div className="p-2 rounded-lg bg-gray-200 text-[#242f6a]">
                <span>Loading...</span> {/* You can replace this with a spinner or animation */}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Section */}
      <div className="w-[90%] flex items-center justify-center space-x-2 border-2 border-[#19a282] rounded-full p-2 bg-white shadow-lg">
        {/* Input Field */}
        <div className="flex-grow">
          <input
            type="text"
            placeholder="Message Mars 2.0"
            className="w-full border-none outline-none bg-transparent text-[#242f6a] placeholder-[#242f6a] opacity-70 px-4 py-2"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
        </div>

        {/* Clear Button */}
        {message && (
          <div className="cursor-pointer p-2" onClick={() => setMessage('')}>
            <AiOutlineClear size={24} className="text-[#242f6a]" />
          </div>
        )}

        {/* Send Button */}
        <div
          className="cursor-pointer bg-[#19a282] hover:bg-[#217964] p-3 rounded-full transition"
          onClick={handleSendbtn}
        >
          <FiSend size={28} className="text-white" />
        </div>
      </div>
    </div>
  );
}

export default Chats;
