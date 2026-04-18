/**
 * SpeechBubble
 *
 * Muestra siempre el texto de presentación de AIMO quemado.
 * Cuando la fase es "loading", superpone los tres puntos animados
 * sobre el texto (no lo reemplaza) para indicar que AIMO está pensando.
 *
 * Props:
 *   phase: string — fase actual del juego ("intro" | "user_turn" | "loading" | "responding")
 */

const STATIC_TEXT =
  "¡Hola! Soy AIMO, tu compañero de apoyo emocional. Estoy aquí para escucharte sin juzgarte.";

export default function SpeechBubble({ phase }) {
  const isLoading = phase === "loading";

  return (
    <div
      className={`speech-bubble-pixel${isLoading ? " bubble-thinking" : ""}`}
      role="status"
      aria-live="polite"
    >
      {/* Texto quemado: siempre visible */}
      <span className={`bubble-static-text${isLoading ? " bubble-text-dimmed" : ""}`}>
        {STATIC_TEXT}
      </span>

      {/* Overlay de puntos: solo visible cuando AIMO está pensando */}
      {isLoading && (
        <span className="bubble-loading-overlay" aria-label="AIMO pensando">
          <span className="dot-pulse" />
          <span className="dot-pulse" />
          <span className="dot-pulse" />
        </span>
      )}
    </div>
  );
}