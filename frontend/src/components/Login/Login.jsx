import React, { useState } from 'react';
import { FaEye, FaEyeSlash, FaArrowRight, FaSpinner } from 'react-icons/fa';
import { FiUser, FiLock } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import illustration1 from '../../assets/AI-Powered Industrial Solutionss.jpg';
import { useFrappeAuth } from 'frappe-react-sdk';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';


function Login() {
  const [login_username, setLoginUsername] = useState('');
  const [login_password, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const { currentUser,login } = useFrappeAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (!login_username || !login_password) {
      setError("Please enter both username and password.");
      setIsLoading(false);
      return;
    }
    
    try {
      await login({username:login_username,password: login_password});
      toast.success("Login successful!", {
        position: "top-center",
        autoClose: 2000,
        hideProgressBar: true,
        closeOnClick: true,
        pauseOnHover: false,
        draggable: false,
      });
      navigate("/chat");
    } catch (err) {
      console.error("Login failed:", err);
      setError("Invalid username or password.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-6xl w-full bg-white rounded-xl overflow-hidden shadow-lg flex flex-col md:flex-row">
        {/* Left Side - Illustration */}
        <div className="hidden md:block md:w-1/2 bg-gradient-to-br from-[#0e2044] to-[#41b655] relative overflow-hidden">
          <div className="absolute inset-0 bg-black/10" />
          <img 
            src={illustration1} 
            className="w-full h-full object-cover object-center"
            alt="AI-Powered Industrial Solutions"
          />
          
          <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
            <h2 className="text-3xl font-bold mb-2">MarsAIX Platform</h2> {/* Changed by Jenith on 15-5-25 9:49 */}
            <p className="text-gray-200">
              {/* Your gateway to intelligent industrial solutions */}
              Establish your Industrial Project seamlessly with our AI-powered analysis{/* Changed by Jenith on 15-5-25 9:49 */}
            </p>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="w-full md:w-1/2 py-12 px-8 sm:px-12 lg:px-16 flex flex-col justify-center">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <span className="text-3xl font-bold text-[#0e2044]">Mars</span>
              <span className="text-3xl font-bold text-[#41b655]">AIX</span>
            </div>
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">Welcome back</h1>
            <p className="text-gray-600">Sign in to continue building your industrial project</p>{/* Changed by Jenith on 15-5-25 9:50 */}
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label htmlFor="login_username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FiUser className="text-gray-400" />
                </div>
                <input
                  type="text"
                  id="login_username"
                  placeholder="Enter your username"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                  value={login_username}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="mb-6">
              <label htmlFor="login_password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FiLock className="text-gray-400" />
                </div>
                <input
                  type={showLoginPassword ? "text" : "password"}
                  id="login_password"
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                  value={login_password}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition"
                  onClick={() => setShowLoginPassword(!showLoginPassword)}
                >
                  {showLoginPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
              <div className="flex justify-end mt-2">
                <button
                  type="button"
                  className="text-sm text-[#41b655] hover:text-[#0e2044] transition"
                  onClick={()=>{navigate("/forgotpassword")}}
                >
                  Forgot password?
                </button>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 shadow-md flex items-center justify-center ${isLoading ? 'opacity-80' : ''}`}
            >
              {isLoading ? (
                <>
                  <FaSpinner className="animate-spin mr-2" />
                  Signing In...
                </>
              ) : (
                <>
                  Sign In <FaArrowRight className="ml-2" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <button
                onClick={() => navigate('/signup')}
                className="text-[#41b655] font-medium hover:text-[#0e2044] transition"
              >
                Sign up
              </button>
            </p>
          </div>

           <div className="mt-8 border-t border-gray-200 pt-6 text-center">
            <button
              className="text-sm text-gray-500 hover:text-gray-700 transition"
              onClick={()=> navigate('/chat')}
            >
              Continue as guest
            </button>
          </div> 
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}

export default Login;