import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { FaXmark } from "react-icons/fa6";

const Failure = () => {
  const imageRef = useRef(null);
  const textRef = useRef(null);
  console.log('..')
  useEffect(() => {
    // Animation for image
    gsap.fromTo(
      imageRef.current,
      { opacity: 0, scale: 0.5 },
      { opacity: 1, scale: 1, duration: 1, ease: 'elastic.out(1, 0.75)' }
    );

    // Animation for text
    gsap.fromTo(
      textRef.current,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8, delay: 0.5, ease: 'power2.out' }
    );
  }, []);

  return (
  <div className='p-4 bg-white flex items-center justify-center h-screen w-screen'>
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
          We couldn't process your data. Please try again or contact support if the issue persists.
        </p>
      </div>
    </div>
   </div>
  )

};

export default Failure;
