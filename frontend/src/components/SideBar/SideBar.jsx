import React, { useState, useEffect, useContext, useCallback, useRef } from 'react';
import { IoSearch, IoSettingsSharp } from "react-icons/io5";
import { FaChevronDown, FaChevronUp, FaRegEdit } from "react-icons/fa";
import { BsThreeDotsVertical } from "react-icons/bs";
import { TbLayoutSidebarRightCollapse, TbLayoutSidebarLeftCollapse } from "react-icons/tb";
import { FaRegLightbulb } from 'react-icons/fa';
import newsymbol from '../../assets/New MarsAIX White - Edited.png'
import Settings from "../Settings/Settings";
import { useFrappeAuth, useFrappeGetDocList, FrappeContext, useFrappeEventListener, useFrappeUpdateDoc } from 'frappe-react-sdk';
import { replace, useNavigate, useParams } from 'react-router-dom';
import { use } from 'react';
import './SideBar.css'
import SearchContainer from './SearchContainer';
import FeasibilityStudy from '../Feasibilitystudy/FeasibilityStudy';
import { HiOutlineDocumentReport } from "react-icons/hi";
import { HistoryIcon } from '../../Icons/icon';
import { useDispatch } from 'react-redux';
import { addFeasibilityId } from '../../Redux/Store/Featuresilces/Feasibility';
import { FiX } from 'react-icons/fi';
import { FiTrash2 } from "react-icons/fi";
import { TiMessages } from "react-icons/ti";

