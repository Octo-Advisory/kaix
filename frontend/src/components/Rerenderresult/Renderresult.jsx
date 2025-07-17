import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux';
import Responseloader from '../Responseloader/Responseloader';
import { useSearchParams } from 'react-router-dom';
import { useFrappeGetDoc } from 'frappe-react-sdk';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Approvalresult from '../ResultScreens/Approvalresult';
import IndustryResultScreen from '../ResultScreens/IndustryResultScreen';
import { jsxs } from 'react/jsx-runtime';
import Vendorresult from '../ResultScreens/Vendorresult';
import Empresult from '../ResultScreens/Empresult';

function Renderresult() {
    const [rederResult, setRederResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [params] = useSearchParams();
    const sessionId = params.get('session');
    const name = params.get('name')
    // console.log("sedsion and name is", sessionId, name);
    const { data } = useFrappeGetDoc("Chat history", name)

    useEffect(() => {
        setLoading(true)
        if(!data) return;
        console.log("Checking intention:", data.intension);
        switch (data.intension) {
            case "Query to search Incentives":
                const result = JSON.parse(data.result)
                setRederResult(<Incentiveresult result={result} source="SolutionScreen" rerender={1} />)
                break;
            case "Query to Get Approvals":
                const result1 = JSON.parse(data.result)
                setRederResult(<Approvalresult result={result1.result} source="SolutionScreen" rerender={1} />)
                break;
            case "Query to build industry from Scratch":
                const result2 = JSON.parse(data.result)
                setRederResult(<IndustryResultScreen result={result2.result} source="SolutionScreen" rerender={1}/>)
                break;
            case "Query to Search Vendors":
                const result3 = JSON.parse(data.result)
                setRederResult(<Vendorresult result={result3.result} source="SolutionScreen" rerender={1}/>)
                break;
            case "Query to Get Employee Search":
                const result4 = JSON.parse(data.result)
                setRederResult(<Empresult  result={result4.result} rerender={1}/>)
                break;
            default:
                break;
        }
        setLoading(false) 
    }, [data])

    return (
        <div>
            {loading && <Responseloader />}
            {rederResult}
        </div>
    )
}

export default Renderresult