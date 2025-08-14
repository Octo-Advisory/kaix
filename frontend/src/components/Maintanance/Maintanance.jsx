import { useState, useEffect } from 'react';
import { FaTools, FaHardHat, FaServer, FaEnvelope, FaTwitter, FaInstagram, FaLinkedin } from 'react-icons/fa';
import { motion } from 'framer-motion';

function Maintanance() {
    const [daysLeft, setDaysLeft] = useState(0);
  
    useEffect(() => {
      // Calculate days until launch (example: June 30, 2023)
      const launchDate = new Date('2025-04-30');
      const today = new Date();
      const diffTime = launchDate - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      setDaysLeft(diffDays > 0 ? diffDays : 0);
    }, []);
  
    return (
      <div className="max-h-100vh bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-2xl bg-white rounded-xl shadow-2xl overflow-hidden"
        >
          <div className="p-8 sm:p-10">
            <div className="flex flex-col items-center">
              <motion.div
                animate={{ 
                  rotate: [0, 10, -10, 0],
                  scale: [1, 1.1, 1]
                }}
                transition={{ 
                  repeat: Infinity, 
                  repeatType: "reverse", 
                  duration: 2 
                }}
                className="text-6xl mb-6 text-amber-500"
              >
                <FaTools />
              </motion.div>
  
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-800 mb-2 text-center">
                Site Under Construction
              </h1>
              
              <p className="text-gray-600 text-center mb-8">
                We're building something amazing! Our team is working hard to deliver an exceptional experience.
              </p>
  
              <div className="w-full mb-8">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Progress</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <motion.div 
                    className="h-3 rounded-full bg-gradient-to-r from-amber-400 to-amber-600"
                    initial={{ x: '-100%' }}
                    animate={{ x: '100%' }}
                    transition={{ 
                      repeat: Infinity, 
                      duration: 2,
                      ease: "linear"
                    }}
                    style={{ width: '30%' }}
                  />
                </div>
              </div>
  
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 w-full">
                <div className="bg-amber-50 p-4 rounded-lg border border-amber-100">
                  <div className="flex items-center justify-center mb-2">
                    <FaHardHat className="text-2xl text-amber-500" />
                  </div>
                  <p className="text-center font-medium text-gray-700">Development</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                  <div className="flex items-center justify-center mb-2">
                    <FaServer className="text-2xl text-blue-500" />
                  </div>
                  <p className="text-center font-medium text-gray-700">Testing</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
                  <div className="flex items-center justify-center mb-2">
                    <div className="text-2xl text-purple-500">🚀</div>
                  </div>
                  <p className="text-center font-medium text-gray-700">Launch</p>
                </div>
              </div>
  
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {daysLeft > 0 ? `Estimated launch in ${daysLeft} days` : 'Launching soon!'}
                </h3>
                <p className="text-gray-600">Febuary 30, 2026</p>
              </div>
  
              <div className="flex space-x-4 mb-6">
                <div className="text-gray-500">
                  <FaTwitter className="text-xl" />
                </div>
                <div className="text-gray-500">
                  <FaInstagram className="text-xl" />
                </div>
                <div className="text-gray-500">
                  <FaLinkedin className="text-xl" />
                </div>
              </div>
  
              <div className="flex items-center text-gray-500">
                <FaEnvelope className="mr-2" />
                <span>info@marsbazaar.com</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    );
  };

export default Maintanance;