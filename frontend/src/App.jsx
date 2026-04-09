import { useState, useEffect, useRef } from 'react'
import WorldBackground from './components/WorldBackground'
import AimoCharacter   from './components/AimoCharacter'
import SpeechBubble    from './components/SpeechBubble'
import ConvoLog        from './components/ConvoLog'
import UserInput       from './components/UserInput'
import AdminPanel      from './components/AdminPanel'
import { useTypewriter } from './hooks/useTypewriter'
import './App.css'

const PHASES = { INTRO:'intro', USER:'user_turn', LOAD:'loading', RESPOND:'responding' }

const GREETING = '¡Hola! Soy AIMO, tu compañero de apoyo emocional. Estoy aquí para escucharte sin juzgarte. ¿Qué te tiene rondando la cabeza hoy?'

const USE_API = true

function mockResponse() {
  return {
    response: 'Escucho que estás cargando algo que pesa. No tienes que enfrentarlo solo. ¿Qué es lo que sientes con más fuerza ahora mismo?',
    evaluation: {
      perspective_taking: { score: 4, justification: 'El agente refleja el estado emocional del usuario de forma contextualizada.' },
      fantasy:            { score: 3, justification: 'La respuesta usa lenguaje empático funcional.' },
      empathic_concern:   { score: 5, justification: '"No tienes que enfrentarlo solo" transmite calidez genuina.' },
      personal_distress:  { score: 1, justification: 'El agente mantiene compostura total.' },
    },
  }
}

export default function App() {
  const [phase,       setPhase]       = useState(PHASES.INTRO)
  const [messages,    setMessages]    = useState([])
  const [adminOpen,   setAdminOpen]   = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false) // ← Nuevo estado para el modal de Historial
  const sessionId = useRef(`s_${Date.now()}`)
  const { displayed, isTyping, type } = useTypewriter()

  useEffect(() => {
    const t = setTimeout(() => {
      type(GREETING, 28, () => setPhase(PHASES.USER))
    }, 600)
    return () => clearTimeout(t)
  },[]) // eslint-disable-line

  const handleSend = async (userMsg) => {
    setPhase(PHASES.LOAD)
    type('Hmm... déjame pensar en eso...', 38)
    setMessages(prev =>[...prev, { role: 'user', text: userMsg }])

    try {
      let data
      if (USE_API) {
        const res = await fetch('/api/chat', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ message: userMsg, session_id: sessionId.current }),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        data = await res.json()
      } else {
        await new Promise(r => setTimeout(r, 1800))
        data = mockResponse()
      }

      setMessages(prev =>[...prev, {
        role:       'aimo',
        text:       data.response,
        evaluation: data.evaluation ?? null,
      }])
      setPhase(PHASES.RESPOND)
      type(data.response, 26, () => setPhase(PHASES.USER))

    } catch (err) {
      console.error('[AIMO]', err)
      const errMsg = '¡Ups! Tuve un problema de conexión. ¿Puedes intentarlo de nuevo?'
      setMessages(prev => [...prev, { role: 'aimo', text: errMsg }])
      setPhase(PHASES.RESPOND)
      type(errMsg, 28, () => setPhase(PHASES.USER))
    }
  }

  const handleReset = async () => {
    if (USE_API) {
      try {
        await fetch('/api/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId.current }),
        })
      } catch (_) {}
    }
    sessionId.current = `s_${Date.now()}`
    setMessages([])
    setPhase(PHASES.INTRO)
    setTimeout(() => type(GREETING, 28, () => setPhase(PHASES.USER)), 200)
  }

  const evalCount = messages.filter(m => m.role === 'aimo' && m.evaluation).length

  return (
    <div className="game-root">
      <div className="scanlines" aria-hidden />

      {/* ── Entorno de fondo ── */}
      <WorldBackground />

      {/* ── Interfaz HUD Superior Derecha ── */}
      <div className="top-right-hud">
        <button 
          className="hud-btn" 
          onClick={() => setHistoryOpen(true)}
          aria-label="Abrir historial"
        >
          <span className="admin-icon">📜</span>
          <span className="admin-label">HISTORIAL</span>
        </button>
        
        <button
          className="hud-btn"
          onClick={() => setAdminOpen(true)}
          aria-label="Panel de métricas AERI"
        >
          <span className="admin-icon">⭐</span>
          <span className="admin-label">ADMIN</span>
          {evalCount > 0 && <span className="admin-badge">{evalCount}</span>}
        </button>
      </div>

      {/* ── Personaje AIMO centrado y su Globo de Diálogo ── */}
      <div className={`character-col phase-${phase}`}>
        <div className="speech-wrap-aimo">
          <SpeechBubble
            text={displayed}
            isTyping={isTyping}
            isLoading={phase === PHASES.LOAD}
          />
        </div>
        <AimoCharacter phase={phase} />
        <div className="aimo-ground-shadow" /> 
      </div>

      {/* ── Input del usuario (Caja estilo RPG inferior) ── */}
      <div className="rpg-input-col">
        <UserInput
          enabled={phase === PHASES.USER}
          onSend={handleSend}
        />
      </div>

      {/* ── Modales ── */}
      {historyOpen && (
        <ConvoLog messages={messages} onReset={handleReset} onClose={() => setHistoryOpen(false)} />
      )}

      {adminOpen && (
        <AdminPanel messages={messages} onClose={() => setAdminOpen(false)} />
      )}
    </div>
  )
}