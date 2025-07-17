import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { useFrappeGetDocList, useFrappeAuth, useFrappeUpdateDoc } from 'frappe-react-sdk';
import { FaXmark } from 'react-icons/fa6';

const FailureScreen = ({text}) => {
  const navigate = useNavigate();

  const messages = "Oops! Something didn't go as planned. Sorry for the Inconvinience"

  const { currentUser } = useFrappeAuth();
  const { updateDoc } = useFrappeUpdateDoc("Session");

  const [session, setSession] = useState(null);
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [forceButton, setForceButton] = useState(false);

  const { data: sessions, isLoading } = useFrappeGetDocList(
    'Session',
    currentUser
      ? {
          fields: ['name'],
          filters: [['owner', '=', currentUser]],
          orderBy: { field: 'modified', order: 'desc' },
          limit: 1,
        }
      : null
  );

  // Set session ID
  useEffect(() => {
    if (sessions && sessions.length > 0) {
      setSession(sessions[0].name);
    }
  }, [sessions]);

  // After 2 seconds, show countdown
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowCountdown(true);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  // Handle countdown
  useEffect(() => {
    if (!showCountdown || forceButton) return;

    if (countdown === 0) {
      handleNavigation();
    } else {
      const interval = setInterval(() => {
        setCountdown(prev => prev - 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [showCountdown, countdown, forceButton]);

  const clearProgressAndIntention = async (chatId) => {
    try {
      await updateDoc('Session', chatId, {
        progress: [],
        user_intension: "",
        session_states: []
      });
    } catch (error) {
      console.error("Error updating session:", error);
    }
  };

  const handleNavigation = async () => {
    if (session) {
    await clearProgressAndIntention(session)
    window.location.href = `/frontend/chat/${session}`;
  } else {
    window.location.href = `/frontend/chat`;
  }
  };

  return (
    <div className="relative w-screen h-screen flex flex-col gap-4 items-center justify-center">
      {/* <p className="text-2xl md:text-3xl font-semibold text-center">{messages}</p> */}
      <div 
            className={`rounded-xl p-6 border border-red-200 text-center bg-red-50 shadow-sm`}
            style={{ animationDelay: '0.3s' }}
          >
            <div className="flex flex-col items-center">
              <div 
                className={`w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-3`}
              >
                <FaXmark className='h-6 w-6 text-red-500'/>
              </div>
              <h3 className="text-xl font-bold text-red-600 mb-2">Something Went Wrong</h3>
              <p 
                className="text-gray-600"
              >
                {messages}
              </p>
            </div>
          </div>

      {(forceButton || !session) && (
        <button
          className="mt-4 px-5 py-2 bg-gradient-to-br from-[#0e2044] to-[#41b655] text-white rounded shadow"
          onClick={() => {
            setForceButton(true);
            handleNavigation();
          }}
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default FailureScreen;
