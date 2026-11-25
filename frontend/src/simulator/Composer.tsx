import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, deliveryUncertain } from '../api/http'
import type { Channel, Priority, SimulatorCase, SimulatorMessage, SimulatorReceipt, SimulatorRepository } from './contract'
import { categoryLabels, channelExamples, priorityLabels } from './presentation'
import { errorMessage } from './useResource'

type Attempt = { channelId: string; message: SimulatorMessage; key: string }

export function Composer({
  channel, conversation, repository, onSent, onAttemptChange, allowNewMessage = true,
}: {
  channel: Channel
  conversation?: SimulatorCase
  repository: SimulatorRepository
  onSent: (receipt: SimulatorReceipt) => void
  onAttemptChange?: (active: boolean) => void
  allowNewMessage?: boolean
}) {
  const example = channelExamples[channel.type]
  const [text, setText] = useState('')
  const categories = channel.categories?.filter(item => item.active) ??
    Object.entries(categoryLabels).map(([key, name]) => ({ key, name, active: true }))
  const exampleCategory = categories.some(item => item.key === example.category) ? example.category : ''
  const [category, setCategory] = useState<string>(exampleCategory)
  const activeCategory = categories.some(item => item.key === category) ? category : ''
  const [priority, setPriority] = useState<Priority | ''>(example.priority)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<Attempt | null>(null)
  const opensCase = !conversation || conversation.status === 'resolved'

  useEffect(() => {
    onAttemptChange?.(sending || !!pending)
    return () => onAttemptChange?.(false)
  }, [onAttemptChange, pending, sending])

  function editMessage() {
    setPending(null)
    setError(null)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (sending || (!pending && (!allowNewMessage || !text.trim()))) return

    let attempt = pending
    if (!attempt) {
      const message: SimulatorMessage = { text: text.trim() }
      if (conversation) message.external_conversation_id = conversation.external_conversation_id
      if (opensCase && activeCategory) message.category = activeCategory
      if (opensCase && priority) message.priority = priority
      attempt = { channelId: channel.id, message, key: crypto.randomUUID() }
    }

    setSending(true)
    setError(null)
    try {
      const receipt = await repository.sendMessage(attempt.channelId, attempt.message, attempt.key)
      setPending(null)
      setText('')
      onSent(receipt)
    } catch (failure) {
      const sessionRejected = failure instanceof ApiError && (failure.status === 401 ||
        ['simulator_session_changed', 'csrf_rejected'].includes(failure.code))
      if (!pending || !sessionRejected) setPending(deliveryUncertain(failure) ? attempt : null)
      setError(errorMessage(failure))
    } finally {
      setSending(false)
    }
  }

  if (!allowNewMessage && !pending && !sending) return null

  return (
    <form className="composer" onSubmit={submit}>
      {opensCase && !pending && (
        <details className="metadata">
          <summary>Classificação da mensagem<span className="classification-preview">{[
            categories.find(item => item.key === activeCategory)?.name,
            priority && priorityLabels[priority],
          ].filter(Boolean).join(' · ') || 'Não informada'}</span></summary>
          <div className="fields">
            <label>
              Categoria
              <select value={activeCategory} onChange={event => setCategory(event.target.value)} disabled={sending}>
                <option value="">Não informar</option>
                {categories.map(item => <option key={item.key} value={item.key}>{item.name}</option>)}
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
        {opensCase && !pending && (
          <button className="text-button" type="button" disabled={sending} onClick={() => {
            setText(example.text)
            setCategory(exampleCategory)
            setPriority(example.priority)
          }}>
            Usar exemplo
          </button>
        )}
      </div>
      <textarea id="message" value={text} onChange={event => setText(event.target.value)} disabled={sending || !!pending}
        rows={opensCase ? 5 : 3} required placeholder="Descreva o que aconteceu…" />
      {error && <p className="error" role="alert">{error}</p>}
      {pending && <p className="muted">A mensagem pode ter sido recebida. Reenvie a tentativa para confirmar.</p>}
      <div className="composer-actions">
        <button className="primary" type="submit" disabled={sending || !text.trim()}>
          {sending ? 'Enviando…' : pending ? 'Confirmar envio anterior' :
            conversation?.status === 'resolved' ? 'Iniciar novo atendimento' : 'Enviar mensagem'}
        </button>
        {pending && (
          <button className="secondary" type="button" disabled={sending} onClick={editMessage}>
            {allowNewMessage ? 'Preparar outra mensagem' : 'Encerrar tentativa'}
          </button>
        )}
      </div>
    </form>
  )
}
