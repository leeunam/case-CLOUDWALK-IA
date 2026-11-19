import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { CaseFilters, Session, StaffCommand } from '../api/contract'
import { ApiError, accessLost } from '../api/http'
import { canHandle } from '../api/permissions'
import { staff } from '../api/staff'
import { categoryLabels, priorityLabels } from '../simulator/presentation'
import { errorMessage, useResource } from '../simulator/useResource'
import { Transcript } from '../Transcript'
import { useCaseRefresh } from '../useCaseRefresh'
import { staffCaseLabels } from './presentation'

const blocks: Record<string, string> = {
  active_capacity: 'O perfil não comporta mais casos ativos.',
  portfolio_limit: 'A carteira atingiu o limite.',
  different_operating_brand: 'O responsável está operando em outra marca.',
  analyst_unavailable: 'O responsável está indisponível para novas atribuições.',
  brand_switch_pending: 'O responsável está preparando a troca de marca.',
  no_eligible_analyst: 'A fila aguarda um analista elegível.',
  queue_access_revoked: 'O responsável perdeu acesso à fila.',
}

type Attempt = { kind: StaffCommand['type']; text: string; command: StaffCommand; key: string }

export function StaffConversation({ id, session, filters, onOpen, onChanged }: {
  id: string
  session: Session
  filters: CaseFilters | null
  onOpen: (id: string) => void
  onChanged: () => void
}) {
  const [revision, setRevision] = useState(0)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [commandError, setCommandError] = useState<string | null>(null)
  const attempt = useRef<Attempt | null>(null)
  const refresh = useCallback(() => setRevision(value => value + 1), [])
  const load = useCallback(() => staff.getConversation(id), [id])
  const { data, error, loading, replaceData } = useResource(load, revision)
  const detail = data?.detail
  const version = detail?.version
  const brand = filters?.brands.find(item => item.id === detail?.brand_id)
  const queue = filters?.queues.find(item => item.id === detail?.queue_id)
  const owned = detail?.assignee?.id === session.user?.attendant_id
  const canAct = detail && !error && canHandle(session, detail)
  const handoff = detail?.handoff

  useCaseRefresh(id, detail ? 'staff' : null, 10000, loading, refresh)
  useEffect(() => {
    if (version !== undefined) onChanged()
  }, [version, onChanged])

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!detail || !canAct || busy || loading) return
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null
    const kind = submitter?.value === 'resolve' ? 'resolve' : submitter?.value === 'wait_for_customer' ? 'wait_for_customer' : 'reply'
    const body = kind === 'resolve' ? '' : text.trim()
    if (kind !== 'resolve' && !body) return
    const command: StaffCommand = kind === 'resolve'
      ? { type: kind, expected_version: detail.version }
      : { type: kind, expected_version: detail.version, text: body }
    if (attempt.current?.kind !== kind || attempt.current.text !== body) {
      attempt.current = { kind, text: body, command, key: crypto.randomUUID() }
    }

    setBusy(true)
    setCommandError(null)
    try {
      await staff.command(id, attempt.current.command, session.csrf_token, attempt.current.key)
      attempt.current = null
      setText('')
      refresh()
      onChanged()
    } catch (failure) {
      if (failure instanceof ApiError && failure.status >= 400 && failure.status < 500) attempt.current = null
      if (accessLost(failure)) replaceData(null)
      if (failure instanceof ApiError && failure.status === 409) {
        setCommandError('O atendimento foi atualizado. Confira o estado atual e tente novamente. Seu rascunho foi preservado.')
        refresh()
        onChanged()
      } else {
        setCommandError(errorMessage(failure))
        if (accessLost(failure)) { refresh(); onChanged() }
      }
    } finally {
      setBusy(false)
    }
  }

  const category = detail?.classification.category
  const priority = detail?.classification.priority
  return (
    <section className="panel workspace" aria-labelledby="staff-conversation-heading">
      <div className="workspace-header">
        <div>
          {(brand || queue) && <p className="context">{[brand?.name, queue?.name].filter(Boolean).join(' · ')}</p>}
          <h2 id="staff-conversation-heading">Conversa</h2>
        </div>
        {detail && <span role="status" className={`case-status ${detail.status}`}>{staffCaseLabels[detail.status]}</span>}
      </div>
      {detail && (
        <div className="case-context">
          <p>{category ? categoryLabels[category as keyof typeof categoryLabels] ?? category : 'Sem categoria'} · {priority ? priorityLabels[priority] : 'Sem prioridade'}</p>
          <p className="muted">{detail.assignee?.type === 'ai' ? 'Atendente de IA' : detail.assignee ? owned ? 'Responsável: você' : 'Responsável: outro analista' : 'Sem responsável'}</p>
          {detail.previous_case_id && (
            <button className="text-button" onClick={() => onOpen(detail.previous_case_id!)}>Ver atendimento anterior</button>
          )}
          {detail.blocking_reason && <p>{blocks[detail.blocking_reason] ?? detail.blocking_reason}</p>}
        </div>
      )}
      {handoff && (
        <section className="handoff" aria-labelledby="handoff-heading">
          <h3 id="handoff-heading">Resumo do encaminhamento</h3>
          <p>{handoff.summary}</p>
          {handoff.message_ids.length > 0 && (
            <ul className="handoff-references" aria-label="Mensagens referenciadas">
              {handoff.message_ids.map(messageId => {
                const message = data?.messages.find(item => item.id === messageId)
                return message && <li key={messageId}><a href={`#message-${messageId}`}>Mensagem {message.sequence}</a></li>
              })}
            </ul>
          )}
        </section>
      )}
      <div className="transcript">
        {loading && !data && <p role="status">Carregando conversa…</p>}
        {error && <div className="notice" role="alert">{error}</div>}
        {data && <Transcript messages={data.messages} references={handoff?.message_ids} staffView />}
      </div>
      <div className="conversation-footer">
        <div className="conversation-tools">
          {detail?.status === 'waiting_resumption' && <p className="muted">A retomada é automática quando houver capacidade na marca do atendimento.</p>}
          {detail?.status === 'waiting_customer' && <p className="muted">Aguardando a resposta do cliente.</p>}
          {detail?.status === 'human_active' && !canAct && <p className="muted">As ações exigem o analista responsável na marca em operação.</p>}
          <button className="secondary" onClick={refresh} disabled={loading}>Atualizar conversa</button>
        </div>
        {commandError && <p className="error" role="alert">{commandError}</p>}
        {canAct && (
          <form className="composer" onSubmit={send}>
            <label htmlFor="staff-reply">Resposta ao cliente</label>
            <textarea id="staff-reply" value={text} onChange={event => setText(event.target.value)} rows={3} disabled={busy} />
            <div className="composer-actions staff-actions">
              <button className="primary" type="submit" value="reply" disabled={loading || busy || !text.trim()}>Enviar resposta</button>
              <button className="secondary" type="submit" value="wait_for_customer" disabled={loading || busy || !text.trim()}>Aguardar cliente</button>
              <button className="secondary" type="submit" value="resolve" disabled={loading || busy}>Resolver atendimento</button>
            </div>
          </form>
        )}
      </div>
    </section>
  )
}
