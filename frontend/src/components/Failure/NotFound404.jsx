import React from 'react';

const NotFound404 = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans overflow-x-hidden">
      {/* Background grid pattern */}
      <div className="fixed inset-0 z-0 opacity-20">
        <div 
          className="absolute inset-0" 
          style={{ 
            backgroundImage: 'radial-gradient(#4CAF50 1px, transparent 1px)',
            backgroundSize: '30px 30px'
          }}
        ></div>
      </div>
      
      <div className="relative z-10 min-h-screen flex items-center justify-center p-6">
        <div className="max-w-4xl w-full">
          {/* Main content */}
          <div className="flex flex-col md:flex-row items-center">
            {/* Left side: 404 text */}
            <div className="w-full md:w-1/2 mb-12 md:mb-0 md:pr-8">
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-green-900/30 text-green-400 text-sm font-medium mb-6 border border-green-800">
                <div className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></div>
               Invalid Route
              </div>
              
              <h1 className="text-8xl font-bold text-white mb-2 [text-shadow:_0_0_10px_rgba(76,_175,_80,_0.7)]">404</h1>
              <h2 className="text-3xl font-bold text-green-400 mb-6">Oops! Page not found.</h2>
              
              <div className="h-1 w-24 bg-green-500 mb-6"></div>
              
              <p className="text-gray-300 mb-8 text-lg">
                The industrial system cannot locate the requested resource. Please verify your page route or return to the main control panel.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <a 
                  href="/frontend" 
                  className="inline-flex justify-center items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-black bg-green-500 hover:bg-green-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition shadow-lg shadow-green-500/30"
                >
                  <svg className="mr-2 -ml-1 w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  Home
                </a>
                <button 
                  onClick={() => window.history.back()} 
                  className="inline-flex justify-center items-center px-6 py-3 border border-green-500 text-base font-medium rounded-md text-green-500 bg-transparent hover:bg-green-900/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition"
                >
                  <svg className="mr-2 -ml-1 w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Previous Location
                </button>
              </div>
            </div>
            
            {/* Right side: Industrial illustration */}
            <div className="w-full md:w-1/2 relative">
              {/* Scanning line effect */}
              <div className="absolute inset-x-0 h-2 bg-green-500/50 z-20 blur-sm animate-[scan_4s_ease-in-out_infinite]"></div>
              
              {/* Industrial monitor frame */}
              <div className="relative border-4 border-gray-700 rounded-lg p-4 bg-gray-900">
                <div className="absolute top-0 right-0 m-2 flex space-x-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
                </div>
                
                {/* Industrial machinery illustration */}
                <svg className="w-full h-auto" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
                  {/* Background grid */}
                  <pattern id="smallGrid" width="10" height="10" patternUnits="userSpaceOnUse">
                    <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#1e293b" strokeWidth="0.5"/>
                  </pattern>
                  <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
                    <rect width="100" height="100" fill="url(#smallGrid)"/>
                    <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#1e293b" strokeWidth="1"/>
                  </pattern>
                  <rect width="300" height="300" fill="url(#grid)" />
                  
                  {/* Central gear */}
                  <g style={{ transformOrigin: '150px 150px', animation: 'rotate 10s linear infinite' }}>
                    <circle cx="150" cy="150" r="50" fill="none" stroke="#4CAF50" strokeWidth="2"/>
                    <circle cx="150" cy="150" r="40" fill="none" stroke="#4CAF50" strokeWidth="1"/>
                    <path d="M150,100 L150,110 M150,190 L150,200 M100,150 L110,150 M190,150 L200,150 M115,115 L122,122 M178,178 L185,185 M115,185 L122,178 M178,122 L185,115" stroke="#4CAF50" strokeWidth="2"/>
                    <circle cx="150" cy="150" r="10" fill="#4CAF50"/>
                  </g>
                  
                  {/* Warning symbols */}
                  <polygon points="50,60 70,60 60,40" fill="none" stroke="#E91E63" strokeWidth="2"/>
                  <text x="60" y="57" fontFamily="Barlow" fontSize="12" fill="#E91E63" textAnchor="middle">!</text>
                  
                  <polygon points="240,60 260,60 250,40" fill="none" stroke="#E91E63" strokeWidth="2"/>
                  <text x="250" y="57" fontFamily="Barlow" fontSize="12" fill="#E91E63" textAnchor="middle">!</text>
                  
                  {/* Error text */}
                  <text x="150" y="240" fontFamily="Barlow" fontSize="24" fill="#FFFFFF" textAnchor="middle" style={{ animation: 'pulse 2s infinite' }}>ERROR</text>
                  <text x="150" y="265" fontFamily="Barlow" fontSize="18" fill="#4CAF50" textAnchor="middle">RESOURCE NOT FOUND</text>
                  
                  {/* Connection lines */}
                  <line x1="60" y1="60" x2="110" y2="110" stroke="#4CAF50" strokeWidth="1" strokeDasharray="5 3"/>
                  <line x1="250" y1="60" x2="190" y2="110" stroke="#4CAF50" strokeWidth="1" strokeDasharray="5 3"/>
                  
                  {/* Digital elements */}
                  <circle cx="60" cy="60" r="5" fill="#4CAF50" style={{ animation: 'pulse 2s infinite' }}/>
                  <circle cx="250" cy="60" r="5" fill="#4CAF50" style={{ animation: 'pulse 2s infinite' }}/>
                  
                  {/* Binary code */}
                  <text x="40" y="100" fontFamily="monospace" fontSize="10" fill="#4CAF50">01001000</text>
                  <text x="40" y="115" fontFamily="monospace" fontSize="10" fill="#4CAF50">01010100</text>
                  <text x="40" y="130" fontFamily="monospace" fontSize="10" fill="#4CAF50">01010100</text>
                  <text x="40" y="145" fontFamily="monospace" fontSize="10" fill="#4CAF50">01010000</text>
                  
                  <text x="230" y="100" fontFamily="monospace" fontSize="10" fill="#4CAF50">00110100</text>
                  <text x="230" y="115" fontFamily="monospace" fontSize="10" fill="#4CAF50">00110000</text>
                  <text x="230" y="130" fontFamily="monospace" fontSize="10" fill="#4CAF50">00110100</text>
                </svg>
                
                {/* Monitor reflection overlay */}
                <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none"></div>
              </div>
            </div>
          </div>
          
          {/* Bottom status bar */}
          <div className="mt-12 flex items-center justify-between text-xs text-gray-500 border-t border-gray-800 pt-4">
            <div>SYSTEM STATUS: OPERATIONAL</div>
            <div className="flex items-center">
              <div className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></div>
              CONNECTION ACTIVE
            </div>
            <div>ID: 404-ERR-2023</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFound404
