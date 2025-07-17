import React, { useState, useEffect, useContext } from 'react';
import { BiSidebar, BiChevronDown, BiPlus } from "react-icons/bi";
import { IoSearch, IoSparklesOutline, IoDiamondOutline, IoMenu, IoSettingsSharp } from "react-icons/io5";
import { FaFolder, FaFolderOpen, FaChevronDown, FaChevronUp, FaRegEdit, FaChevronRight } from "react-icons/fa";
import { RiHistoryLine } from "react-icons/ri";
import { BsThreeDotsVertical } from "react-icons/bs";
import symbol from '../../assets/New Symbol.png'
import { TbLayoutSidebarRightCollapse, TbLayoutSidebarLeftCollapse } from "react-icons/tb";
import { FaFilePdf, FaRegLightbulb } from 'react-icons/fa';
import newsymbol from '../../assets/New MarsAIX White - Edited.png'
import Settings from "../Settings/Settings";
import { useFrappeAuth, useFrappeGetDocList, FrappeContext } from 'frappe-react-sdk';
import { useNavigate } from 'react-router-dom';
import { use } from 'react';
// import '../Chatscreen/Chats  creen.css'
import './SideBar.css'
import SearchContainer from './SearchContainer';
import FeasibilityStudy from '../Feasibilitystudy/FeasibilityStudy';
import { FaArrowRight, FaXmark } from 'react-icons/fa6';
import { HiOutlineDocumentReport } from "react-icons/hi";

