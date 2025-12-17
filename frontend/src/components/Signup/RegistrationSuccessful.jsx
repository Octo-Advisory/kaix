import { useState, useEffect } from 'react';

const RegistrationSuccessful = () => {
  const [showContactModal, setShowContactModal] = useState(false);

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (showContactModal && e.target.id === 'contactModal') {
        setShowContactModal(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showContactModal]);

  const handleGoToDashboard = () => {
    // Navigate to dashboard - replace with your actual navigation logic
    console.log('Navigating to dashboard...');
    window.location.href = 'https://www.marsbazaar.com/'
    // window.location.href = '#dashboard';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full h-[95%] bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* Success Icon */}
        <div className="mb-6">
          <div className="checkmark-animation w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg 
              className="w-10 h-10 text-green-600" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="3" 
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>
        
        {/* Main Message */}
        <div className="fade-in">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">
            Welcome Aboard! 🎉
          </h1>
          
          <p className="text-gray-600 text-lg mb-6 leading-relaxed">
            We've received your request and our team is already on it! We'll get back to you shortly with all the details you need.
          </p>
          
          {/* Status Info */}
          {/* <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-center mb-2">
              <div className="pulse-gentle w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <span className="text-blue-700 font-medium">Processing your request</span>
            </div>
            <p className="text-blue-600 text-sm">
              Expected response time: 24-48 hours
            </p>
          </div> */}
          
          {/* Next Steps */}
          <div className="text-left bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-gray-800 mb-3">What happens next?</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="text-green-500 mr-2">✓</span>
                Your request has been logged in our system
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">⏳</span>
                Our team will review your information
              </li>
              <li className="flex items-start">
                <span className="text-purple-500 mr-2">📧</span>
                You'll receive an email with next steps
              </li>
            </ul>
          </div>
          
          {/* Action Buttons */}
          <div className="space-y-3">
            <button 
              onClick={handleGoToDashboard}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
            >
              Go to Website
            </button>
            
            <button 
              onClick={() => setShowContactModal(true)}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors duration-200"
            >
              Need Help? Contact Us
            </button>
          </div>
        </div>
      </div>

      {/* Contact Modal */}
      {showContactModal && (
        <div 
          id="contactModal"
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
        >
          <div className="bg-white rounded-xl p-6 max-w-sm w-full">
            <h3 className="text-lg font-semibold mb-4">Get in Touch</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center">
                <span className="text-blue-500 mr-3">📧</span>
                <span>info@marsbazaar.com</span>
              </div>
              <div className="flex items-center">
                <span className="text-green-500 mr-3">📱</span>
                <span>+91 635 892 2814</span>
              </div>
              <div className="flex items-center">
                <span className="text-purple-500 mr-3">💬</span>
                <span>Call between 10AM-6PM</span>
              </div>
            </div>
            <button 
              onClick={() => setShowContactModal(false)}
              className="w-full mt-4 bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .checkmark-animation {
          animation: checkmark 0.6s ease-in-out;
        }
        
        @keyframes checkmark {
          0% {
            transform: scale(0);
            opacity: 0;
          }
          50% {
            transform: scale(1.1);
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }
        
        .fade-in {
          animation: fadeIn 0.8s ease-in-out 0.3s both;
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .pulse-gentle {
          animation: pulseGentle 2s infinite;
        }
        
        @keyframes pulseGentle {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }
      `}</style>
    </div>
  );
};

export default RegistrationSuccessful;