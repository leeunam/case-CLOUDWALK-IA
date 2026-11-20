import { useState } from 'react'
import { configuration } from '../api/configuration'
import type { Analyst, BrandSettings, QueueSettings, TeamSettings } from '../api/configuration'
import type { Session } from '../api/contract'
import { Checks, ConfigurationForm } from './ConfigurationForm'

export function BrandEditor({ brand, queues, teams, session, onSaved }: {
  brand: BrandSettings; queues: QueueSettings[]; teams: TeamSettings[]; session: Session; onSaved: () => void
}) {
  return <section>
    <h2>Marca e autorizações</h2>
    <ConfigurationForm key={brand.version} submit="Salvar marca" onSaved={onSaved}
      onSave={data => configuration.updateBrand(session, brand, {
        name: String(data.get('name')).trim(), default_queue_id: String(data.get('queue')),
        team_ids: data.getAll('teams').map(String),
      })}>
      <label>Nome da marca <input name="name" defaultValue={brand.name} required /></label>
      <label>Fila padrão
        <select name="queue" defaultValue={brand.default_queue_id} required>
          {queues.filter(item => item.active).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </label>
      <Checks legend="Equipes autorizadas" name="teams" options={teams} selected={brand.team_ids} />
    </ConfigurationForm>
  </section>
}

export function TeamEditor({ brand, teams, members, session, onSaved }: {
  brand: BrandSettings; teams: TeamSettings[]; members: Analyst[]; session: Session; onSaved: () => void
}) {
  const [id, setId] = useState('')
  const team = teams.find(item => item.id === id)
  const selected = team?.member_user_ids ?? []
  const available = members.map(person => ({ id: person.user_id, name: person.name }))
  const membersById = new Map(available.map(person => [person.id, person.name]))
  const options = [
    ...available,
    ...selected.filter(memberId => !membersById.has(memberId)).map(memberId => ({ id: memberId, name: memberId })),
  ]

  return <section>
    <h2>Equipes e membros</h2>
    <label>Equipe para editar
      <select value={id} onChange={event => setId(event.target.value)}>
        <option value="">Nova equipe em {brand.name}</option>
        {teams.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
    </label>
    {team?.editable === false ? <>
      <p>Esta equipe é compartilhada. A edição exige acesso a todas as marcas vinculadas.</p>
      <ul>{selected.map(memberId => <li key={memberId}>{membersById.get(memberId) ?? memberId}</li>)}</ul>
    </> : <ConfigurationForm key={team ? `${team.id}:${team.version}` : 'new'} submit={team ? 'Salvar equipe' : 'Criar equipe'}
      onSaved={onSaved} onSave={async data => {
        const result = await configuration.saveTeam(session, {
          name: String(data.get('name')).trim(), member_user_ids: data.getAll('members').map(String),
        }, brand.id, team)
        setId(result.id)
      }}>
      <label>Nome da equipe <input name="name" defaultValue={team?.name} required /></label>
      <Checks legend="Membros da equipe" name="members" options={options} selected={selected} />
    </ConfigurationForm>}
  </section>
}
