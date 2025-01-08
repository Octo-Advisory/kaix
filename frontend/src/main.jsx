import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { FrappeProvider } from 'frappe-react-sdk'
import { store } from './Redux/Store/store.js'
import { Provider } from 'react-redux';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <FrappeProvider >
    <Provider store={store}>
      <App />
    </Provider>,
    </FrappeProvider>
  </StrictMode>,
)
