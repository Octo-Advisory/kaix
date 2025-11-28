import { useContext, useEffect, useState, useRef } from 'react';
import { AiOutlineClear } from 'react-icons/ai'; // React Icons
import { FiSend } from 'react-icons/fi';
import { useDispatch, useSelector } from 'react-redux';
import { addInputtext, addLastResultId, addMessage } from '../../Redux/Store/Featuresilces/chat';
import botLogo1 from '../../assets/New Symbol.png';
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import '../Chatscreen/Chatscreen.css';
import userIcon from '../../assets/MarsAIX person icon.png'
import { BsShop } from "react-icons/bs";
import { AiOutlineDollar } from "react-icons/ai";
import { FaUserGroup } from "react-icons/fa6";
import { RiBuilding2Line } from "react-icons/ri";
import newlogo from '../../assets/New MarsAIX blue h - Edited.png'
import Navbar from '../Navbar/Navbar';
import Responseloader from '../Responseloader/Responseloader';
import { FrappeContext, useFrappeAuth, useFrappeCreateDoc, useFrappeGetDoc, useFrappeGetDocList, useFrappeUpdateDoc } from 'frappe-react-sdk'
import { addAIresponse, addSelectedoption } from '../../Redux/Store/Featuresilces/aiResponse';
import { addResult } from '../../Redux/Store/Featuresilces/validation'
import { useNavigate, useParams, useLocation, useBlocker } from "react-router-dom";
import { HiOutlineClipboardDocumentCheck } from "react-icons/hi2";
import SideBar from '../SideBar/SideBar';
import { FaThumbsUp, FaThumbsDown, FaArrowsRotate } from "react-icons/fa6";
import { setFormData, setIsOpen } from '../../Redux/Store/Featuresilces/detailform';
import rehypeRaw from 'rehype-raw';
import remarkBreaks from 'remark-breaks';
import remarkGfm from 'remark-gfm';
import { FaExternalLinkAlt } from 'react-icons/fa';
import { BuildingIcon, BuildingLineIcon, ClearIcon, ClipboardCheckIcon, DollarIcon, SendIcon, ShopIcon, UserGroupIcon } from '../../Icons/icon';
import usePersistedToggle from '../../PersistedState/useToggleState';
import NavigationPrompt from './NavigationPrompt'

