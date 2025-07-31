import { motion } from "framer-motion";
import { useState,useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaSyncAlt } from "react-icons/fa";
import { useFrappeGetDocList, useFrappeAuth, useFrappeUpdateDoc } from 'frappe-react-sdk';


const NoResultsFound = () => {
    
    const navigate = useNavigate();
    const { currentUser } = useFrappeAuth();
    const { updateDoc } = useFrappeUpdateDoc("Session");
    const [session, setSession] = useState(null);

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

  const handleBack = async () => {
    if (session) {
    // await clearProgressAndIntention(session)
    window.location.href = `/frontend/chat/${session}`;
  } else {
    window.location.href = `/frontend/chat`;
  }
  };

  return (
    <section className="design-section active bg-white flex items-center justify-center relative overflow-hidden w-screen h-screen">

      {/* Animated geometric shapes - more subtle */}
      <motion.div 
        className="absolute w-64 h-64 bg-[#0e2044] opacity-[80] rounded-full -right-24 -top-24"
        animate={{
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div 
        className="absolute w-96 h-96 bg-[#41b655] opacity-[80] rounded-full -left-48 -bottom-48"
        animate={{
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1
        }}
      />
      
      <div className="z-10 max-w-lg text-center px-6">
        <motion.div 
          className="mb-8 flex justify-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="w-24 h-24 bg-[#0e2044] rounded-xl flex items-center justify-center transform rotate-45">
            <div className="transform -rotate-45 flex items-center justify-center w-full h-full">
              <svg 
                className="w-12 h-12 text-[#41b655]"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </motion.div>
        
        <motion.h1 
          className="text-4xl font-bold text-[#0e2044] mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          No Data Available
        </motion.h1>
        
        <motion.p 
          className="text-gray-600 mb-8 text-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
       No content available at the moment. Kindly reach out to the support team for help.
        </motion.p>
        
        <motion.div 
          className="flex flex-col sm:flex-row justify-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <motion.button
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#0e2044] to-[#41b655] text-white rounded-lg shadow-md hover:scale-105 transition-all"
            onClick={()=>{handleBack()}}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
          >
            <FaArrowLeft /> Back to Chat
          </motion.button>
          
        </motion.div>
      </div>
    </section>
  );
};

export default NoResultsFound;