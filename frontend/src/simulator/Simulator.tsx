import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import type { ChannelType, SimulatorRepository } from './contract'
import { readPages } from '../api/pagination'
import { brandsFromChannels, createSimulatorApi } from '../api/simulator'
import { Icon } from '../Icon'
import { ConnectionNotice } from '../ConnectionNotice'
import { Topbar } from '../Topbar'
import { caseIdFromUrl, useCaseUrl } from '../useOpenCase'
import { usePagedCases } from '../usePagedCases'
import { navigate, focusAfterNavigation } from './navigation'
import { Composer } from './Composer'
import { Conversation } from './Conversation'
import { createFixtureRepository } from './fixtureRepository'
import { caseLabels, channelLabels, formatTimestamp } from './presentation'
import { useResource } from './useResource'

function selectRepository(): { repository: SimulatorRepository; demo: boolean } {
  const fixture = new URLSearchParams(window.location.search).get('fixture')
  return fixture && ['demo', 'empty', 'error'].includes(fixture)
    ? { repository: createFixtureRepository(fixture), demo: true }
    : { repository: createSimulatorApi(), demo: false }
}

export function Simulator() {
  const [{ repository, demo }] = useState(selectRepository)
  const [catalogRevision, setCatalogRevision] = useState(0)
  const [historyRevision, setHistoryRevision] = useState(0)
  const [{ caseId, showHistory }, dispatch] = useReducer(navigate, null, () => ({
    caseId: caseIdFromUrl(), showHistory: false,
  }))
  useCaseUrl(caseId)
  const workspaceHeading = useRef<HTMLHeadingElement>(null)
  const [brandId, setBrandId] = useState('')
  const [channelType, setChannelType] = useState<ChannelType>('chat')
  const [pendingNewCase, setPendingNewCase] = useState(false)
  const loadCatalog = useCallback(async () => {
    const channels = (await readPages(repository.listChannels)).items
    return { brands: brandsFromChannels(channels), channels }
  }, [repository])
  const catalog = useResource(loadCatalog, catalogRevision)
  const history = usePagedCases(repository.listCases, historyRevision)
  const refreshCatalog = useCallback(() => setCatalogRevision(previous => previous + 1), [])
  const refreshHistory = useCallback(() => setHistoryRevision(previous => previous + 1), [])
  const brands = catalog.data?.brands ?? []
  const channels = catalog.data?.channels ?? []
  const brand = brands.find(item => item.id === brandId) ?? brands[0]
  const brandChannels = Object.keys(channelLabels).flatMap(type =>
    channels.filter(item => item.brand_id === brand?.id && item.type === type),
  )
  const channel = brandChannels.find(item => item.type === channelType) ?? brandChannels[0]
  const selectedCase = history.data?.items.find(item => item.id === caseId)
  const latestCase = selectedCase && history.data?.items.find(item =>
    item.channel_id === selectedCase.channel_id && item.external_conversation_id === selectedCase.external_conversation_id,
  )
  const latestCaseId = latestCase?.id !== caseId ? latestCase?.id : undefined

  useEffect(() => {
    function reconnect() {
      refreshCatalog()
      refreshHistory()
    }
    window.addEventListener('online', reconnect)
    return () => window.removeEventListener('online', reconnect)
  }, [refreshCatalog, refreshHistory])

  function receiveCase(id: string) {
    refreshHistory()
    dispatch({ type: 'receipt', submittedFrom: caseId, caseId: id })
  }

  function openCase(id: string | null, trigger: HTMLButtonElement) {
    flushSync(() => dispatch({ type: 'open', caseId: id }))
    focusAfterNavigation(trigger, workspaceHeading.current)
  }

  return (
    <>
      <Topbar demo={demo} />
      <main className="simulator shell">
        <header className="page-heading">
          <div><h1>Simulador de atendimento</h1>
            <p className="muted">Envie uma mensagem à marca ou continue uma conversa pelo histórico.</p>
          </div>
          <div className="simulator-actions">
            <a className="mode-link" href={demo ? '/' : '/?fixture=demo'}>{demo ? 'Usar API real' : 'Abrir demonstração local'}</a>
            {caseId && <button type="button" className="primary" onClick={event => openCase(null, event.currentTarget)}>
              <Icon name="plus" />Novo atendimento
            </button>}
          </div>
        </header>
        <div className="pane-nav" role="group" aria-label="Painéis do simulador">
          <button type="button" aria-pressed={!showHistory} onClick={() => dispatch({ type: 'showHistory', visible: false })}><Icon name="chat" />{caseId ? 'Conversa' : 'Novo atendimento'}</button>
          <button type="button" aria-pressed={showHistory} onClick={() => dispatch({ type: 'showHistory', visible: true })}><Icon name="history" />Histórico</button>
        </div>
        {!demo && <ConnectionNotice />}
        {catalog.error && (
          <div className="notice catalog-notice" role="alert">
            <p>Não foi possível carregar marcas e canais. {catalog.error}</p>
            <button className="secondary" disabled={catalog.loading} onClick={() => { refreshCatalog(); refreshHistory() }}>
              Recarregar marcas e canais
            </button>
          </div>
        )}
        <div className="simulator-layout" data-history={showHistory}>
          <aside className="panel sidebar" aria-labelledby="history-heading">
            <div className="sidebar-header">
              <h2 id="history-heading"><Icon name="history" />Histórico</h2>
              <button className="icon-button" onClick={refreshHistory} aria-label="Atualizar histórico" disabled={history.loading}>
                <Icon name="refresh" />
              </button>
            </div>
            {!history.data && history.loading && <p className="sidebar-state" role="status">Carregando histórico…</p>}
            {history.error && (
              <div className="notice sidebar-state" role="alert">
                <p>{history.error}</p>
                <button className="secondary" onClick={refreshHistory} disabled={history.loading}>Tentar novamente</button>
              </div>
            )}
            {history.data?.items.length === 0 && <p className="sidebar-state muted">Nenhum atendimento por aqui ainda.</p>}
            {history.data && (
              <ul className="history">
                {history.data.items.map(item => {
                  const itemChannel = channels.find(entry => entry.id === item.channel_id)
                  const itemBrand = brands.find(entry => entry.id === itemChannel?.brand_id)
                  return (
                    <li key={item.id}>
                      <button type="button" onClick={event => openCase(item.id, event.currentTarget)} disabled={pendingNewCase}
                        aria-current={caseId === item.id ? 'true' : undefined}>
                        <strong>{itemChannel && <Icon name={itemChannel.type} />}{itemChannel ? channelLabels[itemChannel.type] : 'Atendimento'}</strong>
                        {itemBrand && <span>{itemBrand.name}</span>}
                        <time className="muted" dateTime={item.updated_at}>{formatTimestamp(item.updated_at)}</time>
                        <span className={`case-status ${item.status}`}>{caseLabels[item.status]}</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
            {history.data?.next_cursor && (
              <button className="secondary sidebar-state" disabled={history.loading} onClick={history.loadMore}>Carregar mais atendimentos</button>
            )}
          </aside>
          {caseId ? (
            <Conversation key={caseId} id={caseId} latestCaseId={latestCaseId} brands={brands} channels={channels} repository={repository} demo={demo}
              headingRef={workspaceHeading} onHistoryChanged={refreshHistory} onOpen={openCase} onReceipt={receiveCase} />
          ) : (
            <section className="panel workspace" aria-labelledby="new-heading">
              <div className="workspace-header">
                <h2 id="new-heading" ref={workspaceHeading} tabIndex={-1}>Novo atendimento</h2>
              </div>
              {!catalog.data && catalog.loading && <p className="workspace-state" role="status">Carregando marcas e canais…</p>}
              {catalog.data && !brand && <p className="workspace-state muted">Nenhuma marca está disponível.</p>}
              {brand && (
                <div className="new-case">
                  <div className="channel-settings">
                  <label className="brand-field">
                    Marca
                    <select value={brand.id} disabled={pendingNewCase} onChange={event => setBrandId(event.target.value)}>
                      {brands.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                    </select>
                  </label>
                  <fieldset className="channel-picker" disabled={pendingNewCase}>
                    <legend>Canal</legend>
                    <div>
                      {brandChannels.map(item => (
                        <label key={item.id} className={channel?.id === item.id ? 'selected' : ''}>
                          <input type="radio" name="channel" value={item.id} checked={channel?.id === item.id}
                            onChange={() => setChannelType(item.type)} />
                          <Icon name={item.type} />{channelLabels[item.type]}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  </div>
                  {channel ? (
                    <Composer key={channel.id} channel={channel} repository={repository} onAttemptChange={setPendingNewCase}
                      onSent={receipt => receiveCase(receipt.case_id)} />
                  ) : <p className="muted">Nenhum canal está disponível para esta marca.</p>}
                </div>
              )}
            </section>
          )}
        </div>
      </main>
    </>
  )
}
