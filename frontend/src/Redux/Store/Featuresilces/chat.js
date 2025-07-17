import { createSlice } from '@reduxjs/toolkit'

const initialState ={
    // messages : [{
    //     sender: 'ai',
    //     text: 'Hello, How can i assist today?',
    //     timestamp: new Date().toISOString(),
    //   }],
    messages : [],
    chatID : null,
    lastId: null,
    addInput : null
}

export const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        addMessage: (state, action) => {
            state.messages = [...state.messages, action.payload]; // Adds a new message to the array
        },
        addChatId: (state,action) => {
            state.chatID = action.payload
        },
        addLastResultId: (state,action) => {
            state.lastId = action.payload
        },
        addInputtext: (state,action) => {
            state.addInput = action.payload
        }
    }
})

export const { addMessage,addChatId,addLastResultId,addInputtext } = chatSlice.actions;
export default chatSlice.reducer;