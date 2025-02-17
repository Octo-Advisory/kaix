import React from 'react'

function Empresult({result}) {
    console.log("Emp resutl is",result);
  return (
    <div>
      {result['is_error']?(<div className='text-black font-bold'>{result['Analytics_response']}</div>):(<img src={`data:image/png;base64,${result['chart_base64']}`} alt="Generated Chart" className='w-full h-full relative object-contain'/>)}
    </div>
  )
}

export default Empresult
