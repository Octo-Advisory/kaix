import React from 'react';
import './loader.css'

import logo from '../../assets/New Symbol.png'; // Make sure this path is correct

const LogoLoader = () => {
  return (
    <div className="relative max-w-full max-h-full w-full h-full flex flex-col gap-4 items-center justify-center bg-transparent ">
      {/* Logo */}
      <img
        src={logo}
        alt="Logo"
        className="logo max-w-[80px] max-h-[80px] w-[80px] h-[80px] object-contain z-10 relative"
      />
        <p className='text-[#0e2044] text-xl font-semibold shimmer-text'>Just a Moment !</p>
      {/* Shimmer Overlay */}
      {/* <div className="absolute w-48 h-48 z-20 pointer-events-none overflow-hidden">
        <div className="shimmer-overlay " />
      </div> */}
    </div>
  );
};

export default LogoLoader;