const SideBar = ({ setSideBar, sideBar }) => {
    const { currentUser } = useFrappeAuth();
    const navigate = useNavigate()
    const call = useContext(FrappeContext)
    const [searchContainerOpen, setSearchContainerOpen] = useState(false)
    const [showFeasibilityHistory, setShowFeasibilityHistory] = useState(true);
    const [showFeasibilityModal, setShowFeasibilityModal] = useState(false);
    const [resultJson, setResultJson] = useState(false);

    // Toggle Feasibility Modal
    const toggleFeasibilityModal = (item) => {
        setShowFeasibilityModal(!showFeasibilityModal);
        setResultJson(item.result_data || {})
    };

    const toggleFeasibility = () => {
        setShowFeasibilityHistory(prev => !prev);
    };

    const feasibilityData = [
        "Feasibility Report #001",
        "Feasibility Report #002",
        "Feasibility Report #003"
    ];

    const getTitle = async (msg) => {
        try {
            const response = await call.post('frontend_app.Management_Class.helpers.utility.generate_chat_title', { 'user_query': msg })
            if (response?.message) {
                console.log(response, response.message, 'this is the called statement method');
            } else {
                console.error('Statement creation failed:', response.message);
            }
        } catch (error) {
            console.error('Error creating the Statement ', error)
        }
    }

    // Fetching session data from Frappe
    const { data } = useFrappeGetDocList("Session", {
        fields: ['*'],
        filters: [['user', '=', currentUser]],
        limit: 1000000,
        orderBy: { field: 'creation', order: 'desc' },
    });
    const { data: reports, mutate } = useFrappeGetDocList("Feasibility Report", {
        fields: ['*'],
        filters: [['user', '=', currentUser]],
        limit: 1000000,
        orderBy: { field: 'creation', order: 'desc' },
    });
    console.log("repors", reports);


    useEffect(() => {
        mutate()
    }, [])
    const [history, setHistory] = useState([]);

    const [expandedSections, setExpandedSections] = useState({
        'Today': true,
        'Yesterday': true,
        'Previous 7 days': true,
    });

    const [showSettings, setShowSettings] = useState(false);
    const [editingMessage, setEditingMessage] = useState(null);
    const [editText, setEditText] = useState('');

    useEffect(() => {
        if (data) {

            const formattedHistory = groupMessagesByDate(data);
            console.log(formattedHistory, 'this is the formatted history')
            setHistory(formattedHistory);
        }
    }, [data]);

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

    sessions.forEach(session => {
        const sessionDate = new Date(session.creation);

        if (sessionDate.toDateString() === today.toDateString()) {
        groupedHistory[0].messages.push({
            id: session.name,
            text: session.name,
            title: session.title
        });
        } else {
        groupedHistory[1].messages.push({
            id: session.name,
            text: session.name,
            title: session.title
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
        console.log("clicked but not working")
        navigate('/chat', { replace: true });
    }

 const getDateFromDatetime = (datetime) => {
  if (!datetime) return "";

  const dateObj = new Date(datetime);

  if (isNaN(dateObj)) return datetime; // Return as-is if invalid

  // Format to YYYY-MM-DD
  return dateObj.toISOString().split("T")[0];
};


    useEffect(() => {
        console.log(history, 'this is the chat history');
    }, [history])

    const [hovered,setHovered] = useState(false)

    return (
        // <div className={`sidebar relative flex flex-col transition-all duration-300 ease-in-out bg-gradient-to-b from-gray-50 to-gray-100 h-full ${sideBar ? 'w-[280px] min-w-[280px] p-4 opacity-100' : 'w-0 min-w-0 p-0 opacity-0 overflow-hidden'}`}>
        <div className={`sidebar relative flex flex-col gap-4 transition-all duration-300 ease-in-out  h-full ${sideBar ? 'w-[280px] min-w-[280px] p-2 opacity-100 bg-gradient-to-b from-[#1C3B6B] to-[#0f2c6c] z-[10]' : ' bg-gradient-to-b from-[#1C3B6B] to-[#0f2c6c] z-[10] border-r border-gray-300 min-w-[60px] w-[60px] p-2 opacity-100 cursor-pointer justify-start'}`} onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} onClick={(e) => {if (!sideBar && e.target === e.currentTarget) {setSideBar(true);}}}>
            {/* Header */}

            {!sideBar ? (
                // Sidebar is closed
                <div className="h-9 w-9 cursor-pointer relative flex items-center justify-center p-1 hover:bg-gray-100 hover:bg-opacity-20 rounded-md" onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} >
                    {hovered ? (
                        <TbLayoutSidebarRightCollapse onClick={() => setSideBar(true)} title="Open Sidebar" className="relative text-3xl font-light text-white" />
                    ) : (
                        <img src={newsymbol} className="relative w-[100%] h-[100%] object-contain" alt="Logo" />
                    )}
                </div>
                ) : (
                // Sidebar is open
                <div className="relative flex flex-row justify-between items-center">
                    <div className="h-9 w-9 cursor-pointer relative flex items-center justify-center p-1 hover:bg-gray-100 hover:bg-opacity-20 rounded-md">
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
            <button title='New Chat' className={` flex h-9 ${sideBar ? 'w-full justify-start py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg  hover:bg-gray-100 hover:bg-opacity-20 transition-all`} onClick={() => createNewChat()}>
                <FaRegEdit  className='text-xl text-white' />
                {sideBar && ( <span className='text-sm text-white font-medium tracking-wide'>New Chat</span>)}
            </button>

            <button title='Search Chats' className={`flex h-9 ${sideBar ? 'w-full justify-start py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg  hover:bg-gray-100 hover:bg-opacity-20 transition-all`} onClick={() => { setSearchContainerOpen(true) }}>
                <IoSearch className='text-white text-xl' />
                {sideBar && (<span className='text-sm text-white font-medium tracking-wide'>Search</span>)}
            </button>

            {/* Feasibility  */}
            {/* <div className={`${sideBar ? 'border-b border-gray-200 pb-4' : ''}`}>
                <button
                    onClick={()=>{sideBar ? toggleFeasibility() : toggleFeasibilityModal()}}
                    className={`flex h-9 ${sideBar ? 'w-full justify-between py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg hover:bg-gray-100 hover:bg-opacity-20 transition-all`}
                >
                    <div className="flex items-center flex-row gap-3 text-white" title='Feasibility Report'>
                            <FaRegLightbulb  className='text-gray-100 text-xl' />
                     
                        {sideBar && (<span className="text-sm text-white font-medium tracking-wide">Feasibility History</span>)}
                    </div>
                    {sideBar && (<div>
                        { showFeasibilityHistory ? (
                            <FaChevronUp className='text-gray-100 font-light text-xs' />
                        ) : (
                            <FaChevronDown className='text-gray-100 font-light text-xs' />
                        )}
                    </div>)}
                </button>

                {sideBar && showFeasibilityHistory && (
                    <ul className="flex-1 overflow-y-auto SideBar-scroll px-1 py-3  mt-2 ml-4 space-y-1 text-sm text-white rounded-md">
                        {reports.map((item, index) => (
                            <li
                                key={index}
                                className="cursor-pointer text-xs p-1 hover:bg-[#41b655] hover:bg-opacity-20 transition-colors rounded-lg"
                                onClick={() => toggleFeasibilityModal(item)}
                            >
                                {item.name}
                            </li>
                        ))}
                    </ul>
                )}
            </div> */}
            {/* Feasibility Section */}
                <div className={`${sideBar ? 'border-b border-gray-200 pb-2' : ''}`}>
                    <button
                        onClick={() => { sideBar ? toggleFeasibility() : toggleFeasibilityModal() }}
                        className={`flex h-9 ${
                            sideBar ? 'w-full justify-between py-1 px-2' : 'w-9 justify-center p-1'
                        } min-w-fit flex-row items-center duration-200 cursor-pointer gap-3 text-white rounded-lg hover:bg-gray-100 hover:bg-opacity-20 transition-all`}
                    >
                        <div className="flex items-center flex-row gap-3 text-white" title='Feasibility Report'>
                            <FaRegLightbulb className='text-gray-100 text-xl' />
                            {sideBar && <span className="text-sm text-white font-medium tracking-wide">Feasibility History</span>}
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
                        <div className="overflow-y-auto SideBar-scroll" style={{ maxHeight: '170px' }}>
                            <ul className="px-1 py-1 mt-2 space-y-1 text-sm text-white rounded-md">
                                {reports?.map((item, index) => {
                                    let date = getDateFromDatetime(item.creation)
                                    let status = item.status
                                    return (
                                        <li
                                            key={index}
                                            className="cursor-pointer text-sm p-2 flex flex-row gap-3 items-center hover:bg-[#41b655] hover:bg-opacity-20 transition-colors rounded-lg"
                                            onClick={() => toggleFeasibilityModal(item)}
                                        >
                                            <span className='flex items-center justify-center flex-shrink-0 h-9 w-9 p-1 duration-200  cursor-pointer text-white rounded-lg bg-gray-100 bg-opacity-20 transition-all'>
                                                <HiOutlineDocumentReport className='text-white text-lg'/>   
                                            </span>
                                            <div className='flex flex-col gap-1 relative w-full'>
                                                <span className='text-white text-sm'>{item.name}</span>
                                                <span className='text-white text-xs flex flex-row gap-2'><p>{date}</p> <p className='relative flex flex-row gap-1 items-center'><span className={`relative h-2 w-2 rounded-full ${status==="Complete" ? 'bg-green-500' : status==="Processing" ? 'bg-orange-500' : status==="Pending" ? 'bg-yellow-500' : 'bg-red-500'}`}></span>{status}</p></span>
                                            </div>
                                        </li>
                                    )
                                })}
                            </ul>
                        </div>
                    )}

                    {sideBar && showFeasibilityHistory &&  (
                        <button
                        onClick={() => { setShowFeasibilityModal(true)}}
                        className={`flex h-9 mt-2 w-full justify-center min-w-fit flex-row items-center duration-200 cursor-pointer gap-3 text-white rounded-lg hover:bg-gray-100 hover:bg-opacity-20 transition-all`}
                        >
                        <div className="flex items-center flex-row gap-3 text-white" title='Feasibility Report'>
                            <span className="text-sm text-white font-medium tracking-wide">View all studies</span>
                            <FaChevronRight className='text-gray-100 text-lg' />
                        </div>
                    </button>
                    )}
                </div>
            
            {/* History Sections */}
         
            {sideBar && (
                <>
                <h2 className='relative text-white text-sm px-2 font-medium select-none tracking-wide'>Chat History</h2>
                <div className="flex-1 overflow-y-auto SideBar-scroll px-1 py-3 rounded-md">
                    {history.map((historyContent, index) =>
                    historyContent.messages && historyContent.messages.length > 0 && (
                        <div key={index} className="pl-2 mb-6  last:mb-0">
                        {/* Group Header (still showing time) */}
                        <div className="mb-2">
                            <h2 className="text-sm select-none font-medium text-white capitalize tracking-wider">
                            {historyContent.time}
                            </h2>
                        </div>

                        {/* All Messages (no toggle/collapse) */}
                        <div className=" flex flex-col gap-2">
                            {historyContent.messages.map((message, idx) => (
                            <div key={idx}>
                                <div
                                className="group flex items-center justify-between p-2 rounded-lg hover:bg-[#41b655] hover:bg-opacity-20 transition-colors cursor-pointer"
                                onClick={() =>
                                    navigate(`/chat/${message.text}`, { replace: true })
                                }
                                >
                                <p
                                    className="text-sm tracking-wide font-light text-white truncate pr-2"
                                    title={message.title}
                                >
                                    {message.title}
                                </p>
                                {/* Optional: actions like 3-dot menu can go here */}
                                </div>
                            </div>
                            ))}
                        </div>
                        </div>
                    )
                    )}
                </div>
                </>
            )}


            {/* Footer */}
            <div className={`mt-auto pt-2 ${sideBar ? 'border-t border-gray-200' : ''}`}>
                
                {currentUser && <button
                    className={`flex h-9 ${sideBar ? 'w-full justify-start py-1 px-2' : 'w-9 justify-center p-1'} min-w-fit flex-row items-center duration-200  cursor-pointer gap-3 text-white rounded-lg shadow-sm hover:bg-gray-100 hover:bg-opacity-20 transition-all`}
                    onClick={() => setShowSettings(true)}
                >
                    <IoSettingsSharp className='text-white text-xl' />
                    {sideBar && (<span className='text-sm font-medium text-white'>Settings</span>)}
                </button>}
            </div>

            {showSettings && <Settings onClose={() => setShowSettings(false)} />}
            {searchContainerOpen && <SearchContainer onClose={() => setSearchContainerOpen(false)} data={history} />}
            {showFeasibilityModal && (
                <FeasibilityStudy
                    isOpen={showFeasibilityModal}
                    onClose={toggleFeasibilityModal}
                    resultJson={resultJson}
                />
            )}
        </div>
    );
};

export default SideBar;