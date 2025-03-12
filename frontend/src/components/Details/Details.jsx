import { useFrappeCreateDoc } from 'frappe-react-sdk';
import React, { useEffect, useState } from 'react';
import { AiOutlineQuestionCircle } from "react-icons/ai";
import { IoClose } from "react-icons/io5";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function Details() {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    mobile: "",
    description: "",
    helpCategory: ""
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const { createDoc, loading, error, isCompleted } = useFrappeCreateDoc();

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("form data", formData);
    try {
      await createDoc("Lead", {
        first_name: formData.name,
        email_id: formData.email,
        mobile_no: formData.mobile,
        status: 'Open',
        custom_lead_category : formData.helpCategory
      });
    } catch (err) {
      console.error("Error Creating User:", err);
    }
  };

  // Show success toast when record creation is completed
  useEffect(() => {
    if (isCompleted) {
      toast.success("Got the details. Our team will contact you soon!");
      setFormData({ name: "", email: "", mobile: "", description: "", helpCategory: "" });
      setIsOpen(false)
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
      {/* Floating Get Help Button */}
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="fixed bottom-8 right-6">
        <button
          onClick={() => setIsOpen(prevState => !prevState)}
          className="group relative flex items-center bg-[#199b7d] text-white px-3 py-2 rounded-full shadow-lg transition"
        >
          <AiOutlineQuestionCircle size={30} className="text-white" />
          <span className="hidden group-hover:block ml-2 transition-opacity">Contact Us</span>
        </button>
      </div>


      {/* Modal */}
      {isOpen && (
        // <div className="fixed inset-0 flex justify-center items-center">

        // </div>
        <div className="bg-[#40c6db] p-6 rounded-lg shadow-lg w-96 fixed bottom-20 right-6">
          {/* Close Button */}
          <button
            className="absolute top-2 right-2 text-gray-600 hover:text-gray-900"
            onClick={() => setIsOpen(false)}
          >
            <IoClose size={24} />
          </button>

          <h2 className="text-xl font-bold mb-4">Need Help?</h2>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block">Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#242f6a]"
              required/>
            </div>
            <div>
              <label className="block">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#242f6a]"
              required/>
            </div>
            <div>
              <label className="block">Mobile Number</label>
              <input
                type="tel"
                name="mobile"
                value={formData.mobile}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#242f6a]"
              required/>
            </div>
            <div>
              <label className="block">Help Category</label>
              <select
                name="helpCategory"
                value={formData.helpCategory}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#242f6a]"
              required>
                <option value="" disabled>--- Select Category ---</option>
                <option value="Incentive">Incentive</option>
                <option value="Technical Support">Approvals</option>
                <option value="General Inquiry">Land</option>
                <option value="General Inquiry">Employment</option>
                <option value="General Inquiry">Suppliers</option>
                <option value="Billing">IT</option>
                <option value="General Inquiry">Website</option>
                <option value="Other">Others</option>
              </select>
            </div>
            <div>
              <label className="block">Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#242f6a] h-32 resize-none"
              ></textarea>
            </div>
            <button
              type="submit"
              className="w-full bg-[#242f6a] hover:bg-[#3f4ea0] text-white py-2 rounded-lg"
            >
              {loading ? 'Creating data...' : 'Send Message'}
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default Details;