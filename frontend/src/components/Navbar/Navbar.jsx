import React from 'react'
// import logo from '../../assets/favicon.png'
import logo from '../../assets/MarsAIX Logo.png'

function Navbar() {
  return (
    <>
      <div className="navbar h-16 w-full flex p-4 items-center pt-10 px-6">
        <div className="left flex gap-2 justify-center items-center">
          <img src={logo} alt="" className='h-32 w-40 top-4 left-4'/>
        </div>
      </div>
    </>
  )
}

export default Navbar
