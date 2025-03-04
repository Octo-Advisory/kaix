import { createSlice } from '@reduxjs/toolkit'

const initialState = {
    analyticsResult : []
}

export const anayticsSlice = createSlice({
    name: 'analytics',
    initialState,
    reducers: {
        addAnalyticsResult: (state, action) => {
            console.log("state and actoin for annalytics",state,action);
            state.analyticsResult.push(action.payload)
        },
    }
})

export const {addAnalyticsResult } = anayticsSlice.actions;
export default anayticsSlice.reducer;