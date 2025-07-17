import { useState, useEffect } from "react";

const Typewriter = ({ text, speed = 30 }) => {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      setDisplayedText((prev) => prev + text.charAt(index));
      index++;
      if (index >= text.length) {
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <ReactMarkdown rehypePlugins={[rehypeRaw]}>
      {displayedText}
    </ReactMarkdown>
  );
};

export default Typewriter;
