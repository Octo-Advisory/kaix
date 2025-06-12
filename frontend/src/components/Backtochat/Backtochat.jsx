import { useEffect, useState } from 'react'
import { useNavigate } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";
import { useDispatch, useSelector } from 'react-redux';
import { clearAiresponse } from '../../Redux/Store/Featuresilces/aiResponse';
import { clearAnalyticsResult } from '../../Redux/Store/Featuresilces/analyticsResult'
import { useFrappeAuth, useFrappeDeleteDoc, useFrappeGetDocList, useFrappeUpdateDoc } from 'frappe-react-sdk';
import { removeVendorResult } from '../../Redux/Store/Featuresilces/validation';

function Backtochat() {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const chatId = useSelector((state) => state.chat.chatID);
    const { updateDoc, loading, error } = useFrappeUpdateDoc("Session");
     const { currentUser } = useFrappeAuth();
     const [latestChatId, setLatestChatId] = useState(null);

     const { data: sessions, isLoading } = useFrappeGetDocList('Session', {
        fields: ['name'],
        filters: currentUser ? [['owner', '=', currentUser]] : [],
        orderBy: {
            field: 'modified',
            order: 'desc'
        },
        limit: 1
    });

    useEffect(() => {
        if (sessions && sessions.length > 0) {
            setLatestChatId(sessions[0].name);
        }
    }, [sessions]);

    const deleteAllProgressRecords = async (chatId) => {
        try {
            await updateDoc("Session", chatId, { progress: [] });
        } catch (error) {
            console.error("Error deleting child table records:", error);
        }
    };

    const clearProgressAndIntention = async (chatId) => {
        try {
            await updateDoc('Session', chatId, {
                progress: [],
                user_intension: "",
                session_states: []
            });
        } catch (error) {
            console.error("Error updating session:", error);
        }
    };

    const handleClick = async () => {
        dispatch(clearAiresponse())
        dispatch(clearAnalyticsResult())
        dispatch(removeVendorResult()) 
        // deleteAllProgressRecords(chatId)
        // try {
        //     await updateDoc("Session", chatId, {
        //         user_intension: "",
        //     });
        //     console.log("Updated Successfully");
        // } catch (err) {
        //     console.error("Error Updating:", err);
        // }
       sessionStorage.removeItem("guest_session_id"); 
       if (latestChatId && currentUser) {
            await clearProgressAndIntention(latestChatId);
            setTimeout(() => {
                navigate(`/chat/${latestChatId}`);        
            }, 0);
        } else {
            setTimeout(() => {
                navigate('/chat');        
            }, 0);
        }
    }
    return (    
        <>
            <div className="p-1 text-center">
                <button
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#0e2044] to-[#41b655] text-white rounded-lg shadow-md hover:bg-blue-600 transition"
                    onClick={handleClick}
                >
                    <FaArrowLeft /> Back to Chat
                </button>
            </div></>
    )
}

export default Backtochat