function Chatscreen() {
  const { currentUser } = useFrappeAuth();
  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');
  const { data: marsConf} = useFrappeGetDoc('Mars Configurations', 'Mars Configurations');
  
  
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const chatId = useSelector((state) => state.chat.chatID);
  let addInput = useSelector((state) => state.chat.addInput)
  
  const feasibilityId = useSelector((state) => state.feasibility.feasibility_id)
  // const [loading, setLoading] = useState(null);
  // const [loadingSession, setLoadingSession] = useState(null);
  const [disabled, setDisabled] = useState(false);
  const { createDoc, isLoading, error } = useFrappeCreateDoc('');
  const [confirmationPending, setConfirmationPending] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState('');
  const responseAi = useSelector((state) => state.ai.aiReponse)
  const [hintsArray, setHintsArray] = useState([])
  const [tempButtons, setTempButtons] = useState(['Yes', 'No'])
  const navigate = useNavigate();
  let { sessionId } = useParams();
  const { call } = useContext(FrappeContext)
  const location = useLocation();
  const [chatLoading, setChatLoading] = useState(true)
  const [loadingStates, setLoadingStates] = useState(new Map());

  const { from, sendMsg, messageToSet,passedIntension } = location.state || {};

useEffect(() => {
  if (sendMsg) {
    // do something only once when arriving
    console.log('Running once for new session');
    if(passedIntension) {
      handleSendbtn(messageToSet,passedIntension)
    }
    else {
      handleSendbtn(messageToSet, '')
    }
    // Optionally clear it
    navigate(location.pathname, { replace: true, state: {} });
  }
}, [sendMsg]);



  const createDiagnostic = (errType, logMsg,chatIdd,sessions)=> {
      let log = ` ${logMsg}`
      try {
        createDoc("AIX Diagnostics Hub", {
        type: errType,
        note: log,
        chat_name: chatIdd,
        session: sessions
        });
      } catch(e) {

      }
  }

  const noResultMessages = [
  "Hmm… I couldn’t find anything matching your search. Could you try a different keyword or check similar options?",
  "Looks like we don’t have that in our list yet — but new items are added all the time! Try another search to see more results.",
  "No exact match found, but let’s explore some other options that might work for you!",
  "I couldn’t find a match for that right now. Want me to help you look for something similar?"
];

  const noResultMsg = noResultMessages[Math.floor(Math.random() * noResultMessages.length)];


  const setSessionLoading = (sessionId, isLoading) => {
    setLoadingStates(prev => {
      const newMap = new Map(prev);
      if (isLoading) {
        newMap.set(sessionId, true);
      } else {
        newMap.delete(sessionId);
      }
      return newMap;
    });
  };

  const isSessionLoading = (sessionId) => {
    return loadingStates.get(sessionId) || false;
  };

  // const blocker = useBlocker(confirmationPending);
  // useEffect(() => {
  //   if (blocker.state === "blocked") {
  //     if (window.confirm("Confirmation is pending. You can’t leave this chat — if you leave, the confirmation will be lost.")) {
  //       blocker.proceed(); // allow navigation
  //     } else {
  //       blocker.reset(); // cancel navigation
  //     }
  //   }
  // }, [blocker]);

  useEffect(() => {
    const beforeUnloadHandler = (e) => {
      if (confirmationPending) {
        e.preventDefault();
        e.returnValue = "Confirmation is pending. If you leave, it will be lost.";
      }
    };
    window.addEventListener("beforeunload", beforeUnloadHandler);
    return () => window.removeEventListener("beforeunload", beforeUnloadHandler);
  }, [confirmationPending]);

  const [newMessageSent, setNewMessageSent] = useState(false);

  if (!sessionId && !currentUser) {
    sessionId = sessionStorage.getItem("guest_session_id")
  }

  useEffect(() => {

    const handleNewChat = async(msg)=> {
      let tempMsg= msg==='The msg we dont want' ? 'The overriden msg to send' : msg

      if(!feasibilityId) return
      if(!addInput) return
      console.log('Making New Chat...')

      setSessionLoading('new-chat', true);
      const nowTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
      const sessionResp = await createDoc("Session", { time: nowTime, user: currentUser || '', });
      if (!sessionResp.name) throw new Error("Failed to create session");
      setSession(sessionResp.name);
      // dispatch(addChatId(sessionResp.name))

      mutate();
      setSessionLoading('new-chat', false);
      setSessionLoading(sessionResp.name, true);
      hintsMutate()
      intensionMutate();

      if (currentUser) {
        setTimeout(() => {
          navigate(`/chat/${sessionResp.name}`, { 
            replace: true,
            state: {
              from: "new-chat-redirect",
              sendMsg: true,
              messageToSet: tempMsg,
            }, 
          })
        }, 200);
      } else {
        sessionStorage.setItem("guest_session_id", sessionResp.name);
      }

    }
    // First: send message & create session
    console.log(addInput,feasibilityId, 'This is the addInput Value 1st level ',sessionId)
    if (addInput) {
      // console.log(addInput,feasibilityId, 'This is the addInput Value 2nd level ')
      // console.log('-----',addInput , 'ADDD INPUTT ------');
      handleNewChat(addInput)
      // handleSendbtn(addInput); // this will internally set the sessionId
    }
  }, [addInput]);


  useEffect(() => {

    
    // Second: once sessionId is available, add to child table if not already present
    const handleFeasibilityChatLink = async () => {
      console.log("In Chat Link", feasibilityId, addInput, sessionId);

      if (!addInput) return;
      if (!feasibilityId || !sessionId) return;

      try {
        const response = await call.get("frappe.client.get", {
          doctype: "Feasibility Report",
          name: feasibilityId,
        });

        const chats = response?.message?.chats || [];

        const alreadyExists = chats.some(chat => chat.session === sessionId);
        // console.log("raw feasibility id", feasibilityId, alreadyExists);

        if (!alreadyExists) {
          console.log('we are here now!!!! to remove the addInput')
          await createDoc("Linked Chats", {
            session: sessionId,
            parent: feasibilityId,
            parenttype: "Feasibility Report",
            parentfield: "chats",
          });
          // dispatch(addInputtext(null))
        }
      } catch (err) {
          createDiagnostic("Others", `Something went wrong while getting feasibility reports in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
        // console.error("Error adding to child table:", err);
      }
    };

    const handleFeasibilitySessionLink = async () => {
      if (!addInput) return;
      if (!feasibilityId || !sessionId) return;
      console.log('Feasibility Link....')
      // console.log("Feasibility ID : ", feasibilityId);
      // console.log("ADD INPUT: ", addInput);
      // console.log("session ID : ", sessionId , data);
      let tempData= await mutate()
      // console.log(tempData, 'Its the Temp Data');
      if(!tempData.feasibility_id || tempData.feasibility_id === '') {
        updateDoc('Session',sessionId, {
          feasibility_id: feasibilityId
        }).then((updatedDoc) => {
          // console.log(updatedDoc, 'Okay Doc Updated')
        }).catch((err) => {
              // console.error('Error updating doc for storing feasibility_id:', err);
            });
      }
    }
    // handleNewChat();
    handleFeasibilityChatLink();
    handleFeasibilitySessionLink();
  }, [sessionId,feasibilityId, addInput]);

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      sessionStorage.removeItem("guest_session_id");
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);
  // console.log("sessoin id from url", sessionId);


  const fetchAIResponse = async (message, confirmationMessage, chatId) => {
    console.log(chatId,'okay')
    try {
      const result = await call.get("frontend_app.Management_Class.Ai_management.AI.ai_module_call", {
        input: message,
        confirmationMessage: confirmationMessage,
        chatId: chatId
      });
      // console.log("message", result);
      return result.message;  // Return the result so that the calling function gets it.
    } catch (err) {
        createDiagnostic("Others", `Something went wrong while calling the AI module in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
      // console.log("error occurred ", err);
      // throw err;  // Rethrow the error if you want to catch it in the caller function.
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
      createDiagnostic("Others", `Something went wrong while creating a chat history record for ${JSON.stringify(chatDoc)} in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
    
    }
  };

  const validationCall = async (aiResponse, user_intension) => {
    try {
      const result = await call.get("frontend_app.Validations.validate.validation", {
        aiResponse: aiResponse,
        user_intension: user_intension
      });
      // console.log("validation result", result);
      return result.message
    } catch (error) {
      createDiagnostic("Others", `Something went wrong while calling validation for ${JSON.stringify(aiResponse)} ${JSON.stringify(user_intension)} in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
    
    }
  }

  const hanldeValidation = async () => {
    try {
      // console.log("chat id", session);

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

      // Check if 'data' is present and contains expected data
      if (userIntesion && userIntesion.data && userIntesion.data.length > 0) {
        const user_intension = userIntesion.data[0].user_intension;

        // Call validation and dispatch result
        const result = await validationCall([responseAi?.at(-1)], user_intension);
        dispatch(addResult(result));
        return result;
      } else {
        createDiagnostic("Others", `Something went wrong cause No data found for given userIntension ${JSON.stringify(userIntesion)} in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
        // console.log("No data found for the given chatId");
      }
    } catch (error) {
      createDiagnostic("Others", `Something went wrong while calling Sesion Record in ChatScreen : ${JSON.stringify(error)}`,chatId,sessionId)
      // console.log("error is here", error);
    }
  };

  const { updateDoc } = useFrappeUpdateDoc()
  const clearProgressAndIntention = async (chatId) => {
    try {
      await updateDoc('Session', chatId, {
        progress: [],
      });
    } catch (error) {
      createDiagnostic("Others", `Something went wrong while Updating the Session record and clearing Intention for ${JSON.stringify(chatId)} in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
      // console.error("Error updating session:", error);
    }
  };

  const handleConfirmation = async (label, response) => {
    console.log('response', response, 'label', label)
    setConfirmationPending(false);
    const confirmationMessages = {
      sender: 'user',
      text: response, //confirmation required
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(confirmationMessages));

    if (label !== 'Refine Requirements' && !label?.startsWith('No') && label && label!== 'Yes, start new chat') {
      let currentSession = session

      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        user: label,
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });
      if (!chatEntry.name) throw new Error("Failed to save user message");

      await handleConfirmationHints()
      mutate(); // Refresh UI to show user message
      // setLoadingSession(sessionId)
      // setLoading(true);
      setSessionLoading(session, true);

      const res = await hanldeValidation();
      // console.log("validation result from chatscreen", res);

      let pass = false, log = null;

      if (Array.isArray(res)) {
        pass = res[0];
        const second = res[1];
        log = typeof second === 'string' ? second : second?.log;
      } else if (res && typeof res === 'object') {
        pass = res.pass_to_analytics;
        log = res.log;
      }

      if(marsConf.validation_check == 0){
        pass = true
      }

      const aiResp = pass
        ? "Thank you for your response; please feel free to reach out with any further industry-related queries."
        : "We have received your query and will get back to you shortly; meanwhile, feel free to share any other questions related to industry approvals, incentives, or vendors.";

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
      // setLoading(false);
      // setLoadingSession(null)
      setSessionLoading(session,false)
      if (pass) {
        dispatch(addSelectedoption(response))
        await clearProgressAndIntention(sessionId)
        navigate(`/progress/${sessionId}`);
      }
    }

    else if (label === "Yes, start new chat") {
       let currentSession = session

      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        user: label,
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });
      if (!chatEntry.name) throw new Error("Failed to save user message");

      await handleConfirmationHints()
      mutate(); // Refresh UI to show user message
      // setLoadingSession(sessionId)
      // setLoading(true);
      setSessionLoading(session, true);
 
      // setLoading(false);
      // setLoadingSession(null)
      setSessionLoading(session,false)
      dispatch(addSelectedoption(response))

      setSessionLoading('new-chat', true);
      const nowTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
      const sessionResp = await createDoc("Session", { time: nowTime, user: currentUser || '', });
      if (!sessionResp.name) throw new Error("Failed to create session");
      setSession(sessionResp.name);
      // dispatch(addChatId(sessionResp.name))

      mutate();
      setSessionLoading('new-chat', false);
      setSessionLoading(sessionResp.name, true);
      hintsMutate()
      intensionMutate();  
      if (currentUser) {
        console.log(response, label, 'Okay we want to check this')
        setTimeout(() => {
          navigate(`/chat/${sessionResp.name}`, { 
            replace: true,
            state: {
              from: "new-chat-redirect",
              sendMsg: true,
              messageToSet: AiResponses.UserQuery,
            }, 
          })
        }, 200);
        // handleSendbtn(label)
      } else {
        sessionStorage.setItem("guest_session_id", sessionResp.name);
      }
    }

    else {
      let currentSession = session;
      // STEP 1: Save user's message with idx
      const idx = chatHistory.length + 1;
      const chatEntry = await createDoc("Chat history", {
        user: label,
        parent: currentSession,
        parentfield: "chat_history",
        parenttype: "Session",
        idx,
      });

      if (!chatEntry.name) throw new Error("Failed to save user message");

      mutate(); // Refresh UI to show user message
      // setLoadingSession(sessionId)
      // setLoading(true);
      setSessionLoading(session, true);

      // STEP 2: Get AI response
      const resp = await fetchAIResponse("NOFROMUSER", confirmationMessage, session);
      
      const aiResponse = resp.Ai_response;

      if (resp.Is_confirmation) {
        await updateDoc("Chat history", chatEntry.name, {
          ai: aiResponse || "Waiting For Confirmation"
        });

        if (resp.options && resp.options.length > 1) {

          setTempButtons(resp.options)
        }
        mutate();
        // setLoading(false);
        // setLoadingSession(null)
        setSessionLoading(session, false);
        setSessionLoading(currentSession, false);
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
      // setLoading(false);
      // setLoadingSession(null)
      setSessionLoading(session, false);
      setDisabled(false)
      console.log('Cleainrg intensiio',sessionId)
      try {
        await updateDoc("Session", sessionId, {
          user_intension: "",
        }).then(()=>{
          console.log('Clearing the intension');
          
        });
      } catch (err) {
        createDiagnostic("Others", `Something went wrong while Updating Session Record for session and clearing user_intension ${JSON.stringify(sessionId)} in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
        // console.error("Error Updating:", err);
      }
    }
  };
  const [session, setSession] = useState(null)
  const { data, mutate } = useFrappeGetDoc('Session', session || '');
  const { data: userintension, mutate: intensionMutate } = useFrappeGetDocList('Session', {
    fields: ['user_intension', 'chat_json', 'title', 'update_title'],
    filters: [['name', '=', session]]
  })

  const [AiResponses, setAiResponses] = useState()
  const chatHistory = data?.chat_history || [];
  // console.log("data is", chatHistory, AiResponses);



  const handleSendbtn = async (msg) => {

    if (!message.trim() && !msg.trim()) return;

    const userMessage = msg ? msg.trim() : message.trim();
    
    setMessage('');
    try {

      // Ensure session exists
      let currentSession = session;

      if (!currentSession) {
        setSessionLoading('new-chat', true);
        const nowTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
        const sessionResp = await createDoc("Session", { time: nowTime, user: currentUser || '', });
        if (!sessionResp.name) throw new Error("Failed to create session");
        setSession(sessionResp.name);
        // dispatch(addChatId(sessionResp.name))
        currentSession = sessionResp.name;

        mutate();
        setSessionLoading('new-chat', false);
        setSessionLoading(currentSession, true);
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
      // setLoadingSession(sessionId)
      // setLoading(true);
      setSessionLoading(session, true);
      setDisabled(true) //added now 

      // STEP 2: Get AI response
      const resp = await fetchAIResponse(userMessage, "", currentSession);
      setAiResponses(resp)
      // console.log("ai response", resp)
      const aiMsg = resp.Ai_response === "Not Available in List" ? noResultMsg : resp.Ai_response 
      const aiResponse = aiMsg;
      
      if (resp.Is_confirmation) {
        await updateDoc("Chat history", chatEntry.name, {
          ai: aiResponse || "Waiting For Confirmation"
        });

        if (resp.options && resp.options.length > 1) {
          // console.log(resp.options, 'this is in handle')
          setTempButtons(resp.options)
        }
        mutate();
        intensionMutate();
        // setLoading(false);
        // setLoadingSession(null)
        // setSessionLoading(session, false);
        setSessionLoading(currentSession || session, false);
        setConfirmationMessage(aiResponse);
        dispatch(addAIresponse(resp))
        setConfirmationPending(true);
        setDisabled(true);
        processChat()
        return;
      }
      if (resp.Trigger_Lead_Generation) {
        let log = `Extracted Data: ${JSON.stringify(resp['State'])} Validation Data : ${JSON.stringify(resp['Validation Data'])}, ${resp.Ai_response} `
        await createDoc("AIX Diagnostics Hub", {
            type: "Data Missing",
            note: log,
            session: sessionId,
            chat_name: chatEntry.name || '' 
        });
      }
      // STEP 3: Update that row with AI response
      await updateDoc("Chat history", chatEntry.name, {
        ai: aiResponse
      });

      mutate(); // Show updated AI message
      intensionMutate();
      // setLoading(false);
      // setLoadingSession(null)
 
      
      setSessionLoading(currentSession, false);
      setSessionLoading(session, false);
      processChat()
      setDisabled(false) // added now

    } catch (error) {
      createDiagnostic("Others", `Something went wrong while sending the message in ChatScreen : ${JSON.stringify(error)}`,chatId,sessionId)
      // console.error("Error sending message:", error);
      // setLoading(false);
      // setLoadingSession(null)
      setSessionLoading(session, false);
    }
  };

  useEffect(() => {

    const fetchTitle = async () => {
      const intension = userintension?.[0]?.user_intension || '';
      const chat_title = userintension?.[0]?.title || '';
      const update_title_check = userintension?.[0]?.update_title || 0;
      const rawJson = userintension?.[0]?.chat_json;
      const fallBackIntensions = ["Valueless queries", "Other industry-related queries", "Negatively Intended Query"];
      if (intension) {
        const isTitleUpdated = update_title_check === 1 ? true : false
        const isFallBack = fallBackIntensions.includes(intension)
        let title = "";
        try {
          const parsedArray = JSON.parse(rawJson);
          const title_to_update = getLastMeaningfulMessage(parsedArray);
          const shouldCallMethod = (isTitleUpdated) ? false :
            (!chat_title || chat_title === 'New Chat') ? true
              : (isFallBack && (!chat_title || chat_title === 'New Chat')) ? true
                : (!isFallBack && !isTitleUpdated) ? true : false

          title = (shouldCallMethod && title_to_update)
            ? await fetchHistoryTitle(title_to_update)
            : null;
        } catch (e) {
          createDiagnostic("Others", `Something went wrong while fetching history Title in ChatScreen : ${JSON.stringify(e)}`,chatId,sessionId)
          // console.error("Invalid JSON format", e);
        }
        if (title) {
          let updateData = { title: title }; // Always update title
          if (!isFallBack) {
            updateData.update_title = 1;
          }
          updateDoc('Session', session, updateData)
            .then((updatedDoc) => {
              setNewMessageSent(true)
            }).catch((err) => {
              // console.error('Error updating doc:', err);
            });
        }
      }
    };

    if (session) {
      fetchTitle();
    }
  }, [userintension, session]);


  // The below will fetch the query hints
  const { data: queryHints, isLoading: hintsLoading } = useFrappeGetDocList('Session', {
    limit: 3,
    filters: [['user', '=', currentUser]],
    fields: ['query_hints', 'modified'],
    orderBy: { field: 'modified', order: 'desc' },
  })
  //The below will be used to get previous sessions chats and update in current session
  const { data: hints, isLoading: queriesLoading, mutate: hintsMutate } = useFrappeGetDocList("Session", {
    fields: ['chat_json', 'modified', 'name'],
    filters: [['user', '=', currentUser]],
    limit: 5,
    orderBy: { field: 'modified', order: 'desc' },
  });


  const processChat = async () => {
    let latestData = await mutate()
    if (latestData && latestData.chat_json && session) {
      const parsedChat = JSON.parse(latestData.chat_json);
      checkAndUpdateTriggerPoints(parsedChat, session);
    }
  };

  const updateHints = async (from) => {
    let latestHints = await hintsMutate()
    if (!latestHints) { return }
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
    let industry = userDoc?.bio ? userDoc.bio : 'Cement'
  
    let responseHints = await fetchHints(allData, industry)
    if (session && responseHints) {
      try {
        const res = await updateDoc("Session", session, {
          query_hints: JSON.stringify(responseHints)
        });
      
        if (from === 'confirmation') {
          const sessionDoc = await mutate();
          let chatArray = JSON.parse(sessionDoc.chat_json || '[]');
          // Reverse loop to find latest human message with method_called === 0 or missing
          for (let i = chatArray.length - 1; i >= 0; i--) {
            let msg = chatArray[i];
            if (msg.type === "human" && (msg.method_called === 0 || msg.method_called === undefined)) {
              chatArray[i].method_called = 1;
              break;
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
        createDiagnostic("Others", `Something went wrong while Updating Session hints  in ChatScreen : ${JSON.stringify(error)}`,chatId,sessionId)
        // console.error("❌ Error updating Session hints or method_called:", error);
        return false
      }

    }
  }

  const handleConfirmationHints = async () => {
    await updateHints('confirmation')
  }

  const checkAndUpdateTriggerPoints = async (chatArray, sessionName) => {
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

          const updatedIndex = zeroIndexes[2]; // The last (i.e., oldest) of the 3 zeroes

          chatArray[updatedIndex].method_called = 1;

          try {
            const response = await updateHints('Chat');
            if (response) {
              const res = await updateDoc("Session", sessionName, {
                chat_json: JSON.stringify(chatArray),
              });
            }
          } catch (error) {
            createDiagnostic("Others", `Something went wrong while updating chat_json in SEssion ${JSON.stringify(sessionName)}  in ChatScreen : ${JSON.stringify(error)}`,chatId,sessionId)
            // console.error("❌ Failed to update chat_json in Session:", error);
          }

          break; // Stop after triggering update
        }
      }
    }
  }

  const { data: defaultHintData } = useFrappeGetDoc("UI Configuration", "ChatScreen")
      const configurations = defaultHintData?.query_hints || [];
      const uiHintsConfig = configurations.map((row) => ({
        title: row.title,
        subtitle: row.subtitle,
        hint: row.hint,
        type: row.type
      }));

  useEffect(() => {
    //default hints
    if (!hintsLoading) {
      let foundHints = null;

      // Go through each record and check for valid query_hints
      for (const record of queryHints) {
        try {
          const parsed = JSON.parse(record.query_hints);
       
          if (Array.isArray(parsed) && parsed.length > 0) {
            let allHaveQuery = parsed.every(item => item.hasOwnProperty('query'));
            let tryingHints = allHaveQuery ? parsed : uiHintsConfig
            
            foundHints = tryingHints;
            break;
          }
        } catch (e) {
          // Not valid JSON or empty — move to next
          continue;
        }
      }
      // Set hintsArray in state
   
      setHintsArray(foundHints || uiHintsConfig);
    }
  }, [hintsLoading, queryHints,defaultHintData])

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
      return result.message;
    } catch (err) {
      createDiagnostic("Others", `Something went wrong while calling generate_chat_title for History Title  in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
      // console.log("error occurred ", err);
      // throw err;  // Rethrow the error if you want to catch it in the caller function.
    }
  }

  const fetchHints = async (queries, industry) => {
    try {
      const result = await call.get("frontend_app.Management_Class.helpers.utility.normalize_queries_with_known_cities", {
        'query_list': queries,
        'input_industry_name': industry
      });
      // const result = await call.get("frontend_app.Management_Class.helpers.utility.generate_query_hints", {
      //   'query_list': queries,
      //   'input_industry_name': industry
      // });
      let hints = result.message || [];

      let newHints = hints.map((hintObj, index) => {
        let matchedHint = iconHints.find(iconHint => iconHint.type === hintObj.module) || {};

        return {
          ...matchedHint,
          hint: hintObj.query,
          ...hintObj
        };
      });
      return newHints;
    } catch (err) {
      createDiagnostic("Others", `Something went wrong while calling generate_query_hints query: ${JSON.stringify(queries)} industry: ${JSON.stringify(industry)} in ChatScreen : ${JSON.stringify(err)}`,chatId,sessionId)
      // console.log("error occurred in Hint Statment Function", err);
    }
  }

  useEffect(() => {

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
  const [sideBar, setSideBar] = usePersistedToggle('aix-nav-state', 'true')

  const renderUserAvatar = (sender) => {
    const isCurrentUser = sender === 'user';

    if (sender !== 'user') {
      return (
        <img
          src={botLogo1}
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

    return (
      <img
        src={userIcon}
        alt="User"
        className="h-8 w-8 relative rounded-full flex-shrink-0"
      />
    );
  };

  useEffect(() => {
    // Validate session ID if provided in URL
    if (sessionId) {
      validateSession(sessionId);
    } else {
      setSession(null);
      setConfirmationMessage('');
      setConfirmationPending(false);
      setDisabled(false);
      // setLoading(false)
      // setLoadingSession(null)
      setSessionLoading(session, false);
    }
  }, [sessionId, currentUser]);

  const validateSession = async (sessionId) => {
   

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
      // console.log("session", session);
      // console.log("current", currentUser);

      // Check if session belongs to the logged-in user
      if (currentUser) {
        if (session.user === currentUser && !session.soft_delete) {
          setSession(session.name);
          navigate(`/chat/${session.name}`, { replace: true });
        } else {
          setSession(null);
          navigate("/chat", { replace: true });
        }
      }

    } catch (error) {
      createDiagnostic("Others", `Something went wrong while validating the session in ChatScreen : ${JSON.stringify(error)}`,chatId,sessionId)

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



  const iconHints = [
    {
      title: "Government Grants",
      subtitle: "Explore available subsidies",
      hint: "Tell me the government incentives for cement industry in Gujarat",
      type: "Incentives"
    },
    {
      title: "Land Options",
      subtitle: "Check availability by location",
      hint: "What land availability exists for cement industry in Vadodara?",
      type: "Build from Scratch"
    },
    {
      title: "Labor Insights",
      subtitle: "Analyze workforce distribution",
      hint: "What are the labor options for cement industry in Bharuch?",
      type: "Employment"
    },
    {
      title: "Vendor Network",
      subtitle: "Find reliable suppliers",
      hint: "What are the vendor options for cement industry in Ahmedabad?",
      type: "Vendor Search"
    },
    {
      title: "Vendor Insights",
      subtitle: "Trusted supplier options",
      hint: "What are the vendor options for cement industry in Surat?",
      type: "Vendor Search"
    },
    {
      title: "Approval Status",
      subtitle: "Licenses & permits overview",
      hint: "What approvals are required for cement plant setup in Vadodara?",
      type: "Approval"
    }
  ];

  useEffect(() => {
    if (sessionId) {
      setChatLoading(true)
      if (chatHistory.length > 0) {
        setChatLoading(false)
      }
    }
  }, [chatHistory, sessionId])

  return (
    <div className='h-screen w-screen relative flex flex-row '>
      {currentUser && <SideBar setSideBar={setSideBar} sideBar={sideBar} newMessageSent={newMessageSent} setNewMessageSent={setNewMessageSent} />}
      <div className="h-screen flex flex-col items-center w-full transition-width duration-300 ease-in-out main-screen">
        <Navbar />
        <div className="flex-1 overflow-y-auto p-4 flex justify-center w-full chatscreen" ref={chatRef}>

          {chatHistory.length > 0 ? (
            <div className="chats flex flex-col w-[50%] mx-auto">
              {[...chatHistory]
                .sort((a, b) => a.idx - b.idx)
                .map((msg, index, arr) => {
                  const isLast = index === arr.length - 1;
                  const isCurrentAi = isLast && msg.ai === AiResponses?.Ai_response;
                  return (
                    <div key={`chat-${msg.name || index}`}>
                      {msg.user?.trim() && (
                        <div className="flex gap-5 justify-start mb-3">
                          {renderUserAvatar("user")}
                          <div className="p-2 rounded-lg max-w-full break-words">
                            <ReactMarkdown rehypePlugins={[rehypeRaw]}>{msg.user}</ReactMarkdown>
                            <div
                              onClick={() => { setMessage(msg.user), textAreaRef.current?.focus(); }}
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
                            {isCurrentAi ? (
                              // <Typewriter text={msg.ai} />
                            <ReactMarkdown
      // IMPORTANT: GFM enables tables
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        h2: ({node, ...props}) => (
          <h2 className="text-base font-bold text-black mt-3 mb-2 pb-1" {...props} />
        ),
        h3: ({node, ...props}) => (
          <h3 className="text-base font-semibold text-black mt-3 mb-2" {...props} />
        ),
        p: ({node, ...props}) => (
          <p className="text-black mb-2 text-md" {...props} />
        ),
        strong: ({node, ...props}) => (
          <strong className="font-semibold text-base text-black" {...props} />
        ),
        ul: ({node, ...props}) => (
          <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />
        ),
        ol: ({node, ...props}) => (
          <ol className="list-decimal pl-5 mb-4 space-y-1" {...props} />
        ),
        li: ({node, ...props}) => (
          <li className="text-black text-base mb-1" {...props} />
        ),

        // ---- Table styling (Tailwind) ----
        table: ({node, ...props}) => (
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full border border-gray-300/70 rounded-lg text-sm">
              {props.children}
            </table>
          </div>
        ),
        thead: ({node, ...props}) => (
          <thead className="bg-gray-50">{props.children}</thead>
        ),
        tbody: ({node, ...props}) => <tbody className="divide-y">{props.children}</tbody>,
        tr: ({node, ...props}) => <tr className="odd:bg-white even:bg-gray-50/50">{props.children}</tr>,
        th: ({node, ...props}) => (
          <th
            className="px-3 py-2 text-left font-semibold text-gray-800 border-b border-gray-300"
            {...props}
          />
        ),
        td: ({node, ...props}) => (
          <td
            className="px-3 py-2 align-top text-gray-900 border-b border-gray-200"
            {...props}
          />
        ),
      }}
    >
      {msg.ai}
    </ReactMarkdown>
                            ) : (
                             <ReactMarkdown
      // IMPORTANT: GFM enables tables
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        h2: ({node, ...props}) => (
          <h2 className="text-base font-bold text-black mt-3 mb-2 pb-1" {...props} />
        ),
        h3: ({node, ...props}) => (
          <h3 className="text-base font-semibold text-black mt-3 mb-2" {...props} />
        ),
        p: ({node, ...props}) => (
          <p className="text-black mb-2 text-md" {...props} />
        ),
        strong: ({node, ...props}) => (
          <strong className="font-semibold text-base text-black" {...props} />
        ),
        ul: ({node, ...props}) => (
          <ul className="list-disc pl-5 mb-4 space-y-1" {...props} />
        ),
        ol: ({node, ...props}) => (
          <ol className="list-decimal pl-5 mb-4 space-y-1" {...props} />
        ),
        li: ({node, ...props}) => (
          <li className="text-black text-base mb-1" {...props} />
        ),

        // ---- Table styling (Tailwind) ----
        table: ({node, ...props}) => (
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full border border-gray-300/70 rounded-lg text-sm">
              {props.children}
            </table>
          </div>
        ),
        thead: ({node, ...props}) => (
          <thead className="bg-gray-50">{props.children}</thead>
        ),
        tbody: ({node, ...props}) => <tbody className="divide-y">{props.children}</tbody>,
        tr: ({node, ...props}) => <tr className="odd:bg-white even:bg-gray-50/50">{props.children}</tr>,
        th: ({node, ...props}) => (
          <th
            className="px-3 py-2 text-left font-semibold text-gray-800 border-b border-gray-300"
            {...props}
          />
        ),
        td: ({node, ...props}) => (
          <td
            className="px-3 py-2 align-top text-gray-900 border-b border-gray-200"
            {...props}
          />
        ),
      }}
    >
      {msg.ai}
    </ReactMarkdown>
                            )}
                            {/* <ReactMarkdown rehypePlugins={[rehypeRaw]}>{msg.ai}</ReactMarkdown> */}
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
                  )
                })
              }

              {/* {loading && loadingSession === sessionId && <Responseloader />} */}
              {(isSessionLoading(sessionId) || !sessionId && isSessionLoading('new-chat')) && <Responseloader />}

              {confirmationPending && (
                <div className="m-0 p-2 rounded-lg w-full flex items-center justify-center">
                  <div className="grid grid-cols-2 gap-4 min-w-[60%] max-w-[80%]">
                    {tempButtons.map((button, index) => (
                      <button
                        key={index}
                        className={`${(button.label === 'Refine Requirements' || button.label.startsWith('No')) ? 'bg-red-400' : 'bg-green-400'} text-white px-4 py-2 rounded-full text-xs cursor-pointer justify-center w-full items-center font-semibold flex flex-row gap-2`}
                        onClick={() => { handleConfirmation(button.label, button.value) }}
                      >
                        {(button.label === 'Refine Requirements' || button.label.startsWith('No')) ? (<FaThumbsDown size={16} />) : (<FaThumbsUp size={16} />)}
                        {button.label}
                      </button>
                    ))}

                  </div>
                </div>
              )}
            </div>
          ) : (chatLoading && sessionId && currentUser) ? <div className="chats flex flex-col w-[50%] mx-auto"><Responseloader /></div> : (
            <div className="flex flex-col gap-2 items-center justify-center h-full w-full">
              <div className='relative text-4xl flex flex-row gap-3 items-center'>
                <p className=" text-[#242f6a]">Welcome to</p>
                <img src={newlogo} className='relative object-contain h-[45px] w-[150px]' />

              </div>
              {hintsArray && hintsArray.length > 3 && (<>
                <p className='text-sm text-gray-600 italic tracking-wide font-normal mb-1 text-center'>I'm your AI assistant for industrial intelligence and data-driven decision making.<br></br> I can help with manufacturing, supply chain, site selection, and much more.</p>
                <p className='text-sm text-gray-600 italic tracking-wide font-normal mb-4 text-center'>What industrial challenge can I help you tackle today?</p>

                <div className='relative p-4 grid grid-cols-3 h-fit w-fit gap-4 items-center'>
                  {hintsArray.map((hints, index) => (
                    <div key={index} onClick={() => { handleHintClick(hints.hint) }} className='relative transition-all duration-300 ease-in-out cursor-pointer bg-white  border-gray-200 hover:border-green-700 hover:-translate-y-0.5 h-full min-w-[150px] border rounded-md max-w-[260px] flex flex-col gap-1 p-3 '>
                      <div className='relative flex flex-row items-center p-1 h-fit gap-2'>
                        <div className='bg-gradient-to-br rounded-md from-[#2C53A3] to-[#70A1D9] relative h-9 w-9 flex items-center justify-center p-2'>
                          {hints.type === "Approval" ? (<ClipboardCheckIcon strokeWidth={2} className='text-white text-lg'  size={22} />) : hints.type === "Vendor Search" ? (<ShopIcon strokeWidth={0.5} className='text-white text-lg' size={22} />) : hints.type === "Incentives" ? (<DollarIcon className='text-white text-lg ' size={24} />) : hints.type === "Employment" ? (<UserGroupIcon className='text-white text-lg' size={22} />) : hints.type === "Build From Scratch" ? (<BuildingLineIcon className='text-white text-lg' size={22} strokeWidth={2}/>) : (<BuildingIcon className='text-white' size={22} />)}
                        </div>
                        <div className='relative flex flex-col items-start'>
                          <p className='text-md font-medium text-black capitalize tracking-wide select-none'>{hints.title}</p>
                          <p className='text-[10px] font-normal text-[#0B2152] capitalize tracking-wide select-none'>{hints.subtitle}</p>
                        </div>
                      </div>

                      <p className='text-xs ml-1 font-normal text-gray-600 tracking-wide select-none leading-relaxed'>{hints.hint}</p>
                    </div>
                  ))}
                </div>
              </>)}
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
              style={{ lineHeight: '1.5' }}
            />
          </div>

          {message && (
            <div className="cursor-pointer p-2" onClick={() => setMessage("")}>
              <ClearIcon size={24} className="text-[#242f6a]" />
            </div>
          )}

          <div
            className={`cursor-pointer p-3 rounded-full flex items-center justify-center transition ${disabled ? "bg-gray-400 cursor-not-allowed" : "bg-[#41b655] hover:bg-[#217964]"
              }`}
            onClick={() => { if (!disabled) handleSendbtn() }}
          >
            <SendIcon size={26} className="text-white" />
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
      </div>
      <NavigationPrompt
        when={confirmationPending}
        message="Confirmation is pending. You can’t leave this chat — if you leave, the confirmation will be lost."
        onConfirm={() => setConfirmationPending(false)}
      />
    </div>
  );
}

export default Chatscreen;