import { useState, useEffect, useRef } from 'react'

/**
 * AdminPanel — Research panel with two tabs:
 *   📊 MÉTRICAS  — AERI + G-Eval scores per turn
 *   🧠 EMOCIONES — Emotional classification per turn
 */

// ── Metrics tab ───────────────────────────────────────────────────────────────

const METRICS = [
  { key: 'perspective_taking',       label: 'Perspective Taking',       abbr: 'PT',  cls: 'g', note: '',              invert: false },
  { key: 'fantasy',                  label: 'Fantasy',                  abbr: 'FT',  cls: 'y', note: '',              invert: false },
  { key: 'personal_distress',        label: 'Personal Distress',        abbr: 'PD',  cls: 'r', note: '↓ menor=mejor', invert: true  },
  { key: 'relevance',                label: 'Relevance',                abbr: 'REL', cls: 'c', note: '',              invert: false },
  { key: 'semantically_appropriate', label: 'Semantically Approp.',     abbr: 'SA',  cls: 'c', note: '',              invert: false },
]

function ScoreBar({ score, cls, invert }) {
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
  const composite = evaluation.composite_score ?? 'N/A'

  return (
    <div className="ap-card">
      <p className="ap-response-preview">
        <span className="ap-preview-label">AIMO:</span> {text.slice(0, 100)}{text.length > 100 ? '…' : ''}
      </p>

      <div className="ap-card-hdr">
        <span className="ap-turn">TURNO {turn}</span>
        <div className="ap-composite-wrap">
          <span className="ap-composite-label">◆ SCORE COMPUESTO</span>
          <span className="ap-composite-score">{composite}<span className="ap-den">/5</span></span>
        </div>
      </div>

      <div className="ap-formula-hint">
        Ponderado: PT×0.30 + REL×0.25 + (6−PD)×0.20 + SA×0.15 + FT×0.10
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

// ── Emotions tab ──────────────────────────────────────────────────────────────

const EMOTION_COLORS = {
  sadness:    'em-sadness',
  anxiety:    'em-anxiety',
  anger:      'em-anger',
  overwhelm:  'em-overwhelm',
  loneliness: 'em-loneliness',
  neutral:    'em-neutral',
}

const EMOTION_EMOJI = {
  sadness:    '💙',
  anxiety:    '🟠',
  anger:      '🔴',
  overwhelm:  '💜',
  loneliness: '🩶',
  neutral:    '💚',
}

function IntensityPips({ value }) {
  return (
    <div className="em-intensity">
      {[1, 2, 3, 4, 5].map(i => (
        <span key={i} className={`em-pip${i <= value ? ' em-pip-on' : ''}`} />
      ))}
      <span className="em-intensity-num">{value}/5</span>
    </div>
  )
}

function EmotionCard({ turn, classification, text }) {
  if (!classification) return null
  const { emotion, intensity, crisis_signal, topic } = classification
  const colorCls = EMOTION_COLORS[emotion] ?? 'em-neutral'

  return (
    <div className="ap-card">
      <p className="ap-response-preview">
        <span className="ap-preview-label">AIMO:</span> {text.slice(0, 100)}{text.length > 100 ? '…' : ''}
      </p>

      <div className="ap-card-hdr">
        <span className="ap-turn">TURNO {turn}</span>
        {crisis_signal && (
          <span className="em-crisis-badge">⚠ CRISIS SIGNAL</span>
        )}
      </div>

      <div className="em-grid">
        <div className="em-field">
          <span className="em-label">EMOCIÓN</span>
          <span className={`em-badge ${colorCls}`}>
            {EMOTION_EMOJI[emotion] ?? '●'} {emotion.toUpperCase()}
          </span>
        </div>

        <div className="em-field">
          <span className="em-label">INTENSIDAD</span>
          <IntensityPips value={intensity} />
        </div>

        <div className="em-field">
          <span className="em-label">TÓPICO</span>
          <span className="em-topic">{topic.toUpperCase()}</span>
        </div>
      </div>
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function AdminPanel({ messages, onClose }) {
  const [activeTab, setActiveTab] = useState('metricas')

  const aimoMessages = messages.filter(m => m.role === 'aimo')

  const evals = aimoMessages
    .map((m, i) => ({ turn: i + 1, evaluation: m.evaluation, text: m.text }))
    .filter(e => e.evaluation)

  const emotions = aimoMessages
    .map((m, i) => ({ turn: i + 1, classification: m.classification, text: m.text }))
    .filter(e => e.classification)

  return (
    <div className="ap-overlay" onClick={onClose}>
      <div className="ap-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Panel de métricas">

        {/* Header */}
        <div className="ap-header">
          <span className="ap-title">⭐ PANEL ADMIN — INVESTIGACIÓN</span>
          <button className="ap-close" onClick={onClose} aria-label="Cerrar panel">✕</button>
        </div>

        {/* Tabs */}
        <div className="ap-tabs">
          <button
            className={`ap-tab${activeTab === 'metricas' ? ' ap-tab-active' : ''}`}
            onClick={() => setActiveTab('metricas')}
          >
            📊 MÉTRICAS {evals.length > 0 && `(${evals.length})`}
          </button>
          <button
            className={`ap-tab${activeTab === 'emociones' ? ' ap-tab-active' : ''}`}
            onClick={() => setActiveTab('emociones')}
          >
            🧠 EMOCIONES {emotions.length > 0 && `(${emotions.length})`}
          </button>
        </div>

        {/* Content */}
        <div className="ap-body">

          {activeTab === 'metricas' && (
            <>
              <div className="ap-info-banner" style={{ marginTop: 0 }}>
                <span>📊 AERI (Lee &amp; Yi, 2023) · Relevance · Semantically Appropriate · Pesos: Davis (1980) + Abd-alrazaq (2019)</span>
              </div>

              <div className="ap-alert-box">
                <span className="ap-alert-title">¡Empathic Concern (EC) eliminada!</span>
                <p className="ap-alert-text">
                  La métrica <em>Semantically Appropriate</em> es su superconjunto — cubre calidez empática + seguridad psicológica + ausencia de positividad tóxica.
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
            </>
          )}

          {activeTab === 'emociones' && (
            <>
              <div className="ap-info-banner" style={{ marginTop: 0 }}>
                <span>🧠 Clasificador emocional · Russell (1980) · Miller &amp; Rollnick (2012) · Beiter et al. (2015)</span>
              </div>

              {emotions.length === 0 ? (
                <div className="ap-empty">
                  <span>🧠</span>
                  <p>No hay clasificaciones aún.<br />Conversa con AIMO para ver<br />el estado emocional detectado.</p>
                </div>
              ) : (
                emotions.map(({ turn, classification, text }) => (
                  <EmotionCard key={turn} turn={turn} classification={classification} text={text} />
                ))
              )}
            </>
          )}

        </div>

      </div>
    </div>
  )
}
