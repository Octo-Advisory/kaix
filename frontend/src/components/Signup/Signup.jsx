import React, { useRef, useState, useEffect, useContext } from 'react';
import illustration1 from '../../assets/AI-Powered Industrial Solutionss.jpg';
import { FaEye, FaEyeSlash, FaArrowRight } from "react-icons/fa";
import { FiUser } from "react-icons/fi";
import { HiOutlineMail, HiOutlineOfficeBuilding, HiOutlineBriefcase } from "react-icons/hi";
import { useNavigate } from 'react-router-dom';
import { useFrappeCreateDoc, FrappeContext,useFrappeGetDocList, useFrappeGetDoc } from 'frappe-react-sdk';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { IoIosArrowDown, IoIosArrowUp } from 'react-icons/io';
import { RiLockPasswordLine } from "react-icons/ri";
import { FiPhone } from "react-icons/fi";
import RegistrationSuccessful from './RegistrationSuccessful';

const useClickOutside = (ref, handler) => {
    useEffect(() => {
        const maybeHandler = (event) => {
            if (ref.current && !ref.current.contains(event.target)) {
                handler();
            }
        };
        document.addEventListener("mousedown", maybeHandler);
        return () => {
            document.removeEventListener("mousedown", maybeHandler);
        };
    }, [ref, handler]);
};

const SignUp = () => {

  const { data: adminToken } = useFrappeGetDoc("Mars Configurations", "admin_token")
  const ADMIN_TOKEN = adminToken?.admin_token
  
      const createDiagnostic = async(errType, logMsg,chatId)=> {
        let log = ` ${logMsg}`
         createDoc("AIX Diagnostics Hub", {
        type: errType,
        note: log,
        });
      }
    const { call } = useContext(FrappeContext)
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        mobile_no: '',
        new_password: '',
        confirmPassword: '',
        interest: '', // company name
        bio: '', // Set default value industry
        otherIndustry: '', //Other industry name
        location: '' // job title 
    });
    
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [industryList,setIndustryList] = useState(['Cement', 'Steel', 'Chemicals', 'Textiles', 'Automotive']);
    const [industryDropdownOpen, setIndustryDropdownOpen] = useState(false);
    const industryNode = useRef(null);

    const [registrationComplete, setRegistrationComplete] = useState(false)
    
    useClickOutside(industryNode, () => setIndustryDropdownOpen(false));
    const navigate = useNavigate();
    const { createDoc } = useFrappeCreateDoc();

    const handleChange = (e) => {
        // console.log(e)
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

     const iconHints = [
    {
      title: "Government Grants",
      subtitle: "Explore available subsidies",
      hint: "Tell me the government incentives for cement industry in Gujarat",
      type: "Incentives"
    },
    {
      title: "Land Options",
      subtitle: "Check availability by location",
      hint: "What land availability exists for cement industry in Vadodara?",
      type: "Build from Scratch"
    },
    {
      title: "Labor Insights",
      subtitle: "Analyze workforce distribution",
      hint: "What are the labor options for cement industry in Bharuch?",
      type: "Employment"
    },
    {
      title: "Vendor Network",
      subtitle: "Find reliable suppliers",
      hint: "What are the vendor options for cement industry in Ahmedabad?",
      type: "Vendor Search"
    },
    {
      title: "Vendor Insights",
      subtitle: "Trusted supplier options",
      hint: "What are the vendor options for cement industry in Surat?",
      type: "Vendor Search"
    },
    {
      title: "Approval Status",
      subtitle: "Licenses & permits overview",
      hint: "What approvals are required for cement plant setup in Rajkot?",
      type: "Approval"
    }
  ];

     const fetchHints = async (queries,industry) => {
    try {
      const result = await call.get("frontend_app.Management_Class.helpers.utility.generate_query_hints", {
        'query_list': [],
        'input_industry_name': industry
      });
      let hints = result.message || [];

      let newHints = hints.map((hintObj, index) => {
        let matchedHint = iconHints.find(iconHint => iconHint.type === hintObj.module) || {};

        return {
          ...matchedHint,
          hint:hintObj.query,
          ...hintObj
        };
      });
      return newHints;
    } catch (err) {
      
      // console.log("error occurred in Hint Statment Function😂", err);
    }
  }

  const {data:industries,mutate} = useFrappeGetDocList('Industry', {
    fields:['name'],
    limit:10000
  })

  useEffect(()=>{
    mutate()
  },[])
  
  const getIndustries = async ()=>{

    if(industries && industries.length>0) {
        let names = industries.map(industry=> industry.name)
        // console.log(names, 'Industry NAmes')
        setIndustryList(names)
    }
  }

  useEffect(()=>{
    getIndustries()
  },[industries])
   const updateUser = async (formData) => {
  const url = `/api/resource/User`;
   if (formData.bio === 'Other' && formData.otherIndustry) {
    formData.bio = formData.otherIndustry;
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        // 'Authorization': 'token d3de1e0e4e25846:9345b96f0c957d9', // Replace with your token
        'Authorization': `token ${ADMIN_TOKEN}`, // Replace with your token
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        "send_welcome_email": 0,
        "enabled":0,
        ...formData,
      }), // Pass fields to update
    });

    if (response) {
      const result = await response.json();
      // let serverMessages = JSON.parse(result?.data?.['_server_messages']);
      //   if (serverMessages && serverMessages.length > 1) {
      //     const errorMessage = JSON.parse(serverMessages[1]).message;
      //     console.log(errorMessage); // Logs the error message, e.g., "User prince567.j@gmail.com already exists"
      //     return false;
      //   }
      // console.log(result, result?.data)
      if(result.data) {
        console.log('User updated successfully:', result);
        setRegistrationComplete(true)
        return true
      }
      else {
       let ErrorMsg = JSON.parse(JSON.parse(result?.['_server_messages'])?.[1])?.message?.replace(/<\/?[^>]+(>|$)/g, "")
       toast.error(ErrorMsg, {
         position: "top-center",
         autoClose: 2000,
         hideProgressBar: true,
         closeOnClick: true,
         pauseOnHover: false,
         draggable: false,
        });
        // createDiagnostic("Registration", `Something Went wrong while Registering due to ${ErrorMsg}`)
      }
    } else {
      const errorData = await response.json();
      createDiagnostic("Registration", `Something Went wrong while Registering due to ${JSON.stringify(errorData)}`)
      // console.error('Failed to update user:', errorData.message);
      return false
    }
  } catch (error) {
    createDiagnostic("Registration", `Something Went wrong while Registering due to ${JSON.stringify(error)}`)
    // console.error('Error updating user:', error);
  }
};

