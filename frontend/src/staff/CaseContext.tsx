import type { StaffCase } from '../api/contract'
import type { Brand, Message } from '../simulator/contract'
import { categoryLabels, formatTimestamp, priorityLabels } from '../simulator/presentation'

const blocks: Record<string, string> = {
  active_capacity: 'O perfil não comporta mais casos ativos.',
  portfolio_limit: 'A carteira atingiu o limite.',
  different_operating_brand: 'O responsável está operando em outra marca.',
  analyst_unavailable: 'O responsável está indisponível para novas atribuições.',
  brand_switch_pending: 'O responsável está preparando a troca de marca.',
  no_eligible_analyst: 'A fila aguarda um analista elegível.',
  queue_access_revoked: 'O responsável perdeu acesso à fila.',
}

const sourceNames = { channel: 'Canal', jev: 'Classificador', supervisor: 'Supervisão' }
const integrationLabels = { idle: 'Sem tentativa em andamento', pending_delivery: 'Aguardando entrega', awaiting_result: 'Aguardando resposta', failed: 'Falha na integração' }

export function CaseContext({ detail, brand, queue, owned, messages, onOpen, onReference }: {
  detail: StaffCase; brand?: Brand; queue?: string; owned: boolean; messages: Message[]
  onOpen: (id: string) => void; onReference: (id: string) => void
}) {
  const { classification, handoff, previous_case_id: previous } = detail
  const category = classification.category
  const categoryName = brand?.categories?.find(item => item.key === category)?.name
  const assignee = detail.assignee?.type === 'ai' ? 'Atendente de IA' : detail.assignee ? (owned ? 'Você' : 'Outro analista') : 'Sem responsável'
  return <div className="context-body">
    {handoff && <section className="handoff" aria-labelledby="handoff-heading">
      <h3 id="handoff-heading">Resumo do encaminhamento</h3>
      <p>{handoff.summary}</p>
      {handoff.message_ids.length > 0 && <ul className="handoff-references" aria-label="Mensagens referenciadas">
        {handoff.message_ids.map(id => {
          const message = messages.find(item => item.id === id)
          return message && <li key={id}><a href={`#message-${id}`} onClick={event => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
            onReference(id)
          }}>Mensagem {message.sequence}</a></li>
        })}
      </ul>}
    </section>}
    <section><h3>Atendimento</h3>
      <dl className="attributes">
        <div><dt>Marca</dt><dd>{brand?.name ?? detail.brand_id}</dd></div>
        <div><dt>Fila</dt><dd>{queue ?? detail.queue_id}</dd></div>
        <div><dt>Responsável</dt><dd>{assignee}</dd></div>
        {detail.human_queue_since && <div><dt>Na fila desde</dt><dd><time dateTime={detail.human_queue_since}>{formatTimestamp(detail.human_queue_since)}</time></dd></div>}
        {detail.status === 'ai_active' && <div><dt>Integração</dt><dd>{integrationLabels[detail.integration_status]}</dd></div>}
      </dl>
      {detail.blocking_reason && <p className="warning">{blocks[detail.blocking_reason] ?? detail.blocking_reason}</p>}
    </section>
    <section><h3>Classificação</h3>
      <dl className="attributes">
        <div><dt>Categoria</dt><dd>{category ? categoryName ?? categoryLabels[category as keyof typeof categoryLabels] ?? category : 'Sem categoria'}
          {classification.category_source && <small>Origem · {sourceNames[classification.category_source]}</small>}</dd></div>
        <div><dt>Prioridade</dt><dd>{classification.priority ? priorityLabels[classification.priority] : 'Sem prioridade'}
          {classification.priority_source && <small>Origem · {sourceNames[classification.priority_source]}</small>}</dd></div>
      </dl>
    </section>
    <details className="record-details"><summary>Registro do caso</summary>
      <dl className="attributes"><div><dt>Identificador</dt><dd><code>{detail.id}</code></dd></div>
        <div><dt>Aberto em</dt><dd>{formatTimestamp(detail.created_at)}</dd></div>
        <div><dt>Atualizado em</dt><dd>{formatTimestamp(detail.updated_at)}</dd></div></dl>
    </details>
    {previous && <button type="button" className="text-button" onClick={() => onOpen(previous)}>Ver atendimento anterior</button>}
  </div>
}
