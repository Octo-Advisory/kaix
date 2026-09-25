import { useFrappeAuth, useFrappeGetDoc } from 'frappe-react-sdk';
import React, { useEffect, useState, useRef } from 'react'
import LogoIcon from '../../assets/New Symbol.png'
import LogoIcon2 from '../../assets/New MarsAIX White - Edited.png'
import { FaXmark } from 'react-icons/fa6';
import { HiOutlinePaperAirplane } from "react-icons/hi";

const FollowUpChat = ({ solutions, selectedProperty }) => {
  const { currentUser } = useFrappeAuth()
  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: 'Hello! How can I help you today?',
      timestamp: new Date(),
      isNew: false // Initial message doesn't need animation
    }
  ]);
  const [message, setMessage] = useState("");
  const [expanded, setExpanded] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const renderUserAvatar = (sender) => {
    const isCurrentUser = sender === 'user';

    if (sender !== 'user') {
      return (
        <img
          src={LogoIcon}
          alt="Bot"
          className="h-8 w-8 relative rounded-full flex-shrink-0"
        />
      );
    }

    if (isCurrentUser && currentUser) {
      if (userDoc?.user_image) {
        return (
          <img
            src={userDoc.user_image}
            alt="User"
            className="h-8 w-8 relative rounded-full object-cover flex-shrink-0"
          />
        );
      } else {
        return (
          <div className="h-8 w-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold flex-shrink-0">
            {currentUser?.charAt(0).toUpperCase()}
          </div>
        );
      }
    }
  };

  const handleSend = () => {
    if (!message.trim()) return;

    // Add user message with isNew flag
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: message.trim(),
      timestamp: new Date(),
      isNew: true
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage("");

    // Simulate AI response after a delay
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        sender: 'ai',
        text: "I'm processing your request. This is an automated response.",
        timestamp: new Date(),
        isNew: true
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Mark messages as not new after animation completes
  useEffect(() => {
    const newMessages = messages.filter(msg => msg.isNew);
    if (newMessages.length > 0) {
      const timer = setTimeout(() => {
        setMessages(prev => 
          prev.map(msg => ({ ...msg, isNew: false }))
        );
      }, 500); // Match this with CSS animation duration

      return () => clearTimeout(timer);
    }
  }, [messages]);

  const MessageBubble = ({ msg }) => {
    const isUser = msg.sender === 'user';

    return (
      <div 
        className={`relative flex gap-2 items-start w-full ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        } ${msg.isNew ? 'message-enter' : ''}`}
      >
        {renderUserAvatar(msg.sender)}
        <div 
          className={`relative w-fit min-w-[20%] max-w-[60%] text-black rounded-3xl p-3 text-justify text-sm ${
            isUser 
              ? 'bg-green-100 rounded-tr-none self-end text-right' 
              : 'bg-blue-100 rounded-tl-none self-start text-left'
          }`}
        >
          {msg.text}
          {/* <div className="text-xs text-gray-500 mt-1">
            {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div> */}
        </div>
      </div>
    );
  };

  return (<>
 {!expanded && (<button
  onClick={() => setExpanded(true)}
  className="group fixed bottom-6 left-1/2 -translate-x-1/2  flex items-center gap-2 z-[53]"
>
  <div className="w-14 h-14 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-lg group-hover:w-16 group-hover:h-16 transition-all duration-300">
    <img src={LogoIcon2} className='relative object-contain h-10 w-10 rounded-full' />
  </div>

  <span className="opacity-0 hidden group-hover:block group-hover:opacity-100 bg-white border px-4 py-2 rounded-xl shadow text-gray-700 text-sm transition-all duration-300">
    Have any queries?
  </span>
</button>)}

    <div className={`fixed inset-0 top-0 left-0  ${expanded ? 'backdrop-blur-sm z-[52]' : 'bg-transparent z-[-1]'} w-screen h-screen`}>
      {/* Floating Chat Button */}
      {/* <div 
        className='flex items-center justify-center w-14 h-14 bg-white fixed top-16 right-8 z-[51] cursor-pointer rounded-full border border-black shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105' 
        onClick={() => setExpanded(true)}
      >
        <img src={LogoIcon} className='h-10 w-10 object-contain relative' alt="Chat Icon" />
      </div> */}



      {/* <button
  onClick={() => setExpanded(true)}
  className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 z-[53]"
>
  <div className="w-14 h-14 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-lg">
    💬
  </div>

  <div className="bg-blue-600 text-white px-3 py-2 rounded-xl shadow-lg text-sm animate-bounce">
    Have any queries?
  </div>
</button> */}



      {/* Chat Window */}
      <div
        className={`fixed bottom-0 left-1/2 -translate-x-1/2 flex flex-col w-[60%] h-[570px] z-[52] shadow-2xl border-2 border-gray-300 bg-white rounded-t-3xl transform transition-all duration-500 ease-in-out ${
          expanded 
            ? "translate-y-0 opacity-100" 
            : "translate-y-full opacity-0"
        }`}
      >
        {/* Header */}
        <div className='relative bg-blue-600 text-white flex flex-row gap-4 items-center justify-between h-14 py-2 px-4 rounded-tl-3xl rounded-tr-3xl shadow-md'>
          <div className='relative flex flex-row items-center gap-4'>
            <img src={LogoIcon2} className='relative object-contain h-8 w-8' alt="Logo" />
            <h2 className='font-semibold'>How may I help you?</h2>
          </div>
          <span 
            className='relative h-7 w-7 rounded-full cursor-pointer bg-gray-100 bg-opacity-20 flex items-center justify-center hover:bg-opacity-30 transition-colors duration-200' 
            onClick={() => setExpanded(false)}
          > 
            <FaXmark /> 
          </span>
        </div>

        {/* Messages Container */}
        <div 
          ref={chatContainerRef}
          className='relative h-full w-full flex flex-col gap-4 overflow-y-auto px-4 py-4 hide-scrollbar flex-1'
        >
          {messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="flex items-center flex-row border-t-2 border-gray-200 gap-3 px-4 py-3 relative bg-white rounded-b-3xl">
          <input
            type="text"
            placeholder="Type a message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1 h-11 bg-transparent rounded-full border border-gray-300 py-2 px-4 placeholder-gray-400 text-black focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200"
            onClick={(e) => e.stopPropagation()}
          />
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleSend();
            }}
            disabled={!message.trim()}
            className={`flex items-center justify-center rounded-full cursor-pointer text-white p-2 h-11 w-11 text-sm font-medium transition-all duration-200 ${
              message.trim() 
                ? 'bg-blue-600 hover:bg-blue-700 hover:scale-105' 
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            <HiOutlinePaperAirplane className='text-lg transform rotate-45' />
          </button>
        </div>
      </div>

      {/* Add CSS animations */}
      <style jsx>{`
        .message-enter {
          animation: messageEnter 0.5s ease-out forwards;
        }
        
        @keyframes messageEnter {
          0% {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          100% {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
    </>
  )
}

export default FollowUpChat