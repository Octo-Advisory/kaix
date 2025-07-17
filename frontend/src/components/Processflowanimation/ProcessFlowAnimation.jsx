// import React, { useState, useEffect } from 'react';

// const ProcessFlowAnimation = () => {
//   const [currentStep, setCurrentStep] = useState(0);
//   const steps = ['upload', 'processing', 'result', 'chat'];
  
//   // Step durations in ms
//   const stepDurations = [3000, 2500, 3000, 3000];

//   useEffect(() => {
//     const timer = setTimeout(() => {
//       setCurrentStep((prev) => (prev + 1) % steps.length);
//     }, stepDurations[currentStep]);

//     return () => clearTimeout(timer);
//   }, [currentStep]);

//   return (
//     <div className="w-full max-w-md mx-auto bg-white rounded-2xl shadow-lg p-6 h-96 flex flex-col">
//       {/* Header with progress indicator */}
//       <div className="text-center mb-6">
//         <h3 className="text-lg font-semibold text-gray-800">Document Analysis Process</h3>
//         <div className="flex justify-center mt-3 space-x-2">
//           {steps.map((_, index) => (
//             <div
//               key={index}
//               className={`h-1.5 w-8 rounded-full transition-all duration-300 ${
//                 index === currentStep ? 'bg-blue-500' : 'bg-gray-200'
//               }`}
//             />
//           ))}
//         </div>
//       </div>

//       {/* Animation Container */}
//       <div className="flex-1 relative overflow-hidden">
//         {/* Upload Step */}
//         {currentStep === 0 && (
//           <div className="h-full flex flex-col items-center justify-center p-4 animate-fade">
//             <div className="relative mb-6">
//               <div className="w-20 h-20 border-2 border-dashed border-blue-300 rounded-xl flex items-center justify-center">
//                 <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
//                 </svg>
//               </div>
//               <div className="absolute -top-2 -right-2">
//                 <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center animate-ping opacity-75"></div>
//               </div>
//             </div>
//             <p className="text-gray-700 font-medium mb-1">Upload Document</p>
//             <p className="text-gray-500 text-sm">Drag & drop your PDF file</p>
//           </div>
//         )}

//         {/* Processing Step */}
//         {currentStep === 1 && (
//           <div className="h-full flex flex-col items-center justify-center p-4 animate-fade">
//             <div className="relative mb-6">
//               <div className="w-16 h-16 border-4 border-blue-100 border-t-blue-500 rounded-full animate-spin"></div>
//               <div className="absolute inset-0 flex items-center justify-center">
//                 <svg className="w-6 h-6 text-blue-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
//                 </svg>
//               </div>
//             </div>
//             <p className="text-gray-700 font-medium mb-1">Analyzing Content</p>
//             <p className="text-gray-500 text-sm">Extracting key insights...</p>
//             <div className="w-48 h-1 bg-gray-200 rounded-full mt-4 overflow-hidden">
//               <div className="h-full bg-blue-500 rounded-full animate-progress"></div>
//             </div>
//           </div>
//         )}

//         {/* Result Step */}
//         {currentStep === 2 && (
//           <div className="h-full flex flex-col items-center justify-center p-4 animate-fade">
//             <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm w-full max-w-xs">
//               <div className="flex items-center justify-between mb-3">
//                 <h4 className="font-medium text-gray-800">Analysis Results</h4>
//                 <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
//                   <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
//                   </svg>
//                 </div>
//               </div>
              
//               <div className="space-y-2">
//                 {['Market Analysis', 'Financial Data', 'Risk Factors'].map((item, index) => (
//                   <div 
//                     key={item}
//                     className="bg-gray-50 border border-gray-200 rounded-lg p-2 animate-slide-up"
//                     style={{ animationDelay: `${index * 0.2}s` }}
//                   >
//                     <div className="flex items-center justify-between">
//                       <span className="text-sm text-gray-700">{item}</span>
//                       <button className="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs transition-colors">
//                         Query
//                       </button>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </div>
//           </div>
//         )}

//         {/* Chat Step */}
//         {currentStep === 3 && (
//           <div className="h-full flex flex-col items-center justify-center p-4 animate-fade">
//             <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm w-full max-w-xs">
//               <div className="flex items-center space-x-2 mb-3">
//                 <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
//                 </svg>
//                 <span className="text-sm font-medium text-gray-700">AI Assistant</span>
//                 <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
//               </div>
              
//               <div className="space-y-3">
//                 <div className="bg-blue-500 text-white rounded-lg p-2 text-sm animate-slide-up">
//                   Tell me about the risk factors
//                 </div>
                
//                 <div className="flex items-center space-x-1 animate-slide-up" style={{ animationDelay: '0.3s' }}>
//                   <div className="flex space-x-1">
//                     <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
//                     <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
//                     <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
//                   </div>
//                   <span className="text-gray-500 text-xs">AI is typing...</span>
//                 </div>
                
//                 <div 
//                   className="bg-gray-50 border border-gray-200 rounded-lg p-2 text-sm animate-slide-up"
//                   style={{ animationDelay: '0.6s' }}
//                 >
//                   The analysis shows 3 main risk factors that need attention...
//                 </div>
//               </div>
//             </div>
//           </div>
//         )}
//       </div>

