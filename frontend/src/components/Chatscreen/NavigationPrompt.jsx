import React, { useEffect } from "react";
import {
  UNSAFE_NavigationContext as NavigationContext,
  useLocation
} from "react-router-dom";

export default function NavigationPrompt({ message, when = true, onConfirm }) {
  const { navigator } = React.useContext(NavigationContext);
  const location = useLocation();

  useEffect(() => {
    if (!when) return;

    const push = navigator.push;
    const replace = navigator.replace;

    navigator.push = (...args) => {
      const [to, options] = args;
      const confirmed = window.confirm(message);
      if (confirmed) {
        if (onConfirm) onConfirm(); // 🔹 reset state in parent
        push.call(navigator, to, options);
      }
    };

    navigator.replace = (...args) => {
      const [to, options] = args;
      const confirmed = window.confirm(message);
      if (confirmed) {
        if (onConfirm) onConfirm(); // 🔹 reset state in parent
        replace.call(navigator, to, options);
      }
    };

    return () => {
      navigator.push = push;
      navigator.replace = replace;
    };
  }, [when, message, navigator, location, onConfirm]);

  return null;
}
