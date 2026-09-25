// import { configureStore, isPending } from '@reduxjs/toolkit';
// import counterReducre from '../Store/Featuresilces/test'
// import chatReducer from '../Store/Featuresilces/chat'
// import aiReducer from '../Store/Featuresilces/aiResponse'
// import validateReducer from '../Store/Featuresilces/validation'
// import analyticsReducer from '../Store/Featuresilces/analyticsResult'
// import detailsReducer from '../Store/Featuresilces/detailform'
// import feasibilityReducer from '../Store/Featuresilces/Feasibility'

// export const store = configureStore({
//   reducer: {
//     counter : counterReducre,
//     chat : chatReducer,
//     ai : aiReducer,
//     validate : validateReducer,
//     analytics : analyticsReducer,
//     details : detailsReducer,
//     feasibility : feasibilityReducer
//   },
// });

// store.js
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import storage from 'redux-persist/lib/storage';
import { persistStore, persistReducer } from 'redux-persist';

import counterReducer from '../Store/Featuresilces/test';
import chatReducer from '../Store/Featuresilces/chat';
import aiReducer from '../Store/Featuresilces/aiResponse';
import validateReducer from '../Store/Featuresilces/validation';
import analyticsReducer from '../Store/Featuresilces/analyticsResult';
import detailsReducer from '../Store/Featuresilces/detailform';
import feasibilityReducer from '../Store/Featuresilces/Feasibility';
import confirmationReducer from '../Store/Featuresilces/confirmation';

const rootReducer = combineReducers({
  counter: counterReducer,
  chat: chatReducer,
  ai: aiReducer,
  validate: validateReducer,
  analytics: analyticsReducer,
  details: detailsReducer,
  feasibility: feasibilityReducer,
  confirmation: confirmationReducer
});

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['confirmation'] // only keep confirmation slice
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({ serializableCheck: false })
});

export const persistor = persistStore(store);