//       {/* Footer */}
//       <div className="text-center mt-4">
//         <p className="text-xs text-gray-500">
//           {currentStep === 0 && 'Step 1: Upload your document'}
//           {currentStep === 1 && 'Step 2: AI processing your file'}
//           {currentStep === 2 && 'Step 3: Review analysis results'}
//           {currentStep === 3 && 'Step 4: Chat with AI assistant'}
//         </p>
//       </div>

//       {/* Animation Styles */}
//       <style jsx>{`
//         @keyframes fade {
//           from { opacity: 0; transform: translateY(10px); }
//           to { opacity: 1; transform: translateY(0); }
//         }
        
//         @keyframes progress {
//           from { width: 0%; }
//           to { width: 100%; }
//         }
        
//         @keyframes slide-up {
//           from { opacity: 0; transform: translateY(10px); }
//           to { opacity: 1; transform: translateY(0); }
//         }
        
//         @keyframes bounce {
//           0%, 100% { transform: translateY(0); }
//           50% { transform: translateY(-5px); }
//         }
        
//         .animate-fade {
//           animation: fade 0.5s ease-out;
//         }
        
//         .animate-progress {
//           animation: progress 2s ease-out;
//         }
        
//         .animate-slide-up {
//           animation: slide-up 0.5s ease-out forwards;
//         }
        
//         .animate-bounce {
//           animation: bounce 1.5s infinite;
//         }
//       `}</style>
//     </div>
//   );
// };

// export default ProcessFlowAnimation;
import React, { useState, useEffect } from 'react';
import { FaFilePdf, FaRegLightbulb } from 'react-icons/fa';
import { FiUploadCloud, FiCheckCircle, FiMessageCircle } from 'react-icons/fi';