const SideBar = ({ setSideBar, sideBar,newMessageSent, setNewMessageSent }) => {
    const { currentUser } = useFrappeAuth();
    const navigate = useNavigate()
    const [searchContainerOpen, setSearchContainerOpen] = useState(false)
    const [showFeasibilityHistory, setShowFeasibilityHistory] = useState(false);
    const [showFeasibilityModal, setShowFeasibilityModal] = useState(false);
    const [resultJson, setResultJson] = useState(false);
    const [hasUnseenReport, setHasUnseenReport] = useState(false);
    const [showChatHistory, setChatHistory] = useState(true)
    const dispatch = useDispatch()
    const { call } = useContext(FrappeContext)
    const [showChatModal, setShowChatModal] = useState(false);
    const [selectedReportChats, setSelectedReportChats] = useState([]);
    const [selectedReportName, setSelectedReportName] = useState('');
    const [openMenuIndex, setOpenMenuIndex] = useState(null);
    const dropdownRefs = useRef({});
    const { updateDoc } = useFrappeUpdateDoc()
    const [openDeleteModal, setOpenDeleteModal] = useState(false)
    const [openDeleteModalId, setOpenDeleteModalId] = useState(false)
    const { sessionId } = useParams();
    

    const handleDelete = async () => {
        try {
            const response = await updateDoc("Session", openDeleteModalId, {
                "soft_delete": 1
            })
            await mutate();
            if(sessionId == openDeleteModalId){
                navigate("/chat", { replace: true });
            }
            if (response) return;

        } catch (error) {
            // console.log("error occured while deleting", error);

        }


    }

    // console.log(sessionId, 'This is the sesssion id fetched from URL')
    // Close dropdown on outside click
    useEffect(() => {
        const handleClickOutside = (event) => {
            const isClickInside = Object.values(dropdownRefs.current).some(ref =>
                ref?.contains(event.target)
            );
            if (!isClickInside) {
                setOpenMenuIndex(null);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);



    const showChatlist = (item) => {
        // Extract chats from the item (assuming chats are in item.chats or similar)
        const chats = item.chats || []; // Adjust this based on your data structure
        setSelectedReportChats(chats);
        setSelectedReportName(item.name);
        setShowChatModal(true);
    };

    // Toggle Feasibility Modal
    const toggleFeasibilityModal = (item) => {
        const isOpening = !showFeasibilityModal;

        if (isOpening) {
            setResultJson(item?.result_data || {});
            dispatch(addFeasibilityId(item?.name));
        }
        setShowFeasibilityModal(isOpening);
    };

    const toggleFeasibility = () => {
        showFeasibilityHistory ? (setShowFeasibilityHistory(false), setChatHistory(true)) : (setShowFeasibilityHistory(true), setChatHistory(false))
    };

    // Fetching session data from Frappe
    const { data, mutate } = useFrappeGetDocList("Session", {
        fields: ['*'],
        filters: [['user', '=', currentUser], ["soft_delete", "!=", 1]],
        limit: 1000000,
        orderBy: { field: 'creation', order: 'desc' },
        revalidateOnMount: true
    });


    // const { data: reports, mutate } = useFrappeGetDocList("Feasibility Report", {
    //     fields: ['*'],
    //     filters: [['user', '=', currentUser]],
    //     limit: 1000000,
    //     orderBy: { field: 'creation', order: 'desc' },
    // });

    // useEffect(() => {
    //     // mutate()
    // }, [])
    const [history, setHistory] = useState([]);

    const [expandedSections, setExpandedSections] = useState({
        'Today': true,
        'Yesterday': true,
        'Previous 7 days': true,
    });

    const [showSettings, setShowSettings] = useState(false);
    const [editingMessage, setEditingMessage] = useState(null);
    const [editText, setEditText] = useState('');
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchReportsWithChats = useCallback(async () => {
        try {
            const response = await call.get("frappe.client.get_list", {
                doctype: "Feasibility Report",
                filters: {
                    owner: ["=", currentUser],
                    status: ["in", ["Complete", "Fail"]]
                },
                fields: ["name", "status", "creation", "result_data"],
                order_by: "creation desc",
                limit: 100
            });

            const summaries = response.message || [];

            const fullReports = await Promise.all(
                summaries.map(async (report) => {
                    try {
                        const fullDoc = await call.get("frappe.client.get", {
                            doctype: "Feasibility Report",
                            name: report.name
                        });
                        return fullDoc.message;
                    } catch (err) {
                        // console.error("Error fetching full report:", err);
                        return null;
                    }
                })
            );

            const validReports = fullReports.filter((r) => r !== null);
            setReports(validReports);
            // console.log(validReports, 'This are the Reports')
        } catch (err) {
            // console.error("Error fetching reports:", err);
        } finally {
            setLoading(false);
        }
    }, [currentUser]);

    useEffect(() => {
        if (currentUser) {
            fetchReportsWithChats();
        }
    }, [currentUser, fetchReportsWithChats]);

    useFrappeEventListener("feasibility_update", (data) => {
        //   console.log("Realtime update received:", data);
        fetchReportsWithChats();
    });


    // useEffect(() => {
    //     if (data) {

    //         const formattedHistory = groupMessagesByDate(data);
    //         setHistory(formattedHistory);
    //     }
    // }, [data, sessionId]);

    useEffect(() => {
    const refreshHistory = async () => {
        if (sessionId) {

            const firstCall = await mutate()
            if(firstCall) {
                const formatted = groupMessagesByDate(firstCall);
                    setHistory(formatted);
            }
            
        } else if (data) {
            // Use current data directly
            const formatted = groupMessagesByDate(data);
            setHistory(formatted);
        }
    };

    refreshHistory();
}, [data, sessionId]);


useEffect(() => {
    const updateSideBar = async ()=>  {
        if (newMessageSent) {
        //   console.log("🔄 Sidebar update triggered due to new message title");
    
          // Your custom logic here (e.g., refresh contacts, highlight active, fetch stats)
          // Example:
          const firstCall = await mutate()
                if(firstCall) {
                    const formatted = groupMessagesByDate(firstCall);
                    setHistory(formatted);
                }
    
          // Reset the trigger so it doesn’t keep firing
          setNewMessageSent(false);
        }
    }
    updateSideBar()
  }, [newMessageSent]);

    // const groupMessagesByDate = (sessions) => {
    //     const today = new Date();
    //     const yesterday = new Date(today);
    //     yesterday.setDate(today.getDate() - 1);
    //     const sevenDaysAgo = new Date(today);
    //     sevenDaysAgo.setDate(today.getDate() - 7);

    //     const groupedHistory = [
    //         { time: 'Today', messages: [] },
    //         { time: 'Yesterday', messages: [] },
    //         { time: 'Previous 7 days', messages: [] },
    //     ];

    //     sessions.forEach(session => {
    //         const sessionDate = new Date(session.creation); // Assuming `creation` is the timestamp

    //         // Check if the session is from today
    //         if (sessionDate.toDateString() === today.toDateString()) {
    //             groupedHistory[0].messages.push({ id: session.name, text: session.name, title: session.title });
    //         }
    //         // Check if the session is from yesterday
    //         else if (sessionDate.toDateString() === yesterday.toDateString()) {
    //             groupedHistory[1].messages.push({ id: session.name, text: session.name, title: session.title });
    //         }
    //         // Check if the session is from within the last 7 days
    //         else if (sessionDate >= sevenDaysAgo) {
    //             groupedHistory[2].messages.push({ id: session.name, text: session.name, title: session.title });
    //         }
    //     });

    //     return groupedHistory;
    // };
    const groupMessagesByDate = (sessions) => {
        const today = new Date();

        const groupedHistory = [
            { time: 'Today', messages: [] },
            { time: 'Previous', messages: [] },
        ];

        // 1. Find the earliest session
let earliestSession = sessions.reduce((earliest, current) => {
    return new Date(current.creation) < new Date(earliest.creation) ? current : earliest;
}, sessions[0]);

// 2. Filter out the earliest session
let remainingSessions = sessions.filter(session => session.name !== earliestSession.name);

// 3. Now group the rest by today's date
remainingSessions.forEach(session => {
    const sessionDate = new Date(session.creation);

    if (sessionDate.toDateString() === today.toDateString()) {
        groupedHistory[0].messages.push({
            id: session.name,
            text: session.name,
            title: session.title,
            date: session.modified,
            intension: session.user_intension
        });
    } else {
        groupedHistory[1].messages.push({
            id: session.name,
            text: session.name,
            title: session.title,
            date: session.modified,
            intension: session.user_intension
        });
    }
});
        return groupedHistory;
    };

    const toggleSection = (time) => {
        setExpandedSections(prev => ({
            ...prev,
            [time]: !prev[time],
        }));
    };

    const deleteMessage = (time, id) => {
        setHistory(prev => prev.map(section => {
            if (section.time === time) {
                return {
                    ...section,
                    messages: section.messages.filter(msg => msg.id !== id),
                };
            }
            return section;
        }));
    };

    const startEditing = (message) => {
        setEditingMessage(message.id);
        setEditText(message.title);
    };

    const saveEdit = (time, id) => {
        setHistory(prev => prev.map(section => {
            if (section.time === time) {
                return {
                    ...section,
                    messages: section.messages.map(msg =>
                        msg.id === id ? { ...msg, text: editText } : msg
                    ),
                };
            }
            return section;
        }));
        setEditingMessage(null);
    };

    const cancelEdit = () => {
        setEditingMessage(null);
    };

    // if (showSettings) {
    //     return <Settings onClose={() => setShowSettings(false)} />;
    // }

    const createNewChat = () => {
        // console.log("clicked but not working")
        navigate('/chat', { replace: true });
    }

    const getDateFromDatetime = (datetime) => {
        if (!datetime) return "";

        const dateObj = new Date(datetime);

        if (isNaN(dateObj)) return datetime; // Return as-is if invalid

        // Format to MM-DD-YYYY
        const month = String(dateObj.getMonth() + 1).padStart(2, '0'); // getMonth() is 0-indexed
        const day = String(dateObj.getDate()).padStart(2, '0');
        const year = dateObj.getFullYear();

        return `${month}-${day}-${year}`;
    };

    const [activeChat, setActiveChat] = useState()
    // useEffect(()=>{
    //     if(activeChat) {
    //         document.title = activeChat
    //     }
    //     else {
    //         document.title = 'MarsAIX'
    //     }    
    // },[[activeChat]])
    const [hovered, setHovered] = useState(false)

    return (
        <div className={`sidebar relative flex flex-col transition-width duration-500 ease-in-out  h-full ${sideBar ? 'w-[280px] min-w-[280px] p-2 opacity-100 bg-gradient-to-b from-[#1C3B6B] to-[#0f2c6c] z-[10]' : ' bg-gradient-to-b from-[#1C3B6B] to-[#0f2c6c] z-[10] border-r border-gray-300 w-[52px] min-w-[52px]  p-1 opacity-100 cursor-pointer justify-start'}`} onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} onClick={(e) => { if (!sideBar && e.target === e.currentTarget) { setSideBar(true); } }}>
            {/* Header */}

            {!sideBar ? (
                // Sidebar is closed
                <div className="h-10 w-10 mb-4 cursor-pointer relative flex items-center justify-center p-1 hover:bg-gray-100 hover:bg-opacity-20 rounded-md" onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} >
                    {hovered ? (
                        <TbLayoutSidebarRightCollapse onClick={() => setSideBar(true)} title="Open Sidebar" className="relative text-3xl font-light text-white" />
                    ) : (
                        <img src={newsymbol} className="relative w-[100%] h-[100%] object-contain" alt="Logo" />
                    )}
                </div>
            ) : (
                // Sidebar is open
                <div className="relative mb-4 flex flex-row justify-between items-center">
                    <div className="h-10 w-10 cursor-pointer relative flex items-center justify-center p-1 hover:bg-gray-100 hover:bg-opacity-20 rounded-md">
                        <img
                            src={newsymbol}
                            className="relative w-[100%] h-[100%] object-contain"
                            alt="Logo"
                        />
                    </div>
                    <div
                        onClick={() => {
                            setSideBar(false);
                            setHovered(false);
                        }}
                        className="relative h-9 w-9 cursor-pointer flex items-center justify-center p-1 hover:bg-gray-100 hover:bg-opacity-20 rounded-md"
                    >
                        <TbLayoutSidebarLeftCollapse

                            title="Close Sidebar"
                            className="text-white text-3xl font-light"
                        />
                    </div>
                </div>
            )}


            {/* New Chat Button */}
            <button title='New Chat' className={` flex flex-shrink-0 h-9 mb-4  ${sideBar ? 'w-full justify-start py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg  hover:bg-gray-100 hover:bg-opacity-20 transition-all`} onClick={() => createNewChat()}>
                <FaRegEdit className='text-xl text-white' />
                {sideBar && (<span className={`text-sm text-white transition-opacity duration-500 ease-in-out font-medium tracking-wide ${sideBar ? 'opacity-100' : 'opacity-0'}`}>New Chat</span>)}
            </button>

            <button title='Search Chats' className={`flex flex-shrink-0 h-9 mb-4 ${sideBar ? 'w-full justify-start py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg  hover:bg-gray-100 hover:bg-opacity-20 transition-all`} onClick={() => { setSearchContainerOpen(true) }}>
                <IoSearch className='text-white text-xl' />
                {sideBar && (<span className={`text-sm text-white transition-opacity duration-500 ease-in-out font-medium tracking-wide ${sideBar ? 'opacity-100' : 'opacity-0'}`}>Search</span>)}
            </button>

            {/* Feasibility Section */}
            <button
                onClick={() => { sideBar ? toggleFeasibility() : toggleFeasibilityModal() }}
                className={`flex h-9 ${sideBar ? 'w-full justify-between py-1 px-2' : 'w-9 justify-center p-1'
                    } ${showFeasibilityHistory ? '' : 'mb-4'} min-w-fit flex-shrink-0 flex-row items-center duration-200 cursor-pointer gap-3 text-white rounded-lg hover:bg-gray-100 hover:bg-opacity-20 `}
            >
                <div className="flex items-center flex-row gap-3 text-white" title='Feasibility Report'>
                    <FaRegLightbulb className='text-gray-100 text-xl' />
                    {sideBar && <span className={`text-sm text-white transition-opacity duration-500 ease-in-out font-medium tracking-wide ${sideBar ? 'opacity-100' : 'opacity-0'}`}>Feasibility History</span>}
                </div>
                {sideBar && (
                    <div>
                        {showFeasibilityHistory ? (
                            <FaChevronUp className='text-gray-100 font-light text-xs' />
                        ) : (
                            <FaChevronDown className='text-gray-100 font-light text-xs' />
                        )}
                    </div>
                )}
            </button>

            {sideBar && showFeasibilityHistory && (
                <div className={`mt-2 overflow-y-auto transition-all duration-500 ease-in-out ${sideBar ? 'opacity-100' : 'opacity-0'} SideBar-scroll ${(!reports || reports.length === 0) ? ' flex flex-col items-center justify-center' : ''} `} style={{ minHeight: '40px' }}>
                    {reports && reports.length > 0 && (
                        <ul className="px-1 py-1 space-y-1  text-sm text-white rounded-md">
                            {reports.map((item, index) => {
                                let date = getDateFromDatetime(item.creation)
                                let status = item.status
                                return (
                                    <li
                                        key={index}
                                        className=" text-sm relative w-full flex flex-row gap-3 items-center"

                                    >
                                        <div onClick={() => toggleFeasibilityModal(item)} className={`relative ${item.chats.length > 0 ? 'w-[80%]' : 'w-full'} flex flex-row gap-3 p-2 text-sm cursor-pointer hover:bg-[#41b655] hover:bg-opacity-20 transition-colors rounded-lg `}>
                                            <span className='flex items-center justify-center flex-shrink-0 h-9 w-9 p-1 duration-200  cursor-pointer text-white rounded-lg bg-gray-100 bg-opacity-20 transition-all'>
                                                <HiOutlineDocumentReport className='text-white text-lg' />
                                            </span>
                                            <div className='flex flex-col gap-1 relative w-[75%]'>
                                                <p className='text-white text-sm truncate' >{item.feasibility_title || item.name}</p>
                                                <span className='text-white text-xs flex flex-row gap-2'>
                                                    <p>{date}</p>
                                                    <p className='relative flex flex-row gap-1 items-center'>
                                                        <span className={`relative h-2 w-2 rounded-full ${status === "Complete" ? 'bg-green-500' : status === "Processing" ? 'bg-orange-500' : status === "Pending" ? 'bg-yellow-500' : 'bg-red-500'}`}></span>
                                                        {status}
                                                    </p>

                                                </span>
                                            </div>
                                        </div>
                                        {item.chats.length > 0 && (<span onClick={() => showChatlist(item)} className="cursor-pointer hover:bg-[#41b655] hover:bg-opacity-20 hover:text-blue-400 h-full px-2 py-4 rounded-lg flex items-center justify-center w-fit transition-colors">
                                            {/* <RiChatSmile3Line className='text-lg' /> */}
                                            <TiMessages className='text-lg text-white' size={16} strokeWidth={1} />
                                        </span>)}
                                    </li>
                                )
                            })}
                        </ul>
                    )}
                    {(!reports || reports.length === 0) && (
                        <p className='text-sm text-gray-300 select-none self-center font-normal'>No Reports Generated Yet</p>
                    )}
                </div>
            )}

            {sideBar && (
                <button onClick={() => { showChatHistory ? (setChatHistory(false), setShowFeasibilityHistory(true)) : (setChatHistory(true), setShowFeasibilityHistory(false)) }} className={`flex h-9 ${showChatHistory ? '' : 'mb-4'}  transition-all duration-500 ease-in-out ${sideBar ? 'opacity-100' : 'opacity-0'} flex-shrink-0 w-full justify-between py-1 px-2 min-w-fit flex-row items-center duration-200 cursor-pointer gap-3 text-white rounded-lg hover:bg-gray-100 hover:bg-opacity-20 `} >
                    <div className="flex items-center flex-row gap-3 text-white" title='Chat History'>
                        <HistoryIcon strokeWidth={2} className='text-gray-100 text-xl' size={20} />
                        <span className="text-sm text-white font-medium tracking-wide">Chat History</span>
                    </div>
                    {sideBar && (
                        <div>
                            {showChatHistory ? (
                                <FaChevronUp className='text-gray-100 font-light text-xs' />
                            ) : (
                                <FaChevronDown className='text-gray-100 font-light text-xs' />
                            )}
                        </div>
                    )}
                </button>)}

            {sideBar && showChatHistory && (<div className={`transition-all duration-500 ease-in-out ${sideBar ? 'opacity-100' : 'opacity-0'} flex-1 mt-2 overflow-y-auto SideBar-scroll px-1 py-3 rounded-md`}>
                {history.map((historyContent, index) =>
                    historyContent.messages && historyContent.messages.length > 0 && (
                        <div key={index} className="pl-2 mb-6 last:mb-0">
                            {/* Group Header */}
                            <div className="mb-2">
                                <h2 className="text-sm select-none font-medium text-white capitalize tracking-wider">
                                    {historyContent.time}
                                </h2>
                            </div>

                            {/* Message List */}
                            <div className="flex flex-col gap-2">
                                {historyContent.messages.map((message, idx) => {
                                    const messageKey = `${index}-${idx}`;

                                    return (
                                        <div key={messageKey} className="relative group" ref={el => (dropdownRefs.current[messageKey] = el)}>
                                            <div
                                                className={`flex items-center justify-between p-2 rounded-lg ${message.id === sessionId ? 'bg-[#41b655] bg-opacity-20' : 'bg-transparent'} hover:bg-[#41b655] hover:bg-opacity-20 transition-colors cursor-pointer`}
                                                onClick={() =>{
                                                    navigate(`/chat/${message.text}`, { replace: true }),
                                                    setActiveChat(message.title)
                                                    // setChatLoader(true)
                                                }
                                                }
                                            >
                                                <p
                                                    className="text-sm tracking-wide font-light text-white truncate pr-2"
                                                    title={message.title}
                                                >
                                                    {message.title}
                                                </p>

                                                {/* 3-dot icon on hover only */}
                                                <div
                                                    className="p-0.5 hover:bg-white hover:bg-opacity-10 rounded hidden group-hover:flex z-10"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setOpenMenuIndex(openMenuIndex === messageKey ? null : messageKey);
                                                    }}
                                                >
                                                    <BsThreeDotsVertical size={14} className="text-white" />
                                                </div>
                                            </div>

                                            {/* Dropdown below 3-dot icon */}
                                            {openMenuIndex === messageKey && (
                                                <div
                                                    className="absolute right-2 top-full mt-1 z-50 bg-white text-black rounded shadow-md text-sm w-28"
                                                >
                                                    <button
                                                        className="flex items-center gap-2 px-4 py-2 hover:bg-red-100 w-full"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setOpenDeleteModalId(message.id)
                                                            setOpenDeleteModal(true)
                                                            setOpenMenuIndex(null);
                                                        }}
                                                    >
                                                        <FiTrash2 size={16} className="text-red-500" />
                                                        Delete
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )
                )}
            </div>)}




            {/* Footer */}
            <div className={`mt-auto pt-2 ${sideBar ? 'border-t border-gray-200' : ''}`}>

                {currentUser && <button
                    className={`flex h-9 ${sideBar ? 'w-full justify-start py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg shadow-sm hover:bg-gray-100 hover:bg-opacity-20 transition-all`}
                    onClick={() => setShowSettings(true)}
                >
                    <IoSettingsSharp className='text-white text-xl' />
                    {sideBar && (<span className={`text-sm text-white transition-opacity duration-500 ease-in-out font-medium tracking-wide ${sideBar ? 'opacity-100' : 'opacity-0'}`}>Settings</span>)}
                </button>}
            </div>

            {showSettings && <Settings onClose={() => setShowSettings(false)} />}
            {searchContainerOpen && <SearchContainer onClose={() => setSearchContainerOpen(false)} data={history} />}
            {showFeasibilityModal && (
                <FeasibilityStudy
                    isOpen={showFeasibilityModal}
                    onClose={toggleFeasibilityModal}
                    resultJson={resultJson}
                    hasUnseenReport={hasUnseenReport}
                    setHasUnseenReport={setHasUnseenReport}
                />
            )}
            {showChatModal && (
                <ChatListModal
                    isOpen={showChatModal}
                    onClose={() => setShowChatModal(false)}
                    chats={selectedReportChats}
                    reportName={selectedReportName}
                />
            )}
            {openDeleteModal && (
                <DeleteChatModal
                    isOpen={openDeleteModal}
                    onClose={() => setOpenDeleteModal(false)}
                    chatTitle={openDeleteModalId}
                    onConfirm={async () => {
                        await handleDelete();   // Ensure deletion completes
                                 // Then trigger refetch
                        setOpenDeleteModal(false);
                    }}
                />
            )}
        </div>
    );
};

export default SideBar;

const ChatListModal = ({ isOpen, onClose, chats, reportName }) => {
    const { call } = useContext(FrappeContext);
    const navigate = useNavigate();
     const [newChats, setNewChats] = useState([]);

    useEffect(() => {
        if (!isOpen || !chats) return;
        const fetchTitles = async () => {
            const newChats = await Promise.all(
                chats.map(async (tempChat) => {
                    try {
                        const fullDoc = await call.get("frappe.client.get", {
                            doctype: "Session",
                            name: tempChat.session
                        });
                        return {
                            ...tempChat,
                            title: fullDoc.message.title
                        };
                    } catch (err) {
                        // console.error("Error fetching the title:", err);
                        return {
                            ...tempChat,
                            title: "New Chat"
                        };
                    }
                })
            );
            setNewChats(newChats);
        };

        fetchTitles();
    }, [chats, isOpen]);

    if (!isOpen) return null;


    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-[40%] h-[65vh] flex flex-col">
                {/* Header */}
                <div className="flex flex-row items-center bg-[#0e2044] rounded-t-lg justify-between p-4 border-b border-gray-200">
                    <div className='relative flex flex-row items-center gap-3'>
                        <span className='relative flex items-center rounded-full justify-center p-2 bg-gray-300 bg-opacity-20'><TiMessages className="text-white" strokeWidth={1} size={20} /></span>
                        <div className='relative flex flex-col items-start w-fit gap-1 '>
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                Feasibility Report Chat History
                            </h3>
                            <p className="text-sm font-normal text-white">Report: {reportName}</p>
                        </div>

                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-full hover:bg-[#2C53A3] transition-colors"
                    >
                        {/* <FaXmark className="text-gray-500 text-lg" /> */}
                        <FiX className='text-white' size={24} />
                    </button>
                </div>

                {/* Chat List */}
                <div className="flex-1 overflow-y-auto p-4">
                    {newChats && newChats.length > 0 ? (
                        <div className="space-y-3">
                            {newChats.map((chat, index) => (
                                <div
                                    key={index}
                                    className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                                    onClick={() => {
                                        navigate(`/chat/${chat.session}`, { replace: true })
                                        onClose()
                                    }
                                    }
                                >
                                    <div className="flex flex-row justify-between items-center">
                                        <span className="text-sm font-medium text-gray-800">
                                            {chat.title || 'New Chat'}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            {new Date(chat.creation || chat.timestamp).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <HistoryIcon className="text-gray-300 text-4xl mx-auto mb-3" size={40} strokeWidth={3} />
                            <p className="text-gray-500 text-sm">No chats found for this report</p>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

const DeleteChatModal = ({
    chatTitle,
    isOpen,
    onClose,
    onConfirm
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-500/50">
            <div className="w-full max-w-md rounded-lg bg-white shadow-lg">
                {/* Header */}
                <div className="border-b border-gray-200 p-5">
                    <h3 className="text-lg font-semibold text-gray-800">Delete Chat</h3>
                </div>

                {/* Body */}
                <div className="p-5">
                    <p className="text-gray-600">
                        Are you sure you want to delete this chat?
                    </p>
                    <p className="mt-3 text-sm text-red-500">
                        This action cannot be undone. All messages will be permanently deleted.
                    </p>
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 border-t border-gray-200 p-4">
                    <button
                        onClick={onClose}
                        className="rounded-md bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        className="rounded-md bg-red-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        Delete
                    </button>
                </div>
            </div>
        </div>
    );
};

