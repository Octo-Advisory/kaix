import { useFrappeGetDoc } from 'frappe-react-sdk';
import React, { useState, useEffect } from 'react';
import { FaFilePdf, FaRegLightbulb } from 'react-icons/fa';
import { FiUploadCloud, FiCheckCircle, FiMessageCircle } from 'react-icons/fi';

const ProcessFlowAnimation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const steps = ['upload', 'processing', 'result', 'chat'];
  const {data} = useFrappeGetDoc("UI Configuration","UI Configuration")
  console.log("datata os ",data?.bfs_vendor_title);
  
   
  // Step durations in ms
  const stepDurations = [3000, 2500, 3000, 3000];

  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, stepDurations[currentStep]);

    return () => clearTimeout(timer);
  }, [currentStep]);

  return (
    <div className="w-full max-w-2xl mx-auto mb-6">
      {/* Header */}
      <div className="text-center mb-4">
        <h3 className="text-lg md:text-xl font-semibold text-[#0B2152] mb-2 flex items-center justify-center">
          <FaRegLightbulb className="mr-2 text-[#70A1D9]" size={20} />
          How It Works
        </h3>
        <p className="text-gray-600 text-xs md:text-sm mb-3">Our AI-powered analysis process in action</p>
        
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
                  { label: 'Project Summary', delay: '0s', color: 'bg-[#2C53A3]' },
                  { label: 'Required Equipment', delay: '0.2s', color: 'bg-[#E91E63]' },
                  { label: 'Follow-up Queries', delay: '0.4s', color: 'bg-[#4CAF50]' }
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
                      <button className="bg-gradient-to-r from-[#2C53A3] to-[#0B2152] text-white px-2 md:px-3 py-0.5 md:py-1 rounded text-xs hover:from-[#0B2152] hover:to-[#2C53A3] transition-all">
                        View
                      </button>
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
                <span className="text-xs md:text-sm font-semibold text-[#0B2152]">AI Assistant Ready</span>
                <div className="w-2 h-2 bg-[#4CAF50] rounded-full animate-pulse"></div>
              </div>
              
              <div className="space-y-2">
                <div className="bg-gradient-to-r from-[#2C53A3] to-[#0B2152] text-white rounded-lg p-2 md:p-3 text-xs md:text-sm animate-slide-up ml-2 md:ml-4">
                  What are the main risk factors for this project?
                </div>
                
                <div className="flex items-center space-x-2 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-[#70A1D9] rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-[#70A1D9] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-[#70A1D9] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-[#2C53A3] text-xs">AI is analyzing...</span>
                </div>
                
                <div 
                  className="bg-[#F5F9FF] border border-[#70A1D9]/30 rounded-lg p-2 md:p-3 text-xs md:text-sm animate-slide-up mr-2 md:mr-4"
                  style={{ animationDelay: '0.6s' }}
                >
                  <div className="flex items-start">
                    <FaRegLightbulb className="text-[#70A1D9] mr-2 mt-0.5 flex-shrink-0" size={10} />
                    <span className="text-[#0B2152]">Based on your analysis, I've identified 3 key risk factors that require attention...</span>
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