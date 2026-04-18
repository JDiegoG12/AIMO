import { useEffect, useRef } from 'react'

const EMOTION_EMOJI = {
  sadness:    '💙',
  anxiety:    '🟠',
  anger:      '🔴',
  overwhelm:  '💜',
  loneliness: '🩶',
  neutral:    '💚',
}

function MsgBubble({ message }) {
  const isUser = message.role === 'user'
  const cl     = !isUser && message.classification ? message.classification : null

  return (
    <div className={`msg-bubble-wrap ${isUser ? 'wrap-user' : 'wrap-aimo'}`}>
      <span className={`msg-who ${isUser ? 'who-user' : 'who-aimo'}`}>
        {isUser ? '[ TÚ ]' : '[ AIMO ]'}
        {cl && (
          <span
            className="msg-em-chip"
            title={`${cl.emotion} · intensidad ${cl.intensity}/5${cl.crisis_signal ? ' ·  crisis' : ''}`}
          >
            {EMOTION_EMOJI[cl.emotion] ?? '●'} {cl.emotion}
          </span>
        )}
      </span>
      <div className={`msg-pixel-bubble ${isUser ? 'bubble-user' : 'bubble-aimo'}`}>
        {message.text}
      </div>
    </div>
  )
}

export default function ConvoLog({ messages, onReset, onClose }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="ap-overlay" onClick={onClose}>
      <div className="ap-panel convo-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Historial de conversación">
        <div className="ap-header">
          <span className="ap-title">HISTORIAL DE CONVERSACIÓN</span>
          <div className="ap-header-actions">
            <button className="ap-close ap-reset" onClick={onReset}>
              ↺ REINICIAR
            </button>
            <button className="ap-close" onClick={onClose} aria-label="Cerrar panel">✕</button>
          </div>
        </div>

        <div className="ap-info-banner">
          <span>Aquí puedes revisar todo lo que has hablado con AIMO.</span>
        </div>

        {/* Scrollable messages */}
        <div className="ap-body convo-scroll-modal" role="log" aria-live="polite">
          {messages.length === 0 ? (
            <div className="ap-empty">
              <span>•</span>
              <p>Escribe tu primer mensaje<br />para comenzar.</p>
            </div>
          ) : (
            messages.map((msg, i) => <MessageItem key={i} message={msg} className="msg-log-item" />)
          )}
          <div ref={bottomRef} />
        </div>

      </div>
    </div>
  )
}