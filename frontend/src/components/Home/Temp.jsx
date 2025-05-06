import React, { useEffect, useState } from "react";
import {
  useFrappeGetDoc,
  useFrappeUpdateDoc,
  useFrappeCreateDoc,
  useFrappeAuth,
} from "frappe-react-sdk";

export default function ChatApp() {
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const { currentUser } = useFrappeAuth();

  const { createDoc } = useFrappeCreateDoc();
  const { updateDoc } = useFrappeUpdateDoc();
  const {
    data: session,
    isLoading,
    error,
    mutate,
  } = useFrappeGetDoc("Session", sessionId, {
    enabled: !!sessionId,
  });

  // Create or fetch session based on user auth state
  useEffect(() => {
    const initializeSession = async () => {
      if (currentUser) {
        // For logged in users - try to find existing session
        try {
          const response = await fetch(
            `/api/method/frappe.client.get_list?doctype=Session&fields=["name"]&filters=[["user","=","${currentUser}"]]&limit_page_length=1`
          );
          const result = await response.json();
          
          if (result.message && result.message.length > 0) {
            // Use existing session
            setSessionId(result.message[0].name);
          } else {
            // Create new session for logged in user
            await createNewSession(currentUser);
          }
        } catch (error) {
          console.error("Error fetching user session:", error);
          // Fallback to creating new session
          await createNewSession(currentUser);
        }
      } else {
        // For guest users - always create new session
        await createNewSession();
      }
    };

    const createNewSession = async (user = null) => {
      const nowTime = new Date();
      const formattedTime = `${nowTime.getFullYear()}-${String(
        nowTime.getMonth() + 1
      ).padStart(2, "0")}-${String(nowTime.getDate()).padStart(
        2,
        "0"
      )} ${String(nowTime.getHours()).padStart(2, "0")}:${String(
        nowTime.getMinutes()
      ).padStart(2, "0")}:${String(nowTime.getSeconds()).padStart(2, "0")}`;

      const doc = { 
        time: formattedTime,
        ...(user && { user: user }) // Add user field if authenticated
      };
      
      const resp = await createDoc("Session", doc);
      setSessionId(resp.name);
    };

    if (!sessionId) {
      initializeSession();
    }
  }, [sessionId, createDoc, currentUser]);

  const sendMessage = async () => {
    if (!input.trim() || !session) return;

    const updatedHistory = [
      ...(session.chat_history || []),
      { user: input, ai: "" },
    ];

    await updateDoc("Session", session.name, {
      chat_history: updatedHistory,
    });

    setInput("");
    mutate();

    // Simulate AI response
    setTimeout(async () => {
      const withAIReply = [...updatedHistory];
      const lastIndex = withAIReply.length - 1;
      withAIReply[lastIndex].ai = `AI Response to "${input}"`;

      await updateDoc("Session", session.name, {
        chat_history: withAIReply,
      });

      mutate();
    }, 1000);
  };

  const renderMessages = () => {
    return (session?.chat_history || []).map((chat, idx) => (
      <div key={idx} className="my-2">
        {chat.user && (
          <div className="text-right bg-blue-200 rounded p-2 max-w-xs ml-auto">
            <p className="text-sm">{chat.user}</p>
            <small className="text-xs text-gray-600">
              {currentUser ? currentUser : "Guest"}
            </small>
          </div>
        )}
        {chat.ai && (
          <div className="text-left bg-green-200 rounded p-2 max-w-xs mr-auto mt-1">
            <p className="text-sm">{chat.ai}</p>
            <small className="text-xs text-gray-600">AI</small>
          </div>
        )}
      </div>
    ));
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <div className="mb-2 text-sm text-gray-600">
        {currentUser ? (
          <p>Logged in as: <strong>{currentUser}</strong></p>
        ) : (
          <p>Guest session</p>
        )}
      </div>
      
      <div className="h-96 overflow-y-auto border rounded p-2 mb-4 bg-gray-100">
        {!sessionId || isLoading ? (
          <p>Loading chat...</p>
        ) : error ? (
          <p>Error loading session.</p>
        ) : (
          renderMessages()
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 border p-2 rounded"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message..."
        />
        <button
          onClick={sendMessage}
          className="bg-blue-500 text-white px-4 py-2 rounded"
          disabled={!sessionId}
        >
          Send
        </button>
      </div>
    </div>
  );
}