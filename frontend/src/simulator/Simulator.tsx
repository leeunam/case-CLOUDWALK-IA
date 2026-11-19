import { useCallback, useEffect, useState } from 'react'
import type { ChannelType } from './contract'
import { Composer } from './Composer'
import { Conversation } from './Conversation'
import { createFixtureRepository } from './fixtureRepository'
import { caseLabels, channelLabels, formatTimestamp } from './presentation'
import { useResource } from './useResource'

const params = new URLSearchParams(window.location.search)
const repository = createFixtureRepository(params.get('fixture'))

async function loadCatalog() {
  const [brands, channels] = await Promise.all([repository.listBrands(), repository.listChannels()])
  return { brands, channels: channels.items }
}

export function Simulator() {
  const [catalogRevision, setCatalogRevision] = useState(0)
  const [historyRevision, setHistoryRevision] = useState(0)
  const [caseId, setCaseId] = useState(params.get('case'))
  const [brandId, setBrandId] = useState('')
  const [channelType, setChannelType] = useState<ChannelType>('chat')
  const catalog = useResource(loadCatalog, catalogRevision)
  const history = useResource(repository.listCases, historyRevision)
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
    const url = new URL(window.location.href)
    if (caseId) url.searchParams.set('case', caseId)
    else url.searchParams.delete('case')
    window.history.replaceState(null, '', url)
  }, [caseId])

  function showCase(id: string) {
    refreshHistory()
    setCaseId(current => current === caseId ? id : current)
  }

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <div className="identity">
            <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
            <span>Help desk</span>
          </div>
          <div className="topbar-actions">
            <span className="mode"><i aria-hidden="true" />Modo simulado</span>
            <a href="/health">Status da API</a>
          </div>
        </div>
      </header>
      <main className="shell">
        <div className="page-heading">
          <h1>Simulador de atendimento</h1>
          {caseId && (
            <button className="primary" onClick={() => setCaseId(null)}>
              <span aria-hidden="true">+</span> Novo atendimento
            </button>
          )}
        </div>
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
                      <button onClick={() => setCaseId(item.id)} aria-current={caseId === item.id ? 'true' : undefined}>
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
          </aside>
          {caseId ? (
            <Conversation key={caseId} id={caseId} latestCaseId={latestCaseId} brands={brands} channels={channels} repository={repository}
              onHistoryChanged={refreshHistory} onOpen={showCase} />
          ) : (
            <section className="panel workspace" aria-labelledby="new-heading">
              <div className="workspace-header">
                <h2 id="new-heading">Novo atendimento</h2>
              </div>
              {!catalog.data && catalog.loading && <p className="workspace-state" role="status">Carregando marcas e canais…</p>}
              {catalog.error && (
                <div className="notice workspace-state" role="alert">
                  <p>{catalog.error}</p>
                  <button className="secondary" disabled={catalog.loading} onClick={() => setCatalogRevision(value => value + 1)}>
                    Tentar novamente
                  </button>
                </div>
              )}
              {catalog.data && !brand && <p className="workspace-state muted">Nenhuma marca está disponível.</p>}
              {brand && (
                <div className="new-case">
                  <label className="brand-field">
                    Marca
                    <select value={brand.id} onChange={event => setBrandId(event.target.value)}>
                      {brands.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                    </select>
                  </label>
                  <fieldset className="channel-picker">
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
                    <Composer key={channel.id} channel={channel} repository={repository}
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
