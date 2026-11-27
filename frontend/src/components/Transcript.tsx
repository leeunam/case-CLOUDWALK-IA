import type { Message } from '../simulator/contract'
import { authorLabels, formatTimestamp } from '../simulator/presentation'

export function Transcript({ messages, references, staffView = false }: {
  messages: Message[]
  references?: string[]
  staffView?: boolean
}) {
  if (!messages.length) return <p className="muted">Ainda não há mensagens neste atendimento.</p>
  return (
    <ol className="messages" aria-label="Mensagens" aria-live="polite">
      {messages.map(message => (
        <li id={`message-${message.id}`} className={`message ${message.author.type === 'customer' ? 'customer' : message.author.type === 'human' || message.author.type === 'ai' ? 'outgoing' : ''}`}
          key={message.id} tabIndex={references?.includes(message.id) ? -1 : undefined}>
          <div className="message-meta">
            <strong>{staffView && message.author.type === 'customer' ? 'Cliente' : authorLabels[message.author.type]}</strong>
            <time dateTime={message.created_at}>{formatTimestamp(message.created_at)}</time>
          </div>
          <p>{message.text}</p>
        </li>
      ))}
    </ol>
  )
}
