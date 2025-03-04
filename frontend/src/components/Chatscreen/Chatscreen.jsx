import React, { useContext, useEffect, useState } from 'react';
import { AiOutlineClear, AiOutlineSend } from 'react-icons/ai'; // React Icons
import { FiSend } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { addChatId, addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo1 from '../../assets/favicon.jpeg';
import useChatScroll from '../Hooks/useChatScroll'; // Import the hook
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import '../Chatscreen/Chatscreen.css';
import userIcon from '../../assets/user.png'
import Navbar from '../Navbar/Navbar';
import Responseloader from '../Responseloader/Responseloader';
import { FrappeContext, useFrappeCreateDoc } from 'frappe-react-sdk'
import ProgressScreen from '../ProgressScreen/ProgressScreen'
import { addAIresponse, clearAiresponse } from '../../Redux/Store/Featuresilces/aiResponse';
import { addResult } from '../../Redux/Store/Featuresilces/validation'
import { useTypewriter } from "react-simple-typewriter";
import { useNavigate } from "react-router-dom";
import Details from '../Details/Details';

function Chatscreen() {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const chatId = useSelector((state) => state.chat.chatID);
  const [loading, setLoading] = useState(false);
  const [dataloading, setDataloading] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const [showerror, setShowerror] = useState(null);
  const { createDoc, isLoading, error } = useFrappeCreateDoc('');
  const [partialResponse, setPartialResponse] = useState('');
  const [confirmationPending, setConfirmationPending] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState('');
  const [isProgressVisible, setIsProgressVisible] = useState(false);
  const responseAi = useSelector((state) => state.ai.aiReponse)
  const [placeholder, setPlaceholder] = useState("");
  const [charIndex, setCharIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const navigate = useNavigate();
  //Create frappe context to call apis
  const { call } = useContext(FrappeContext)

  const suggestions = [
    "I want to build industry....",
    "I want to see incetives for cement factory....",
    "I want to get approvals to setup industry....",
    "I want to see employement....",
    "I want suppliers for industry...."
  ]

  const createSessionid = () => {
    const nowTime = new Date();
    const formattedTime = `${nowTime.getFullYear()}-${String(nowTime.getMonth() + 1).padStart(2, '0')}-${String(nowTime.getDate()).padStart(2, '0')} ${String(nowTime.getHours()).padStart(2, '0')}:${String(nowTime.getMinutes()).padStart(2, '0')}:${String(nowTime.getSeconds()).padStart(2, '0')}`;
    const doc = { time: formattedTime };
    createDoc("Session", doc).then((resp) => dispatch(addChatId(resp.name)));
  }

  const fetchAIResponse = async (message, chatId) => {
    try {
      const result = await call.get("frontend_app.Management_Class.Ai_management.AI.ai_module_call", {
        input: message,
        chatId: chatId
      });
      console.log("message", result);

      return result.message;  // Return the result so that the calling function gets it.
    } catch (err) {
      console.log("error occurred 😂", err);
      throw err;  // Rethrow the error if you want to catch it in the caller function.
    }
  };


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
          parentfield: "chat_history",
          parenttype: "Session",
        };
        try {
          await createDoc("Chat history", chatDoc);
        } catch (error) {
          console.error('Error saving to child table:', error);
        }
      }
    }
  };

  const handleSendbtn = async () => {
    if (message.trim()) {
      // if (messages.length === 0 && !chatId) {
      //   createSessionid();
      //   return;
      // }
      const newUserMessage = {
        sender: 'user',
        text: message,
        timestamp: new Date().toISOString(),
      };

      dispatch(addMessage(newUserMessage));
      setMessage('');
      setLoading(true)
      // setDisabled(true)

      const resp = await fetchAIResponse(message, chatId);
      console.log("ai response is", resp);
      const aiResponse = resp.Ai_response
      console.log("reponse is", aiResponse);

      if (resp.Is_confirmation) {
        setLoading(false)
        const aiResponse1 = "Waiting For Confirmation"
        const newAIMessage = {
          sender: 'ai',
          text: aiResponse1,
          timestamp: new Date().toISOString(),
        };
        dispatch(addMessage(newAIMessage));
        // let index = -1;

        // const typingInterval = setInterval(() => {
        //   setPartialResponse((prev) => prev + aiResponse1.charAt(index));
        //   index++;
        //   if (index >= aiResponse.length) {
        //     clearInterval(typingInterval);
        //     const newAIMessage = {
        //       sender: 'ai',
        //       text: aiResponse1,
        //       timestamp: new Date().toISOString(),
        //     };
        //     dispatch(addMessage(newAIMessage));
        //     setPartialResponse(''); // Clear partial response
        //     setDisabled(false);
        //   }
        // }, 5);
        dispatch(addAIresponse(resp))
        setConfirmationMessage(aiResponse);
        setConfirmationPending(true);
        setLoading(false);
        // setDisabled(true);
        return;
      }

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

  const validationCall = async (aiResponse, user_intension) => {
    try {
      const result = await call.get("frontend_app.Validations.validate.validation", {
        aiResponse: aiResponse,
        user_intension: user_intension
      });
      console.log("validation result", result);
      return result.message
    } catch (error) {
      console.log("error 🤣", error);

    }
  }

  const hanldeValidation = async () => {
    try {
      const respo = await fetch(`api/resource/Session?fields=["user_intension"]&filters=[["name","=","${chatId}"]]&order_by=modified asc`, {
        method: 'GET',
        headers: {
          // 'Authorization': 'token your_api_token', // Replace with actual token
          'Content-Type': 'application/json'
        }
      });

      const userIntesion = await respo.json()
      const user_intension = userIntesion['data'][0]['user_intension']

      const result = await validationCall(responseAi, user_intension)
      dispatch(addResult(result))
      return result

    } catch (error) {
      console.log("error is", error);

    }
  }

  const handleConfirmation = async (response) => {
    setConfirmationPending(false);
    const confirmationMessage = {
      sender: 'user',
      text: response === 'yes' ? 'Yes' : 'No',
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(confirmationMessage));

    // const newAIMessage = {
    //   sender: 'ai',
    //   text: "Thank you for response",
    //   timestamp: new Date().toISOString(),
    // };
    // dispatch(addMessage(newAIMessage));
    // setDisabled(false);

    if (response == 'yes') {
      const validationResult = await hanldeValidation()
      console.log("validation result from chatscreen", validationResult);
      // console.log("validation result1", validationResult[0]);
      const aiResp = validationResult && validationResult.length > 0
    ? (validationResult[0] ? "Thank you for your response" : "We have your query, we will get back to you soon.")
    : "We have your query, we will get back to you soon.";
        const newAIMessage = {
          sender: 'ai',
          text: aiResp,
          timestamp: new Date().toISOString(),
        };
      dispatch(addMessage(newAIMessage));
      // if (validationResult[0]) {
        setIsProgressVisible(true);
        navigate("/progress");
        // setTimeout(() => {
        //   setIsProgressVisible(true);
        // }, 0); // Ensure setTimeout executes properly
      // }
    } else {
      const newAIMessage = {
        sender: 'ai',
        text: "Alright! If you ever feel like chatting or need help, just let me know.",
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(newAIMessage));
      dispatch(clearAiresponse())
    }
  };

  useEffect(() => {
    storeChatInChildTable();
  }, [messages])

  useEffect(() => {
    if (messages.length === 0 && !chatId) {
      createSessionid();
      // return;    
    }
  }, [])

  useEffect(() => {
    const suggestion = suggestions[suggestionIndex];

    if (!isDeleting && charIndex < suggestion.length) {
      const timeout = setTimeout(() => {
        setPlaceholder(suggestion.substring(0, charIndex + 1));
        setCharIndex(charIndex + 1);
      }, 50);
      return () => clearTimeout(timeout);
    } else if (isDeleting && charIndex > 0) {
      const timeout = setTimeout(() => {
        setPlaceholder(suggestion.substring(0, charIndex - 1));
        setCharIndex(charIndex - 1);
      }, 30);
      return () => clearTimeout(timeout);
    } else if (!isDeleting && charIndex === suggestion.length) {
      setTimeout(() => setIsDeleting(true), 1000);
    } else if (isDeleting && charIndex === 0) {
      setIsDeleting(false);
      setSuggestionIndex((prev) => (prev + 1) % suggestions.length);
    }
  }, [charIndex, suggestionIndex, isDeleting]);

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

      {/* {isProgressVisible && (
        <div className="absolute top-0 left-0 right-0 bottom-0 bg-opacity-50 bg-black z-50 flex justify-center items-center">
          <ProgressScreen />
        </div>
      )} */}
      <div className="w-[50%] flex items-center justify-center mt-5 mb-4 space-x-2 border-2 border-[#19a282] rounded-full p-2 bg-white shadow-lg">
        <div className="flex-grow">
        <textarea
          placeholder={messages.length > 0 ? "Message Mars 2.0" : placeholder}
          className="w-full border-none outline-none bg-transparent text-black placeholder-[#242f6a] opacity-70 px-4 h-6 resize-none overflow-y-auto placeholder-opacity-75"
          value={message}
          maxLength={250}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
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
        <Details/>
    </div>
  );
}

export default Chatscreen;