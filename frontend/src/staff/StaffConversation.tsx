import { useCallback, useEffect, useState, useSyncExternalStore } from 'react'
import type { FormEvent } from 'react'
import type { CaseFilters, Session, StaffCommand } from '../api/contract'
import { ApiError, accessLost } from '../api/http'
import { canHandle } from '../api/permissions'
import { staff } from '../api/staff'
import { Icon } from '../components/Icon'
import { CaseContext } from './CaseContext'
import { errorMessage, useResource } from '../hooks/useResource'
import { Transcript } from '../components/Transcript'
import { useCaseRefresh } from '../hooks/useCaseRefresh'
import { SupervisorActions } from './SupervisorActions'
import type { SessionCommandAttempts } from './commandAttempt'
import { staffCaseLabels } from './presentation'

const retryLabels: Record<StaffCommand['type'], string> = {
  reply: 'Confirmar resposta anterior',
  wait_for_customer: 'Confirmar espera anterior',
  resolve: 'Confirmar resolução anterior',
  classification: 'Confirmar correção anterior',
  transfer: 'Confirmar transferência anterior',
  retry_agent: 'Confirmar recuperação anterior',
  force_handoff: 'Confirmar encaminhamento anterior',
}

export function StaffConversation({ id, session, attempts, filters, onOpen, onChanged }: {
  id: string
  session: Session
  attempts: SessionCommandAttempts
  filters: CaseFilters | null
  onOpen: (id: string) => void
  onChanged: () => void
}) {
  const [revision, setRevision] = useState(0)
  const [text, setText] = useState('')
  const [contextOpen, setContextOpen] = useState(false)
  const [commandError, setCommandError] = useState<string | null>(null)
  const [confirmation, setConfirmation] = useState<string | null>(null)
  const refresh = useCallback(() => setRevision(value => value + 1), [])
  const load = useCallback(() => staff.getConversation(id), [id])
  const { data, error, loading, replaceData } = useResource(load, revision)
  const subscribe = useCallback((notify: () => void) => attempts.subscribe(id, change => {
    if (change === 'access_lost') replaceData(null)
    if (change !== 'changed') refresh()
    notify()
  }), [attempts, id, refresh, replaceData])
  const attempt = useSyncExternalStore(subscribe, () => attempts.get(id))
  const busy = attempt?.status === 'sending' || attempt?.status === 'confirming'
  const pending = attempt?.status === 'sending' ? null : attempt
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

  async function runCommand(command?: StaffCommand) {
    if (loading || (!command && !canConfirm)) return false
    const current = attempts.begin(id, version, command)
    if (!current) return false

    setCommandError(null)
    setConfirmation(null)
    try {
      await staff.command(id, current.command, session, current.key)
    } catch (failure) {
      attempts.settle(id, current, { failure })
      if (failure instanceof ApiError && failure.status === 409) {
        setCommandError(failure.code === 'version_conflict'
          ? 'O atendimento foi atualizado. Confira o estado atual antes de tentar novamente.'
          : errorMessage(failure))
        onChanged()
      } else {
        setCommandError(errorMessage(failure))
        if (accessLost(failure)) onChanged()
      }
      return false
    }

    attempts.settle(id, current)
    setText('')
    if (current.status === 'confirming') setConfirmation('A tentativa anterior foi confirmada. Confira o estado atual antes de iniciar outra ação.')
    else if (supervisor) setConfirmation('Ação de supervisão aplicada.')
    onChanged()
    return true
  }

  function showReference(messageId: string) {
    setContextOpen(false)
    requestAnimationFrame(() => {
      const reference = document.getElementById(`message-${messageId}`)
      reference?.focus()
      reference?.scrollIntoView({ block: 'nearest' })
    })
  }

  const commandFeedback = <>
    {commandError && <p className="error" role="alert">{commandError}</p>}
    {confirmation && <p role="status">{confirmation}</p>}
    {detail && !error && pending && (
      <div className="composer">
        <p className="muted">A ação pode ter sido aplicada. Reenvie a tentativa para confirmar.</p>
        {'text' in pending.command && <p>{pending.command.text}</p>}
        <div className="composer-actions staff-actions">
          <button className="primary" type="button" disabled={busy || loading || !canConfirm}
            onClick={() => void runCommand()}>{retryLabels[pending.command.type]}</button>
          <button className="secondary" type="button" disabled={busy} onClick={() => {
            attempts.abandon(id)
            setCommandError(null)
          }}>Preparar outra ação</button>
        </div>
      </div>
    )}
  </>

  return (
    <div className="case-desk" data-context={contextOpen && !!detail} data-has-detail={!!detail}>
      <section className="staff-conversation" aria-labelledby="staff-conversation-heading">
        <header className="workspace-header">
          <div>
            <h2 id="staff-conversation-heading" tabIndex={-1}>Conversa</h2>
            {(brand || queue) && <p className="context">{[brand?.name, queue?.name].filter(Boolean).join(' · ')}</p>}
          </div>
          <div className="header-tools">
            {detail && <span role="status" className={`case-status ${detail.status}`}>{staffCaseLabels[detail.status]}</span>}
            {detail && <button type="button" className="secondary context-toggle" aria-pressed={contextOpen}
              aria-controls="case-context" onClick={() => setContextOpen(open => !open)}>
              <Icon name={contextOpen ? 'chat' : 'context'} />{contextOpen ? 'Ver conversa' : 'Ver contexto'}
            </button>}
          </div>
        </header>
        <div className="transcript" tabIndex={0} role="region" aria-label="Histórico da conversa">
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
          {(!supervisor || !detail) && commandFeedback}
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
      {detail && <aside id="case-context" className="case-context" aria-labelledby="context-heading">
        <div className="sidebar-header"><h2 id="context-heading">Contexto do caso</h2></div>
        {error && <p role="alert" className="notice">{error}</p>}
        <CaseContext detail={detail} brand={brand} queue={queue?.name} owned={owned}
          messages={data?.messages ?? []} onOpen={onOpen} onReference={showReference} />
        {supervisor && <div className="case-supervision">
          <h3>Supervisão</h3>
          {commandFeedback}
          {!error && <SupervisorActions detail={detail} filters={filters} revision={revision}
            disabled={loading || busy || !!pending} run={runCommand} />}
        </div>}
      </aside>}
    </div>
  )
}
