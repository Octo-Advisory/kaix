// hooks/useAIResponse.js
import { useState } from 'react';

export const useAIResponse = () => {
  // const [loading, setLoading] = useState(false);

  const fetchAIResponse = async (userMessage) => {
    const API_URL =
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyA0re42NbCbdFuTIsPnvreArTxRJvjkMUA";

    const requestBody = {
      contents: [
        {
          parts: [{ text: userMessage }],
        },
      ],
    };

    // setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      const aiMessage = data?.candidates[0]?.content?.parts[0].text.trim() || "I'm sorry, I couldn't process that.";
      return aiMessage;
    } catch (error) {
      console.error('Error fetching AI response:', error);
      return "Something went wrong. Please try again.";
    } finally {
      // setLoading(false);
    }
  };

  return { fetchAIResponse };
};
