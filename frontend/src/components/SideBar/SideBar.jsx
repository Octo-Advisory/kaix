import React, { useState, useEffect } from 'react';
import { BiSidebar } from "react-icons/bi";
import { IoSearch } from "react-icons/io5";

const SideBar = ({ setSideBar,sideBar }) => {
    const[history,setHistory] = useState([{'time':'Today', 'messages':['Give me Incentives for Vadodara', 'Give me Approvals required to eat food']}, {'time':'Yesterday', 'messages':['Give me Cement', 'I am Mr Nobody', 'I want to build a company']}, {'time':'Previous 7 days', 'messages':['Give me Cement', 'I am Mr Nobody', 'I want to build a company']}])
  return (
    <div className={`sideBar border-r relative flex flex-col transition-all gap-6 duration-300 ease-in-out bg-gray-100 overflow-hidden justify-start items-center h-full ${sideBar ? 'w-[20%] p-3 opacity-100': 'w-0 p-0 opacity-0'}`}>
            <div className='relative flex flex-row justify-between w-full'>
              <BiSidebar className='text-[#0e2044] relative' size={30} onClick={()=>{setSideBar(false)}}/>
              <IoSearch className='text-[#0e2044] relative' size={30}/>
            </div>
            <button className='w-full py-1 bg-[#41b655] relative text-center text-white text-base rounded-md'>New Chat</button>
            <hr className='relative w-full border border-gray-200'/>
            <div className='relative flex flex-col mt-2 gap-10 items-start w-full'>
              
              {history.map((historyContent,index)=>(
                <div key={index} className='flex flex-col gap-1 relative w-full overflow-hidden'>
                  <h2 className='text-base font-semibold'>{historyContent.time}</h2>
                  {historyContent.messages.map((messages,idx)=>(
                    <p key={idx} className='text-md whitespace-nowrap text-gray-400'>{messages}</p>
                  ))}
                </div>
              ))}
              
            </div>
            <div className='absolute bottom-2 left-0 p-2 w-full flex flex-col gap-3'>
              <hr className='relative w-full border border-gray-200'/>
              <a className='relative rounded-md w-full p-1 text-center cursor-pointer hover:bg-gray-200'>Upgrade Plan</a>
            </div>
        </div>
  );
}

export default SideBar;  
