import React, { useState, useEffect } from 'react'
import { IoClose } from "react-icons/io5";
import { useNavigate } from 'react-router-dom';

const SearchContainer = ({ onClose, data }) => {
    const [searchQuery, setSearchQuery] = useState('')
    const [filteredData, setFilteredData] = useState([])
    const navigate = useNavigate()

    
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

    useEffect(() => {
        console.log(data,searchQuery)
    if (!searchQuery.trim()) {
        // If search is empty, show all data without filtering
        setFilteredData(data.filter(item => item.messages && item.messages.length > 0));
        return;
    }

    const result = data.map(historyContent => ({
        ...historyContent,
        messages: Array.isArray(historyContent?.messages)
            ? historyContent.messages.filter(message =>
                message?.title?.toLowerCase?.().includes(searchQuery.toLowerCase())
            )
            : []
    })).filter(historyContent => historyContent.messages.length > 0);
    console.log(result)
    setFilteredData(result);
}, [data, searchQuery]);
// Re-run when data or searchQuery changes

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 w-screen h-screen flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl w-[40%] h-[65vh] overflow-hidden flex flex-col">
                <div className='relative flex flex-row bg-[#0e2044] h-20 items-center justify-between gap-2 p-4'>
                    <input 
                        placeholder='Search Chats...' 
                        type='text' 
                        className='text-lg placeholder:text-gray-300 text-white bg-transparent outline-none p-2 w-full' 
                        value={searchQuery} 
                        onChange={(e) => { setSearchQuery(e.target.value) }} 
                        autoFocus
                    />
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-white hover:bg-opacity-20 transition">
                        <IoClose className="text-xl text-white" />
                    </button>
                </div>
                <div className='relative flex-1 w-full p-2 flex-col items-start overflow-y-auto'>
                    {filteredData.length === 0 ? (
                        <p className="p-4 text-gray-500">No matching chats found</p>
                    ) : (
                        filteredData.map((historyContent, index) => (
                            <div key={index} className='mb-6 last:mb-0'>
                                <div className='flex items-center justify-between mb-2'>
                                    <div className='flex items-center ml-4 gap-2'>
                                        <h2 className='text-md font-semibold text-gray-700 tracking-wider'>
                                            {historyContent.time}
                                        </h2>
                                    </div>
                                </div>

                                <div className='ml-2 flex flex-col gap-2'>
                                    {historyContent.messages.map((message, idx) => {
                                        let date = getDateFromDatetime(message.date)
                                        return (<div 
                                            key={idx}
                                            className='p-3 border border-gray-200 flex flex-row justify-between rounded-lg hover:bg-gray-50 transition-colors cursor-pointer'
                                            onClick={() => {
                                                navigate(`/chat/${message.text}`, { replace: true });
                                                onClose();
                                            }}
                                        >
                                            <p className='text-sm text-gray-600 truncate pr-2' title={message.title}>
                                                {message.title}
                                            </p>
                                            
                                            <div className='relative flex flex-row gap-2 items-center'>
                                            <p className='relative text-xs text-gray-500 pr-2'>{date}</p>
                                            </div>
                                        </div>)
                                })}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}

export default SearchContainer