const [errorField, setErrorField] = useState(null)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const contactRegex = /^\d{10}$/;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        setErrorField(null);

    if (formData.first_name === '') {
    setError('Please Enter First Name');
    setErrorField('first_name'); // highlight bio field
    setIsLoading(false);
    return;
  }

  if (formData.last_name === '') {
    setError('Please Enter Last Name');
    setErrorField('last_name'); // highlight bio field
    setIsLoading(false);
    return;
  }

  if (!emailRegex.test(formData.email)) {
  setError('Please enter a valid email address');
  setErrorField('email');
  setIsLoading(false)
  return;
}

if(!contactRegex.test(formData.mobile_no)) {
  setError('Please Enter a valid Phone Number');
  setErrorField('mobile_no')
  setIsLoading(false)
  return;
}

    if (formData.new_password === '') {
    setError('Please enter a password');
    setErrorField('password'); // highlight password fields
    setIsLoading(false);
    return;
  }
    if (formData.confirmPassword === '') {
    setError('Please Re enter the password');
    setErrorField('confirmpassword'); // highlight password fields
    setIsLoading(false);
    return;
  }
    if (formData.new_password !== formData.confirmPassword) {
    setError('Passwords do not match');
    setErrorField('passwordnotmatch'); // highlight password fields
    setIsLoading(false);
    return;
  }

  if (formData.bio === '') {
    setError('Please select industry');
    setErrorField('industry'); // highlight bio field
    setIsLoading(false);
    return;
  }
  if (formData.bio === 'Other' && formData.otherIndustry === '') {
    setError('Please Enter the Other Industry Name')
    setErrorField('otherIndustry');
    setIsLoading(false)
    return;
  }

   const isValidIndustry = industryList.some(
        (industry) => industry.toLowerCase() === formData.bio.toLowerCase()
    );

    if (!isValidIndustry && !formData.bio==='Other') {
        setError('Please select a valid industry from the list');
        setErrorField('industry')
        setIsLoading(false);
        return;
    }
  
  if (formData.location === '') {
    setError('Please Enter Job Title');
    setErrorField('job_title'); // highlight bio field
    setIsLoading(false);
    return;
  }
 
  


        try {
            // await createDoc("User", {
            //     ...formData,
            //     send_welcome_email: 0,
            // });
            let res = await updateUser(formData)
            if(res) {
                const hints = await fetchHints('some',formData.bio)
                if(hints && hints.length>0) {
                    await createDoc("Session",{
                        'user': formData.email,
                        'query_hints': JSON.stringify(hints),
                    })
                }
    
                toast.success("Registration successful!", {
                    position: "top-center",
                    autoClose: 2000,
                    hideProgressBar: true,
                    closeOnClick: true,
                    pauseOnHover: false,
                    draggable: false,
                });
    
                // Reset form
                setFormData({
                    first_name: '',
                    last_name: '',
                    email: '',
                    mobile_no: '',
                    new_password: '',
                    confirmPassword: '',
                    interest: '',
                    bio: '',
                    otherIndustry:'',
                    location: ''
                });
    
                // Navigate after delay
                // setTimeout(() => {
                //     navigate('/login');
                // }, 1500);
                setTimeout(() => {
                  setRegistrationComplete(true)
                }, 1500);
            }
            else {
                setError('Registration failed. Please try again.');
            }

        } catch (error) {
            // console.error('Error:', error);
            setError(error.message || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const formRef = useRef(null)
    useEffect(()=>{
        // console.log(error, 'OKay Error')
        // console.log(errorField)
        if(error && error!== '') {
            if(formRef.current) {
                formRef.current.scrollTop = 0;
            }
        }
    },[error])

    if(registrationComplete) {
      return <RegistrationSuccessful />
    }

    return (
        <div className="h-screen w-full bg-gray-50 flex items-center justify-center p-8">
            <div className="max-w-[1400px] w-full bg-white rounded-xl h-[95%] shadow-lg flex flex-col md:flex-row">
                {/* Left Side - Form */}
                <div ref={formRef} className="w-full md:w-1/2 py-4 px-8 sm:px-12 lg:px-16 flex h-full flex-col justify-evenly overflow-y-auto">
                    <div className="text-center mb-6">
                        {/* <div className="flex items-center justify-center mb-4">
                            <span className="text-3xl font-bold text-[#0e2044]">Mars</span>
                            <span className="text-3xl font-bold text-[#41b655]">AIX</span>
                        </div> */}
                        <h1 className="text-2xl font-semibold text-gray-800 mb-2">Create your account</h1>
                        <p className="text-gray-600">Find your perfect industrial property with AI-powered Analysis</p>
                    </div>

                    <form onSubmit={handleSubmit} className='relative'>
                        {/* {error && (
                            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                                {error}
                            </div>
                        )} */}

                        <div className="flex gap-4 mb-4">
                            <div className="w-1/2">
                                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                                    First Name <span className='text-red-600'>*</span> {errorField==='first_name' ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter First Name</span>) : ''}
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <FiUser className="text-gray-400" />
                                    </div>
                                    <input
                                        type="text"
                                        id="first_name"
                                        name="first_name"
                                        placeholder="First Name"
                                        className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition ${errorField === 'first_name' ? 'border-red-500' : 'border-gray-300'}`}
                                        value={formData.first_name}
                                        onChange={handleChange}
                                        // required
                                    />
                                </div>
                            </div>
                            <div className="w-1/2">
                                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                                    Last Name <span className='text-red-600'>*</span>  {errorField==='last_name' ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter Last Name</span>) : ''}
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <FiUser className="text-gray-400" />
                                    </div>
                                    <input
                                        type="text"
                                        id="last_name"
                                        name="last_name"
                                        placeholder="Last Name"
                                        className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] ${errorField === 'last_name' ? 'border-red-500' : 'border-gray-300'} outline-none transition`}
                                        value={formData.last_name}
                                        onChange={handleChange}
                                        // required
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="mb-4 flex gap-4">
                          <div className='w-1/2'>
                           <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                                Email <span className='text-red-600'>*</span> {errorField==='email' ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter Valid Email</span>) : ''}
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <HiOutlineMail className="text-gray-400" />
                                </div>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    placeholder="Email"
                                    className={`w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] ${errorField === 'email' ? 'border-red-500' : 'border-gray-300'} outline-none transition`}
                                    value={formData.email}
                                    onChange={handleChange}
                                    // required
                                />
                            </div>
                          </div>
                          <div className='w-1/2'>
                            <label htmlFor="mobile_no" className="block text-sm font-medium text-gray-700 mb-1">
                                  Mobile No <span className='text-red-600'>*</span> {errorField==='mobile_no' ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter Valid Mobile No</span>) : ''}
                              </label>
                              <div className="relative">
                                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                      <FiPhone className="text-gray-400" />
                                  </div>
                                  <input
                                      type="text"
                                      id="mobile_no"
                                      name="mobile_no"
                                      placeholder="Mobile Number"
                                      className={`w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] ${errorField === 'mobile_no' ? 'border-red-500' : 'border-gray-300'} outline-none transition`}
                                      value={formData.mobile_no}
                                      onChange={handleChange}
                                      // required
                                  />
                              </div>
                          </div>
                           
                        </div>

                        <div className="mb-4 flex gap-4">
                          <div className='w-1/2'>
                            <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
                                Password <span className='text-red-600'>*</span> {(errorField==='password' || errorField==='passwordnotmatch') ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter Correct Password</span>) : ''}
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <RiLockPasswordLine className="text-gray-400" />
                                </div>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    id="new_password"
                                    name="new_password"
                                    placeholder="Password"
                                    className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] ${(errorField === 'password' || errorField==='passwordnotmatch') ? 'border-red-500' : 'border-gray-300'}  outline-none transition`}
                                    value={formData.new_password}
                                    onChange={handleChange}
                                    // required
                                />
                                <button
                                    type="button"
                                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <FaEyeSlash /> : <FaEye />}
                                </button>
                            </div>
                          </div>

                          <div className='w-1/2'>
                              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                                Confirm Password <span className='text-red-600'>*</span> {(errorField==='confirmpassword' || errorField==='passwordnotmatch') ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter Correct Password</span>) : ''}
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <RiLockPasswordLine className="text-gray-400" />
                                </div>
                                <input
                                    type={showConfirmPassword ? "text" : "password"}
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    placeholder="Confirm Password"
                                    className={`w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] ${(errorField === 'confirmpassword' || errorField==='passwordnotmatch') ? 'border-red-500' : 'border-gray-300'} outline-none transition`}
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    // required
                                />
                                <button
                                    type="button"
                                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                >
                                    {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
                                </button>
                            </div>
                          </div>
                        </div>
   

                        <div className="mb-4 flex gap-4">
                          
                          <div className={`${formData.bio === 'Other' ? 'w-1/2' : 'w-full'}`}>
                            <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-1">
                              Industry <span className='text-red-600'>*</span> {(errorField==='password' || errorField==='industry') ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Select Industry From the List</span>) : ''}
                            </label>
                            <div className='relative w-full' ref={industryNode}>
                              <div className="relative">
                                <input
                                  type="text"
                                  placeholder="Search or select industry"
                                  className={`w-full pl-4 pr-10 py-3 border rounded-lg focus:ring-2 focus:ring-[#41b655] outline-none transition ${errorField === 'industry' ? 'border-red-500' : 'border-gray-300'}`}
                                  value={formData.bio === 'Industry' ? '' : formData.bio}
                                  onChange={(e) => {
                                    const searchTerm = e.target.value;
                                    setFormData(prev => ({...prev, bio: searchTerm}));
                                    setIndustryDropdownOpen(true);
                                  }}
                                  onClick={() => setIndustryDropdownOpen(true)}
                                />
                                <button 
                                  type="button"
                                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                                  onClick={() => setIndustryDropdownOpen(!industryDropdownOpen)}
                                >
                                  {!industryDropdownOpen ? <IoIosArrowDown /> : <IoIosArrowUp />}
                                </button>
                              </div>
                              
                              <div className={`absolute z-10 mt-1 w-full rounded-md bg-white shadow-lg border border-gray-200 transition-all max-h-48 overflow-y-auto ${industryDropdownOpen ? 'opacity-100 visible' : 'opacity-0 invisible'}`}>
                                {industryList
                                  .filter(industry => 
                                    industry.toLowerCase().includes(formData.bio.toLowerCase())
                                  )
                                  .map((industry) => (
                                    <div 
                                      key={industry}
                                      className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 ${formData.bio === industry ? 'bg-gray-100 font-medium' : ''}`}
                                      onClick={() => {
                                        setFormData(prev => ({...prev, bio: industry}));
                                        setIndustryDropdownOpen(false);
                                      }}
                                    >
                                      {industry}
                                    </div>
                                  ))}
                                
                                {/* Show message when no results found */}
                                {industryList.filter(industry => 
                                  industry.toLowerCase().includes(formData.bio.toLowerCase())
                                ).length === 0 && (
                                  <div className="px-4 py-2 text-sm text-gray-500">
                                    No industries found
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          {formData.bio=== 'Other' && (<div className={`${formData.bio === 'Other' ? 'w-1/2' : ''}`}>
                            <label htmlFor="otherIndustry" className="block text-sm font-medium text-gray-700 mb-1">
                                Other Industry <span className='text-red-600'>*</span> {(errorField==='otherIndustry') ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter the Industy Name</span>) : ''}
                            </label>
                            <input type='text' name='otherIndustry' id='otherIndustry' placeholder='Type Industry Name' className={`w-full py-3 pl-4 border rounded-lg focus:ring-2 focus:ring-[#41b655] outline-none transition ${errorField === 'otherIndustry' ? 'border-red-500' : 'border-gray-300'}`} value={formData.otherIndustry} onChange={handleChange}/>
                          </div>)}
                        </div>

                        <div className="flex gap-4 mb-4">
                            {/* Company Name */}
                            <div className="w-1/2">
                                <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1">
                                Company Name (optional)
                                </label>
                                <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <HiOutlineOfficeBuilding className="text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    id="interest"
                                    name="interest"
                                    placeholder="Company Name"
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                    value={formData.interest}
                                    onChange={handleChange}
                                />
                                </div>
                            </div>

                            {/* Job Title */}
                            <div className="w-1/2">
                                <label htmlFor="job_title" className="block text-sm font-medium text-gray-700 mb-1">
                                Job Title <span className='text-red-600'>*</span> {errorField==='job_title'  ? (<span className='ml-2 relative text-red-600 text-xs tracking-wide'>Please Enter a Job Title</span>) : ''}
                                </label>
                                <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <HiOutlineBriefcase className="text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    id="location"
                                    name="location"
                                    placeholder="Ex: Senior Manager"
                                    className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] ${errorField === 'job_title' ? 'border-red-500' : 'border-gray-300'} outline-none transition`}
                                    value={formData.location}
                                    onChange={handleChange}
                                    // required
                                />
                                </div>
                            </div>
                        </div>


                        <button
                            type="submit"
                            disabled={isLoading}
                            className={`w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 shadow-md flex items-center justify-center ${isLoading ? 'opacity-80 cursor-not-allowed' : ''}`}
                        >
                            {isLoading ? (
                                <span className="animate-pulse">Creating Account...</span>
                            ) : (
                                <>
                                    Sign Up <FaArrowRight className="ml-2" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-gray-600">
                            Already have an account?{' '}
                            <button
                                onClick={() => navigate('/login')}
                                className="text-[#41b655] font-medium hover:text-[#0e2044] transition"
                            >
                                Sign In
                            </button>
                        </p>
                    </div>
                </div>

                {/* Right Side - Illustration */}
                <div className="hidden md:block md:w-1/2 bg-gradient-to-br from-[#0e2044] to-[#41b655] relative overflow-hidden rounded-r-xl">
                    <div className="absolute inset-0 bg-black/10" />
                    <img 
                        src={illustration1} 
                        className="w-full h-full object-cover object-center"
                        alt="AI-Powered Industrial Solutions"
                    />
                    <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
                        <h2 className="text-3xl font-bold mb-2">MarsAIX Platform</h2>
                        <p className="text-gray-200">
                            Establish your Industrial Project seamlessly with our AI-powered analysis
                        </p>
                    </div>
                </div>
            </div>
            <ToastContainer />
        </div>
    );
};  

export default SignUp;