import React, { useEffect, useState } from 'react';
import { AiOutlineClear, AiOutlineSend } from 'react-icons/ai'; // React Icons
import { FiSend } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { addChatId, addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo1 from '../../assets/favicon.jpeg';
import { useAIResponse } from '../Hooks/useAIResponse';
import useChatScroll from '../Hooks/useChatScroll'; // Import the hook
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import '../Chatscreen/Chatscreen.css';
import userIcon from '../../assets/user.png'
import Navbar from '../Navbar/Navbar';
import Responseloader from '../Responseloader/Responseloader';
import { useFrappeCreateDoc } from 'frappe-react-sdk'
import ProgressScreen from '../ProgressScreen/ProgressScreen'

function Chatscreen() {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const chatId = useSelector((state) => state.chat.chatID);
  const { fetchAIResponse } = useAIResponse();
  const [loading, setLoading] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const { createDoc, isLoading, error } = useFrappeCreateDoc('');
  const [partialResponse, setPartialResponse] = useState('');
  const [confirmationPending, setConfirmationPending] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState('');
  const [isProgressVisible, setIsProgressVisible] = useState(false);

  const createSessionid = () => {
    const nowTime = new Date();
    const formattedTime = `${nowTime.getFullYear()}-${String(nowTime.getMonth() + 1).padStart(2, '0')}-${String(nowTime.getDate()).padStart(2, '0')} ${String(nowTime.getHours()).padStart(2, '0')}:${String(nowTime.getMinutes()).padStart(2, '0')}:${String(nowTime.getSeconds()).padStart(2, '0')}`;
    const doc = { time: formattedTime };
    createDoc("testing", doc).then((resp) => dispatch(addChatId(resp.name)));
  }

  const storeChatInChildTable = async () => {
    const messageLength = messages.length

    if (messageLength > 0 && messageLength % 4 === 0) {

      for (let i = 0; i <= 1; i++) {
        const ain = messageLength - (2 * i + 1);   // AI message index
        const uin = messageLength - (2 * i + 2);   // User message index

        const chatDoc = {
          user: messages[uin]['text'],
          ai: messages[ain]['text'],
          parent: chatId,
          parentfield: "chats",
          parenttype: "testing",
        };
        try {
          await createDoc("Chats", chatDoc);
        } catch (error) {
          console.error('Error saving to child table:', error);
        }
      }
    }
  };

  const handleSendbtn = async () => {
    if (message.trim()) {
      const newUserMessage = {
        sender: 'user',
        text: message,
        timestamp: new Date().toISOString(),
      };

      if (messages.length === 0 && !chatId) {
        createSessionid();
      }

      dispatch(addMessage(newUserMessage));
      setMessage('');
      setLoading(true)
      setDisabled(true)

      if (message.toLowerCase() === 'ok') {
        setConfirmationMessage('Are you sure you want to proceed?');
        setConfirmationPending(true);
        setLoading(false);
        setDisabled(true);
        return;
      }

      const aiResponse = await fetchAIResponse(message);

      let index = -1;
      setLoading(false)
      const typingInterval = setInterval(() => {
        setPartialResponse((prev) => prev + aiResponse.charAt(index));
        index++;
        if (index >= aiResponse.length) {
          clearInterval(typingInterval);
          const newAIMessage = {
            sender: 'ai',
            text: aiResponse,
            timestamp: new Date().toISOString(),
          };
          dispatch(addMessage(newAIMessage));
          setPartialResponse(''); // Clear partial response
          setDisabled(false);
        }
      }, 5);


    }
  };

  const handleConfirmation = (response) => {
    setConfirmationPending(false);
    const confirmationMessage = {
      sender: 'user',
      text: response === 'yes' ? 'Yes' : 'No',
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(confirmationMessage));

    const newAIMessage = {
      sender: 'ai',
      text: "Thank you for response",
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(newAIMessage));
    setDisabled(false);

    if(response == 'yes'){
      setTimeout(() => {
        setIsProgressVisible(true)
      }, 1000);
    }
  };

  useEffect(() => {
    storeChatInChildTable();
  }, [messages])

  const ref = useChatScroll(messages);

  return (
    <div className="h-screen flex flex-col items-center">
      <Navbar />
      <div className="flex-1 overflow-y-auto p-4 flex justify-center w-full chatscreen" ref={ref}>
        {messages.length > 0 ? (<div
          className="chats flex flex-col space-y-5 w-[50%] mx-auto"
        // ref={ref}
        >
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-5 justify-start`}
            >
              {msg.sender !== 'user' ? (
                <img
                  src={botLogo1}
                  alt=""
                  className="h-8 w-8 relative rounded-full"
                />
              ) : (
                <img
                  src={userIcon}
                  alt=""
                  className="h-8 w-8 relative rounded-full"
                />
              )}
              <div className="p-2 rounded-lg max-w-full break-words">
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))}
          {partialResponse && (
            <div className="flex gap-5 justify-start">
              <img
                src={botLogo1}
                alt=""
                className="h-8 w-8 relative rounded-full"
              />
              <div className="p-2 rounded-lg max-w-full">
                <ReactMarkdown>{partialResponse}</ReactMarkdown>
              </div>
            </div>
          )}
          {loading && (
            <Responseloader />
          )}
        </div>) : (<div className='flex justify-center items-center'><p className='text-5xl text-[#242f6a]'>What can I help with?</p></div>)}

      </div>

      {confirmationPending && (
        <div className="confirmation-box  p-4 rounded-lg w-[45%] flex flex-col items-center">
          <p className='text-[#242f6a]'>{confirmationMessage}</p>
          <div className="flex space-x-4 mt-2">
            <button
              className="bg-green-500 text-white px-4 py-2 rounded"
              onClick={() => handleConfirmation('yes')}
            >
              Yes
            </button>
            <button
              className="bg-red-500 text-white px-4 py-2 rounded"
              onClick={() => handleConfirmation('no')}
            >
              No
            </button>
          </div>
        </div>
      )}

      {isProgressVisible && (
        <div className="absolute top-0 left-0 right-0 bottom-0 bg-opacity-50 bg-black z-50 flex justify-center items-center">
            <ProgressScreen />
        </div>
      )}
      <div className="w-[50%] flex items-center justify-center mt-5 mb-4 space-x-2 border-2 border-[#19a282] rounded-full p-2 bg-white shadow-lg">
        <div className="flex-grow">
          <input
            type="text-area"
            placeholder="Message Mars 2.0"
            className="w-full border-none outline-none bg-transparent text-[#242f6a] placeholder-[#242f6a] opacity-70 px-4 py-2"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                if (!disabled) {
                  handleSendbtn();
                }
              }
            }}
          />
        </div>

        {message && (
          <div className="cursor-pointer p-2" onClick={() => setMessage('')}>
            <AiOutlineClear size={24} className="text-[#242f6a]" />
          </div>
        )}

        <div
          className={`cursor-pointer p-3 rounded-full transition ${disabled ? 'bg-gray-400 cursor-not-allowed' : 'bg-[#19a282] hover:bg-[#217964]'}`}
          onClick={!disabled ? handleSendbtn : null}
        >
          <FiSend size={28} className="text-white" />
        </div>
      </div>

      <div className="alert-msg mb-5">
        <p className='text-xs text-[#242f6a]'>Mars 2.0 can make mistakes. Check important info.</p>
      </div>
    </div>
  );
}

export default Chatscreen;