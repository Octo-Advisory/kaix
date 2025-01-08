import { useEffect, useRef } from 'react';

function useChatScroll(dep) {
  const ref = useRef(null); // Create a ref for the chat container

  useEffect(() => {
    // Scroll the chat container to the bottom when the dependency changes
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [dep]); // Dependency on `dep`, which could be messages or any other state

  return ref; // Return the ref
}

export default useChatScroll;
