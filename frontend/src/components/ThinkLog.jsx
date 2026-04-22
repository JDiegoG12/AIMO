/**
 * ThinkLog — Panel de cadena de pensamiento de AIMO por turno.
 * Muestra el contenido interno <think>...</think> separado de la
 * respuesta visible, para análisis de investigación.
 */

export default function ThinkLog({ messages, onClose }) {
  const turns = messages
    .filter(m => m.role === 'aimo' && m.thinking)
    .map((m, i) => ({ turn: i + 1, thinking: m.thinking, text: m.text }))

  return (
    <div className="ap-overlay" onClick={onClose}>
      <div className="ap-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Cadena de pensamiento">

        {/* Header */}
        <div className="ap-header">
          <span className="ap-title">💭 CADENA DE PENSAMIENTO</span>
          <button className="ap-close" onClick={onClose} aria-label="Cerrar panel">✕</button>
        </div>

        <div className="ap-info-banner">
          <span>✦ Razonamiento interno de AIMO (tokens &lt;think&gt;) — no visible al usuario.</span>
        </div>

        <div className="ap-body">
          {turns.length === 0 ? (
            <div className="ap-empty">
              <span>💭</span>
              <p>Sin pensamientos registrados.<br />Conversa con AIMO para ver<br />su razonamiento interno.</p>
            </div>
          ) : (
            turns.map(({ turn, thinking, text }) => (
              <div className="ap-card" key={turn}>
                <p className="ap-response-preview">
                  <span className="ap-preview-label">AIMO:</span> {text.slice(0, 90)}{text.length > 90 ? '…' : ''}
                </p>

                <div className="ap-card-hdr">
                  <span className="ap-turn">TURNO {turn}</span>
                  <span className="think-tag-label">&lt;think&gt;</span>
                </div>

                <div className="think-block">
                  {thinking}
                </div>
              </div>
            ))
          )}
        </div>

      </div>
    </div>
  )
}