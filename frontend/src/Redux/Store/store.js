import { configureStore, isPending } from '@reduxjs/toolkit';
import counterReducre from '../Store/Featuresilces/test'
import chatReducer from '../Store/Featuresilces/chat'

export const store = configureStore({
  reducer: {
    counter : counterReducre,
    chat : chatReducer
  },
});
