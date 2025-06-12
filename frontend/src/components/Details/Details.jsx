import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useFrappeCreateDoc } from 'frappe-react-sdk';
import { AiOutlineQuestionCircle, AiOutlineUser, AiOutlineMail, AiOutlinePhone } from "react-icons/ai";
import { IoClose, IoChevronDown } from "react-icons/io5";
import { BsChatSquareText } from "react-icons/bs";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { setIsOpen, resetForm, setFormData } from '../../Redux/Store/Featuresilces/detailform';

function Details() {
  const dispatch = useDispatch();
  const { isOpen, formData } = useSelector(state => state.details);
  const [charCount, setCharCount] = useState(formData.description.length || 0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { createDoc, loading, error, isCompleted } = useFrappeCreateDoc();

  const handleChange = (e) => {
    const { name, value } = e.target;
    dispatch(setFormData({ [name]: value }));
    if (name === 'description') setCharCount(value.length);
  };

  const handleClose = () => {
    dispatch(setIsOpen(false));
    dispatch(resetForm());
    setCharCount(0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await createDoc("Lead", {
        first_name: formData.name,
        email_id: formData.email,
        mobile_no: formData.mobile,
        status: 'Open',
        custom_lead_category: formData.helpCategory,
        description: formData.description // optional
      });
    } catch (err) {
      console.error("Error Creating User:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Success toast
  useEffect(() => {
    if (isCompleted) {
      toast.success("Got the details. Our team will contact you soon!");
      handleClose();
    }
  }, [isCompleted]);

  // Error toast
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

      {/* Floating Contact Button */}
      <div className="fixed bottom-8 right-8 z-50">
        <button
          onClick={() => dispatch(setIsOpen(!isOpen))}
          className="group relative flex items-center justify-center bg-gradient-to-br from-[#0e2044] to-[#41b655] text-white p-4 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
          style={{ width: '60px', height: '60px' }}
          aria-label="Contact Us"
        >
          <AiOutlineQuestionCircle size={28} />
          <span className="absolute opacity-0 group-hover:opacity-100 bg-gray-800 text-white text-sm px-2 py-1 rounded whitespace-nowrap -top-10 left-1/2 transform -translate-x-1/2 transition-opacity duration-300">
            Contact Us
          </span>
        </button>
      </div>

      {/* Contact Form Modal */}
      {isOpen && (
        <div className="bg-white rounded-xl shadow-2xl w-96 fixed bottom-28 right-8 z-40 animate-fade-in-up">
          {/* Modal Header */}
          <div className="bg-gradient-to-r from-[#0e2044] to-[#41b655] p-4 rounded-t-xl text-white">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold">Need Help?</h2>
                <p className="text-xs opacity-90">We'll get back to you shortly</p>
              </div>
              <button onClick={handleClose} aria-label="Close">
                <IoClose size={24} />
              </button>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {/* Name */}
            <div className="relative">
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Full Name"
                className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:outline-none"
                required
              />
              <AiOutlineUser className="absolute left-3 top-3 text-gray-400" size={18} />
            </div>

            {/* Email */}
            <div className="relative">
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Email Address"
                className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:outline-none"
                required
              />
              <AiOutlineMail className="absolute left-3 top-3 text-gray-400" size={18} />
            </div>

            {/* Mobile */}
            <div className="relative">
              <input
                type="tel"
                name="mobile"
                value={formData.mobile}
                onChange={handleChange}
                placeholder="Phone Number"
                className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:outline-none"
                required
              />
              <AiOutlinePhone className="absolute left-3 top-3 text-gray-400" size={18} />
            </div>

            {/* Help Category */}
            <div className="relative">
              <select
                name="helpCategory"
                value={formData.helpCategory}
                onChange={handleChange}
                className="w-full px-4 pl-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:outline-none appearance-none"
                required
              >
                <option value="" disabled>Select a category</option>
                <option value="Incentive">Incentive</option>
                <option value="Approvals">Approvals</option>
                <option value="Land">Land</option>
                <option value="Employment">Employment</option>
                <option value="Suppliers">Suppliers</option>
              </select>
              <BsChatSquareText className="absolute left-3 top-3 text-gray-400" size={16} />
              <IoChevronDown className="absolute right-3 top-3 text-gray-400" size={18} />
            </div>

            {/* Description */}
            <div>
              <textarea
                name="description"
                rows="3"
                maxLength="300"
                value={formData.description}
                onChange={handleChange}
                placeholder="How can we help you?"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:outline-none resize-none"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Brief description of your needs</span>
                <span>{charCount}/300</span>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center py-2.5 px-4 rounded-lg text-white bg-gradient-to-r from-[#0e2044] to-[#41b655] hover:from-[#41b655] hover:to-[#0e2044] transition-all disabled:opacity-70"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0..." />
                  </svg>
                  Sending...
                </>
              ) : 'Send Message'}
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default Details;
