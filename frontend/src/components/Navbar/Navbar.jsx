import React, { useState, useEffect, useContext } from 'react';
import { FrappeContext, useFrappeAuth, useFrappeEventListener, useFrappeGetDoc } from 'frappe-react-sdk';
import { useNavigate } from 'react-router-dom';
import newlogo from '../../assets/New MarsAIX blue h - Edited.png'
import {FiSettings, FiLogOut } from 'react-icons/fi';
import Settings from '../Settings/Settings';
import { FaRegLightbulb } from 'react-icons/fa';
import "../Navbar/Navbar.css"
import FeasibilityStudy from '../Feasibilitystudy/FeasibilityStudy';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Navbar = () => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showFeasibilityModal, setShowFeasibilityModal] = useState(false);
  const [isOpenSettings, setIsOpenSettings] = useState(false);
  const [hasUnseenReport, setHasUnseenReport] = useState(false);

  const navigate = useNavigate();
  const { currentUser, logout } = useFrappeAuth();
  const { call } = useContext(FrappeContext);
  const { data: userDoc } = useFrappeGetDoc('User', currentUser || '');

  const profileImage = userDoc?.user_image;

  // Check for unseen reports when component mounts or user changes
  useEffect(() => {
    if (currentUser) {
      checkForUnseenReports();
    }
  }, [currentUser]);

  // Function to check for unseen feasibility reports
  const checkForUnseenReports = async () => {
    if (!currentUser) return;

    try {
      const unseenCheck = await call.get("frappe.client.get_list", {
        doctype: "Feasibility Report",
        filters: {
          owner: ["=", currentUser],
          status: ["=", "Complete", "Fail"],
          seen_by_user: ["=", 0]
        },
        fields: ["name"],
        limit_page_length: 1
      });

      if (unseenCheck.message && unseenCheck.message.length > 0) {
        setHasUnseenReport(true);
      } else {
        setHasUnseenReport(false);
      }
    } catch (error) {
      console.error("Error checking for unseen reports:", error);
    }
  };

  // Toggle Feasibility Modal
  const toggleFeasibilityModal = () => {
    setShowFeasibilityModal(!showFeasibilityModal);
  };

  const handleLogout = async () => {
    try {
      await logout();
      sessionStorage.removeItem("guest_session_id")
      navigate('/login');
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  useFrappeEventListener("feasibility_analysis_done", (data) => {
    console.log("📡 Received event data:", data);
    if(showFeasibilityModal) return;

    const toastId = toast.success("Feasibility Process is Completed! Check result.", {
      position: "top-center",
      autoClose: 8000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      // onClick: function () {
      //   setShowFeasibilityModal(true);
      //   setHasUnseenReport(true);
      //   toast.dismiss();
      // },
    });
  });

  return (
    <>
      <div className="navbar h-16 py-2 w-full flex flex-row items-center pl-1 pr-6 justify-between">
        <div className="relative flex flex-row gap-2 justify-center items-center py-2">
            <img src={newlogo} className='relative object-contain h-[120px] w-[120px] -top-2 mix-blend-multiply'  />
        </div>

        <div className="relative flex items-center gap-4">
          {/* Enhanced Feasibility Study Button */}
          {currentUser && (
            <div className="relative">
              <button
                onClick={toggleFeasibilityModal}
                className="flex items-center gap-2 bg-[#2C53A3] hover:bg-[#0B2152] text-white px-4 py-2 rounded-md transition-colors group relative"
              >
                <FaRegLightbulb className="mr-1" />
                Feasibility Report

                {/* Enhanced Red Indicator with better styling */}
                {hasUnseenReport && (
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 border-2 border-white rounded-full animate-pulse shadow-lg"></span>
                )}

                <div className="absolute hidden group-hover:block top-full mt-2 left-0 w-64 bg-white text-gray-800 p-3 rounded-lg shadow-lg z-50 border border-gray-200">
                  <h4 className="font-medium text-[#0B2152] mb-1">AI-Powered Feasibility Analysis</h4>
                  <p className="text-xs text-gray-600">
                    Upload project documents to receive instant AI-generated feasibility reports with key insights and recommendations.
                  </p>
                  {hasUnseenReport && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                      <strong>New report available!</strong> Click to view your latest analysis.
                    </div>
                  )}
                </div>
              </button>
            </div>
          )}

          {/* Enhanced Feasibility Study Modal */}
          {showFeasibilityModal && (
            <FeasibilityStudy
              isOpen={showFeasibilityModal}
              onClose={toggleFeasibilityModal}
              hasUnseenReport={hasUnseenReport}
              setHasUnseenReport={setHasUnseenReport}
            />
          )}

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

      <ToastContainer
        position="top-right"
        autoClose={8000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
        className="mt-16"
      />
    </>
  );
}

export default Navbar;