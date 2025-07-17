import React, { useContext, useEffect, useState, useRef } from 'react';
import { AiOutlineClear, AiOutlineConsoleSql, AiOutlineSend } from 'react-icons/ai'; // React Icons
import { FiSend } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { addChatId, addInputtext, addLastResultId, addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo1 from '../../assets/New Symbol.png';
import useChatScroll from '../Hooks/useChatScroll'; // Import the hook
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import '../Chatscreen/Chatscreen.css';
import userIcon from '../../assets/MarsAIX person icon.png'
import Navbar from '../Navbar/Navbar';
import Responseloader from '../Responseloader/Responseloader';
import { FrappeContext, useFrappeAuth, useFrappeCreateDoc, useFrappeGetDoc, useFrappeGetDocList, useFrappeUpdateDoc } from 'frappe-react-sdk'
import { addAIresponse, addSelectedoption, clearAiresponse } from '../../Redux/Store/Featuresilces/aiResponse';
import { addResult } from '../../Redux/Store/Featuresilces/validation'
import { replace, useLocation, useNavigate, useParams } from "react-router-dom";
import Details from '../Details/Details';
import { BiSidebar } from "react-icons/bi";
import { IoEllipseSharp, IoSearch } from "react-icons/io5";
import SideBar from '../SideBar/SideBar';
import { FaThumbsUp, FaThumbsDown, FaRegCopy, FaArrowsRotate } from "react-icons/fa6";
import { resetForm, setFormData, setIsOpen } from '../../Redux/Store/Featuresilces/detailform';
import { all } from 'axios';
import rehypeRaw from 'rehype-raw';
import { FaExternalLinkAlt } from 'react-icons/fa';
import { PiCopyBold } from 'react-icons/pi';
import { marked } from 'marked';


// const TypewriterMarkdown = ({ text, speed = 20 }) => {
//   const [displayed, setDisplayed] = useState('');
//   const [index, setIndex] = useState(0);
//   const html = marked.parse(text); // Convert markdown to HTML

//   useEffect(() => {
//     if (index < html.length) {
//       const timeout = setTimeout(() => {
//         setDisplayed(html.slice(0, index + 1));
//         setIndex(index + 1);
//       }, speed);
//       return () => clearTimeout(timeout);
//     }
//   }, [index, html, speed]);

//   return (
//     <div
//       className="prose prose-sm text-black" // Optional: Tailwind prose for better markdown look
//       dangerouslySetInnerHTML={{ __html: displayed }}
//     />
//   );
// };


function Chatscreen() {
  const [showDetails, setShowDetails] = useState(false);
  const { currentUser } = useFrappeAuth();
  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const chatId = useSelector((state) => state.chat.chatID);
  const addInput = useSelector((state)=>state.chat.addInput)
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
  const [hintsArray, setHintsArray] = useState([])
  const [tempButtons, setTempButtons] = useState(['Yes', 'No'])
  const navigate = useNavigate();
  let { sessionId } = useParams();
  const location = useLocation();
  //Create frappe context to call apis
  const { call } = useContext(FrappeContext)

  if (!sessionId && !currentUser) {
    sessionId = sessionStorage.getItem("guest_session_id")
  }

  useEffect(() => {
    if(addInput){
      setMessage(addInput)
    }
  }, [addInput])

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      sessionStorage.removeItem("guest_session_id");
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);
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

  const  handleConfirmation = async (label,response) => {
    console.log('response',response, 'label',label)
    setConfirmationPending(false);
    const confirmationMessages = {
      sender: 'user',
      // text: response === 'yes' ? 'Yes' : 'No',
      text: response, //confirmation required
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(confirmationMessages));

    if (label !== 'Refine Requirements' && !label?.startsWith('No') && label) {
      let currentSession = session

      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        // user: 'Yes',
        user: label,
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      }); 
      console.log(chatEntry,'this is the updated Doc chat history')
      if (!chatEntry.name) throw new Error("Failed to save user message");

      await handleConfirmationHints()
      mutate(); // Refresh UI to show user message
      setLoading(true);

      const res = await hanldeValidation();
      console.log("validation result from chatscreen", res);

      let pass = false, log = null;

      if (Array.isArray(res)) {
        pass = res[0];
        const second = res[1];
        log = typeof second === 'string' ? second : second?.log;
      } else if (res && typeof res === 'object') {
        pass = res.pass_to_analytics;
        log = res.log;
      }

      const aiResp = pass
        ? "Thank you for your response"
        : "We have your query, we will get back to you soon..";

      if (!pass && log) {
        // handleOpenHelp();
        setDisabled(false);
        await createDoc("AIX Diagnostics Hub", {
          type: "Validation Error",
          note: log,
          session: sessionId,
          chat_name: chatEntry.name || ''
        });
      }



      // STEP 3: Update that row with AI response
      await updateDoc("Chat history", chatEntry.name, {
        ai: aiResp
      });
      mutate(); // Show updated AI message  
      setLoading(false);
      // if (validationResult[0]) {
      dispatch(addSelectedoption(response))
      navigate(`/progress/${sessionId}`);
    // }
    } else {
      let currentSession = session;
      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        // user: "No",
        user: label,
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });

      if (!chatEntry.name) throw new Error("Failed to save user message");

      mutate(); // Refresh UI to show user message
      setLoading(true);

      // STEP 2: Get AI response
      const resp = await fetchAIResponse("NOFROMUSER", confirmationMessage, session);
      const aiResponse = resp.Ai_response;

      if (resp.Is_confirmation) {
        await updateDoc("Chat history", chatEntry.name, {
          ai: aiResponse || "Waiting For Confirmation"
        });

        if(resp.options && resp.options.length > 1) {
          console.log(resp.options, 'this is in confirmation');
          
          setTempButtons(resp.options)
        }
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
      setDisabled(false)
      try {
        await updateDoc("Session", sessionId, {
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
  const { data: userintension, mutate: intensionMutate } = useFrappeGetDocList('Session', {
    fields: ['user_intension', 'chat_json'],
    filters: [['name', '=', session]]
  })

  const chatHistory = data?.chat_history || [];
  console.log("data is", chatHistory);

  const handleSendbtn = async (msg) => {
    // await CheckToCallHints()
    if (!message.trim() && !msg.trim()) return;

    const userMessage = msg ? msg.trim() : message.trim();
    setMessage('');
    try {

      // Ensure session exists
      let currentSession = session;

      if (!currentSession) {
        const nowTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
        const sessionResp = await createDoc("Session", { time: nowTime, user: currentUser || '' });
        if (!sessionResp.name) throw new Error("Failed to create session");
        setSession(sessionResp.name);
        // dispatch(addChatId(sessionResp.name))
        currentSession = sessionResp.name;
        mutate();
        hintsMutate()
        intensionMutate();

        if (currentUser) {
          setTimeout(() => {
            navigate(`/chat/${currentSession}`, { replace: true })
          }, 200);
        } else {
          sessionStorage.setItem("guest_session_id", currentSession);
        }

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
      dispatch(addLastResultId(chatEntry.name))

      mutate(); // Refresh UI to show user message
      intensionMutate();
      hintsMutate()
      setLoading(true);
      setDisabled(true) //added now 

      // STEP 2: Get AI response
      const resp = await fetchAIResponse(userMessage, "", currentSession);
      console.log("ai response",resp)
      const aiResponse = resp.Ai_response;

      if (resp.Is_confirmation) {
        await updateDoc("Chat history", chatEntry.name, {
          ai: aiResponse || "Waiting For Confirmation"
        });

        if(resp.options && resp.options.length > 1) {
          console.log(resp.options, 'this is in handle')
          setTempButtons(resp.options)
        }
        mutate();
        intensionMutate();
        setLoading(false);
        setConfirmationMessage(aiResponse);
        dispatch(addAIresponse(resp))
        setConfirmationPending(true);
        setDisabled(true);
        processChat()
        return;
      }

      // STEP 3: Update that row with AI response
      await updateDoc("Chat history", chatEntry.name, {
        ai: aiResponse
      });

      mutate(); // Show updated AI message
      intensionMutate();
      setLoading(false);
      processChat()
      setDisabled(false) // added now
      // await processChat()
      


    } catch (error) {
      console.error("Error sending message:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchTitle = async () => {
      const intension = userintension?.[0]?.user_intension || '';
      if (intension) {
        const rawJson = userintension?.[0]?.chat_json;
        let title = "";
        try {
          const parsedArray = JSON.parse(rawJson);
          const title_to_update = getLastMeaningfulMessage(parsedArray);
          const isInvalidIntention = !intension || intension === "Valueless queries";

          title = isInvalidIntention
            ? "New Chat"
            : title_to_update
              ? await fetchHistoryTitle(title_to_update)
              : "New Chat";
        } catch (e) {
          console.error("Invalid JSON format", e);
        }
        if (title) {
          updateDoc('Session', session, {
            title: title
          }).then((updatedDoc) => {
            console.log('Title updated:✔️', updatedDoc);
          }).catch((err) => {
            console.error('Error updating doc:', err);
          });
        }
      }
    };

    if (session) {
      fetchTitle();
    }
  }, [userintension]);

  // The below will fetch the query hints
  const { data: queryHints, isLoading: hintsLoading } = useFrappeGetDocList('Session', {
    limit: 3,
    filters: [['user', '=', currentUser]],
    fields: ['query_hints', 'modified'],
    orderBy: { field: 'modified', order: 'desc' },
  })
  //The below will be used to get previous sessions chats and update in current session
  const { data: hints, isLoading: queriesLoading, mutate:hintsMutate } = useFrappeGetDocList("Session", {
    fields: ['chat_json', 'modified', 'name'],
    filters: [['user', '=', currentUser]],
    limit: 5,
    orderBy: { field: 'modified', order: 'desc' },
  });
   

const processChat = async () => {
  console.log('Got in the Process Chats.........')
  let latestData = await mutate()
  console.log(latestData, 'this are the chats ',session)
  if (latestData && latestData.chat_json && session) {
    const parsedChat = JSON.parse(latestData.chat_json);
  // const refinedData = addMethodCalledIfHuman(parsedChat);
  // console.log('This is our Refined Chat', parsedChat);
  checkAndUpdateTriggerPoints(parsedChat, session);

  }
};

const updateHints =async (from)=>{
  let latestHints = await hintsMutate()
  if(!latestHints) { return }
  let allData = latestHints.map(session => {
      const chatArray = JSON.parse(session.chat_json || '[]');
      // Step 1: Start from end, collect last 10 human messages
      const result = [];
      for (let i = chatArray.length - 1; i >= 0 && result.length < 10; i--) {
        const item = chatArray[i];
        if (item.type === "human" && item.content) {
          result.unshift(item.content);
        }
      }
      return result;
    }).reverse();
  let industry = userDoc ? userDoc?.bio : 'Cement'
  console.log('INPUT PASSED IN HINTS METHOD CALL', industry, allData)
  let responseHints = await fetchHints(allData,industry)
  
  if (session && responseHints) {
    try {
      const res = await updateDoc("Session", session, {
        query_hints: JSON.stringify(responseHints)
      });
      console.log(res, "Query Hints Updated for the Session .....✅");
      if(from==='confirmation'){
        const sessionDoc = await mutate();
        let chatArray = JSON.parse(sessionDoc.chat_json || '[]');
        // Reverse loop to find latest human message with method_called === 0 or missing
        for (let i = chatArray.length - 1; i >= 0; i--) {
          let msg = chatArray[i];
          if (msg.type === "human" && (msg.method_called === 0 || msg.method_called === undefined)) {
            chatArray[i].method_called = 1;
            break; // only update the latest one
          }
        }

        // Save updated chat_json
        await updateDoc("Session", session, {
          chat_json: JSON.stringify(chatArray)
        });
        return true
      }
      return true
    } catch (error) {
      console.error("❌ Error updating Session hints or method_called:", error);
      return false
    }   
   
  }
}

const handleConfirmationHints = async()=> {
  let hintsUpdated = await updateHints('confirmation')
  hintsUpdated ? console.log('QUERY HINTS UPDATED FOR COnFiRMATION....✅...') : console.log('Hints are Not Updated on Confirmation...❌')
}

  
function addMethodCalledIfHuman(data, methodValue = 0) {
  return data.map(item => {
    if (item.type === "human" && !item.hasOwnProperty("method_called")) {
      return { ...item, method_called: methodValue };
    }
    return item;
  });
}

const checkAndUpdateTriggerPoints = async(chatArray, sessionName)=> {
  let consecutiveZeros = 0;
  let zeroIndexes = [];

  for (let i = chatArray.length - 1; i >= 0; i--) {
    const msg = chatArray[i];

    if (msg.type === "human") {
      if (msg.method_called === 1) {
        // Stop entirely if any 1 is found
        break;
      }

      if (msg.method_called === 0) {
        consecutiveZeros++;
        zeroIndexes.unshift(i); // Keep index in original array order
      }

      if (consecutiveZeros === 3) {
        console.log("🔁 Triggering update due to 3 consecutive method_called: 0 at indexes:", zeroIndexes);

        const updatedIndex = zeroIndexes[2]; // The last (i.e., oldest) of the 3 zeroes

        chatArray[updatedIndex].method_called = 1;

        try {
          console.log('Calling the update function for Chat Count')
          const response = await updateHints('Chat');
          if (response) {
            const res = await updateDoc("Session", sessionName, {
              chat_json: JSON.stringify(chatArray),
            });
            console.log(res, "✅ Chat JSON Updated for Hints (from message counts)");
          }
        } catch (error) {
          console.error("❌ Failed to update chat_json in Session:", error);
        }

        break; // Stop after triggering update
      }
    }
  }
}



  useEffect(() => {
    //default hints
    let temp = ["I'm planning a 1 MTPA cement manufacturing unit in Bharuch ", "List approvals needed to start a food processing unit in Gujarat", "List all licenses required to start a textile unit in Vadodara", "What benefits does Gujarat offer for toy manufacturing startups?"]
    if (!hintsLoading) {
      let foundHints = null;
      // Go through each record and check for valid query_hints
      for (const record of queryHints) {
        try {
          const parsed = JSON.parse(record.query_hints);
          if (Array.isArray(parsed) && parsed.length > 0) {
            foundHints = parsed;
            break;
          }
        } catch (e) {
          // Not valid JSON or empty — move to next
          continue;
        }
      }
      // Set hintsArray in state
      setHintsArray(foundHints || temp);
    }
  }, [hintsLoading, queryHints])

  function getLastMeaningfulMessage(chatArray) {
    if (!Array.isArray(chatArray)) return null;

    const blacklist = ["yes", "no"];

    for (let i = chatArray.length - 1; i >= 0; i--) {
      const msg = chatArray[i];
      if (msg?.type === "human") {
        const content = msg.content?.trim().toLowerCase();
        if (content && !blacklist.includes(content)) {
          return msg.content; // ✅ return original content (not lowercased)
        }
      }
    }

    return null; // ❌ nothing meaningful found
  }

  const fetchHistoryTitle = async (intension) => {
    try {
      const result = await call.get("frontend_app.Management_Class.helpers.utility.generate_chat_title", {
        'user_query': intension,
      });
      console.log("Got the statement title", result);
      return result.message;
    } catch (err) {
      console.log("error occurred 😂", err);
      throw err;  // Rethrow the error if you want to catch it in the caller function.
    }
  }

  const fetchHints = async (queries,industry) => {
    try {
      const result = await call.get("frontend_app.Management_Class.helpers.utility.formatting_input_query_list", {
        'raw_nested_list': queries,
        'input_industry_name': industry
      });
      console.log("Got the Hint Statements", result);
      return result.message;
    } catch (err) {
      console.log("error occurred in Hint Statment Function😂", err);
    }
  }

  useEffect(() => {
    console.log("ascdsdd", currentUser, sessionId);

    if (!currentUser && !session) {
      const guestSessionId = sessionStorage.getItem("guest_session_id");
      if (guestSessionId) {
        setSession(guestSessionId);
      }
    }
  }, [currentUser, session]);

  useEffect(() => {
    if (messages.length >= 2) {
      storeLatestChatInChildTable();
    }
  }, [messages]);
  
  const chatRef = useRef(null)
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [chatHistory]);
  const [sideBar, setSideBar] = useState(true)

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
      console.log("user", currentUser);

      validateSession(sessionId);
    } else {
      setSession(null);
      setConfirmationMessage('');
      setConfirmationPending(false);
      setDisabled(false);
      setLoading(false)
    }
  }, [sessionId, currentUser]);

  const validateSession = async (sessionId) => {
    console.log("comegere with", sessionId, currentUser);

    if (sessionStorage.getItem("guest_session_id") && currentUser) {
      // Not logged in, redirect to /chat
      setSession(null);
      navigate("/chat", { replace: true });
      return;
    }
    if (!currentUser && sessionStorage.getItem("guest_session_id")) {
      return;
    }

    try {
      const res = await fetch(`/api/resource/Session/${sessionId}`);

      if (!res.ok) {
        // Invalid session ID
        setSession(null);
        navigate("/chat", { replace: true });
        return;
      }

      const sessionData = await res.json();
      const session = sessionData.data;
      console.log("session", session);
      console.log("current", currentUser);

      // Check if session belongs to the logged-in user
      if (currentUser) {
        if (session.user === currentUser) {
          setSession(session.name);
          navigate(`/chat/${session.name}`, { replace: true });
        } else {
          setSession(null);
          navigate("/chat", { replace: true });
        }
      }

    } catch (error) {
      console.error("Error validating session:", error);
      setSession(null);
      navigate("/chat", { replace: true });
    }
  };

  useEffect(() => {
    mutate(data)
  }, [])

  const handleOpenHelp = () => {
    dispatch(setFormData({ description: "I need help." }));
    dispatch(setIsOpen(true));
  };

  const textAreaRef = useRef(null)
  const handleHintClick = (hint) => {
    setMessage(hint);            // 👈 set the message from hint
    textAreaRef.current?.focus(); // 👈 move cursor to textarea
  };
  const handlerenderresult = (msg) => {
    window.open(`/frontend/result?session=${sessionId}&name=${msg.name}`, '_blank')
  }

  return (
    <div className='h-screen w-screen relative flex flex-row '>
      {currentUser && <SideBar setSideBar={setSideBar} sideBar={sideBar} />}
      <div className="h-screen flex flex-col items-center w-full transition-width duration-300 ease-in-out main-screen">
        <Navbar setSideBar={setSideBar} sideBar={sideBar} />
        <div className="flex-1 overflow-y-auto p-4 flex justify-center w-full chatscreen" ref={chatRef}>

          {chatHistory.length > 0 ? (
            <div className="chats flex flex-col w-[50%] mx-auto">
              {[...chatHistory]
                .sort((a, b) => a.idx - b.idx)
                .map((msg, index) => (
                  <div key={`chat-${msg.name || index}`}>
                    {msg.user?.trim() && (
                      <div className="flex gap-5 justify-start mb-3">
                        {renderUserAvatar("user")}
                        <div className="p-2 rounded-lg max-w-full break-words">
                          <ReactMarkdown rehypePlugins={[rehypeRaw]}>{msg.user}</ReactMarkdown>
                          <div
                            onClick={()=>{setMessage(msg.user), textAreaRef.current?.focus();}}
                            className=" flex flex-row items-center text-gray-700 w-fit bg-gray-200 gap-2 cursor-pointer text-xs p-2 transition-all duration-300  rounded-md hover:bg-gray-300"
                            title="Copy & set to input"
                          >
                            <FaArrowsRotate />
                          </div>
                        </div>
                      </div>
                    )}
                    {msg.ai?.trim() && (
                      <div className="flex gap-5 justify-start mb-3">
                        <img
                          src={botLogo1}
                          alt="AI"
                          className="h-8 w-8 relative rounded-full top-1"
                        />
                        <div className="p-2 rounded-lg max-w-full break-words">
                          <ReactMarkdown rehypePlugins={[rehypeRaw]}>{msg.ai}</ReactMarkdown>
                          {/* <TypewriterMarkdown text={msg.ai}/> */}
                          {msg.result && (
                            <button
                              title="View Result"
                              onClick={() => handlerenderresult(msg)}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 border border-blue-100 rounded-md transition-colors duration-150"
                            >
                              <FaExternalLinkAlt className="w-3 h-3" />
                              View Result
                            </button>
                          )}
                        </div>
                        
                      </div>
                    )}

                  </div>
                ))
              }

              {loading && session === sessionId && <Responseloader />}

              {confirmationPending && (
                <div className="m-0 p-2 rounded-lg w-full flex items-center justify-center">
                  {/* <p className='text-[#242f6a]'>{confirmationMessage}</p> */}
                  <div className="grid grid-cols-2 gap-4 min-w-[60%] max-w-[80%]">
                    {tempButtons.map((button,index)=> (
                    <button
                      key={index}
                      className={`${(button.label=== 'Refine Requirements' || button.label.startsWith('No')) ? 'bg-red-500' : 'bg-green-500'} text-white px-4 py-2 rounded-full text-xs cursor-pointer justify-center w-full items-center font-semibold flex flex-row gap-2`}
                      onClick={() => {handleConfirmation(button.label,button.value)}}
                    >
                      {(button.label=== 'Refine Requirements' || button.label.startsWith('No')) ? (<FaThumbsDown size={16} />) :(<FaThumbsUp size={16} />) }
                       {button.label}
                    </button>
                  ))}
                    {/* <button
                      className="bg-green-500 text-white px-4 py-2 rounded-md text-xs cursor-pointer font-semibold flex flex-row gap-2"
                      onClick={() => handleConfirmation('yes')}
                    >
                      <FaThumbsUp size={16} /> Yes
                    </button>
                    <button
                      className="bg-red-500 text-white px-4 py-2 rounded-md text-xs cursor-pointer font-semibold flex flex-row gap-2"
                      onClick={() => handleConfirmation('no')}
                    >
                      <FaThumbsDown size={16} />  No
                    </button> */}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-2 items-center justify-center h-full w-full">
              <p className="text-4xl text-[#242f6a]">What can I help with?</p>
              {hintsArray && hintsArray.length > 3 && (<><p className='text-md text-gray-700 italic font-semibold mb-4'>Not sure where to begin with? Try one of these</p>
                <div className='relative p-4 flex flex-col h-fit w-fit gap-4 items-center'>
                  <div className='relative p-2 text-xs bg-blue-200 text-black   rounded-xl w-fit h-fit whitespace-nowrap cursor-pointer font-semibold' onClick={() => { handleHintClick(hintsArray?.[0]) }}>{hintsArray?.[0]}</div>
                  <div className='relative flex flex-row gap-4 w-fit h-fit'>
                    <div className='relative p-2 text-xs text-black bg-blue-200  rounded-xl w-fit h-fit whitespace-nowrap cursor-pointer font-semibold' onClick={() => { handleHintClick(hintsArray?.[1]) }}>{hintsArray?.[1]}</div>
                    <div className='relative p-2 text-xs text-black bg-blue-200  rounded-xl w-fit h-fit whitespace-nowrap cursor-pointer font-semibold ' onClick={() => { handleHintClick(hintsArray?.[2]) }}>{hintsArray?.[2]}</div>
                  </div>
                  <div className='relative p-2 text-xs text-black  bg-blue-200  rounded-xl w-fit h-fit whitespace-nowrap cursor-pointer font-semibold' onClick={() => { handleHintClick(hintsArray?.[3]) }}>{hintsArray?.[3]}</div>
                </div> </>)}
            </div>
          )}
        </div>

        <div className="w-[50%] flex items-center justify-center mt-5 mb-4 space-x-2 border-2 border-[#41b655] rounded-xl p-2 bg-white shadow-lg">
          <div className="flex-grow">
            <textarea
              placeholder={messages.length > 0 ? "Message Mars AIX" : "Message Mars AIX"}
              className="w-full border-none outline-none bg-transparent text-black placeholder-[#242f6a] opacity-70 px-4 py-2 resize-none overflow-y-auto max-h-20 placeholder-opacity-75" // Adjusted classes
              value={message}
              maxLength={250}
              ref={textAreaRef}
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
            className={`cursor-pointer p-3 rounded-full flex items-center justify-center transition ${disabled ? "bg-gray-400 cursor-not-allowed" : "bg-[#41b655] hover:bg-[#217964]"
              }`}
            onClick={() => { if (!disabled) handleSendbtn() }}
          >
            <FiSend size={26} className="text-white" />
          </div>
        </div>

        <div className="alert-msg mb-5">
          <p className="text-xs text-[#242f6a]">
            MarsAIX is still learning and can make mistakes. Please contact us by filling the contact form{" "}
            <span
              className="text-blue-500 underline cursor-pointer"
              onClick={handleOpenHelp}
            >
              here
            </span>{" "}
            to confirm data correctness.
          </p>
        </div>
        {/* <Details /> */}
      </div>
    </div>
  );
}

export default Chatscreen;