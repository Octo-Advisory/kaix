import React from 'react';
import './loader.css'

import logo from '../../assets/New Symbol.png'; // Make sure this path is correct

const LogoLoader = ({text}) => {
  return (
    <div className="relative max-w-full max-h-full w-full h-full min-h-screen min-w-screen flex flex-col gap-4 items-center justify-center bg-transparent ">
      {/* Logo */}
      <img
        src={logo}
        alt="Logo"
        className="logo max-w-[80px] max-h-[80px] w-[80px] h-[80px] object-contain z-10 relative"
      />
        <p className='text-[#0e2044] text-xl font-semibold shimmer-text'>{text}</p>
      
    </div>
  );
};

export default LogoLoader;
