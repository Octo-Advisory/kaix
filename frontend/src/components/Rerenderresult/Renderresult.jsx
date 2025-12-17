// import React, { useEffect, useState } from 'react'
// import { useDispatch, useSelector } from 'react-redux';
// import { useNavigate, useSearchParams } from 'react-router-dom';
import { FrappeContext, useFrappeAuth, useFrappeGetDoc } from 'frappe-react-sdk';
import Incentiveresult from '../ResultScreens/Incentiveresult';
import Approvalresult from '../ResultScreens/Approvalresult';
import IndustryResultScreen from '../ResultScreens/IndustryResultScreen';
import { jsxs } from 'react/jsx-runtime';
import Vendorresult from '../ResultScreens/Vendorresult';
import Empresult from '../ResultScreens/Empresult';
// import LogoLoader from '../Responseloader/LogoLoader';

// function Renderresult() {
//     const [rederResult, setRederResult] = useState(null)
//     const [loading, setLoading] = useState(false)
//     const [params] = useSearchParams();
//     const sessionId = params.get('session');
//     const name = params.get('name')
//     // console.log("sedsion and name is", sessionId, name);
//     const { data } = useFrappeGetDoc("Chat history", name)

//     useEffect(() => {
//         setLoading(true)
//         if(!data) return;
//         console.log("Checking intention:", data.intension);
//         switch (data.intension) {
//             case "Query to search Incentives":
//                 const result = JSON.parse(data.result)
//                 setRederResult(<Incentiveresult res={result} source="SolutionScreen" rerender={1} />)
//                 break;
//             case "Query to Get Approvals":
//                 const result1 = JSON.parse(data.result)
//                 setRederResult(<Approvalresult result={result1.result} source="SolutionScreen" rerender={1} />)
//                 break;
//             case "Query to build industry from Scratch":
//                 const result2 = JSON.parse(data.result)
//                 setRederResult(<IndustryResultScreen result={result2.result} source="SolutionScreen" rerender={1}/>)
//                 break;
//             case "Query to Search Vendors":
//                 const result3 = JSON.parse(data.result)
//                 setRederResult(<Vendorresult result={result3.result} source="SolutionScreen" rerender={1}/>)
//                 break;
//             case "Query to Get Employee Search":
//                 const result4 = JSON.parse(data.result)
//                 setRederResult(<Empresult  result={result4.result} rerender={1}/>)
//                 break;
//             default:
//                 break;
//         }
//         setLoading(false) 
//     }, [data])

//     return (
//         <div>
//             {loading && <LogoLoader text={"Loading..."} />}
//             {rederResult}
//         </div>
//     )
// }

// export default Renderresult
import React, { useContext, useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FaExclamationTriangle, FaSignInAlt, FaHome, FaArrowLeft, FaInfoCircle } from 'react-icons/fa';
import { MdOutlineEmojiObjects } from 'react-icons/md';
import LogoLoader from '../Responseloader/LogoLoader';


