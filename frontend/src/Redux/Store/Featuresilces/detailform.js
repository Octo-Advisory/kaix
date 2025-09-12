import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  isOpen: false,
  formData: {
    name: '',
    email: '',
    mobile: '',
    description: '',
    helpCategory: ''
  }
};

const detailsSlice = createSlice({
  name: 'details',
  initialState,
  reducers: {
    setIsOpen: (state, action) => {
      state.isOpen = action.payload;
    },
    setFormData: (state, action) => {
      state.formData = {
        ...state.formData,
        ...action.payload
      };
    },
    resetForm: (state) => {
      state.formData = initialState.formData;
    }
  }
});

export const { setIsOpen, setFormData, resetForm } = detailsSlice.actions;
export default detailsSlice.reducer;