import React, { useState } from 'react';
import illustration1 from '../../assets/AI-Powered Industrial Solutions.jpg';
import { FaEye, FaEyeSlash, FaArrowRight } from "react-icons/fa";
import { FiUser } from "react-icons/fi";
import { HiOutlineMail } from "react-icons/hi";
import { useNavigate } from 'react-router-dom';
import { useFrappeCreateDoc } from 'frappe-react-sdk';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const SignUp = () => {
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        new_password: '',
        confirmPassword: ''
    });
    
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const {createDoc,loading,isCompleted} = useFrappeCreateDoc()

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

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
  
      try {
          const res = await createDoc("User", {
              ...formData,
              send_welcome_email: 0
          });
  
          // If creation is successful, show toast and reset form
          toast.success("Register successful!", {
              position: "top-center",
              autoClose: 2000,
              hideProgressBar: true,
              closeOnClick: true,
              pauseOnHover: false,
              draggable: false,
          });
  
          setFormData({
              first_name: '',
              last_name: '',
              email: '',
              new_password: '',
              confirmPassword: ''
          });
  
      } catch (error) {
          console.error('Error:', error);
          setError('Internal server error. Please try again.');
          setIsLoading(false);
          return;
      }
  
      // Simulate delay for UX
      setTimeout(() => {
          setIsLoading(false);
          navigate('/login');
      }, 1500);
  };

    return (
        <div className="min-h-screen w-full bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-6xl w-full bg-white rounded-xl overflow-hidden shadow-lg flex flex-col md:flex-row">
                {/* Left Side - Form */}
                <div className="w-full md:w-1/2 py-12 px-8 sm:px-12 lg:px-16 flex flex-col justify-center">
                    <div className="text-center mb-8">
                        <div className="flex items-center justify-center mb-4">
                            <span className="text-3xl font-bold text-[#0e2044]">Mars</span>
                            <span className="text-3xl font-bold text-[#41b655]">AIX</span>
                        </div>
                        <h1 className="text-2xl font-semibold text-gray-800 mb-2">Create your account</h1>
                        <p className="text-gray-600">Find your perfect industrial property with AI-powered Analysis</p>
                    </div>

                    <form onSubmit={handleSubmit}>
                        {error && (
                            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        <div className="flex gap-4 mb-4">
                            <div className="w-1/2">
                                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
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
                                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
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
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                                Password
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <FiUser className="text-gray-400" />
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
                                    <FiUser className="text-gray-400" />
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

                        <button
                            type="submit"
                            disabled={isLoading}
                            className={`w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 shadow-md flex items-center justify-center ${isLoading ? 'opacity-80' : ''}`}
                        >
                            {isLoading ? (
                                <>
                                    <span className="animate-pulse">Creating Account...</span>
                                </>
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
                <div className="hidden md:block md:w-1/2 bg-gradient-to-br from-[#0e2044] to-[#41b655] relative overflow-hidden">
                    <div className="absolute inset-0 bg-black/10" />
                    <img 
                        src={illustration1} 
                        className="w-full h-full object-cover object-center"
                        alt="AI-Powered Industrial Solutions"
                    />
                    <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
                        <h2 className="text-3xl font-bold mb-2">MarsInfraAIX Platform</h2>
                        <p className="text-gray-200">
                            Your gateway to intelligent industrial solutions
                        </p>
                    </div>
                </div>
            </div>
            <ToastContainer />
        </div>
    );
};  

export default SignUp;