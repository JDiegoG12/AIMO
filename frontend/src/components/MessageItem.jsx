import { useState, useEffect, useRef } from "react";

const TYPEWRITER_SPEED = 18; // ms per character — fast but readable

// Simple inline markdown renderer: **bold**, line breaks, numbered lists
function renderMarkdown(text) {
  return text.split("\n").map((line, lineIdx) => {
    // Split on **...** pairs
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const rendered = parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
    return (
      <span key={lineIdx}>
        {lineIdx > 0 && <br />}
        {rendered}
      </span>
    );
  });
}

export default function MessageItem({ message, isTyping, onTypingDone, className = "" }) {
  const isUser = message.role === "user";
  const [displayed, setDisplayed] = useState(
    isTyping ? "" : message.text
  );
  const timerRef = useRef(null);
  const doneCalledRef = useRef(false);
  // Ref attached to this bubble — used for continuous scroll while typing
  const bubbleRef = useRef(null);

  useEffect(() => {
    if (!isTyping) {
      setDisplayed(message.text);
      return;
    }

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

  // Scroll this bubble into view on every character while typing
  useEffect(() => {
    if (isTyping && bubbleRef.current) {
      bubbleRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [displayed, isTyping]);

  return (
    <article
      ref={bubbleRef}
      className={`msg-item msg-bubble-wrap ${isUser ? "wrap-user" : "wrap-aimo"} ${className}`.trim()}
    >
      <p
        className={`msg-item-text msg-pixel-bubble ${isUser ? "bubble-user" : "bubble-aimo"}`}
      >
        <span className="msg-role-prefix">{isUser ? "[ TÚ ]" : "[ AIMO ]"}</span>{" "}
        {renderMarkdown(displayed)}
        {isTyping && <span className="tw-cursor" aria-hidden>_</span>}
      </p>
    </article>
  );
}