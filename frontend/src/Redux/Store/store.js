import { configureStore, isPending } from '@reduxjs/toolkit';
import counterReducre from '../Store/Featuresilces/test'
import chatReducer from '../Store/Featuresilces/chat'
import aiReducer from '../Store/Featuresilces/aiResponse'
import validateReducer from '../Store/Featuresilces/validation'
import analyticsReducer from '../Store/Featuresilces/analyticsResult'

export const store = configureStore({
  reducer: {
    counter : counterReducre,
    chat : chatReducer,
    ai : aiReducer,
    validate : validateReducer,
    analytics : analyticsReducer
  },
});