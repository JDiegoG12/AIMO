/**
 * SpeechBubble — Pixel-art RPG speech bubble.
 * Shows typewriter text with blinking cursor,
 * or animated dots while the agent is loading.
 */
export default function SpeechBubble({ text, isTyping, isLoading }) {
  return (
    <div className="speech-bubble-pixel" role="status" aria-live="polite">
      {/* decorative star in corner */}
      <span className="bubble-star" aria-hidden>⭐</span>

      {isLoading ? (
        <span className="loading-dots" aria-label="AIMO pensando">
          <span>●</span><span>●</span><span>●</span>
        </span>
      ) : (
        <>
          {text || '\u00A0'}
          {isTyping && <span className="tw-cursor" aria-hidden />}
        </>
      )}
    </div>
  )
}
