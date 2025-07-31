import React, { useRef, useState, useEffect, useContext } from 'react';
import illustration1 from '../../assets/AI-Powered Industrial Solutionss.jpg';
import { FaEye, FaEyeSlash, FaArrowRight } from "react-icons/fa";
import { FiUser } from "react-icons/fi";
import { HiOutlineMail, HiOutlineOfficeBuilding, HiOutlineBriefcase } from "react-icons/hi";
import { useNavigate } from 'react-router-dom';
import { useFrappeCreateDoc, FrappeContext,useFrappeGetDocList } from 'frappe-react-sdk';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { IoIosArrowDown, IoIosArrowUp } from 'react-icons/io';
import { RiLockPasswordLine } from "react-icons/ri";

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
    const { call } = useContext(FrappeContext)
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        new_password: '',
        confirmPassword: '',
        interest: '',
        bio: '', // Set default value
        location: ''
    });
    
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [industryList,setIndustryList] = useState(['Cement', 'Steel', 'Chemicals', 'Textiles', 'Automotive']);
    const [industryDropdownOpen, setIndustryDropdownOpen] = useState(false);
    const industryNode = useRef(null);
    
    useClickOutside(industryNode, () => setIndustryDropdownOpen(false));
    const navigate = useNavigate();
    const { createDoc } = useFrappeCreateDoc();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

     const fetchHints = async (queries,industry) => {
    try {
      const result = await call.get("frontend_app.Management_Class.helpers.utility.formatting_input_query_list", {
        'raw_nested_list': [],
        'input_industry_name': industry
      });
      console.log("Got the Hint Statements", result);
      return result.message;
    } catch (err) {
      console.log("error occurred in Hint Statment Function😂", err);
    }
  }

  const {data:industries} = useFrappeGetDocList('Industry', {
    fields:['name']
  })
  
  const getIndustries = async ()=>{

    if(industries && industries.length>0) {
        let names = industries.map(industry=> industry.name)
        console.log(names, 'Industry NAmes')
        setIndustryList(names)
    }
  }

  useEffect(()=>{
    getIndustries()
  },[industries])


    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        
        // Validate passwords match
        if (formData.new_password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setIsLoading(false);
            return;
        }
        if(formData.bio === 'Industry'){
            setError('Please select industry');
            setIsLoading(false)
            return
        }

        try {
            await createDoc("User", {
                ...formData,
                send_welcome_email: 0
            });

            const hints = await fetchHints('some',formData.bio)
            if(hints && hints.length>0) {
                await createDoc("Session",{
                    'user': formData.email,
                    'query_hints': JSON.stringify(hints)
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
                new_password: '',
                confirmPassword: '',
                interest: '',
                bio: '',
                location: ''
            });

            // Navigate after delay
            setTimeout(() => {
                navigate('/login');
            }, 1500);

        } catch (error) {
            console.error('Error:', error);
            setError(error.message || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const formRef = useRef(null)
    useEffect(()=>{
        if(error && error!== '') {
            if(formRef.current) {
                formRef.current.scrollTop = 0;
            }
        }
    },[error])

    return (
        <div className="h-screen w-full bg-gray-50 flex items-center justify-center p-8">
            <div className="max-w-7xl w-full bg-white rounded-xl h-[90%] shadow-lg flex flex-col md:flex-row">
                {/* Left Side - Form */}
                <div ref={formRef} className="w-full md:w-1/2 py-12 px-8 sm:px-12 lg:px-16 flex h-full flex-col overflow-y-auto">
                    <div className="text-center mb-8">
                        <div className="flex items-center justify-center mb-4">
                            <span className="text-3xl font-bold text-[#0e2044]">Mars</span>
                            <span className="text-3xl font-bold text-[#41b655]">AIX</span>
                        </div>
                        <h1 className="text-2xl font-semibold text-gray-800 mb-2">Create your account</h1>
                        <p className="text-gray-600">Find your perfect industrial property with AI-powered Analysis</p>
                    </div>

                    <form onSubmit={handleSubmit} className='relative'>
                        {error && (
                            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        <div className="flex gap-4 mb-4">
                            <div className="w-1/2">
                                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                                    First Name
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
                                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                        value={formData.first_name}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="w-1/2">
                                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                                    Last Name
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
                                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                        value={formData.last_name}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="mb-4">
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                                Email
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
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                        </div>

                        <div className="mb-4">
                            <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
                                Password
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
                                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                    value={formData.new_password}
                                    onChange={handleChange}
                                    required
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

                        <div className="mb-6">
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                                Confirm Password
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
                                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
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

                        <div className="mb-4">
  <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-1">
    Industry
  </label>
  <div className='relative w-full' ref={industryNode}>
    <div className="relative">
      <input
        type="text"
        placeholder="Search or select industry"
        className="w-full pl-4 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] outline-none transition"
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
    
    <div className={`absolute z-10 mt-1 w-full rounded-md bg-white shadow-lg border border-gray-200 transition-all max-h-60 overflow-y-auto ${industryDropdownOpen ? 'opacity-100 visible' : 'opacity-0 invisible'}`}>
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
                                    id="company_name"
                                    name="company_name"
                                    placeholder="Company Name"
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                    value={formData.company_name}
                                    onChange={handleChange}
                                />
                                </div>
                            </div>

                            {/* Job Title */}
                            <div className="w-1/2">
                                <label htmlFor="job_title" className="block text-sm font-medium text-gray-700 mb-1">
                                Job Title
                                </label>
                                <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <HiOutlineBriefcase className="text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    id="job_title"
                                    name="job_title"
                                    placeholder="Ex: Senior Manager"
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                                    value={formData.job_title}
                                    onChange={handleChange}
                                    required
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

                    <div className="mt-8 text-center">
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