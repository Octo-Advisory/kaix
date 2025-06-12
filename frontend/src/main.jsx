import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { FrappeProvider } from 'frappe-react-sdk'
import { store } from './Redux/Store/store.js'
import { Provider } from 'react-redux';
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary.jsx'


const getSiteName = () => {
  // @ts-ignore
  if (window.frappe?.boot?.versions?.frappe && (window.frappe.boot.versions.frappe.startsWith('15') || window.frappe.boot.versions.frappe.startsWith('16'))) {
    // @ts-ignore
    return window.frappe?.boot?.sitename ?? import.meta.env.VITE_SITE_NAME
  }
  return import.meta.env.VITE_SITE_NAME

}
// console.log("socket port",import.meta.env.VITE_SOCKET_PORT,getSiteName());

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <FrappeProvider socketPort={import.meta.env.VITE_SOCKET_PORT} siteName={getSiteName()}>
      <Provider store={store}>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </Provider>
    </FrappeProvider>
  </StrictMode>
)