import { createSlice } from '@reduxjs/toolkit'

const initialState = {
    aiReponse : [],
    selectedOption : null
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
        },
        addSelectedoption: (state,action) =>{
            state.selectedOption = action.payload
        }
    }
})

export const { addAIresponse, clearAiresponse ,addSelectedoption} = aiSlice.actions;
export default aiSlice.reducer;