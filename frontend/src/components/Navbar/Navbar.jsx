import React from 'react'
import logo from '../../assets/favicon.png'

function Navbar() {
  return (
    <>
      <div className="navbar h-16 w-full flex p-4 items-center pt-10 px-6">
        <div className="left flex gap-2 justify-center items-center">
          <img src={logo} alt="" className='h-8 w-8 relative'/>
          <h3 className='text-2xl text-[#242f6a]'>Mars 2.0</h3>
        </div>
      </div>
    </>
  )
}

export default Navbar
