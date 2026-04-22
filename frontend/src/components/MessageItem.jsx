import { useState, useEffect, useRef } from "react";

const TYPEWRITER_SPEED = 18; // ms per character — fast but readable

export default function MessageItem({ message, isTyping, onTypingDone, className = "" }) {
  const isUser = message.role === "user";
  const [displayed, setDisplayed] = useState(
    // User messages and already-rendered AIMO messages show full text immediately
    isTyping ? "" : message.text
  );
  const timerRef = useRef(null);
  const doneCalledRef = useRef(false);

  useEffect(() => {
    if (!isTyping) {
      // If this message is no longer the typing one (e.g. after reset), show full text
      setDisplayed(message.text);
      return;
    }

    // Start typewriter
    setDisplayed("");
    doneCalledRef.current = false;
    let i = 0;
    const text = message.text;

    timerRef.current = setInterval(() => {
      i += 1;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(timerRef.current);
        if (!doneCalledRef.current) {
          doneCalledRef.current = true;
          onTypingDone?.();
        }
      }
    }, TYPEWRITER_SPEED);

    return () => clearInterval(timerRef.current);
  }, [isTyping]); // eslint-disable-line

  return (
    <article
      className={`msg-item msg-bubble-wrap ${isUser ? "wrap-user" : "wrap-aimo"} ${className}`.trim()}
    >
      <p
        className={`msg-item-text msg-pixel-bubble ${isUser ? "bubble-user" : "bubble-aimo"}`}
      >
        <span className="msg-role-prefix">{isUser ? "[ TÚ ]" : "[ AIMO ]"}</span>{" "}
        {displayed}
        {isTyping && <span className="tw-cursor" aria-hidden>_</span>}
      </p>
    </article>
  );
}