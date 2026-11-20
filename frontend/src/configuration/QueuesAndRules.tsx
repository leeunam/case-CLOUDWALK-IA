import { useState } from 'react'
import type { Catalog, QueueSettings, Rule, TeamSettings } from '../api/configuration'
import { configuration } from '../api/configuration'
import type { Session } from '../api/contract'
import type { Priority } from '../simulator/contract'
import { ConfigurationForm, Checks } from './ConfigurationForm'

export function Queues({ brand, session, queues, teams, onSaved }: {
  brand: string; session: Session; queues: QueueSettings[]; teams: TeamSettings[]; onSaved: () => void
}) {
  const [id, setId] = useState('')
  const entry = queues.find(queue => queue.id === id)

  return <section>
    <h2>Filas</h2>
    <label>Fila para editar
      <select value={id} onChange={event => setId(event.target.value)}>
        <option value="">Nova fila</option>
        {queues.map(queue => <option key={queue.id} value={queue.id}>{queue.name}{queue.active ? '' : ' (inativa)'}</option>)}
      </select>
    </label>
    <ConfigurationForm key={entry ? `${entry.id}:${entry.version}` : 'new'} submit={entry ? 'Salvar fila' : 'Criar fila'}
      onSaved={onSaved} onSave={async data => {
        const result = await configuration.saveQueue(session, brand, {
          name: String(data.get('name')).trim(), active: data.has('active'), team_ids: data.getAll('teams').map(String),
        }, entry)
        setId(result.id)
      }}>
      <label>Nome da fila <input name="name" defaultValue={entry?.name} required /></label>
      <label><input type="checkbox" name="active" defaultChecked={entry?.active ?? true} /> Fila ativa</label>
      <Checks legend="Equipes responsáveis" name="teams" options={teams} selected={entry?.team_ids ?? []} />
    </ConfigurationForm>
  </section>
}

export function Rules({ brand, session, rules, queues, catalog, onSaved }: {
  brand: string; session: Session; rules: Rule[]; queues: QueueSettings[]; catalog: Catalog; onSaved: () => void
}) {
  const [id, setId] = useState('')
  const rule = rules.find(entry => entry.id === id)
  const activeQueues = queues.filter(queue => queue.active || queue.id === rule?.queue_id)
  const categories = catalog.categories.filter(item => item.active || item.key === rule?.category)
  const nextPosition = Math.max(0, ...rules.filter(entry => entry.active).map(entry => entry.position)) + 10

  return <section>
    <h2>Regras de encaminhamento</h2>
    <label>Regra para editar
      <select value={id} onChange={event => setId(event.target.value)}>
        <option value="">Nova regra</option>
        {rules.map(entry => <option key={entry.id} value={entry.id}>
          {entry.position} · {queues.find(queue => queue.id === entry.queue_id)?.name}{entry.active ? '' : ' (inativa)'}
        </option>)}
      </select>
    </label>
    <ConfigurationForm key={rule ? `${rule.id}:${rule.version}` : 'new'} submit="Publicar regra" onSaved={onSaved}
      onSave={async data => {
        const result = await configuration.saveRule(session, brand, {
          active: data.has('active'), position: Number(data.get('position')), queue_id: String(data.get('queue')),
          category: String(data.get('category')) || null, priority: (String(data.get('priority')) || null) as Priority | null,
        }, rule)
        setId(result.id)
      }}>
      <label>Posição <input name="position" type="number" min="1" step="1" defaultValue={rule?.position ?? nextPosition} required /></label>
      <label>Fila de destino
        <select name="queue" defaultValue={rule?.queue_id ?? ''} required>
          <option value="" disabled>Selecione uma fila</option>
          {activeQueues.map(queue => <option key={queue.id} value={queue.id}>{queue.name}</option>)}
        </select>
      </label>
      <label>Categoria
        <select name="category" defaultValue={rule?.category ?? ''}>
          <option value="">Qualquer categoria</option>
          {categories.map(category => <option key={category.key} value={category.key}>{category.name}</option>)}
        </select>
      </label>
      <label>Prioridade
        <select name="priority" defaultValue={rule?.priority ?? ''}>
          <option value="">Qualquer prioridade</option>
          {catalog.priorities.map(priority => <option key={priority.key} value={priority.key}>{priority.name}</option>)}
        </select>
      </label>
      <label><input type="checkbox" name="active" defaultChecked={rule?.active ?? true} /> Regra ativa</label>
    </ConfigurationForm>
  </section>
}
