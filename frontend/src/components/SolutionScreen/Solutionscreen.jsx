import React from 'react'

function Solutionscreen({result}) {
    console.log("final result",result)
  return (
    <div className='w-full h-full flex items-center justify-center'>
      {/* Solution is here!! */}
      {result['is_error']?(<div className='text-black font-bold'>{result['Analytics_response']}</div>):(<img src={`data:image/png;base64,${result['chart_base64']}`} alt="Generated Chart" className='w-full h-full relative object-contain'/>)}
    </div>
  )
}

export default Solutionscreen