function Renderresult() {
  const {call} = useContext(FrappeContext)
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const name = params.get('name');

  const [isLoading, setIsLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  const [chatDoc, setChatDoc] = useState(null);
  const [renderResult, setRenderResult] = useState(null);
  const [error, setError] = useState(null);

   const retrieveData = async (data) => {
  
    try {

      const convertJson = await call.post("frontend_app.Management_Class.helpers.utility.retrieve_and_decompress", {
        compressed_data: data,
      },
      {
          headers: {
            'Expect': '' // 👈 Clear problematic header
          }
      }
    )
    // console.log(convertJson, 'this is the msg');
    return {
      "result": convertJson.message
    }
    } catch (err) {
      // console.error("Error Storing Result json:", err);
      // createDiagnostic("Land & Approvals", `Something went wrong while storing the result json ${JSON.stringify(err)} in Build From Scratch`,lastChatId)
      return []; // Return empty for this batch on error
    }
  }

  useEffect(() => {
    const validateSessionAndFetch = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // 1. Get the logged-in user from Frappe
        const userRes = await fetch('/api/method/frappe.auth.get_logged_user', {
          method: 'GET',
          credentials: 'include',
        });

        if (!userRes.ok) throw new Error('Session invalid or expired');

        const userData = await userRes.json();
        const user = userData.message;

        if (!user) {
          setError({ type: 'not_logged_in', message: 'You need to be logged in to view this content.' });
          setIsLoading(false);
          return;
        }

        setCurrentUser(user);

        // 2. Validate the document name exists
        if (!name) {
          setError({ type: 'invalid_url', message: 'The requested result could not be found.' });
          setIsLoading(false);
          return;
        }

        // 3. Fetch Chat history doc
        const docRes = await fetch(`/api/resource/Chat history/${name}`, {
          method: 'GET',
          credentials: 'include',
        });

        if (!docRes.ok) {
          if (docRes.status === 404) {
            throw new Error('The requested result does not exist or has been deleted.');
          } else {
            throw new Error('Failed to fetch the requested result.');
          }
        }

        const docData = await docRes.json();
        const doc = docData.data;
        setChatDoc(doc);

        // 4. Check ownership
        if (doc.owner !== user) {
          setError({
            type: 'unauthorized',
            message: 'You do not have permission to view this result.',
          });
          setIsLoading(false);
          return;
        }

        // 5. Parse and set result component (original unchanged)
        let parsedResult = JSON.parse(doc.result);

        // if(doc.intension!=='Query to Get Employee Search') {
          let tempData = await retrieveData(parsedResult);
          parsedResult = tempData
        // }

        switch (doc.intension) {
          case 'Query to search Incentives':
            setRenderResult(<Incentiveresult res={parsedResult.result} source="SolutionScreen" rerender={1} />);
            break;
          case 'Query to Get Approvals':
            setRenderResult(<Approvalresult result={parsedResult.result} source="SolutionScreen" rerender={1} />);
            break;
          case 'Query to build industry from Scratch':
            setRenderResult(<IndustryResultScreen result={parsedResult.result} source="SolutionScreen" rerender={1} />);
            break;
          case 'Query to Search Vendors':
            setRenderResult(<Vendorresult result={parsedResult.result} source="SolutionScreen" rerender={1} />);
            break;
          case 'Query to Get Employee Search':
            setRenderResult(<Empresult result={parsedResult.result} rerender={1} />);
            break;
          default:
            setRenderResult(
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">No Preview Available</h3>
                <p className="text-gray-600">This result type cannot be displayed.</p>
              </div>
            );
        }

        setIsLoading(false);
      } catch (err) {
        // console.error('Error:', err);
        setError({
          type: 'generic',
          message: err.message || 'An unexpected error occurred while loading the result.',
        });
        setIsLoading(false);
      }
    };

    validateSessionAndFetch();
  }, [name]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full text-center">
          <LogoLoader text="Preparing your result..." />
          <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <FaInfoCircle className="h-5 w-5 text-blue-700" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-700">
                  Please wait while we securely load your data...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error states
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
          <div className={`p-5 ${error.type === 'unauthorized' ? 'bg-red-500' : error.type === 'not_logged_in' ? 'bg-blue-600' : 'bg-purple-600'} text-white`}>
            <div className="flex items-center justify-center">
              {error.type === 'unauthorized' ? (
                <FaExclamationTriangle className="h-10 w-10 mr-3" />
              ) : error.type === 'not_logged_in' ? (
                <FaSignInAlt className="h-10 w-10 mr-3" />
              ) : (
                <MdOutlineEmojiObjects className="h-10 w-10 mr-3" />
              )}
              <h2 className="text-xl font-bold">
                {error.type === 'unauthorized' ? 'Access Denied' : 
                 error.type === 'not_logged_in' ? 'Login Required' : 
                 'Oops! Something Went Wrong'}
              </h2>
            </div>
          </div>
          
          <div className="p-6">
            <p className="text-gray-700 mb-6 text-center">{error.message}</p>
            
            <div className="flex flex-col space-y-3">
              {error.type === 'not_logged_in' ? (
                <button
                  onClick={() => navigate('/frontend/login')}
                  className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
                >
                  <FaSignInAlt className="mr-2" /> Login to Continue
                </button>
              ) : (
                <button
                  onClick={() => navigate(-1)}
                  className="w-full flex items-center justify-center px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md transition"
                >
                  <FaArrowLeft className="mr-2" /> Go Back
                </button>
              )}
              
              <button
                onClick={() => navigate('/')}
                className="w-full flex items-center justify-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-md transition"
              >
                <FaHome className="mr-2" /> Return to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Original renderResult output (unchanged)
  return (
    <div>
      {renderResult || (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white p-8 rounded-lg shadow-md text-center max-w-md">
            <MdOutlineEmojiObjects className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">No Content Available</h3>
            <p className="mt-1 text-sm text-gray-500">The result you requested is empty or cannot be displayed.</p>
            <div className="mt-6">
              <button
                onClick={() => navigate(-1)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                <FaArrowLeft className="mr-2" /> Go Back
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Renderresult;
