import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { FaXmark } from "react-icons/fa6";
import completed from '../../assets/cancel.png'; // Assuming the completed image is imported
// import Backtochat from '../Backtochat/Backtochat';

const Failure = () => {
  const imageRef = useRef(null);
  const textRef = useRef(null);

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

  // return (
  //   <div
  //     className="h-[70%] w-[50%] flex flex-col justify-evenly items-center z-20 bg-white"
  //   >
  //     {/* Container for the rectangles */}
  //     <div className="Rectangle-Container relative h-auto sm:h-[70%] md:h-[60%] lg:h-[50%] w-full sm:w-[90%] md:w-[80%] lg:w-[70%] self-center flex justify-center items-center">
  //       {/* <video className="ConfirmationVideo relative object-cover h-[100%] w-[100%]" height="100%" width="100%" ref={ConfirmationVideo}  autoPlay muted >
  //         <source src={sampleVideo} type="video/mp4" />
  //         Your browser does not support the video tag.
  //       </video> */}
  //       <img
  //         ref={imageRef}
  //         src={completed}
  //         className=" object-contain h-[85%] w-[57%] relative"
  //         alt="Completion image"
  //       />
  //     </div>

  //     <div
  //       ref={textRef}
  //       className="Failure-text relative text-2xl font-bold sm:text-xl md:text-2xl lg:text-2xl"
  //     >
  //      Sorry But Something Went Wrong
  //     </div>
  //     {/* <Backtochat/> */}
  //   </div>
  // );
};

export default Failure;
