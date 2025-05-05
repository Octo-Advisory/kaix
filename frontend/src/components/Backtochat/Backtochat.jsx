import React from 'react'
import { useNavigate } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";
import { useDispatch, useSelector } from 'react-redux';
import { clearAiresponse } from '../../Redux/Store/Featuresilces/aiResponse';
import { clearAnalyticsResult } from '../../Redux/Store/Featuresilces/analyticsResult'
import { useFrappeDeleteDoc, useFrappeUpdateDoc } from 'frappe-react-sdk';
import { removeVendorResult } from '../../Redux/Store/Featuresilces/validation';

function Backtochat() {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const chatId = useSelector((state) => state.chat.chatID);
    const { updateDoc, loading, error } = useFrappeUpdateDoc("Session");

    const deleteAllProgressRecords = async (chatId) => {
        try {
            await updateDoc("Session", chatId, { progress: [] });
        } catch (error) {
            console.error("Error deleting child table records:", error);
        }
    };

    const handleClick = async () => {
        dispatch(clearAiresponse())
        dispatch(clearAnalyticsResult())
        dispatch(removeVendorResult()) 
        deleteAllProgressRecords(chatId)
        try {
            await updateDoc("Session", chatId, {
                user_intension: "",
            });
            console.log("Updated Successfully");
        } catch (err) {
            console.error("Error Updating:", err);
        }
        navigate("/chat")
    }
    return (    
        <>
            <div className="p-1 text-center">
                <button
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-2xl shadow-md hover:bg-blue-600 transition"
                    onClick={handleClick}
                >
                    <FaArrowLeft /> Back to Chat
                </button>
            </div></>
    )
}

export default Backtochat