const ProcessFlowAnimation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const steps = ['upload', 'processing', 'result', 'chat'];
  
  // Step durations in ms
  const stepDurations = [3000, 2500, 3000, 3000];

  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, stepDurations[currentStep]);

    return () => clearTimeout(timer);
  }, [currentStep]);

  return (
    <div className="w-full max-w-2xl mx-auto mb-3">
      {/* Header */}
      <div className="text-center mb-4">
        <h3 className="text-lg md:text-xl font-semibold text-[#0B2152] mb-2 flex items-center justify-center">
          <FaRegLightbulb className="mr-2 text-[#70A1D9]" size={20} />
          How It Works
        </h3>
        {/* <p className="text-gray-600 text-xs md:text-sm mb-3">Our AI-powered analysis process in action</p> */}
        
        {/* Progress Steps */}
        <div className="flex justify-center items-center space-x-2 md:space-x-4 mb-4">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div className={`w-6 h-6 md:w-8 md:h-8 rounded-full border-2 flex items-center justify-center text-xs font-medium transition-all duration-500 ${
                index === currentStep 
                  ? 'bg-[#2C53A3] border-[#2C53A3] text-white' 
                  : index < currentStep 
                    ? 'bg-[#4CAF50] border-[#4CAF50] text-white'
                    : 'bg-white border-[#70A1D9] text-[#70A1D9]'
              }`}>
                {index < currentStep ? '✓' : index + 1}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-8 md:w-12 h-0.5 mx-1 md:mx-2 transition-all duration-500 ${
                  index < currentStep ? 'bg-[#4CAF50]' : 'bg-[#70A1D9]/30'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Animation Container - Responsive Height */}
      <div className="bg-[#F5F9FF] border border-[#70A1D9]/30 rounded-xl p-4 md:p-6 min-h-[200px] max-h-[250px] flex flex-col justify-center">
        
        {/* Upload Step */}
        {currentStep === 0 && (
          <div className="flex flex-col items-center justify-center text-center animate-fade-in py-4">
            <div className="relative mb-4">
              <div className="w-16 h-16 md:w-20 md:h-20 border-2 border-dashed border-[#70A1D9] rounded-xl flex items-center justify-center bg-white shadow-sm">
                <FiUploadCloud className="text-[#2C53A3] animate-bounce" size={24} />
              </div>
              <div className="absolute -top-1 -right-1">
                <div className="w-4 h-4 md:w-6 md:h-6 bg-[#4CAF50] rounded-full flex items-center justify-center animate-ping opacity-75">
                  <div className="w-2 h-2 md:w-3 md:h-3 bg-[#4CAF50] rounded-full"></div>
                </div>
              </div>
            </div>
            <h4 className="text-base md:text-lg font-semibold text-[#0B2152] mb-2">Upload Document</h4>
            <p className="text-sm text-[#2C53A3] max-w-xs px-2">
              Drag & drop your PDF file or browse to select your feasibility study document
            </p>
          </div>
        )}

        {/* Processing Step */}
        {currentStep === 1 && (
          <div className="flex flex-col items-center justify-center text-center animate-fade-in py-4">
            <div className="relative mb-4">
              <div className="w-16 h-16 md:w-20 md:h-20 border-4 border-[#70A1D9]/30 border-t-[#2C53A3] rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <FaRegLightbulb className="text-[#2C53A3] animate-pulse" size={20} />
              </div>
            </div>
            <h4 className="text-base md:text-lg font-semibold text-[#0B2152] mb-2">AI Analysis in Progress</h4>
            <p className="text-sm text-[#2C53A3] max-w-xs px-2 mb-3">
              Our advanced AI is extracting key insights and structuring your data
            </p>
            <div className="w-48 md:w-64 h-1.5 md:h-2 bg-[#70A1D9]/30 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-[#2C53A3] to-[#4CAF50] rounded-full animate-progress"></div>
            </div>
          </div>
        )}

        {/* Result Step */}
        {currentStep === 2 && (
          <div className="flex flex-col items-center justify-center animate-fade-in py-2">
            <div className="bg-white border border-[#70A1D9]/30 rounded-xl p-3 md:p-4 shadow-sm w-full max-w-xs md:max-w-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-[#0B2152] flex items-center text-sm md:text-base">
                  <FaFilePdf className="text-red-500 mr-2" size={14} />
                  Analysis Complete
                </h4>
                <div className="w-5 h-5 md:w-6 md:h-6 bg-[#4CAF50] rounded-full flex items-center justify-center">
                  <FiCheckCircle className="text-white" size={12} />
                </div>
              </div>
              
              <div className="space-y-2">
                {[
                  { label: 'Build From Scratch', delay: '0s', color: 'bg-[#2C53A3]' },
                  { label: 'Incetives', delay: '0.2s', color: 'bg-[#E91E63]' },
                  { label: 'Approvals', delay: '0.4s', color: 'bg-[#4CAF50]' }
                ].map((item, index) => (
                  <div 
                    key={item.label}
                    className="bg-[#F5F9FF] border border-[#70A1D9]/30 rounded-lg p-2 md:p-3 animate-slide-up"
                    style={{ animationDelay: item.delay }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className={`w-2 h-2 ${item.color} rounded-full mr-2 md:mr-3`}></div>
                        <span className="text-xs md:text-sm text-[#0B2152] font-medium">{item.label}</span>
                      </div>
                      {/* <button className="bg-gradient-to-r from-[#2C53A3] to-[#0B2152] text-white px-2 md:px-3 py-0.5 md:py-1 rounded text-xs hover:from-[#0B2152] hover:to-[#2C53A3] transition-all">
                        View
                      </button> */}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chat Step */}
        {currentStep === 3 && (
          <div className="flex flex-col items-center justify-center animate-fade-in py-2">
            <div className="bg-white border border-[#70A1D9]/30 rounded-xl p-3 md:p-4 shadow-sm w-full max-w-xs md:max-w-sm">
              <div className="flex items-center space-x-2 mb-3">
                <FiMessageCircle className="text-[#2C53A3]" size={14} />
                <span className="text-xs md:text-sm font-semibold text-[#0B2152]">MarsAIX Chat screen</span>
                <div className="w-2 h-2 bg-[#4CAF50] rounded-full animate-pulse"></div>
              </div>
              
              <div className="space-y-2">
                <div className="bg-gradient-to-r from-[#2C53A3] to-[#0B2152] text-white rounded-lg p-2 md:p-3 text-xs md:text-sm animate-slide-up ml-2 md:ml-4">
                 I want to build 1TPA cement factory
                </div>
                
                <div className="flex items-center space-x-2 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-[#70A1D9] rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-[#70A1D9] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-[#70A1D9] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-[#2C53A3] text-xs">AI is replying...</span>
                </div>
                
                <div 
                  className="bg-[#F5F9FF] border border-[#70A1D9]/30 rounded-lg p-2 md:p-3 text-xs md:text-sm animate-slide-up mr-2 md:mr-4"
                  style={{ animationDelay: '0.6s' }}
                >
                  <div className="flex items-start">
                    <FaRegLightbulb className="text-[#70A1D9] mr-2 mt-0.5 flex-shrink-0" size={10} />
                    <span className="text-[#0B2152]">Based on your analysis, I've identified key Quries...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}  
      </div>

      {/* Footer */}
      <div className="text-center mt-4">
        <p className="text-sm text-[#2C53A3] font-medium">
          {currentStep === 0 && 'Step 1: Upload your document'}
          {currentStep === 1 && 'Step 2: AI processing your file'}
          {currentStep === 2 && 'Step 3: Review analysis results'}
          {currentStep === 3 && 'Step 4: Chat with AI assistant'}
        </p>
      </div>

      {/* Animation Styles */}
      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes progress {
          from { width: 0%; }
          to { width: 100%; }
        }
        
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(15px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
        
        .animate-fade-in {
          animation: fade-in 0.6s ease-out;
        }
        
        .animate-progress {
          animation: progress 2s ease-out;
        }
        
        .animate-slide-up {
          animation: slide-up 0.5s ease-out forwards;
          opacity: 0;
        }
        
        .animate-bounce {
          animation: bounce 2s infinite;
        }
      `}</style>
    </div>
  );
};

export default ProcessFlowAnimation;
