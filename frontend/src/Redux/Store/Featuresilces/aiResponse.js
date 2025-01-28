import { createSlice } from '@reduxjs/toolkit'

const initialState = {
    aiReponse : []
}

export const aiSlice = createSlice({
    name: 'ai',
    initialState,
    reducers: {
        addAIresponse: (state, action) => {
            console.log("action and state", action, state);
            state.aiReponse.push(action.payload)
        },
        clearAiresponse: (state) =>{
            state.aiReponse = [];
        }
    }
})

export const { addAIresponse, clearAiresponse } = aiSlice.actions;
export default aiSlice.reducer;