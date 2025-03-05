import React from 'react'
import { useNavigate } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";

function Backtochat() {
    const navigate = useNavigate();
    return (
        <>
            <div className="p-1 text-center">
                <button
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-2xl shadow-md hover:bg-blue-600 transition"
                    onClick={() => navigate("/")}
                >
                    <FaArrowLeft /> Back to Chat
                </button>
            </div></>
    )
}

export default Backtochat
