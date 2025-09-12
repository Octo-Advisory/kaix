import { useState, useEffect } from 'react';
// import localforage from 'localforage';
import Cookies from 'js-cookie';


/**
 * Hook to persist and toggle boolean state using localForage
 */
// export default function usePersistedToggle(key, initialValue = false) {
//   const [state, setState] = useState(initialValue);

//   // Load saved state on mount
//   useEffect(() => {
//     localforage.getItem(key)
//       .then((saved) => {
//         if (typeof saved === 'boolean') {
//           setState(saved);
//         }
//       })
//       .catch((err) => {
//         console.error(`Failed to load ${key} from localForage`, err);
//       });
//   }, [key]);

//   // Save state when it changes
//   useEffect(() => {
//     localforage.setItem(key, state).catch((err) => {
//       console.error(`Failed to save ${key} to localForage`, err);
//     });
//   }, [key, state]);

//   // Toggle function
//   const toggle = () => setState((prev) => !prev);

//   return [state, toggle];
// }

export default function usePersistedToggle(key, initialValue = false) {
  const [state, setState] = useState(initialValue);

  // Load saved state from cookies on mount
  useEffect(() => {
    const cookieValue = Cookies.get(key);
    if (cookieValue === 'true') {
      setState(true);
    } else if (cookieValue === 'false') {
      setState(false);
    }
  }, [key]);

  // Save state to cookies when it changes
  useEffect(() => {
    Cookies.set(key, state.toString(), { expires: 365 }); // Expires in 1 year
  }, [key, state]);

  // Toggle function
  const toggle = () => setState((prev) => !prev);

  return [state, toggle];
}
