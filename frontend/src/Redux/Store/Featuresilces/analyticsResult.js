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
        clearAnalyticsResult : (state) => {
            state.analyticsResult = [];
        }
    }
})

export const {addAnalyticsResult,clearAnalyticsResult } = anayticsSlice.actions;
export default anayticsSlice.reducer;