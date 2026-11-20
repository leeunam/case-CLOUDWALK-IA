import { useCallback, useState } from 'react'
import { configuration } from '../api/configuration'
import type { BrandSettings } from '../api/configuration'
import type { Session } from '../api/contract'
import { readPages } from '../api/pagination'
import { formatTimestamp } from '../simulator/presentation'
import { useResource } from '../simulator/useResource'
import { usePagedCases } from '../usePagedCases'
import { BrandEditor, TeamEditor } from './BrandsAndTeams'
import { CatalogEditor, Profiles } from './CatalogAndProfiles'
import { Queues, Rules } from './QueuesAndRules'

const tabs = {
  queues: 'Filas',
  rules: 'Regras',
  brand: 'Marca e equipes',
  catalog: 'Catálogo',
  profiles: 'Perfis',
  audit: 'Auditoria',
} as const

const resourceNames: Record<string, string> = {
  brand: 'Marca', team: 'Equipe', queue: 'Fila', routing_rule: 'Regra',
  catalog: 'Catálogo', capacity_profile: 'Perfil',
}

function Audit({ brand, revision }: { brand: string; revision: number }) {
  const load = useCallback((cursor?: string) => configuration.audit(brand, cursor), [brand])
  const audit = usePagedCases(load, revision)

  return <section>
    <h2>Auditoria administrativa</h2>
    {audit.loading && !audit.data && <p role="status">Carregando auditoria…</p>}
    {audit.error && <p role="alert">{audit.error}</p>}
    {audit.data?.items.length === 0 && <p>Nenhuma alteração registrada para esta marca.</p>}
    {audit.data?.items.map(item => <details key={item.id} className="configuration-audit">
      <summary>{resourceNames[item.resource_type] ?? item.resource_type} · versão {item.version} · {formatTimestamp(item.occurred_at)}</summary>
      <dl>
        <div><dt>Supervisor</dt><dd>{item.actor.id}</dd></div>
        <div><dt>Recurso</dt><dd>{item.resource_id}</dd></div>
        <div><dt>Correlação</dt><dd>{item.correlation_id}</dd></div>
      </dl>
      <div className="configuration-comparison">
        <div><h3>Antes</h3><pre>{item.before ? JSON.stringify(item.before, null, 2) : 'Criação'}</pre></div>
        <div><h3>Depois</h3><pre>{JSON.stringify(item.after, null, 2)}</pre></div>
      </div>
    </details>)}
    {audit.data?.next_cursor && <button className="secondary" onClick={audit.loadMore} disabled={audit.loading}>Carregar mais alterações</button>}
  </section>
}

const loadBrands = () => readPages(configuration.brands)
type Tab = keyof typeof tabs

function BrandConfiguration({ brand, session, tab, revision, onSaved }: {
  brand: BrandSettings; session: Session; tab: Exclude<Tab, 'audit'>; revision: number; onSaved: () => void
}) {
  const load = useCallback(async () => {
    const [queues, teams, rules, catalog, members, analysts] = await Promise.all([
      ['queues', 'rules', 'brand'].includes(tab) ? readPages(cursor => configuration.queues(brand.id, cursor)) : null,
      ['queues', 'brand'].includes(tab) ? readPages(configuration.teams) : null,
      tab === 'rules' ? readPages(cursor => configuration.rules(brand.id, cursor)) : null,
      ['rules', 'catalog'].includes(tab) ? configuration.catalog(brand.id) : null,
      tab === 'brand' ? readPages(async cursor => {
        const page = await configuration.members(cursor)
        return { ...page, items: page.items.map(person => ({ ...person, id: person.user_id })) }
      }) : null,
      tab === 'profiles' ? readPages(async cursor => {
        const page = await configuration.analysts(brand.id, cursor)
        return { ...page, items: page.items.map(person => ({ ...person, id: person.user_id })) }
      }) : null,
    ])
    return { queues: queues?.items ?? [], teams: teams?.items ?? [], rules: rules?.items ?? [],
      catalog, members: members?.items ?? [], analysts: analysts?.items ?? [] }
  }, [brand.id, tab])
  const resource = useResource(load, revision)
  const data = resource.data
  if (resource.error) return <p role="alert">{resource.error}</p>
  if (!data) return <p role="status">Carregando configuração…</p>

  const shared = { session, onSaved }
  const queues = data.queues
  return <div aria-busy={resource.loading}>
    {tab === 'queues' && <Queues brand={brand.id} queues={queues}
      teams={data.teams.filter(team => brand.team_ids.includes(team.id))} {...shared} />}
    {tab === 'rules' && data.catalog && <Rules brand={brand.id} queues={queues} rules={data.rules} catalog={data.catalog} {...shared} />}
    {tab === 'brand' && <div className="configuration-comparison">
      <BrandEditor brand={brand} queues={queues} teams={data.teams} {...shared} />
      <TeamEditor brand={brand} teams={data.teams} members={data.members} {...shared} />
    </div>}
    {tab === 'catalog' && data.catalog && <CatalogEditor key={data.catalog.version} catalog={data.catalog} {...shared} />}
    {tab === 'profiles' && <Profiles analysts={data.analysts} revision={revision} {...shared} />}
  </div>
}

export function ConfigurationPanel({ session, onChange }: { session: Session; onChange: () => void }) {
  const [brandId, setBrandId] = useState('')
  const [tab, setTab] = useState<Tab>('queues')
  const [revision, setRevision] = useState(0)
  const [notice, setNotice] = useState('')
  const brands = useResource(loadBrands, revision)
  const data = brands.data?.items ?? []
  const brand = data.find(item => item.id === brandId) ?? data[0]

  function refresh() {
    setNotice('')
    setRevision(previous => previous + 1)
  }

  function onSaved() {
    setRevision(previous => previous + 1)
    setNotice('Configuração publicada.')
    onChange()
  }

  return <section className="panel configuration-panel" aria-labelledby="configuration-heading">
    <div className="page-heading">
      <h2 id="configuration-heading">Configuração operacional</h2>
      <button className="secondary" onClick={refresh} disabled={brands.loading}>Atualizar configuração</button>
    </div>
    {brands.error && <p role="alert">{brands.error}</p>}
    {brands.loading && !brands.data && <p role="status">Carregando marcas…</p>}
    {brand && <>
      <label>Marca da configuração
        <select value={brand.id} onChange={event => { setBrandId(event.target.value); setNotice('') }}>
          {data.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </label>
      <nav className="configuration-tabs" aria-label="Áreas de configuração">
        {(Object.keys(tabs) as Tab[]).map(item => <button type="button" key={item}
          className={tab === item ? 'primary' : 'secondary'} aria-pressed={tab === item}
          onClick={() => { setTab(item); setNotice('') }}>{tabs[item]}</button>)}
      </nav>
      {notice && <p role="status">{notice}</p>}
      {tab === 'audit' ? <Audit key={brand.id} brand={brand.id} revision={revision} /> :
        <BrandConfiguration key={`${brand.id}:${tab}`} brand={brand} session={session} tab={tab} revision={revision} onSaved={onSaved} />}
    </>}
    {!brands.loading && !brand && !brands.error && <p>Nenhuma marca autorizada para configuração.</p>}
  </section>
}
