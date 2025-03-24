import React from 'react'
import botLogo1 from '../../assets/MarsAIX icon.png';
import { AiFillZhihuCircle } from 'react-icons/ai';

function Responseloader() {
    return (
        <div className="w-full flex gap-5">
             <img src={botLogo1} alt="" className="h-8 w-8 relative rounded-full" />
             <div className="flex flex-col w-[90%] gap-1">
            <hr className="rounded-md border-none bg-gray-200 bg-gradient-to-r from-[#81cafe] via-[#ffffff] to-[#81cafe] p-2 animate-scroll-bg" />
            <hr className="rounded-md border-none bg-gray-200 bg-gradient-to-r from-[#81cafe] via-[#ffffff] to-[#81cafe] p-2 animate-scroll-bg" />
            <hr className="rounded-md w-[50%] border-none bg-gray-200 bg-gradient-to-r from-[#81cafe] via-[#ffffff] to-[#81cafe] p-2 animate-scroll-bg" />
             </div>
        </div>
    )
}

export default Responseloader