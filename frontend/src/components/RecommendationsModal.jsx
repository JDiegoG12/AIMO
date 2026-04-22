/**
 * RecommendationsModal — Shows the final AIMO recommendations in a
 * scrollable, readable panel. Auto-opens when the pipeline completes.
 */
export default function RecommendationsModal({ text, onClose }) {
  if (!text) return null

  // Split on newlines so numbered lists and paragraphs render correctly
  const lines = text.split('\n')

  return (
    <div className="rec-overlay" onClick={onClose}>
      <div className="rec-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Recomendaciones de AIMO">

        {/* Header */}
        <div className="rec-header">
          <span className="rec-title">★ RECOMENDACIONES DE AIMO</span>
          <button className="ap-close" onClick={onClose} aria-label="Cerrar">✕</button>
        </div>

        {/* Content */}
        <div className="rec-body">
          {lines.map((line, i) => {
            const trimmed = line.trim()
            if (!trimmed) return <div key={i} className="rec-spacer" />
            // Style numbered items (1. 2. 3.) differently
            const isItem = /^\d+\./.test(trimmed)
            return (
              <p key={i} className={isItem ? 'rec-item' : 'rec-text2'}>
                {trimmed}
              </p>
            )
          })}
        </div>

        {/* Footer */}
        <div className="rec-footer">
          <span className="rec-footer-note">★ CONVERSACIÓN FINALIZADA — Reinicia para comenzar de nuevo</span>
        </div>

      </div>
    </div>
  )
}