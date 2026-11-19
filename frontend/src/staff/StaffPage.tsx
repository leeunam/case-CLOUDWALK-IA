import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { CaseFilters, ListFilters, OperationUpdate, Session } from '../api/contract'
import { ApiError } from '../api/http'
import { getSession, staff } from '../api/staff'
import { categoryLabels, formatTimestamp, priorityLabels } from '../simulator/presentation'
import { errorMessage, useResource } from '../simulator/useResource'
import { Topbar } from '../Topbar'
import { useOpenCase } from '../useOpenCase'
import { usePagedCases } from '../usePagedCases'
import { StaffConversation } from './StaffConversation'
import { staffCaseLabels } from './presentation'

function Login({ session, onSession }: { session: Session; onSession: (session: Session) => void }) {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setError(null)
    setBusy(true)
    try {
      onSession(await staff.login(String(form.get('email')).trim(), String(form.get('password')), session.csrf_token))
    } catch (failure) {
      setError(errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="panel signin" onSubmit={login}>
      <h1>Entrar na operação</h1>
      <label>E-mail <input name="email" type="email" autoComplete="username" required /></label>
      <label>Senha <input name="password" type="password" autoComplete="current-password" required /></label>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="primary" disabled={busy} type="submit">{busy ? 'Entrando…' : 'Entrar'}</button>
    </form>
  )
}

function CaseList({ filters, catalog, revision, caseId, onOpen }: {
  filters: ListFilters; catalog: CaseFilters | null; revision: number; caseId: string | null; onOpen: (id: string) => void
}) {
  const read = useCallback((cursor?: string) => staff.listCases(filters, cursor), [filters])
  const list = usePagedCases(read, revision)
  return (
    <>
      {list.loading && !list.data && <p className="sidebar-state" role="status">Carregando atendimentos…</p>}
      {list.error && <p className="notice sidebar-state" role="alert">{list.error}</p>}
      {list.data?.items.length === 0 && <p className="sidebar-state muted">Nenhum atendimento encontrado.</p>}
      <ul className="history">
        {list.data?.items.map(item => {
          const brand = catalog?.brands.find(entry => entry.id === item.brand_id)?.name
          const queue = catalog?.queues.find(entry => entry.id === item.queue_id)?.name
          const category = item.classification.category
          const label = category ? categoryLabels[category as keyof typeof categoryLabels] ?? category : 'Atendimento'
          return (
            <li key={item.id}>
              <button onClick={() => onOpen(item.id)} aria-current={caseId === item.id ? 'true' : undefined}>
                <strong>{label}</strong>
                {(brand || queue) && <span>{[brand, queue].filter(Boolean).join(' · ')}</span>}
                <time className="muted" dateTime={item.updated_at}>{formatTimestamp(item.updated_at)}</time>
                <span className={`case-status ${item.status}`}>{staffCaseLabels[item.status]}</span>
              </button>
            </li>
          )
        })}
      </ul>
      {list.data?.next_cursor && (
        <button className="secondary sidebar-state" onClick={list.loadMore} disabled={list.loading}>Carregar mais atendimentos</button>
      )}
    </>
  )
}

function Inbox({ session, onSession, refreshSession, onLogout }: {
  session: Session; onSession: (value: Session) => void; refreshSession: () => void; onLogout: () => void
}) {
  const [revision, setRevision] = useState(0)
  const [filterRevision, setFilterRevision] = useState(0)
  const [filters, setFilters] = useState<ListFilters>({})
  const [caseId, setCaseId] = useOpenCase()
  const [busy, setBusy] = useState(false)
  const [operationError, setOperationError] = useState<string | null>(null)
  const { data: catalog, error: catalogError } = useResource(staff.filters, filterRevision)
  const operation = session.operation
  const refreshInbox = useCallback(() => setRevision(previous => previous + 1), [])
  const refreshAll = useCallback(() => {
    refreshInbox()
    refreshSession()
  }, [refreshInbox, refreshSession])

  useEffect(() => {
    const interval = window.setInterval(refreshAll, 15000)
    window.addEventListener('online', refreshAll)
    return () => {
      window.clearInterval(interval)
      window.removeEventListener('online', refreshAll)
    }
  }, [refreshAll])

  function reload() {
    setFilterRevision(value => value + 1)
    refreshAll()
  }

  async function updateOperation(data: OperationUpdate) {
    setBusy(true)
    setOperationError(null)
    try {
      onSession(await staff.updateOperation(data, session))
      refreshInbox()
    } catch (failure) {
      setOperationError(errorMessage(failure))
      if (failure instanceof ApiError && [401, 403, 409].includes(failure.status)) reload()
    } finally {
      setBusy(false)
    }
  }

  async function logout() {
    setBusy(true)
    setOperationError(null)
    try {
      await staff.logout(session)
      const url = new URL(window.location.href)
      url.searchParams.delete('case')
      window.history.replaceState(null, '', url)
      onLogout()
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) onLogout()
      else setOperationError(errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-heading">
        <h1>Caixa de atendimento</h1>
        <div className="staff-controls">
          <span>{session.user?.name}</span>
          <button className="secondary" type="button" disabled={busy} onClick={logout}>Sair da operação</button>
        </div>
      </div>
      {operation && (
        <section className="panel operation" aria-label="Operação do analista">
          <label>Marca em operação
            <select value={operation.switch_target_brand_id ?? operation.active_brand_id ?? ''} disabled={busy || !catalog}
              onChange={event => void updateOperation({ switch_target_brand_id: event.target.value })}>
              <option value="" disabled>Selecione uma marca</option>
              {catalog?.brands.map(brand => <option key={brand.id} value={brand.id}>{brand.name}</option>)}
            </select>
          </label>
          <span>Ativos <strong>{operation.active_count}</strong></span>
          <span>Carteira <strong>{operation.portfolio_count}/{operation.portfolio_limit}</strong></span>
          <label className="availability">
            <input type="checkbox" checked={operation.available} disabled={busy}
              onChange={event => void updateOperation({ available: event.target.checked })} />
            Disponível para atribuições
          </label>
          {operation.switch_target_brand_id && (
            <div className="staff-controls">
              <p role="status">Troca pendente. Marca atual: {catalog?.brands.find(brand => brand.id === operation.active_brand_id)?.name ?? '—'}.</p>
              <button className="secondary" disabled={busy} onClick={() => void updateOperation({ switch_target_brand_id: null })}>Cancelar troca</button>
            </div>
          )}
        </section>
      )}
      {operationError && <p className="notice catalog-notice" role="alert">{operationError}</p>}
      {catalogError && <p className="notice catalog-notice" role="alert">{catalogError}</p>}
      <div className="layout">
        <aside className="panel sidebar" aria-labelledby="staff-cases-heading">
          <div className="sidebar-header">
            <h2 id="staff-cases-heading">Atendimentos</h2>
            <button className="icon-button" onClick={reload} aria-label="Atualizar caixa">↻</button>
          </div>
          <div className="case-filters">
            <label>Marca
              <select value={filters.brand_id ?? ''} onChange={event => setFilters({ ...filters, brand_id: event.target.value, queue_id: '' })}>
                <option value="">Todas</option>
                {catalog?.brands.map(brand => <option key={brand.id} value={brand.id}>{brand.name}</option>)}
              </select>
            </label>
            <label>Fila
              <select value={filters.queue_id ?? ''} onChange={event => setFilters({ ...filters, queue_id: event.target.value })}>
                <option value="">Todas</option>
                {catalog?.queues.filter(queue => !filters.brand_id || queue.brand_id === filters.brand_id)
                  .map(queue => <option key={queue.id} value={queue.id}>{queue.name}</option>)}
              </select>
            </label>
            <label>Estado
              <select value={filters.status ?? ''} onChange={event => setFilters({ ...filters, status: event.target.value as ListFilters['status'] })}>
                <option value="">Todos</option>
                {Object.entries(staffCaseLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </label>
            <label>Responsável
              <select value={filters.assignee ?? ''} onChange={event => setFilters({ ...filters, assignee: event.target.value as ListFilters['assignee'] })}>
                <option value="">Todos</option>
                {session.user?.role === 'analyst' && <option value="me">Meus casos</option>}
                <option value="unassigned">Sem responsável</option>
              </select>
            </label>
            <label>Categoria
              <select value={filters.category ?? ''} onChange={event => setFilters({ ...filters, category: event.target.value })}>
                <option value="">Todas</option>
                {Object.entries(categoryLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </label>
            <label>Prioridade
              <select value={filters.priority ?? ''} onChange={event => setFilters({ ...filters, priority: event.target.value as ListFilters['priority'] })}>
                <option value="">Todas</option>
                {Object.entries(priorityLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </label>
          </div>
          <CaseList key={JSON.stringify(filters)} filters={filters} catalog={catalog} revision={revision} caseId={caseId} onOpen={setCaseId} />
        </aside>
        {caseId
          ? <StaffConversation key={caseId} id={caseId} session={session} filters={catalog} onOpen={setCaseId} onChanged={refreshAll} />
          : <section className="panel workspace-state"><p>Selecione um atendimento para acompanhar a conversa.</p></section>}
      </div>
    </>
  )
}

export function StaffPage() {
  const [revision, setRevision] = useState(0)
  const { data: session, loading, error, replaceData } = useResource(getSession, revision)
  const refresh = useCallback(() => setRevision(value => value + 1), [])
  const loggedIn = session?.user?.role === 'analyst' || session?.user?.role === 'supervisor'

  return (
    <>
      <Topbar staffPage />
      <main className="shell">
        {error && (
          <div className="notice catalog-notice" role="alert">
            <p>{error}</p>
            <button className="secondary" onClick={refresh} disabled={loading}>Tentar novamente</button>
          </div>
        )}
        {!session && loading && <p role="status">Conferindo sessão…</p>}
        {session && (loggedIn
          ? <Inbox key={session.user?.id} session={session} onSession={replaceData} refreshSession={refresh}
              onLogout={() => { replaceData(null); refresh() }} />
          : <Login session={session} onSession={replaceData} />)}
      </main>
    </>
  )
}
