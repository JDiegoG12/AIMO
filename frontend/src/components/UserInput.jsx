import { useState, useRef, useCallback } from 'react'

export default function UserInput({ enabled, complete, onSend }) {
  const [value,   setValue]   = useState('')
  const textareaRef = useRef(null)

  const autoResize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`
  },[])

  const handleChange = (e) => {
    setValue(e.target.value)
    autoResize()
  }

  const submit = () => {
    const t = value.trim()
    if (!t || !enabled) return
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    onSend(t)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
  }

  const placeholder = complete
    ? '— Conversación finalizada —'
    : enabled
      ? 'Escribe aquí tu respuesta...'
      : 'AIMO está escribiendo...'

  return (
    <div className={`user-input-row${enabled ? '' : ' input-locked'}${complete ? ' input-complete' : ''}`}>

      {/* Pixel speech bubble tipo RPG — Sin colita */}
      <div className={`user-pixel-bubble${enabled ? '' : ' bubble-disabled'}${complete ? ' bubble-complete' : ''}`}>
        <div className="user-who-label">
           <span className="user-who-dot" aria-hidden /> [ TÚ ]
        </div>
        <textarea
          ref={textareaRef}
          className="user-textarea"
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKey}
          disabled={!enabled || complete}
          rows={2}
          aria-label="Mensaje para AIMO"
        />
      </div>

      {/* Send button */}
      <button
        className="send-btn"
        onClick={submit}
        disabled={!enabled || !value.trim() || complete}
        aria-label="Enviar"
      >
        ENVIAR<br />►
      </button>
    </div>
  )
}