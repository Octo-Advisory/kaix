import React, { useState, useEffect } from "react";
import { 
  FaEnvelope, 
  FaPaperPlane, 
  FaArrowLeft, 
  FaEye, 
  FaEyeSlash,
  FaCheckCircle,
  FaSpinner
} from "react-icons/fa";
import { GoLock } from "react-icons/go";
import { useNavigate } from "react-router-dom";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const ForgotPassword = () => {
  const [step, setStep] = useState(1);
  const [countdown, setCountdown] = useState(30);
  const [direction, setDirection] = useState("forward");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (countdown > 0 && step === 2) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown, step]);

  const goToStep = (newStep) => {
    setDirection(newStep > step ? "forward" : "backward");
    setStep(newStep);
  };

  const handleSendCode = async () => {
    if (!email) {
      toast.error("Please enter your email address");
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch("/api/method/frontend_app.Management_Class.helpers.otp.forgot_password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "request_otp", email }),
      });
      const data = await response.json();
      if (data.message.status === "success") {
        toast.success(`Verification code sent to ${email}`);
        setCountdown(30);
        goToStep(2);
      } else {
        toast.error(data.message.message || "Failed to send OTP");
      }
    } catch {
      toast.error("Error sending OTP");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!otp || otp.length !== 6) {
      toast.error("Please enter a valid 6-digit code");
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch("/api/method/frontend_app.Management_Class.helpers.otp.forgot_password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "verify_otp", email, otp }),
      });
      const data = await response.json();
      if (data.message.status === "success" && data.message.verified) {
        toast.success("OTP verified!");
        goToStep(3);
      } else {
        toast.error(data.message.message || "Invalid OTP");
      }
    } catch {
      toast.error("Error verifying OTP");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch("/api/method/frontend_app.Management_Class.helpers.otp.forgot_password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset_password", email, new_password: newPassword }),
      });
      const data = await response.json();
      if (data.message.status === "success") {
        toast.success("Password reset successfully!");
        navigate('/login')
        setEmail("");
        setOtp("");
        setNewPassword("");
      } else {
        toast.error(data.message.message || "Failed to reset password");
      }
    } catch {
      toast.error("Error resetting password");
    } finally {
      setIsLoading(false);
    }
  };

  const resendCode = () => {
    if (countdown > 0) return;
    setCountdown(30);
    toast.info("Verification code resent to your email");
  };

  return (
    <div className="min-h-screen w-full bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <span className="text-3xl font-bold text-[#0e2044]">Mars</span>
            <span className="text-3xl font-bold text-[#41b655]">AIX</span>
          </div>
          
          <div className="relative flex flex-col gap-2 items-center mb-6">
            {/* Step indicator */}
            <div className="flex justify-center mb-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center">
                  <div 
                    className={`w-8 h-8 rounded-full flex items-center justify-center 
                      ${step >= i ? 'bg-[#41b655] text-white' : 'bg-gray-200 text-gray-600'}
                      ${i === step ? 'ring-2 ring-[#41b655] ring-offset-2' : ''}`}
                  >
                    {i}
                  </div>
                  {i < 3 && (
                    <div className={`w-12 h-1 ${step > i ? 'bg-[#41b655]' : 'bg-gray-200'}`}></div>
                  )}
                </div>
              ))}
            </div>

            {/* Step titles */}
            {step === 1 && (
              <>
                <h1 className="font-bold text-2xl">Forgot Password</h1>
                <p className="text-gray-600">
                  We'll help you reset it and get back on track
                </p>
              </>
            )}
            {step === 2 && (
              <>
                <h1 className="font-bold text-2xl">Verify OTP</h1>
                <p className="text-gray-600">
                  Check your email for the code
                </p>
              </>
            )}
            {step === 3 && (
              <>
                <h1 className="font-bold text-2xl">Reset Password</h1>
                <p className="text-gray-600">Create a new secure password</p>
              </>
            )}
          </div>
        </div>

        <div className="relative w-full min-h-[250px] overflow-hidden">
          <div className="relative w-full h-full">
            {/* Step 1 - Email Input */}
            <div
              className={`absolute top-0 left-0 w-full flex flex-col gap-4 transition-all duration-500 ease-in-out ${
                step === 1
                  ? "opacity-100 translate-x-0"
                  : direction === "forward"
                  ? "-translate-x-full opacity-0"
                  : "translate-x-full opacity-0"
              }`}
            >
              <div className="w-full flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">Email Address</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <FaEnvelope className="text-gray-400" />
                  </div>
                  <input
                    type="email"
                    placeholder="you@company.com"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>
              <button
                className="w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 shadow-md flex items-center justify-center"
                onClick={handleSendCode}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <FaSpinner className="animate-spin mr-2" />
                    Sending...
                  </>
                ) : (
                  <>
                    Send Verification Code <FaPaperPlane className="ml-2" />
                  </>
                )}
              </button>
            </div>

            {/* Step 2 - OTP Verification */}
            <div
              className={`absolute top-0 left-0 w-full flex flex-col gap-4 transition-all duration-500 ease-in-out ${
                step === 2
                  ? "opacity-100 translate-x-0"
                  : step < 2
                  ? "translate-x-full opacity-0"
                  : "-translate-x-full opacity-0"
              }`}
            >
              <p className="text-gray-600 text-center">
                We've sent a 6-digit code to <span className="font-semibold">{email}</span>
              </p>
              <div className="w-full flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">Verification Code</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <GoLock className="text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="6-digit Code"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    maxLength={6}
                  />
                </div>
              </div>
              <button
                className="w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 shadow-md"
                onClick={handleVerifyCode}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <FaSpinner className="animate-spin mr-2 inline" />
                    Verifying...
                  </>
                ) : (
                  "Verify Code"
                )}
              </button>
              <div className="text-center text-sm text-gray-500">
                {countdown > 0 ? (
                  `Resend code in ${countdown}s`
                ) : (
                  <button 
                    className="text-[#41b655] hover:text-[#0e2044] transition"
                    onClick={resendCode}
                  >
                    Resend Code
                  </button>
                )}
              </div>
            </div>

            {/* Step 3 - Password Reset */}
            <div
              className={`absolute top-0 left-0 w-full flex flex-col gap-4 transition-all duration-500 ease-in-out ${
                step === 3
                  ? "opacity-100 translate-x-0"
                  : "translate-x-full opacity-0"
              }`}
            >
              <div className="w-full flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">New Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <GoLock className="text-gray-400" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="New Password"
                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
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
              <div className="w-full flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">Confirm Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <GoLock className="text-gray-400" />
                  </div>
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm Password"
                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-[#41b655] outline-none transition"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
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
                className="w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 shadow-md"
                onClick={handleResetPassword}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <FaSpinner className="animate-spin mr-2 inline" />
                    Updating...
                  </>
                ) : (
                  "Update Password"
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/login')}
            className="flex items-center justify-center gap-1 text-[#41b655] hover:text-[#0e2044] transition mx-auto"
          >
            <FaArrowLeft size={14} /> Return to Sign In
          </button>
        </div>

        <div className="mt-8 border-t border-gray-200 pt-6 text-center text-sm text-gray-500">
          <p>Need Help? <button className="text-[#41b655] hover:text-[#0e2044] transition">Contact Support</button></p>
          <p className="mt-2">© 2025 MarsInfrAIX. All rights reserved.</p>
        </div>
      </div>
      <ToastContainer position="top-center" autoClose={3000} hideProgressBar />
    </div>
  );
};

export default ForgotPassword;