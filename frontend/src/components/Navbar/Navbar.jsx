import React, { useState, useEffect } from 'react';
import { useFrappeAuth, useFrappeGetDoc } from 'frappe-react-sdk';
import { useNavigate } from 'react-router-dom';
import logo from '../../assets/MarsAIX Logo.png';
import newlogo from '../../assets/New MarsAIX blue h.png'
import { RiFlashlightFill } from 'react-icons/ri';
import { FiUser, FiSettings, FiLogOut, FiChevronDown, FiMenu, FiX } from 'react-icons/fi';
import Settings from '../Settings/Settings';
import icon from '../../assets/MarsAIX icon.png'
import { BiSidebar } from "react-icons/bi";

const Navbar = ({ setSideBar, sideBar }) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [isOpenSettings, setIsOpenSettings] = useState(false);
  const navigate = useNavigate();
  const { currentUser, logout } = useFrappeAuth();

  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');

  const profileImage = userDoc?.user_image;

  const handleLogout = async () => {
    try {
      await logout();
      sessionStorage.removeItem("guest_session_id")
      navigate('/login');
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <div className="navbar h-16 py-2 w-full flex flex-row items-center pl-2 pr-6 justify-between">
      <div className="relative flex flex-row gap-2 justify-center items-center py-2">
        {!sideBar && currentUser && (
          <BiSidebar onClick={() => setSideBar(true)} className="cursor-pointer" size={30} />
        )}
        <img src={newlogo} className='relative object-contain h-[140px] w-[140px] mix-blend-multiply' />
        {/* <div className='flex relative flex-row '>
          <span className='relative text-[#0e2044] text-2xl font-extrabold'>Mars</span>
          <span className='relative text-[#41b655] text-2xl font-extrabold'>AIX</span>
        </div> */}
      </div>

      <div className="relative flex items-center gap-4">
        {currentUser ? (
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
            >
              {profileImage ? (
                <img
                  src={profileImage}
                  alt="Profile"
                  className="w-11 h-11 rounded-full object-cover relative"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white text-lg">
                  {currentUser.charAt(0).toUpperCase()}
                </div>
              )}
            </button>

            {showDropdown && (
              <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 divide-y divide-gray-100 focus:outline-none z-50">
                <div className="py-1">
                  <button
                    onClick={() => {
                      setIsOpenSettings(true)
                      setShowDropdown(false);
                    }}
                    className="group flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                  >
                    <FiSettings className="mr-3 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
                    Settings
                  </button>
                </div>
                <div className="py-1">
                  <button
                    onClick={handleLogout}
                    className="group flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                  >
                    <FiLogOut className="mr-3 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Sign Up
            </button>
          </div>
        )}
      </div>
      {isOpenSettings && <Settings onClose={() => setIsOpenSettings(false)} />}
    </div>
  );
}

export default Navbar;  
