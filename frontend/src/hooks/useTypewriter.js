import { useState, useRef, useCallback, useEffect } from 'react'

/**
 * Imperatively driven typewriter hook.
 *
 * Usage:
 *   const { displayed, isTyping, type } = useTypewriter()
 *   type('Hello world!', 35, () => console.log('done'))
 */
export function useTypewriter() {
  const [displayed, setDisplayed] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const timerRef  = useRef(null)
  const onDoneRef = useRef(null)

  const type = useCallback((text, speed = 32, onDone) => {
    // Cancel any running animation
    if (timerRef.current) clearInterval(timerRef.current)
    onDoneRef.current = onDone

    if (!text) {
      setDisplayed('')
      setIsTyping(false)
      onDone?.()
      return
    }

    setDisplayed('')
    setIsTyping(true)
    let i = 0

    timerRef.current = setInterval(() => {
      i += 1
      setDisplayed(text.slice(0, i))
      if (i >= text.length) {
        clearInterval(timerRef.current)
        setIsTyping(false)
        onDoneRef.current?.()
      }
    }, speed)
  }, [])

  // Cleanup on unmount
  useEffect(() => () => clearInterval(timerRef.current), [])

  return { displayed, isTyping, type }
}
