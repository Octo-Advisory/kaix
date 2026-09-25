import { createSlice } from '@reduxjs/toolkit'

const initialState = {
    feasibility_id : null
}

export const feasibilitySlice = createSlice({
    name: 'feasibility',
    initialState,
    reducers: {
        addFeasibilityId: (state, action) => {
            state.feasibility_id = action.payload
        },
        // clearAiresponse: (state) =>{
        //     state.feasibility_id = null;
        // },
    }
})

export const { addFeasibilityId, clearAiresponse} = feasibilitySlice.actions;
export default feasibilitySlice.reducer;