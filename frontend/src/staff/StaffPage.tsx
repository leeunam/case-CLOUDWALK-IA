import { useCallback, useEffect, useState } from 'react'
import { Icon } from '../Icon'
import { ConnectionNotice } from '../ConnectionNotice'
import { Login } from './Login'
import { CaseList } from './CaseList'
import { StaffNavigation } from './StaffNavigation'
import { currentView, filtersForView, viewLabels, type StaffView } from './navigation'
import type { ListFilters, OperationUpdate, Session } from '../api/contract'
import { ApiError } from '../api/http'
import { getSession, staff } from '../api/staff'
import { errorMessage, useResource } from '../simulator/useResource'
import { Topbar } from '../Topbar'
import { ConfigurationPanel } from '../configuration/ConfigurationPanel'
import { useOpenCase } from '../useOpenCase'
import { StaffConversation } from './StaffConversation'
import { SessionCommandAttempts } from './commandAttempt'
import { CaseFilterControls } from './CaseFilterControls'
import { OperationControls } from './OperationControls'

function Inbox({ session, onSession, refreshSession, onLogout }: {
  session: Session; onSession: (value: Session) => void; refreshSession: () => void; onLogout: () => void
}) {
  const [revision, setRevision] = useState(0)
  const [filterRevision, setFilterRevision] = useState(0)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [attempts] = useState(() => new SessionCommandAttempts())
  const [filters, setFilters] = useState<ListFilters>({})
  const [caseId, setCaseId] = useOpenCase()
  const [pane, setPane] = useState<'list' | 'conversation'>(() => caseId ? 'conversation' : 'list')
  const [busy, setBusy] = useState(false)
  const [operationError, setOperationError] = useState<string | null>(null)
  const { data: catalog, error: catalogError } = useResource(staff.filters, filterRevision)
  const operation = session.operation
  const isSupervisor = session.user?.role === 'supervisor'
  const refreshInbox = useCallback(() => setRevision(previous => previous + 1), [])
  const refreshAll = useCallback(() => {
    refreshInbox()
    refreshSession()
  }, [refreshInbox, refreshSession])

  useEffect(() => {
    function refreshAccess() {
      setFilterRevision(value => value + 1)
      refreshAll()
    }
    const interval = window.setInterval(refreshAccess, 15000)
    window.addEventListener('online', refreshAccess)
    return () => {
      window.clearInterval(interval)
      window.removeEventListener('online', refreshAccess)
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

  const view = settingsOpen ? 'configuration' : currentView(filters, isSupervisor)
  function navigate(next: StaffView) {
    setSettingsOpen(next === 'configuration')
    if (next !== 'configuration') {
      setFilters(previous => filtersForView(previous, next))
      setPane('list')
    }
  }
  function openCase(id: string) {
    setCaseId(id)
    setPane('conversation')
    requestAnimationFrame(() => document.getElementById('staff-conversation-heading')?.focus())
  }

  return (
    <div className="staff-app">
      <StaffNavigation session={session} view={view} onView={navigate} busy={busy} onLogout={() => void logout()} />
      <main className="staff-main">
        <header className="operation-header">
          <div className="operation-title"><h1>{viewLabels[view]}</h1>
            <span className="compact-user">{session.user?.name}</span>
          </div>
          {operation && <OperationControls operation={operation} catalog={catalog} busy={busy} updateOperation={updateOperation} />}
        </header>
        <ConnectionNotice />
        {operationError && <p className="notice catalog-notice" role="alert">{operationError}</p>}
        {catalogError && <p className="notice catalog-notice" role="alert">{catalogError}</p>}
        {isSupervisor && settingsOpen && <ConfigurationPanel session={session} onChange={reload} />}
        <div className="inbox-shell" hidden={settingsOpen}>
          <div className="pane-nav" aria-label="Painéis da caixa" role="group">
            <button type="button" aria-pressed={pane === 'list'} onClick={() => setPane('list')}><Icon name="list" />Lista</button>
            <button type="button" aria-pressed={pane === 'conversation'} disabled={!caseId} onClick={() => setPane('conversation')}><Icon name="chat" />Conversa</button>
          </div>
          <div className="inbox" data-pane={pane}>
            <aside className="case-list" aria-labelledby="staff-cases-heading">
              <div className="sidebar-header">
                <h2 id="staff-cases-heading">Atendimentos</h2>
                <button type="button" className="icon-button" onClick={reload} aria-label="Atualizar caixa"><Icon name="refresh" /></button>
              </div>
              <CaseFilterControls filters={filters} setFilters={setFilters} catalog={catalog} analyst={!isSupervisor} />
              <CaseList key={JSON.stringify(filters)} filters={filters} catalog={catalog} revision={revision} caseId={caseId} onOpen={openCase} />
            </aside>
            {caseId
              ? <StaffConversation key={caseId} id={caseId} session={session} attempts={attempts} filters={catalog}
                  onOpen={openCase} onChanged={refreshAll} />
              : <section className="empty-conversation"><Icon name="inbox" /><h2>Nenhum atendimento selecionado</h2><p>Selecione um caso na lista para acompanhar a conversa.</p></section>}
          </div>
        </div>
      </main>
    </div>
  )
}

export function StaffPage() {
  const [revision, setRevision] = useState(0)
  const { data: session, loading, error, replaceData } = useResource(getSession, revision)
  const refresh = useCallback(() => setRevision(value => value + 1), [])
  const loggedIn = session?.user?.role === 'analyst' || session?.user?.role === 'supervisor'

  return (
    <>
      {!loggedIn && <Topbar staffPage />}
      {error && (
        <div className="notice catalog-notice" role="alert">
          <p>{error}</p>
          <button className="secondary" onClick={refresh} disabled={loading}>Tentar novamente</button>
        </div>
      )}
      {!session && loading && <p className="workspace-state" role="status">Conferindo sessão…</p>}
      {session && (loggedIn
        ? <Inbox key={`${session.user?.role}:${session.user?.id}`} session={session} onSession={replaceData} refreshSession={refresh}
            onLogout={() => { replaceData(null); refresh() }} />
        : <main className="login-layout"><Login session={session} onSession={replaceData} /></main>)}
    </>
  )
}
