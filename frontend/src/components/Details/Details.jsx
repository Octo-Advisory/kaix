import { useFrappeCreateDoc } from 'frappe-react-sdk';
import React, { useEffect, useState } from 'react';
import { AiOutlineQuestionCircle, AiOutlineUser, AiOutlineMail, AiOutlinePhone } from "react-icons/ai";
import { IoClose, IoChevronDown } from "react-icons/io5";
import { BsChatSquareText } from "react-icons/bs";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function Details({ isOpen, setIsOpen }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    mobile: "",
    description: "",
    helpCategory: ""
  });

  // const [isOpen, setIsOpen]= useState(false)
  const [charCount, setCharCount] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleNewMessage = () => {
    setFormData({
      name: '',
      email: '',
      mobile: '',
      helpCategory: '',
      description: '',
      terms: false
    });
    setCharCount(0);
    setIsSubmitted(false);
  };

  // const [isOpen, setIsOpen] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (name === 'description') {
      setCharCount(value.length);
    }
  };

  const { createDoc, loading, error, isCompleted } = useFrappeCreateDoc();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await createDoc("Lead", {
        first_name: formData.name,
        email_id: formData.email,
        mobile_no: formData.mobile,
        status: 'Open',
        custom_lead_category: formData.helpCategory
      });
    } catch (err) {
      console.error("Error Creating User:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show success toast when record creation is completed
  useEffect(() => {
    if (isCompleted) {
      toast.success("Got the details. Our team will contact you soon!");
      setFormData({ name: "", email: "", mobile: "", description: "", helpCategory: "" });
      setIsOpen(false);
    }
  }, [isCompleted]);

  // Show error toast if an error occurs
  useEffect(() => {
    if (error) {
      toast.error(`Error: ${error.message}`);
    }
  }, [error]);

  return (
    <>
      <ToastContainer 
        position="top-right" 
        autoClose={3000}
        toastClassName="rounded-lg shadow-md"
        progressClassName="bg-gradient-to-r from-[#0e2044] to-[#41b655]"
      />
      
      {/* Floating Get Help Button */}
      <div className="fixed bottom-8 right-8 z-50">
        <button
          onClick={() => setIsOpen(prevState => !prevState)}
          className="group relative flex items-center justify-center bg-gradient-to-br from-[#0e2044] to-[#41b655] text-white p-4 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
          style={{ width: '60px', height: '60px' }}
          aria-label="Contact Us"
        >
          <AiOutlineQuestionCircle size={28} className="text-white" />
          <span className="absolute opacity-0 group-hover:opacity-100 bg-gray-800 text-white text-sm px-2 py-1 rounded whitespace-nowrap -top-10 left-1/2 transform -translate-x-1/2 transition-opacity duration-300">
            Contact Us
          </span>
        </button>
      </div>

      {/* Modal - Positioned above the button */}
      {isOpen && (
        <div className="bg-white rounded-xl shadow-2xl w-96 fixed bottom-28 right-8 z-40 animate-fade-in-up">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-[#0e2044] to-[#41b655] p-4 rounded-t-xl text-white">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold">Need Help?</h2>
                <p className="text-xs opacity-90">We'll get back to you shortly</p>
              </div>
              <button
                className="text-white hover:text-gray-200 transition-colors"
                onClick={() => setIsOpen(false)}
                aria-label="Close"
              >
                <IoClose size={24} />
              </button>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {/* Name Field */}
            <div className="relative">
              <div className="relative">
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Full Name"
                  className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#41b655] focus:border-transparent transition-all"
                  required
                />
                <AiOutlineUser className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              </div>
            </div>

            {/* Email Field */}
            <div className="relative">
              <div className="relative">
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Email Address"
                  className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#41b655] focus:border-transparent transition-all"
                  required
                />
                <AiOutlineMail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              </div>
            </div>

            {/* Mobile Field */}
            <div className="relative">
              <div className="relative">
                <input
                  type="tel"
                  id="mobile"
                  name="mobile"
                  value={formData.mobile}
                  onChange={handleChange}
                  placeholder="Phone Number"
                  className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#41b655] focus:border-transparent transition-all"
                  required
                />
                <AiOutlinePhone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              </div>
            </div>

            {/* Category Field */}
            <div className="relative">
              <div className="relative">
                <select
                  id="helpCategory"
                  name="helpCategory"
                  value={formData.helpCategory}
                  onChange={handleChange}
                  className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#41b655] focus:border-transparent appearance-none transition-all"
                  required
                >
                  <option value="" disabled className="text-gray-400">Select a category</option>
                  <option value="Incentive">Incentive</option>
                  <option value="Approvals">Approvals</option>
                  <option value="Land">Land</option>
                  <option value="Employment">Employment</option>
                  <option value="Suppliers">Suppliers</option>
                </select>
                <BsChatSquareText className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
                <IoChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" size={18} />
              </div>
            </div>

            {/* Description Field */}
            <div className="relative">
              <div className="relative">
                <textarea
                  id="description"
                  name="description"
                  rows="3"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="How can we help you?"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#41b655] focus:border-transparent transition-all resize-none"
                  maxLength="300"
                ></textarea>
                <div className="flex justify-between mt-1">
                  <p className="text-xs text-gray-500">Brief description of your needs</p>
                  <span className={`text-xs ${charCount > 300 ? 'text-red-500' : 'text-gray-500'}`}>
                    {charCount}/300
                  </span>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all duration-300 hover:shadow-md disabled:opacity-70"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Sending...
                  </>
                ) : (
                  'Send Message'
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}

export default Details;