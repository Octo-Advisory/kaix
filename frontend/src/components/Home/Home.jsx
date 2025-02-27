import React, { useContext, useEffect, useState } from 'react';
import { gsap } from 'gsap'; // Import GSAP for animations
import logo2 from '../../assets/logo2.png'; // Company logo
import marsBg from '../../assets/mars-bg.jpg'; // Background image
import Chatscreen from '../Chatscreen/Chatscreen';
import { useSelector } from 'react-redux';
import { FrappeContext } from 'frappe-react-sdk';
import Test from '../TestComponent/Test';
import TestComponent from '../TestComponent/TestComponent';
// import { useFrappeDocumentEventListener } from 'frappe-react-sdk';

function Home() {
  const [stage, setStage] = useState(1);

  useEffect(() => {
    if (stage === 0) {
      // GSAP animation for the logo when the stage is 0
      gsap.fromTo(
        ".logo", // Targeting the logo element
        { opacity: 0, y: 0, scale: 0.4 }, // Initial properties
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 3, // Duration of the animation
          ease: "power3.out", // Easing for smooth transition
          onComplete: () => {
            // After the animation completes, wait for 1 second and then change the stage
            setTimeout(() => setStage(1), 1000);
          },
        }
      );
    }
  }, [stage]); // This effect will run every time `stage` changes

  return (
    <>
    {stage === 0 ? (<div className='h-screen w-full flex justify-center items-center bg-cover bg-center' style={{backgroundImage : `url(${marsBg})`}}>
      <div className="logo-container">
        <img src={logo2} alt="" className='logo h-56 w-full relative'/>
      </div>
    </div>):(<Chatscreen />)}
      {/* <Test/> */}
      {/* <TestComponent/> */}
    </>
  );
}

export default Home;