import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  confirmations: {
    // chatId: { message: "Do you want to proceed?", status: "pending|yes|no",options: [] }
  }
};

const confirmationSlice = createSlice({
  name: 'confirmation',
  initialState,
  reducers: {
    // Set new confirmation message for a chat
    setConfirmation(state, action) {
      const { chatId, message, options } = action.payload;
      state.confirmations[chatId] = { message, status: true , options : options};
    },

    // Update user's choice (yes / no)
    setConfirmationResponse(state, action) {
      const { chatId, status } = action.payload;
      if (state.confirmations[chatId]) {
        state.confirmations[chatId].status = status;
      }
    },

    // Completely remove confirmation for a chat
    clearConfirmation(state, action) {
      const chatId  = action.payload;
      if (!chatId) return;
      delete state.confirmations[chatId];
    }
  }
});

export const { setConfirmation, setConfirmationResponse, clearConfirmation } = confirmationSlice.actions;
export default confirmationSlice.reducer;
