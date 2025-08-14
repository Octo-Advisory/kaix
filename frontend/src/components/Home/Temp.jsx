// import React, { useEffect, useRef, useReducer } from "react";
// import ReactMarkdown from "react-markdown";
// import rehypeRaw from "rehype-raw";

// export default function TypewriterWithStaticUI() {
//   const markdownText = `
// # 👋 Hello

// This is a **typewriter effect** inside _ReactMarkdown_.

// - Bullet 1
// - Bullet 2

// > "Let the markdown flow..."
// `;

//   return (
//     <div className="p-6 max-w-3xl mx-auto border rounded shadow">
//       <h1 className="text-2xl font-bold">Parent UI</h1>
//       <p className="mb-4 text-gray-600">This part of the UI does not re-render.</p>

//       {/* Typewriter subcomponent */}
//       <MarkdownTyper markdownText={markdownText} />
//     </div>
//   );
// }

// const MarkdownTyper = React.memo(function MarkdownTyper({ markdownText }) {
//   const textRef = useRef("");
//   const indexRef = useRef(0);
//   const [, forceUpdate] = useReducer((x) => x + 1, 0);

//   useEffect(() => {
//     const interval = setInterval(() => {
//       if (indexRef.current < markdownText.length) {
//         textRef.current += markdownText[indexRef.current];
//         indexRef.current++;
//         forceUpdate(); // trigger rerender only here
//       } else {
//         clearInterval(interval);
//       }
//     }, 20);

//     return () => clearInterval(interval);
//   }, [markdownText]);

//   return (
//     <div className="mt-6 p-4 bg-white rounded border shadow">
//       <ReactMarkdown rehypePlugins={[rehypeRaw]}>
//         {textRef.current}
//       </ReactMarkdown>
//     </div>
//   );
// });
import React from 'react';
import { FaHome, FaArrowLeft } from 'react-icons/fa';

const NotFoundPage = () => {
  const handleGoBack = () => {
    window.history.back();
  };

  return (
    <div className="min-h-screen bg-[#0B2152] relative overflow-hidden font-['Inter']">
      {/* Grid Background */}
      <div 
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(44, 83, 163, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(44, 83, 163, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      ></div>
      
      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center px-4 py-12">
        <div className="text-center">
          {/* 404 Text */}
          <h1 className="text-[150px] md:text-[200px] font-bold text-[#70A1D9]/20 leading-none">404</h1>
          
          <div className="mt-[-60px] md:mt-[-80px] relative z-20">
            {/* Industrial Illustration */}
            <div className="flex justify-center mb-8">
              <svg className="w-64 h-48" viewBox="0 0 240 120" xmlns="http://www.w3.org/2000/svg">
                {/* Factory silhouette */}
                <rect x="20" y="70" width="200" height="50" fill="#0B2152" stroke="#2C53A3" strokeWidth="1"/>
                
                {/* Factory buildings */}
                <rect x="30" y="40" width="20" height="30" fill="#2C53A3"/>
                <rect x="60" y="50" width="20" height="20" fill="#2C53A3"/>
                <rect x="90" y="30" width="20" height="40" fill="#2C53A3"/>
                <rect x="120" y="45" width="30" height="25" fill="#2C53A3"/>
                <rect x="160" y="35" width="15" height="35" fill="#2C53A3"/>
                <rect x="185" y="55" width="25" height="15" fill="#2C53A3"/>
                
                {/* Chimneys */}
                <rect x="35" y="20" width="10" height="20" fill="#2C53A3"/>
                <rect x="95" y="10" width="10" height="20" fill="#2C53A3"/>
                <rect x="165" y="15" width="8" height="20" fill="#2C53A3"/>
                
                {/* Windows with pulse animation */}
                <rect x="35" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="55" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="75" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="95" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="115" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="135" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="155" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="175" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                <rect x="195" y="80" width="10" height="10" fill="#70A1D9" className="opacity-60 animate-pulse"/>
                
                {/* Land */}
                <path d="M0,120 L240,120 L240,100 C220,105 200,95 180,100 C160,105 140,95 120,100 C100,105 80,95 60,100 C40,105 20,95 0,100 Z" fill="#4CAF50"/>
                
                {/* Digital elements */}
                <circle cx="35" cy="25" r="2" fill="#E91E63" className="opacity-60 animate-pulse"/>
                <circle cx="95" cy="15" r="2" fill="#E91E63" className="opacity-60 animate-pulse"/>
                <circle cx="165" cy="20" r="2" fill="#E91E63" className="opacity-60 animate-pulse"/>
              </svg>
            </div>
            
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Page Not Found</h2>
            
            <p className="text-[#70A1D9] mb-8 max-w-md mx-auto">
              The industrial solution you're looking for cannot be found. Please check the URL or navigate back to the dashboard.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="/" 
                className="inline-flex justify-center items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-[#4CAF50] hover:bg-[#3d8b40] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4CAF50] transition-colors duration-300"
              >
                <FaHome className="mr-2 -ml-1 w-5 h-5" />
                Return to Dashboard
              </a>
              <button 
                onClick={handleGoBack} 
                className="inline-flex justify-center items-center px-6 py-3 border border-[#2C53A3] text-base font-medium rounded-md text-white bg-transparent hover:bg-[#2C53A3]/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2C53A3] transition-colors duration-300"
              >
                <FaArrowLeft className="mr-2 -ml-1 w-5 h-5" />
                Go Back
              </button>
            </div>
          </div>
          
          {/* AI Element (Separate from industrial) */}
          <div className="absolute bottom-4 right-4 md:bottom-8 md:right-8">
            <svg className="w-16 h-16 md:w-24 md:h-24" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              {/* Circuit board pattern */}
              <rect x="10" y="10" width="80" height="80" fill="none" stroke="#70A1D9" strokeWidth="1" strokeDasharray="4 2"/>
              <circle cx="20" cy="20" r="3" fill="#70A1D9"/>
              <circle cx="80" cy="20" r="3" fill="#70A1D9"/>
              <circle cx="20" cy="80" r="3" fill="#70A1D9"/>
              <circle cx="80" cy="80" r="3" fill="#70A1D9"/>
              <circle cx="50" cy="50" r="5" fill="#E91E63" className="opacity-60 animate-pulse"/>
              <line x1="20" y1="20" x2="50" y2="50" stroke="#70A1D9" strokeWidth="1"/>
              <line x1="80" y1="20" x2="50" y2="50" stroke="#70A1D9" strokeWidth="1"/>
              <line x1="20" y1="80" x2="50" y2="50" stroke="#70A1D9" strokeWidth="1"/>
              <line x1="80" y1="80" x2="50" y2="50" stroke="#70A1D9" strokeWidth="1"/>
            </svg>
          </div>
          
          {/* Footer */}
          <div className="absolute bottom-4 left-0 right-0 text-center text-[#70A1D9]/60 text-sm">
            <p>© {new Date().getFullYear()} Industrial AI Solutions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;