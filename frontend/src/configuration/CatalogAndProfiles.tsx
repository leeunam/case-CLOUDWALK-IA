import { useCallback, useState } from 'react'
import { configuration } from '../api/configuration'
import type { Analyst, Catalog, CatalogCategory, Profile, ProfileInput } from '../api/configuration'
import type { Session } from '../api/contract'
import { ApiError } from '../api/http'
import { useResource } from '../hooks/useResource'
import { ConfigurationForm } from './ConfigurationForm'

export function CatalogEditor({ catalog, session, onSaved }: {
  catalog: Catalog; session: Session; onSaved: () => void
}) {
  const [added, setAdded] = useState(0)
  const categories: CatalogCategory[] = [...catalog.categories, ...Array.from({ length: added }, () => ({
    key: '', name: '', active: true,
  }))]

  return <section>
    <h2>Catálogo de classificação</h2>
    <ConfigurationForm submit="Publicar catálogo" onSaved={onSaved} onSave={data =>
      configuration.saveCatalog(session, catalog, categories.map((_, index) => ({
        key: String(data.get(`key-${index}`)).trim(), name: String(data.get(`name-${index}`)).trim(),
        active: data.has(`active-${index}`),
      })))}>
      {categories.map((category, index) => <div className="configuration-row" key={category.key || index}>
        <label>Chave <input name={`key-${index}`} defaultValue={category.key} readOnly={!!category.key}
          pattern="[a-z][a-z0-9_]*" required /></label>
        <label>Nome da categoria <input name={`name-${index}`} defaultValue={category.name} required /></label>
        <label><input type="checkbox" name={`active-${index}`} defaultChecked={category.active} /> Ativa</label>
      </div>)}
      <div className="staff-controls">
        <button className="secondary" type="button" onClick={() => setAdded(value => value + 1)}>Adicionar categoria</button>
        {added > 0 && <button className="text-button" type="button" onClick={() => setAdded(value => value - 1)}>Remover último rascunho</button>}
      </div>
    </ConfigurationForm>
    <h3>Prioridades</h3>
    <dl>{catalog.priorities.map(item => <div key={item.key}><dt>{item.name}</dt><dd>{item.description}</dd></div>)}</dl>
  </section>
}

type Pair = ProfileInput['alternatives'][number][number]

function ProfileForm({ profile, analyst, catalogs, session, onSaved }: {
  profile: Profile | null; analyst: Analyst; catalogs: Catalog[]; session: Session; onSaved: () => void
}) {
  const categories = Array.from(new Map(catalogs.flatMap(catalog =>
    catalog.categories.filter(category => category.active).map(category => [category.key, category] as const),
  )).values())
  const priorities = catalogs[0]?.priorities ?? []
  const newPair = (): Pair => ({ priority: 'basic', category: categories[0]?.key ?? '', limit: 1 })
  const [alternatives, setAlternatives] = useState(() => profile?.alternatives ?? [[newPair()]])

  function changePair(group: number, index: number, change: Partial<Pair>) {
    setAlternatives(previous => previous.map((pairs, position) => position === group
      ? pairs.map((pair, offset) => offset === index ? { ...pair, ...change } : pair)
      : pairs))
  }

  return <ConfigurationForm submit={profile ? 'Publicar versão do perfil' : 'Criar perfil'} onSaved={onSaved}
    onSave={data => configuration.saveProfile(session, analyst.user_id, {
      portfolio_limit: Number(data.get('limit')), alternatives,
    }, profile ?? undefined)}>
    {profile && <p>Versão publicada {profile.version}</p>}
    <label>Limite de carteira <input name="limit" type="number" min="1" step="1" defaultValue={profile?.portfolio_limit ?? 1} required /></label>
    <p>Cada alternativa precisa comportar todos os atendimentos ativos ao mesmo tempo.</p>
    {alternatives.map((pairs, group) => <fieldset className="configuration-checks" key={group}>
      <legend>Alternativa {group + 1}</legend>
      {pairs.map((pair, index) => <div className="configuration-row" key={index}>
        <label>Prioridade
          <select value={pair.priority} onChange={event => changePair(group, index, { priority: event.target.value as Pair['priority'] })} required>
            {priorities.map(item => <option key={item.key} value={item.key}>{item.name}</option>)}
          </select>
        </label>
        <label>Categoria
          <select value={pair.category} onChange={event => changePair(group, index, { category: event.target.value })} required>
            <option value="">Selecione uma categoria</option>
            {!!pair.category && !categories.some(item => item.key === pair.category) && <option value={pair.category}>{pair.category} (inativa)</option>}
            {categories.map(item => <option key={item.key} value={item.key}>{item.name}</option>)}
          </select>
        </label>
        <label>Máximo simultâneo
          <input type="number" min="1" step="1" value={Number.isNaN(pair.limit) ? '' : pair.limit}
            onChange={event => changePair(group, index, { limit: event.target.valueAsNumber })} required />
        </label>
        {pairs.length > 1 && <button type="button" className="text-button" onClick={() =>
          setAlternatives(previous => previous.map((items, offset) => offset === group ? items.filter((_, i) => i !== index) : items))
        }>Remover par</button>}
      </div>)}
      <div className="staff-controls">
        <button type="button" className="secondary" onClick={() =>
          setAlternatives(previous => previous.map((items, offset) => offset === group ? [...items, newPair()] : items))
        }>Adicionar par</button>
        {alternatives.length > 1 && <button className="text-button" type="button" onClick={() =>
          setAlternatives(previous => previous.filter((_, offset) => offset !== group))
        }>Remover alternativa</button>}
      </div>
    </fieldset>)}
    <button type="button" className="secondary" onClick={() => setAlternatives(previous => [...previous, [newPair()]])}>
      Adicionar alternativa
    </button>
  </ConfigurationForm>
}

function AnalystProfile({ analyst, session, revision, onSaved }: {
  analyst: Analyst; session: Session; revision: number; onSaved: () => void
}) {
  const load = useCallback(async () => {
    const [profile, catalogs] = await Promise.all([
      configuration.profile(analyst.user_id).catch(failure => {
        if (failure instanceof ApiError && failure.status === 404) return null
        throw failure
      }),
      Promise.all((analyst.brand_ids ?? []).map(configuration.catalog)),
    ])
    return { profile, catalogs }
  }, [analyst])
  const resource = useResource(load, revision)

  if (resource.error) return <p role="alert">{resource.error}</p>
  if (!resource.data || resource.loading) return <p role="status">Carregando perfil…</p>
  const { profile, catalogs } = resource.data
  return <ProfileForm key={profile?.version ?? 'new'} profile={profile} analyst={analyst} catalogs={catalogs}
    session={session} onSaved={onSaved} />
}

export function Profiles({ analysts, session, revision, onSaved }: {
  analysts: Analyst[]; session: Session; revision: number; onSaved: () => void
}) {
  const [id, setId] = useState('')
  const analyst = analysts.find(item => item.user_id === id)

  return <section>
    <h2>Perfis de capacidade</h2>
    <label>Analista
      <select value={id} onChange={event => setId(event.target.value)}>
        <option value="">Selecione um analista</option>
        {analysts.map(item => <option key={item.user_id} value={item.user_id}>{item.name}</option>)}
      </select>
    </label>
    {analyst && <AnalystProfile key={analyst.user_id} analyst={analyst} session={session} revision={revision} onSaved={onSaved} />}
  </section>
}
