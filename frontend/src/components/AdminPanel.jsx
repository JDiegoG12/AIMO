import { useEffect, useRef } from 'react'

/**
 * AdminPanel — Panel de métricas AERI + G-Eval para el investigador.
 * Métricas activas: PT, FT, PD (AERI), Relevance, Semantically Appropriate.
 */

const METRICS =[
  { key: 'perspective_taking',       label: 'Perspective Taking',       abbr: 'PT',  cls: 'g', note: '',              invert: false },
  { key: 'fantasy',                  label: 'Fantasy',                  abbr: 'FT',  cls: 'y', note: '',              invert: false },
  { key: 'personal_distress',        label: 'Personal Distress',        abbr: 'PD',  cls: 'r', note: '↓ menor=mejor', invert: true  },
  // Usamos 'c' (cyan) para estas dos porque las clases 'b' y 'p' no existen en tu CSS
  { key: 'relevance',                label: 'Relevance',                abbr: 'REL', cls: 'c', note: '',              invert: false },
  { key: 'semantically_appropriate', label: 'Semantically Approp.',     abbr: 'SA',  cls: 'c', note: '',              invert: false },
]

function ScoreBar({ score, cls, invert }) {
  // Para PD (invertida) la barra visual representa el "bien" (score bajo = barra larga)
  const pct = invert ? ((6 - score) / 5) * 100 : (score / 5) * 100
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.width = '0%'
    const id = requestAnimationFrame(() =>
      requestAnimationFrame(() => { el.style.width = `${pct}%` })
    )
    return () => cancelAnimationFrame(id)
  }, [pct])

  return (
    <div className="ap-bar-wrap">
      <div ref={ref} className={`ap-bar-fill ap-${cls}`} style={{ width: '0%' }} />
    </div>
  )
}

function EvalCard({ turn, evaluation, text }) {
  if (!evaluation) return null

  // Obtenemos el Score Compuesto desde tu objeto evaluation
  const composite = evaluation.composite_score ?? 'N/A'

  return (
    <div className="ap-card">
      <p className="ap-response-preview">
        <span className="ap-preview-label">AIMO:</span> {text.slice(0, 100)}{text.length > 100 ? '…' : ''}
      </p>

      <div className="ap-card-hdr">
        <span className="ap-turn">TURNO {turn}</span>
        
        {/* Score Compuesto integrado con el CSS correcto */}
        <div className="ap-composite-wrap">
          <span className="ap-composite-label">◆ SCORE COMPUESTO</span>
          <span className="ap-composite-score">{composite}<span className="ap-den">/5</span></span>
        </div>
      </div>
      
      <div className="ap-formula-hint">
        Promedio:[ PT + FT + (6 − PD) + REL + SA ] ÷ 5
      </div>

      <div className="ap-metrics-list">
        {METRICS.map(({ key, label, abbr, cls, note, invert }) => {
          const m = evaluation[key]
          if (!m) return null
          return (
            <div className="ap-metric" key={key}>
              <div className="ap-metric-row">
                <span className={`ap-abbr ap-${cls}`}>{abbr}</span>
                <span className="ap-metric-label">{label}</span>
                <span className={`ap-score ap-${cls}`}>{m.score}<span className="ap-den">/5</span></span>
                {note && <span className="ap-note">{note}</span>}
              </div>
              <ScoreBar score={m.score} cls={cls} invert={invert} />
              <p className="ap-just">» {m.justification}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function AdminPanel({ messages, onClose }) {
  const evals = messages
    .filter(m => m.role === 'aimo' && m.evaluation)
    .map((m, i) => ({ turn: i + 1, evaluation: m.evaluation, text: m.text }))

  return (
    <div className="ap-overlay" onClick={onClose}>
      <div className="ap-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Panel de métricas">

        {/* Header */}
        <div className="ap-header">
          <span className="ap-title">⭐ PANEL ADMIN — MÉTRICAS AERI + G-EVAL</span>
          <button className="ap-close" onClick={onClose} aria-label="Cerrar panel">✕</button>
        </div>

        {/* Info banner */}
        <div className="ap-info-banner">
          <span>📊 AERI (Lee &amp; Yi, 2023) · Relevance · Semantically Appropriate</span>
        </div>

        {/* Content */}
        <div className="ap-body">
          
          {/* EC removal justification con la caja de Alerta del CSS */}
          <div className="ap-alert-box">
            <span className="ap-alert-title">¡Empathic Concern (EC) eliminada!</span>
            <p className="ap-alert-text">
              La métrica <em>Semantically Appropriate</em> es su superconjunto — cubre calidez empática + seguridad psicológica + ausencia de positividad tóxica, haciendo EC redundante.
            </p>
          </div>

          {evals.length === 0 ? (
            <div className="ap-empty">
              <span>⭐</span>
              <p>No hay evaluaciones aún.<br />Conversa con AIMO para ver<br />las métricas aquí.</p>
            </div>
          ) : (
            evals.map(({ turn, evaluation, text }) => (
              <EvalCard key={turn} turn={turn} evaluation={evaluation} text={text} />
            ))
          )}
        </div>

      </div>
    </div>
  )
}