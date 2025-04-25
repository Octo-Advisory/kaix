import React, { useContext, useEffect, useState } from 'react';
import { gsap } from 'gsap'; // Import GSAP for animations
import logo2 from '../../assets/logo2.png'; // Company logo
import marsBg from '../../assets/mars-bg.jpg'; // Background image
import Chatscreen from '../Chatscreen/Chatscreen';
import { useSelector } from 'react-redux';
import { FrappeContext } from 'frappe-react-sdk';
import Test from '../TestComponent/Test';
import TestComponent from '../TestComponent/TestComponent';
import MapComponent from '../MapComponent/MapComponent';
import Industryresult from '../ResultScreens/Industryresult';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Vendorresult from '../ResultScreens/Vendorresult';
import Approvalresult from '../ResultScreens/Approvalresult';
import Maintanance from '../Maintanance/Maintanance';
import Login from '../Login/Login';
// import Temp from './Temp';
// import { useFrappeDocumentEventListener } from 'frappe-react-sdk';

function Home() {
  return (
    <>
    <Chatscreen />
    {/* <MapComponent/> */}
      {/* <Vendorresult /> */}
      {/* <Incentiveresult /> */}
      {/* <Industryresult /> */}
      {/* <Approvalresult /> */}
      {/* <Login/> */}
      {/* <Maintanance/> */}
      {/* <Temp /> */}
    </>
  );
}

export default Home;