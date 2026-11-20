import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { CaseFilters, Session, StaffCommand } from '../api/contract'
import { ApiError, accessLost, deliveryUncertain } from '../api/http'
import { canHandle } from '../api/permissions'
import { staff } from '../api/staff'
import { categoryLabels, priorityLabels } from '../simulator/presentation'
import { errorMessage, useResource } from '../simulator/useResource'
import { Transcript } from '../Transcript'
import { useCaseRefresh } from '../useCaseRefresh'
import { SupervisorActions } from './SupervisorActions'
import { beginCommandAttempt } from './commandAttempt'
import type { CommandAttempt } from './commandAttempt'
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

const retryLabels: Record<StaffCommand['type'], string> = {
  reply: 'Confirmar resposta anterior',
  wait_for_customer: 'Confirmar espera anterior',
  resolve: 'Confirmar resolução anterior',
  classification: 'Confirmar correção anterior',
  transfer: 'Confirmar transferência anterior',
  retry_agent: 'Confirmar recuperação anterior',
  force_handoff: 'Confirmar encaminhamento anterior',
}

export function StaffConversation({ id, session, filters, onOpen, onChanged }: {
  id: string
  session: Session
  filters: CaseFilters | null
  onOpen: (id: string) => void
  onChanged: () => void
}) {
  const [revision, setRevision] = useState(0)
  const [text, setText] = useState('')
  const [commandError, setCommandError] = useState<string | null>(null)
  const [confirmation, setConfirmation] = useState<string | null>(null)
  const [attempt, setAttempt] = useState<CommandAttempt | null>(null)
  const latestAttempt = useRef<CommandAttempt | null>(null)
  const busy = attempt?.status === 'sending' || attempt?.status === 'confirming'
  const pending = attempt?.status === 'sending' ? null : attempt
  const refresh = useCallback(() => setRevision(value => value + 1), [])
  const load = useCallback(() => staff.getConversation(id), [id])
  const { data, error, loading, replaceData } = useResource(load, revision)
  const detail = data?.detail
  const version = detail?.version
  const brand = filters?.brands.find(item => item.id === detail?.brand_id)
  const queue = filters?.queues.find(item => item.id === detail?.queue_id)
  const owned = detail?.assignee?.id === session.user?.attendant_id
  const canAct = detail && !error && canHandle(session, detail)
  const switchPending = !!session.operation?.switch_target_brand_id
  const supervisor = session.user?.role === 'supervisor'
  const canConfirm = detail && !error && (supervisor || (
    session.user?.role === 'analyst' && detail.brand_id === session.operation?.active_brand_id && (owned || detail.status === 'resolved')
  ))
  const handoff = detail?.handoff

  useCaseRefresh(id, detail ? 'staff' : null, 10000, loading, refresh)
  useEffect(() => {
    if (version !== undefined) onChanged()
  }, [version, onChanged])

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!detail || !canAct || pending || busy || loading) return
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null
    const kind = submitter?.value === 'resolve' ? 'resolve' : submitter?.value === 'wait_for_customer' ? 'wait_for_customer' : 'reply'
    const body = kind === 'resolve' ? '' : text.trim()
    if ((kind !== 'resolve' && !body) || (kind === 'wait_for_customer' && switchPending)) return
    const command: StaffCommand = kind === 'resolve'
      ? { type: kind, expected_version: detail.version }
      : { type: kind, expected_version: detail.version, text: body }
    await runCommand(command)
  }

  function updateAttempt(next: CommandAttempt | null) {
    latestAttempt.current = next
    setAttempt(next)
  }

  async function runCommand(command?: StaffCommand) {
    if (loading || (!command && !canConfirm)) return false
    const current = beginCommandAttempt(latestAttempt.current, version, command)
    if (!current) return false

    updateAttempt(current)
    setCommandError(null)
    setConfirmation(null)
    try {
      await staff.command(id, current.command, session, current.key)
    } catch (failure) {
      const stillUncertain = deliveryUncertain(failure) || (current.status === 'confirming' && accessLost(failure))
      updateAttempt(stillUncertain ? { ...current, status: 'uncertain' } : null)
      if (accessLost(failure)) replaceData(null)
      if (failure instanceof ApiError && failure.status === 409) {
        setCommandError(failure.code === 'version_conflict'
          ? 'O atendimento foi atualizado. Confira o estado atual antes de tentar novamente.'
          : errorMessage(failure))
        refresh()
        onChanged()
      } else {
        setCommandError(errorMessage(failure))
        if (accessLost(failure)) { refresh(); onChanged() }
      }
      return false
    }

    updateAttempt(null)
    setText('')
    if (current.status === 'confirming') setConfirmation('A tentativa anterior foi confirmada. Confira o estado atual antes de iniciar outra ação.')
    else if (supervisor) setConfirmation('Ação de supervisão aplicada.')
    refresh()
    onChanged()
    return true
  }

  const category = detail?.classification.category
  const categoryName = brand?.categories?.find(item => item.key === category)?.name
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
          <p>{category ? categoryName ?? categoryLabels[category as keyof typeof categoryLabels] ?? category : 'Sem categoria'} · {priority ? priorityLabels[priority] : 'Sem prioridade'}</p>
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
          {detail?.status === 'human_active' && !canAct && !supervisor && <p className="muted">As ações exigem o analista responsável na marca em operação.</p>}
          <button className="secondary" onClick={refresh} disabled={loading}>Atualizar conversa</button>
        </div>
        {commandError && <p className="error" role="alert">{commandError}</p>}
        {confirmation && <p role="status">{confirmation}</p>}
        {pending && (
          <div className="composer">
            <p className="muted">A ação pode ter sido aplicada. Reenvie a tentativa para confirmar.</p>
            {'text' in pending.command && <p>{pending.command.text}</p>}
            <div className="composer-actions staff-actions">
              <button className="primary" type="button" disabled={busy || loading || !canConfirm}
                onClick={() => void runCommand()}>{retryLabels[pending.command.type]}</button>
              <button className="secondary" type="button" disabled={busy} onClick={() => {
                if (latestAttempt.current?.status !== 'uncertain') return
                updateAttempt(null)
                setCommandError(null)
              }}>Preparar outra ação</button>
            </div>
          </div>
        )}
        {detail && supervisor && !error &&
          <SupervisorActions detail={detail} filters={filters} revision={revision}
            disabled={loading || busy || !!pending} run={runCommand} />}
        {canAct && !pending && (
          <form className="composer" onSubmit={send}>
            <label htmlFor="staff-reply">Resposta ao cliente</label>
            <textarea id="staff-reply" value={text} onChange={event => setText(event.target.value)} rows={3} disabled={busy} />
            <div className="composer-actions staff-actions">
              <button className="primary" type="submit" value="reply" disabled={loading || busy || !text.trim()}>Enviar resposta</button>
              <button className="secondary" type="submit" value="wait_for_customer"
                disabled={loading || busy || switchPending || !text.trim()}>Aguardar cliente</button>
              <button className="secondary" type="submit" value="resolve" disabled={loading || busy}>Resolver atendimento</button>
            </div>
            {switchPending && <p className="muted">A espera pelo cliente fica indisponível durante a troca de marca.</p>}
          </form>
        )}
      </div>
    </section>
  )
}
