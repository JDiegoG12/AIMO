import { useState, useRef, useCallback } from 'react'

export default function UserInput({ enabled, complete, onSend }) {
  const [value,   setValue]   = useState('')
  const textareaRef = useRef(null)

  const autoResize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 66)}px`
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
    <div className={`user-input-row${enabled ? '' : ' input-locked'}`}>
      <div className="user-pixel-bubble">
        <span className="user-who-label">[ TÚ ]</span>
        <textarea
          ref={textareaRef}
          id="user-message-input"
          className="user-textarea"
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKey}
          disabled={!enabled}
          rows={1}
          aria-label="Mensaje para AIMO"
        />
      </div>

      <button
        className="send-btn"
        onClick={submit}
        disabled={!enabled || !value.trim() || complete}
        aria-label="Enviar"
      >
        ENVIAR
      </button>
    </div>
  )
}