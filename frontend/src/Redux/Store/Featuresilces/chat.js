import { createSlice } from '@reduxjs/toolkit'

const initialState ={
    // messages : [{
    //     sender: 'ai',
    //     text: 'Hello, How can i assist today?',
    //     timestamp: new Date().toISOString(),
    //   }],
    messages : [],
    chatID : null
}

export const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        addMessage: (state, action) => {
            state.messages.push(action.payload); // Adds a new message to the array
        },
        addChatId: (state,action) => {
            state.chatID = action.payload
        }
    }
})

export const { addMessage,addChatId } = chatSlice.actions;
export default chatSlice.reducer;