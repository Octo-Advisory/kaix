import React, { useState, useEffect } from 'react';
import { useFrappeAuth } from 'frappe-react-sdk';
import { useNavigate } from 'react-router-dom';
import logo from '../../assets/MarsAIX Logo.png';
import { RiFlashlightFill } from 'react-icons/ri';
import { FiUser, FiSettings, FiLogOut, FiChevronDown, FiMenu, FiX } from 'react-icons/fi';
import Settings from '../Settings/Settings';

function Navbar() {
  const [showDropdown, setShowDropdown] = useState(false);
  const [isOpenSettings, setIsOpenSettings] = useState(false);
  const navigate = useNavigate();
  const { currentUser, logout } = useFrappeAuth();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <div className="navbar h-16 w-full flex p-4 items-center pt-10 px-6 justify-between">
      <div className="left flex gap-2 justify-center items-center">
        <img 
          src={logo} 
          alt="MarsAIX Logo" 
          className='h-32 w-40 top-4 left-4 cursor-pointer'
          onClick={() => navigate('/chat')}
        />
      </div>
      
      <div className="right flex items-center gap-4">
        {currentUser ? (
          <div className="relative">
            <button 
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 rounded-full p-2 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white">
                {currentUser.charAt(0).toUpperCase()}
              </div>
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
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => navigate('/signup')}
                  className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-colors shadow-sm flex items-center rounded-lg"
                >
                  <RiFlashlightFill className="mr-2" />
                  Sign Up
                </button>
              </div>
            )}
      </div>

          {isOpenSettings && <Settings onClose = {() => setIsOpenSettings(false)}/>}  
    </div>
  );
}

export default Navbar;  
