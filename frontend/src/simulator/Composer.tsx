import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Category, Channel, Priority, SimulatorCase, SimulatorMessage, SimulatorReceipt, SimulatorRepository } from './contract'
import { categoryLabels, channelExamples, priorityLabels } from './presentation'
import { errorMessage } from './useResource'

export function Composer({
  channel, conversation, repository, onSent, onSendingChange,
}: {
  channel: Channel
  conversation?: SimulatorCase
  repository: SimulatorRepository
  onSent: (receipt: SimulatorReceipt) => void
  onSendingChange?: (sending: boolean) => void
}) {
  const example = channelExamples[channel.type]
  const [text, setText] = useState('')
  const [category, setCategory] = useState<Category | ''>(example.category)
  const [priority, setPriority] = useState<Priority | ''>(example.priority)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const attempt = useRef<{ fingerprint: string; key: string } | null>(null)
  const opensCase = !conversation || conversation.status === 'resolved'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!text.trim() || sending) return

    const message: SimulatorMessage = { text: text.trim() }
    if (conversation) message.external_conversation_id = conversation.external_conversation_id
    if (opensCase && category) message.category = category
    if (opensCase && priority) message.priority = priority
    const fingerprint = JSON.stringify([channel.id, message])
    if (attempt.current?.fingerprint !== fingerprint) {
      attempt.current = { fingerprint, key: crypto.randomUUID() }
    }

    setSending(true)
    onSendingChange?.(true)
    setError(null)
    try {
      const receipt = await repository.sendMessage(channel.id, message, attempt.current.key)
      attempt.current = null
      setText('')
      onSent(receipt)
    } catch (failure) {
      setError(errorMessage(failure))
    } finally {
      setSending(false)
      onSendingChange?.(false)
    }
  }

  return (
    <form className="composer" onSubmit={submit}>
      {opensCase && (
        <details className="metadata">
          <summary>Classificação da mensagem</summary>
          <div className="fields">
            <label>
              Categoria
              <select value={category} onChange={event => setCategory(event.target.value as Category | '')} disabled={sending}>
                <option value="">Não informar</option>
                {Object.entries(categoryLabels).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
            <label>
              Prioridade
              <select value={priority} onChange={event => setPriority(event.target.value as Priority | '')} disabled={sending}>
                <option value="">Não informar</option>
                {Object.entries(priorityLabels).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
          </div>
        </details>
      )}
      <div className="message-label">
        <label htmlFor="message">{opensCase ? 'Mensagem' : 'Sua resposta'}</label>
        {opensCase && (
          <button className="text-button" type="button" disabled={sending} onClick={() => {
            setText(example.text)
            setCategory(example.category)
            setPriority(example.priority)
          }}>
            Usar exemplo
          </button>
        )}
      </div>
      <textarea id="message" value={text} onChange={event => setText(event.target.value)} disabled={sending}
        rows={opensCase ? 5 : 3} required placeholder="Descreva o que aconteceu…" />
      {error && <p className="error" role="alert">{error}</p>}
      <div className="composer-actions">
        <button className="primary" type="submit" disabled={sending || !text.trim()}>
          {sending ? 'Enviando…' : conversation?.status === 'resolved' ? 'Iniciar novo atendimento' : 'Enviar mensagem'}
        </button>
      </div>
    </form>
  )
}
