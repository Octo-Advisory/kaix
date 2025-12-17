import { createSlice } from '@reduxjs/toolkit'

const initialState ={
    validation_result : []
}

export const validateSlice = createSlice({
    name:'validate',
    initialState,
    reducers : {
        addResult: (state, action) => {
            state.validation_result.push(action.payload); // Adds a new message to the array
        },
        removeVendorResult: (state) => {
            state.validation_result = []
        }
    }
})



export const { addResult ,removeVendorResult} = validateSlice.actions;
export default validateSlice.reducer;