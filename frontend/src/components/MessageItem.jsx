/**
 * MessageItem — Chat bubble.
 * AERI metrics removed from here → now live in AdminPanel.
 */
export default function MessageItem({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className="msg-row">
      <span className={`msg-who ${isUser ? 'user' : 'aimo'}`}>
        {isUser ? '[ TÚ ]' : '[ AIMO ]'}
      </span>
      <div className={`msg-text ${isUser ? 'user-txt' : 'aimo-txt'}`}>
        {message.text}
      </div>
    </div>
  )
}
