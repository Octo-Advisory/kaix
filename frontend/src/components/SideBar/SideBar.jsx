import React, { useState } from 'react';
import { BiSidebar, BiChevronDown, BiPlus } from "react-icons/bi";
import { IoSearch, IoSparklesOutline, IoDiamondOutline } from "react-icons/io5";
import { RiHistoryLine } from "react-icons/ri";
import { BsThreeDotsVertical } from "react-icons/bs";
import Settings from "../Settings/Settings"

const SideBar = ({ setSideBar, sideBar }) => {
    const [history, setHistory] = useState([
        {'time':'Today', 'messages':[
            {id: 1, text: 'Give me Incentives for Vadodara'},
            {id: 2, text: 'Give me Approvals required to eat food'}
        ]}, 
        {'time':'Yesterday', 'messages':[
            {id: 3, text: 'Give me Cement'},
            {id: 4, text: 'I am Mr Nobody'},
            {id: 5, text: 'I want to build a company'}
        ]}, 
        {'time':'Previous 7 days', 'messages':[
            {id: 6, text: 'Give me Cement'},
            {id: 7, text: 'I am Mr Nobody'},
            {id: 8, text: 'I want to build a company'}
        ]}
    ]);
    
    const [expandedSections, setExpandedSections] = useState({
        'Today': true,
        'Yesterday': true,
        'Previous 7 days': true
    });
    
    const [showSettings, setShowSettings] = useState(false);
    const [editingMessage, setEditingMessage] = useState(null);
    const [editText, setEditText] = useState('');

    const toggleSection = (time) => {
        setExpandedSections(prev => ({
            ...prev,
            [time]: !prev[time]
        }));
    };

    const deleteMessage = (time, id) => {
        setHistory(prev => prev.map(section => {
            if (section.time === time) {
                return {
                    ...section,
                    messages: section.messages.filter(msg => msg.id !== id)
                };
            }
            return section;
        }));
    };

    const startEditing = (message) => {
        setEditingMessage(message.id);
        setEditText(message.text);
    };

    const saveEdit = (time, id) => {
        setHistory(prev => prev.map(section => {
            if (section.time === time) {
                return {
                    ...section,
                    messages: section.messages.map(msg => 
                        msg.id === id ? {...msg, text: editText} : msg
                    )
                };
            }
            return section;
        }));
        setEditingMessage(null);
    };

    const cancelEdit = () => {
        setEditingMessage(null);
    };

    if (showSettings) {
        return <Settings onClose={() => setShowSettings(false)} />;
    }

    return (
        <div className={`sidebar relative flex flex-col transition-all duration-300 ease-in-out bg-gradient-to-b from-gray-50 to-gray-100 h-full ${sideBar ? 'w-[280px] min-w-[280px] p-4 opacity-100' : 'w-0 min-w-0 p-0 opacity-0 overflow-hidden'}`}>
            {/* Header */}
            <div className='flex flex-row justify-between items-center mb-6'>
                <button 
                    onClick={() => setSideBar(false)}
                    className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
                >
                    <BiSidebar className='text-gray-700' size={22} />
                </button>
                <div className='relative flex items-center'>
                    <button className="p-2 rounded-lg hover:bg-gray-200 transition-colors">
                        <IoSearch className='text-gray-700' size={20} />
                    </button>
                </div>
            </div>
            
            {/* New Chat Button */}
            <button className='w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-lg shadow-sm hover:shadow-md transition-all mb-6'>
                <BiPlus size={18} />
                <span className='font-medium'>New Chat</span>
            </button>
            
            {/* History Sections */}
            <div className='flex-1 overflow-y-auto custom-scrollbar'>
                {history.map((historyContent, index) => (
                    <div key={index} className='mb-6 last:mb-0'>
                        <div 
                            className='flex items-center justify-between cursor-pointer mb-2'
                            onClick={() => toggleSection(historyContent.time)}
                        >
                            <div className='flex items-center gap-2'>
                                <RiHistoryLine className='text-gray-500' size={16} />
                                <h2 className='text-sm font-semibold text-gray-700 uppercase tracking-wider'>
                                    {historyContent.time}
                                </h2>
                            </div>
                            <BiChevronDown 
                                className={`text-gray-500 transition-transform ${expandedSections[historyContent.time] ? 'rotate-0' : '-rotate-90'}`} 
                                size={18} 
                            />
                        </div>
                        
                        {expandedSections[historyContent.time] && (
                            <div className='ml-6 flex flex-col gap-2'>
                                {historyContent.messages.map((message, idx) => (
                                    <div key={idx}>
                                        {editingMessage === message.id ? (
                                            <div className="flex flex-col gap-2 p-2 bg-white rounded-lg border border-gray-200">
                                                <input
                                                    type="text"
                                                    value={editText}
                                                    onChange={(e) => setEditText(e.target.value)}
                                                    className="w-full p-1 border-b border-gray-200 focus:outline-none focus:border-blue-500"
                                                    autoFocus
                                                />
                                                <div className="flex justify-end gap-2">
                                                    <button 
                                                        onClick={cancelEdit}
                                                        className="px-2 py-1 text-sm text-gray-500 hover:text-gray-700"
                                                    >
                                                        Cancel
                                                    </button>
                                                    <button 
                                                        onClick={() => saveEdit(historyContent.time, message.id)}
                                                        className="px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                                                    >
                                                        Save
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className='group flex items-center justify-between p-2 rounded-lg hover:bg-gray-200 transition-colors cursor-pointer'>
                                                <p className='text-sm text-gray-600 truncate pr-2'>{message.text}</p>
                                                <div className="relative">
                                                    <button 
                                                        className='opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-gray-700'
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            // For demo purposes, we'll show the dropdown on click
                                                            const dropdown = document.getElementById(`dropdown-${message.id}`);
                                                            dropdown.classList.toggle('hidden');
                                                        }}
                                                    >
                                                        <BsThreeDotsVertical size={14} />
                                                    </button>
                                                    <div 
                                                        id={`dropdown-${message.id}`}
                                                        className="hidden absolute right-0 z-10 mt-1 w-40 bg-white rounded-md shadow-lg border border-gray-200"
                                                    >
                                                        <div className="py-1">
                                                            <button 
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    startEditing(message);
                                                                    document.getElementById(`dropdown-${message.id}`).classList.add('hidden');
                                                                }}
                                                                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                                            >
                                                                Rename
                                                            </button>
                                                            <button 
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    deleteMessage(historyContent.time, message.id);
                                                                    document.getElementById(`dropdown-${message.id}`).classList.add('hidden');
                                                                }}
                                                                className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                                                            >
                                                                Delete
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
            
            {/* Footer */}
            <div className='mt-auto pt-4 border-t border-gray-200'>
                <button className='w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-200 transition-colors mb-2'>
                    <div className='p-1.5 rounded-md bg-gradient-to-br from-purple-100 to-blue-100'>
                        <IoSparklesOutline className='text-purple-600' size={18} />
                    </div>
                    <span className='text-sm font-medium text-gray-700'>Upgrade to Pro</span>
                </button>
                
                <button 
                    className='w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-200 transition-colors'
                    onClick={() => setShowSettings(true)}
                >
                    <div className='p-1.5 rounded-md bg-gradient-to-br from-amber-100 to-yellow-100'>
                        <IoDiamondOutline className='text-amber-600' size={18} />
                    </div>
                    <span className='text-sm font-medium text-gray-700'>Settings</span>
                </button>
            </div>
        </div>
    );
}

export default SideBar;