import { useCallback, useEffect, useState } from 'react'
import type { ChannelType, SimulatorRepository } from './contract'
import { readPages } from '../api/pagination'
import { brandsFromChannels, createSimulatorApi } from '../api/simulator'
import { Topbar } from '../Topbar'
import { useOpenCase } from '../useOpenCase'
import { usePagedCases } from '../usePagedCases'
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
  const [caseId, setCaseId] = useOpenCase()
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

  function showCase(id: string) {
    refreshHistory()
    setCaseId(current => current === caseId ? id : current)
  }

  return (
    <>
      <Topbar demo={demo} />
      <main className="shell">
        <div className="page-heading">
          <h1>Simulador de atendimento</h1>
          {caseId && (
            <button className="primary" onClick={() => setCaseId(null)}>
              <span aria-hidden="true">+</span> Novo atendimento
            </button>
          )}
        </div>
        <p className="mode-link"><a href={demo ? '/' : '/?fixture=demo'}>{demo ? 'Usar API real' : 'Abrir demonstração local'}</a></p>
        {catalog.error && (
          <div className="notice catalog-notice" role="alert">
            <p>Não foi possível carregar marcas e canais. {catalog.error}</p>
            <button className="secondary" disabled={catalog.loading} onClick={() => { refreshCatalog(); refreshHistory() }}>
              Recarregar marcas e canais
            </button>
          </div>
        )}
        <div className="layout">
          <aside className="panel sidebar" aria-labelledby="history-heading">
            <div className="sidebar-header">
              <h2 id="history-heading">Histórico</h2>
              <button className="icon-button" onClick={refreshHistory} aria-label="Atualizar histórico" disabled={history.loading}>
                <span aria-hidden="true">↻</span>
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
                      <button onClick={() => setCaseId(item.id)} disabled={pendingNewCase}
                        aria-current={caseId === item.id ? 'true' : undefined}>
                        <strong>{itemChannel ? channelLabels[itemChannel.type] : 'Atendimento'}</strong>
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
              onHistoryChanged={refreshHistory} onOpen={showCase} />
          ) : (
            <section className="panel workspace" aria-labelledby="new-heading">
              <div className="workspace-header">
                <h2 id="new-heading">Novo atendimento</h2>
              </div>
              {!catalog.data && catalog.loading && <p className="workspace-state" role="status">Carregando marcas e canais…</p>}
              {catalog.data && !brand && <p className="workspace-state muted">Nenhuma marca está disponível.</p>}
              {brand && (
                <div className="new-case">
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
                          {channelLabels[item.type]}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  {channel ? (
                    <Composer key={channel.id} channel={channel} repository={repository} onAttemptChange={setPendingNewCase}
                      onSent={receipt => showCase(receipt.case_id)} />
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
