import React, {useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import completed from '../../assets/Screenshot 2025-01-07 171330.png'; // Assuming the completed image is imported
import Solutionscreen from '../SolutionScreen/Solutionscreen';

const ConfirmationBox = ({result}) => {
  const imageRef = useRef(null);
  const textRef = useRef(null);
  const [showResults, setShowresults] = useState(false)

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

    const timer = setTimeout(() => {
      setShowresults(true);
    }, 3000);

    // Clean up timeout if component is unmounted
    return () => clearTimeout(timer);
  }, []);

  return (
   <>
      {!showResults ?( <div
        className="ConfirmationBox h-[70%] w-[60%] flex flex-col justify-evenly items-center absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 bg-white"
      >
        {/* Container for the rectangles */}
        <div className="Rectangle-Container relative h-[60%]  w-[100%]  self-center flex justify-center items-center">
          {/* <video className="ConfirmationVideo relative object-cover h-[100%] w-[100%]" height="100%" width="100%" ref={ConfirmationVideo}  autoPlay muted >
            <source src={sampleVideo} type="video/mp4" />
            Your browser does not support the video tag.
          </video> */}
          <img
            ref={imageRef}
            src={completed}
            className="w-full object-contain h-[100%] max-w-full self-center"
            alt="Completion image"
          />
        </div>
  
        <div
          ref={textRef}
          className="Success-text relative  font-bold sm:text-md md:text-xl lg:text-2xl"
        >
          All the pieces are in place – here are the results!
        </div></div>): (<div
      className="ConfirmationBox h-[90%] w-[80%] flex flex-col justify-evenly items-center absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 bg-white"
    ><Solutionscreen result={result}/></div>)}
    </>
  );
};

export default ConfirmationBox;
