import { useCallback, useState } from 'react'
import { configuration } from '../api/configuration'
import type { CaseFilters, StaffCase, StaffCommand } from '../api/contract'
import { readPages } from '../api/pagination'
import { staff } from '../api/staff'
import { ConfigurationForm } from '../configuration/ConfigurationForm'
import type { Priority } from '../simulator/contract'
import { categoryLabels, formatTimestamp, priorityLabels } from '../simulator/presentation'
import { useResource } from '../simulator/useResource'
import { usePagedCases } from '../usePagedCases'

function Transfer({ detail, revision, run }: {
  detail: StaffCase; revision: number; run: (command: StaffCommand) => Promise<void>
}) {
  const [queueId, setQueueId] = useState(detail.queue_id)
  const loadQueues = useCallback(() => readPages(cursor => configuration.queues(detail.brand_id, cursor)), [detail.brand_id])
  const queues = useResource(loadQueues, revision)
  const active = queues.data?.items.filter(queue => queue.active) ?? []
  const queue = active.find(item => item.id === queueId)

  return <details className="configuration-audit">
    <summary>Transferir atendimento</summary>
    {queues.error && <p role="alert">{queues.error}</p>}
    <label>Fila de destino
      <select value={queueId} onChange={event => setQueueId(event.target.value)} disabled={!active.length}>
        {!queue && <option value={queueId}>Selecione uma fila</option>}
        {active.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
    </label>
    {queue && <TransferForm key={queue.id} detail={detail} queue={queue.id} revision={revision} run={run} />}
  </details>
}

function TransferForm({ detail, queue, revision, run }: {
  detail: StaffCase; queue: string; revision: number; run: (command: StaffCommand) => Promise<void>
}) {
  const load = useCallback(() => readPages(async cursor => {
    const page = await configuration.queueAnalysts(detail.brand_id, queue, cursor)
    return { ...page, items: page.items.map(person => ({ ...person, id: person.user_id })) }
  }), [detail.brand_id, queue])
  const candidates = useResource(load, revision)
  return <ConfigurationForm submit="Transferir" onSave={data => run({
    type: 'transfer', expected_version: detail.version, reason: String(data.get('reason')).trim(),
    destination_queue_id: queue, destination_assignee_id: String(data.get('assignee')) || null,
  })}>
    {candidates.error && <p role="alert">{candidates.error}</p>}
    <label>Responsável de destino
      <select name="assignee" defaultValue="">
        <option value="">Distribuição automática</option>
        {candidates.data?.items.map(person => <option key={person.attendant_id} value={person.attendant_id}>{person.name}</option>)}
      </select>
    </label>
    <label>Motivo da transferência <input name="reason" required /></label>
  </ConfigurationForm>
}

function CaseAudit({ id, revision }: { id: string; revision: number }) {
  const load = useCallback((cursor?: string) => staff.audit(id, cursor), [id])
  const audit = usePagedCases(load, revision)
  return <>
    {audit.loading && !audit.data && <p role="status">Carregando auditoria…</p>}
    {audit.error && <p role="alert">{audit.error}</p>}
    <ul>{audit.data?.items.map(item => <li key={item.id}>
      <time dateTime={item.occurred_at}>{formatTimestamp(item.occurred_at)}</time> · {item.type}
      {item.reason && <p>{item.reason}</p>}
      {item.routing && <p>Fila {item.routing.queue_id} · {item.routing.rule_id
        ? `Regra ${item.routing.rule_id}, versão ${item.routing.rule_version}` : 'Fila padrão'}</p>}
    </li>)}</ul>
    {audit.data?.next_cursor && <button className="secondary" disabled={audit.loading} onClick={audit.loadMore}>Carregar mais eventos</button>}
  </>
}

export function SupervisorActions({ detail, filters, revision, run }: {
  detail: StaffCase; filters: CaseFilters | null; revision: number; run: (command: StaffCommand) => Promise<void>
}) {
  const [auditOpen, setAuditOpen] = useState(false)
  const [force, setForce] = useState(false)
  const categories = filters?.brands.find(brand => brand.id === detail.brand_id)?.categories ??
    Object.entries(categoryLabels).map(([key, name]) => ({ key, name, active: true }))
  const active = categories.filter(category => category.active)
  const canTransfer = ['waiting_human', 'human_active', 'waiting_customer', 'waiting_resumption'].includes(detail.status)
  const failed = detail.status === 'ai_active' && detail.integration_status === 'failed'

  return <section aria-label="Ações de supervisão">
    {failed && <details open className="configuration-audit">
      <summary>Recuperar integração da IA</summary>
      <ConfigurationForm submit={force ? 'Encaminhar para humano' : 'Tentar IA novamente'} onSave={data => {
        const reason = String(data.get('reason')).trim()
        const expected_version = detail.version
        return run(force
          ? { type: 'force_handoff', expected_version, reason, summary: String(data.get('summary')).trim() }
          : { type: 'retry_agent', expected_version, reason })
      }}>
        <label>Ação de recuperação
          <select value={force ? 'handoff' : 'retry'} onChange={event => setForce(event.target.value === 'handoff')}>
            <option value="retry">Tentar IA novamente</option>
            <option value="handoff">Forçar encaminhamento humano</option>
          </select>
        </label>
        <label>Motivo da recuperação <input name="reason" required /></label>
        {force && <label>Resumo para o analista <textarea name="summary" required /></label>}
      </ConfigurationForm>
    </details>}
    {detail.status !== 'resolved' && <details className="configuration-audit">
      <summary>Corrigir classificação</summary>
      <ConfigurationForm key={`${detail.classification.category}:${detail.classification.priority}`}
        submit="Aplicar correção" onSave={data => run({
          type: 'classification', expected_version: detail.version, reason: String(data.get('reason')).trim(),
          category: String(data.get('category')), priority: String(data.get('priority')) as Priority,
        })}>
        <label>Categoria revisada
          <select name="category" required defaultValue={active.some(item => item.key === detail.classification.category) ? detail.classification.category! : ''}>
            <option value="">Selecione uma categoria</option>
            {active.map(item => <option key={item.key} value={item.key}>{item.name}</option>)}
          </select>
        </label>
        <label>Prioridade revisada
          <select name="priority" required defaultValue={detail.classification.priority ?? ''}>
            <option value="">Selecione uma prioridade</option>
            {Object.entries(priorityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label>Motivo da correção <input name="reason" required /></label>
      </ConfigurationForm>
    </details>}
    {canTransfer && <Transfer detail={detail} revision={revision} run={run} />}
    <details className="configuration-audit" onToggle={event => setAuditOpen(event.currentTarget.open)}>
      <summary>Auditoria do atendimento</summary>
      {auditOpen && <CaseAudit id={detail.id} revision={revision} />}
    </details>
  </section>
}
