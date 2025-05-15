import React, { useContext, useEffect, useState } from 'react';
import { AiOutlineClear, AiOutlineSend } from 'react-icons/ai'; // React Icons
import { FiSend } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { addChatId, addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo1 from '../../assets/MarsAIX icon.png';
import useChatScroll from '../Hooks/useChatScroll'; // Import the hook
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import '../Chatscreen/Chatscreen.css';
import userIcon from '../../assets/MarsAIX person icon.png'
import Navbar from '../Navbar/Navbar';
import Responseloader from '../Responseloader/Responseloader';
import { FrappeContext, useFrappeAuth, useFrappeCreateDoc, useFrappeGetDoc, useFrappeUpdateDoc } from 'frappe-react-sdk'
import { addAIresponse, clearAiresponse } from '../../Redux/Store/Featuresilces/aiResponse';
import { addResult } from '../../Redux/Store/Featuresilces/validation'
import { replace, useLocation, useNavigate, useParams } from "react-router-dom";
import Details from '../Details/Details';
import { BiSidebar } from "react-icons/bi";
import { IoSearch } from "react-icons/io5";
import SideBar from '../SideBar/SideBar';

function Chatscreen() {
  const [showDetails, setShowDetails] = useState(false);
  const { currentUser } = useFrappeAuth();
  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const chatId = useSelector((state) => state.chat.chatID);
  const [loading, setLoading] = useState(false);
  const [disabled, setDisabled] = useState(false);
  const { createDoc, isLoading, error } = useFrappeCreateDoc('');
  const [partialResponse, setPartialResponse] = useState('');
  const [confirmationPending, setConfirmationPending] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState('');
  const responseAi = useSelector((state) => state.ai.aiReponse)
  const [placeholder, setPlaceholder] = useState("");
  const [charIndex, setCharIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const location = useLocation();
  //Create frappe context to call apis
  const { call } = useContext(FrappeContext)
  console.log("sessoin id from url", sessionId);

  const suggestions = [
    "I want to build 1 million tonnes per annum steel factory....",
    "Show me incentives for cement factory in Vadodara....",
    "Can I get a list of approvals needed to set up a pharma unit in Bharuch....",
    "What is manpower availability in Anand....",
    "I am looking for suppliers for cement industry in Ahmedabad...."
  ]

  const createSessionid = () => {
    const nowTime = new Date();
    const formattedTime = `${nowTime.getFullYear()}-${String(nowTime.getMonth() + 1).padStart(2, '0')}-${String(nowTime.getDate()).padStart(2, '0')} ${String(nowTime.getHours()).padStart(2, '0')}:${String(nowTime.getMinutes()).padStart(2, '0')}:${String(nowTime.getSeconds()).padStart(2, '0')}`;
    const doc = { time: formattedTime };
    createDoc("Session", doc).then((resp) => dispatch(addChatId(resp.name)));
  }

  const fetchAIResponse = async (message, confirmationMessage, chatId) => {
    try {
      const result = await call.get("frontend_app.Management_Class.Ai_management.AI.ai_module_call", {
        input: message,
        confirmationMessage: confirmationMessage,
        chatId: chatId
      });
      console.log("message", result);
      return result.message;  // Return the result so that the calling function gets it.
    } catch (err) {
      console.log("error occurred 😂", err);
      throw err;  // Rethrow the error if you want to catch it in the caller function.
    }
  };


  const storeLatestChatInChildTable = async () => {
    const messageLength = messages.length;

    // Ensure there is at least one complete User-AI pair
    if (messageLength < 2) return;

    // Extract latest user-AI pair
    const ain = messageLength - 1; // AI message index
    const uin = messageLength - 2; // User message index

    // Ensure correct message type (assuming alternate sequence: User → AI)
    if (messages[uin]['sender'] !== 'user' || messages[ain]['sender'] !== 'ai') {
      return; // Skip storing if the order is incorrect
    }

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
  };

  const handleSendbtn1 = async () => {
    if (message.trim()) {
      const newUserMessage = {
        sender: 'user',
        text: message,
        timestamp: new Date().toISOString(),
      };

      dispatch(addMessage(newUserMessage));
      setMessage('');
      setLoading(true)
      setDisabled(true)

      const resp = await fetchAIResponse(message, "", chatId);
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
        dispatch(addAIresponse(resp))
        setConfirmationMessage(aiResponse);
        setConfirmationPending(true);
        setLoading(false);
        setDisabled(true);
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
      console.log("chat id", session);

      const respo = await fetch(`/api/resource/Session?fields=["user_intension"]&filters=[["name","=","${session}"]]&order_by=modified asc`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Check if the response is successful (status 200)
      if (!respo.ok) {
        throw new Error(`Request failed with status ${respo.status}`);
      }

      // Parse the JSON response correctly
      const userIntesion = await respo.json();
      console.log("userIntention", userIntesion);

      // Check if 'data' is present and contains expected data
      if (userIntesion && userIntesion.data && userIntesion.data.length > 0) {
        const user_intension = userIntesion.data[0].user_intension;

        // Call validation and dispatch result
        const result = await validationCall(responseAi, user_intension);
        dispatch(addResult(result));
        return result;
      } else {
        console.log("No data found for the given chatId");
      }
    } catch (error) {
      console.log("error is here", error);
    }
  };


  const { updateDoc } = useFrappeUpdateDoc()

  const handleConfirmation = async (response) => {
    setConfirmationPending(false);
    const confirmationMessages = {
      sender: 'user',
      text: response === 'yes' ? 'Yes' : 'No',
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(confirmationMessages));

    if (response == 'yes') {
      let currentSession = session
      
      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        user: 'Yes',
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });

      if (!chatEntry.name) throw new Error("Failed to save user message");

      mutate(); // Refresh UI to show user message
      setLoading(true);

      // STEP 2: Get AI response
      const validationResult = await hanldeValidation()
      console.log("validation result from chatscreen", validationResult);
      const aiResp = validationResult && validationResult.length > 0
        ? (validationResult[0] ? "Thank you for your response" : "We have your query, we will get back to you soon.")
        : "We have your query, we will get back to you soon.";

      // STEP 3: Update that row with AI response
      await updateDoc("Chat history", chatEntry.name, {
        ai: aiResp
      });

      mutate(); // Show updated AI message
      setLoading(false);
      // if (validationResult[0]) {
      navigate(`/progress/${sessionId}`);
    } else {
      let currentSession = session;
      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        user: "No",
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });

      if (!chatEntry.name) throw new Error("Failed to save user message");

      mutate(); // Refresh UI to show user message
      setLoading(true);
      
      // STEP 2: Get AI response
      const resp = await fetchAIResponse("NOFROMUSER", confirmationMessage,session);
      const aiResponse = resp.Ai_response;

      if (resp.Is_confirmation) {
        await updateDoc("Chat history", chatEntry.name, {
          ai: aiResponse || "Waiting For Confirmation"
        });

        mutate();
        setLoading(false);
        setConfirmationMessage(aiResponse);
        setConfirmationPending(true);
        setDisabled(true);
        return;
      }

      // STEP 3: Update that row with AI response
      await updateDoc("Chat history", chatEntry.name, {
        ai: aiResponse
      });

      mutate(); // Show updated AI message
      setLoading(false);

      try {
        await updateDoc("Session", chatId, {
          user_intension: "",
        });
        console.log("Updated Successfully");
      } catch (err) {
        console.error("Error Updating:", err);
      }
    }
  };
  const [session, setSession] = useState(null)
  const { data, mutate } = useFrappeGetDoc('Session', session || '');
  const chatHistory = data?.chat_history || [];
  console.log("data is", chatHistory);

  const handleSendbtn = async () => {
    if (!message.trim()) return;

    const userMessage = message.trim();
    setMessage('');

    try {
      // Ensure session exists
      let currentSession = session;
      if (!currentSession) {
        const nowTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
        const sessionResp = await createDoc("Session", { time: nowTime, user: currentUser || '' });

        if (!sessionResp.name) throw new Error("Failed to create session");
        setSession(sessionResp.name);
        currentSession = sessionResp.name;
        navigate(`/chat/${currentSession}`,{replace:true})
        mutate();
      }

      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        user: userMessage,
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });

      if (!chatEntry.name) throw new Error("Failed to save user message");

      mutate(); // Refresh UI to show user message
      setLoading(true);

      // STEP 2: Get AI response
      const resp = await fetchAIResponse(userMessage, "", currentSession);
      const aiResponse = resp.Ai_response;

      if (resp.Is_confirmation) {
        await updateDoc("Chat history", chatEntry.name, {
          ai: aiResponse || "Waiting For Confirmation"
        });

        mutate();
        setLoading(false);
        setConfirmationMessage(aiResponse);
        dispatch(addAIresponse(resp))
        setConfirmationPending(true);
        setDisabled(true);
        return;
      }

      // STEP 3: Update that row with AI response
      await updateDoc("Chat history", chatEntry.name, {
        ai: aiResponse
      });

      mutate(); // Show updated AI message
      setLoading(false);

    } catch (error) {
      console.error("Error sending message:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (messages.length >= 2) {
      storeLatestChatInChildTable();
    }
  }, [messages]);

  // useEffect(() => {
  //   if (messages.length === 0 && !chatId) {
  //     createSessionid();
  //     // return;    
  //   }
  // }, [])

  // useEffect(() => {
  //   const suggestion = suggestions[suggestionIndex];

  //   if (!isDeleting && charIndex < suggestion.length) {
  //     const timeout = setTimeout(() => {
  //       setPlaceholder(suggestion.substring(0, charIndex + 1));
  //       setCharIndex(charIndex + 1);
  //     }, 50);
  //     return () => clearTimeout(timeout);
  //   } else if (isDeleting && charIndex > 0) {
  //     const timeout = setTimeout(() => {
  //       setPlaceholder(suggestion.substring(0, charIndex - 1));
  //       setCharIndex(charIndex - 1);
  //     }, 30);
  //     return () => clearTimeout(timeout);
  //   } else if (!isDeleting && charIndex === suggestion.length) {
  //     setTimeout(() => setIsDeleting(true), 1000);
  //   } else if (isDeleting && charIndex === 0) {
  //     setIsDeleting(false);
  //     setSuggestionIndex((prev) => (prev + 1) % suggestions.length);
  //   }
  // }, [charIndex, suggestionIndex, isDeleting]);

  const ref = useChatScroll(messages);
  const [sideBar, setSideBar] = useState(false)

  const renderUserAvatar = (sender) => {
    const isCurrentUser = sender === 'user';

    if (sender !== 'user') {
      return (
        <img
          src={botLogo1}
          alt="Bot"
          className="h-8 w-8 relative rounded-full"
        />
      );
    }

    if (isCurrentUser && currentUser) {
      if (userDoc?.user_image) {
        return (
          <img
            src={userDoc.user_image}
            alt="User"
            className="h-8 w-8 relative rounded-full object-cover"
          />
        );
      } else {
        return (
          <div className="h-8 w-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
            {currentUser?.charAt(0).toUpperCase()}
          </div>
        );
      }
    }

    return (
      <img
        src={userIcon}
        alt="User"
        className="h-8 w-8 relative rounded-full"
      />
    );
  };

  useEffect(() => {
    // Validate session ID if provided in URL
    if (sessionId) {
      validateSession(sessionId);
    }else{
      setSession(null);
      setConfirmationMessage('');
      setConfirmationPending(false);
      setDisabled(false);
    }
  }, [sessionId, session]);

  const validateSession = async (sessionId) => {
    try {
      const res = await fetch(`/api/resource/Session/${sessionId}`);
      if (!res.ok) {
        setSession(null)
        navigate("/chat", { replace: true })
      }
      const sessionData = await res.json();
      console.log("result is ", sessionData.data.name);
      if (sessionData.data.name) {
        setSession(sessionData.data.name)
      }
      else {
        navigate("/chat", { replace: true })
      }
    } catch (error) {
      if (!error.message.includes("404")) {
      console.error("Unexpected error validating session:", error);
      }
      // setInvalidSession(true);
      setSession(null);
    }
  };


  return (
    <div className='h-screen w-screen relative flex flex-row '>
      {currentUser && <SideBar setSideBar={setSideBar} sideBar={sideBar} />}
      <div className="h-screen flex flex-col items-center w-full transition-width duration-300 ease-in-out main-screen">
        <Navbar setSideBar={setSideBar} sideBar={sideBar} />
        <div className="flex-1 overflow-y-auto p-4 flex justify-center w-full chatscreen" ref={ref}>
          {chatHistory.length > 0 ? (
            <div className="chats flex flex-col space-y-5 w-[50%] mx-auto">
              {[...chatHistory]
                .sort((a, b) => a.idx - b.idx)
                .map((msg, index) => (
                  <div key={`chat-${msg.name || index}`}>
                    {msg.user?.trim() && (
                      <div className="flex gap-5 justify-start mb-2">
                        {renderUserAvatar("user")}
                        <div className="p-2 rounded-lg max-w-full break-words">
                          <ReactMarkdown>{msg.user}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                    {msg.ai?.trim() && (
                      <div className="flex gap-5 justify-start">
                        <img
                          src={botLogo1}
                          alt="AI"
                          className="h-8 w-8 relative rounded-full"
                        />
                        <div className="p-2 rounded-lg max-w-full break-words">
                          <ReactMarkdown>{msg.ai}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              }

              {partialResponse && (
                <div className="flex gap-5 justify-start">
                  <img src={botLogo1} alt="AI" className="h-8 w-8 relative rounded-full" />
                  <div className="p-2 rounded-lg max-w-full">
                    <ReactMarkdown>{partialResponse}</ReactMarkdown>
                  </div>
                </div>
              )}

              {loading && <Responseloader />}
            </div>
          ) : (
            <div className="flex justify-center items-center">
              <p className="text-5xl text-[#242f6a]">What can I help with?</p>
            </div>
          )}
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

        <div className="w-[50%] flex items-center justify-center mt-5 mb-4 space-x-2 border-2 border-[#19a282] rounded-3xl p-2 bg-white shadow-lg">
          <div className="flex-grow">
            <textarea
              placeholder={messages.length > 0 ? "Message Mars 2.0" : "Message Mars 2.0"}
              className="w-full border-none outline-none bg-transparent text-black placeholder-[#242f6a] opacity-70 px-4 py-2 resize-none overflow-y-auto max-h-20 placeholder-opacity-75" // Adjusted classes
              value={message}
              maxLength={250}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (!disabled) {
                    handleSendbtn();
                  }
                }
              }}
              style={{ lineHeight: '1.5' }} //added line height to make it more readable.
            />
          </div>

          {message && (
            <div className="cursor-pointer p-2" onClick={() => setMessage("")}>
              <AiOutlineClear size={24} className="text-[#242f6a]" />
            </div>
          )}

          <div
            className={`cursor-pointer p-3 rounded-full transition ${disabled ? "bg-gray-400 cursor-not-allowed" : "bg-[#19a282] hover:bg-[#217964]"
              }`}
            onClick={!disabled ? handleSendbtn : null}
          >
            <FiSend size={28} className="text-white" />
          </div>
        </div>

        <div className="alert-msg mb-5">
          <p className="text-xs text-[#242f6a]">
            MarsInfraAIX is still learning and can make mistakes. Please contact us by filling the contact form{" "}
            <span
              className="text-blue-500 underline cursor-pointer"
              onClick={() => setShowDetails(true)}
            >
              here
            </span>{" "}
            to confirm data correctness.
          </p>
        </div>
        <Details isOpen={showDetails} setIsOpen={setShowDetails} />
      </div>
    </div>
  );
}

export default Chatscreen;