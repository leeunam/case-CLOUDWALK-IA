import { useCallback, useEffect, useState, type Ref } from 'react'
import type { Brand, Channel, SimulatorReceipt, SimulatorRepository } from './contract'
import { Transcript } from '../components/Transcript'
import { useCaseRefresh } from '../hooks/useCaseRefresh'
import { Composer } from './Composer'
import { caseLabels, channelLabels } from './presentation'
import { useResource } from '../hooks/useResource'

export function Conversation({
  id, latestCaseId, brands, channels, repository, demo, headingRef, onHistoryChanged, onOpen, onReceipt,
}: {
  id: string
  latestCaseId?: string
  brands: Brand[]
  channels: Channel[]
  repository: SimulatorRepository
  demo: boolean
  headingRef: Ref<HTMLHeadingElement>
  onHistoryChanged: () => void
  onOpen: (id: string, trigger: HTMLButtonElement) => void
  onReceipt: (id: string) => void
}) {
  const [revision, setRevision] = useState(0)
  const refresh = useCallback(() => setRevision(previous => previous + 1), [])
  const load = useCallback(() => repository.getConversation(id), [repository, id])
  const { data, error, loading } = useResource(load, revision)
  const detail = data?.detail
  const channel = channels.find(item => item.id === detail?.channel_id)
  const brand = brands.find(item => item.id === channel?.brand_id)
  const updatedAt = detail?.updated_at
  const previousCaseId = detail?.previous_case_id

  useEffect(() => {
    if (updatedAt) onHistoryChanged()
  }, [updatedAt, onHistoryChanged])

  const demoPolling = channel?.type === 'chat' && detail?.status === 'ai_active' && !error ? 1000 : null
  useCaseRefresh(id, demo || !detail ? null : 'simulator', demo ? demoPolling : 10000, loading, refresh)

  function handleSent(receipt: SimulatorReceipt) {
    if (receipt.case_id === id) refresh()
    onReceipt(receipt.case_id)
  }

  return (
    <section className="panel workspace" aria-labelledby="conversation-heading">
      <div className="workspace-header">
        <div>
          {channel && <p className="context">{channelLabels[channel.type]}{brand && ` · ${brand.name}`}</p>}
          <h2 id="conversation-heading" ref={headingRef} tabIndex={-1}>Conversa</h2>
        </div>
        {detail && <span role="status" className={`case-status ${detail.status}`}>{caseLabels[detail.status]}</span>}
      </div>
      {previousCaseId && (
        <div className="previous-case">
          <button className="text-button" onClick={event => onOpen(previousCaseId, event.currentTarget)}>Ver atendimento anterior</button>
        </div>
      )}
      <div className="transcript" tabIndex={0} role="region" aria-label="Histórico da conversa">
        {!data && loading && <p role="status">Carregando conversa…</p>}
        {error && (
          <div className="notice" role="alert">
            <p>{error}</p>
            <button className="secondary" onClick={refresh} disabled={loading}>Tentar novamente</button>
          </div>
        )}
        {data && <Transcript messages={data.messages} />}
      </div>
      {(latestCaseId || (channel && detail)) && (
        <div className="conversation-footer">
          {latestCaseId ? (
            <button className="secondary" onClick={event => onOpen(latestCaseId, event.currentTarget)}>Abrir atendimento mais recente</button>
          ) : channel && detail && (
            <div className="conversation-tools">
              <p className="muted">
                {detail.status === 'resolved'
                  ? 'Uma nova mensagem abre outro atendimento nesta conversa.'
                  : channel.type === 'chat'
                    ? 'O chat busca novas mensagens enquanto o atendimento está ativo.'
                    : 'Volte pelo histórico ou atualize para consultar novas respostas.'}
              </p>
              <button className="secondary" onClick={refresh} disabled={loading}>Atualizar conversa</button>
            </div>
          )}
          {channel && detail && (
            <Composer channel={channel} conversation={detail} repository={repository} onSent={handleSent}
              allowNewMessage={!latestCaseId} />
          )}
        </div>
      )}
    </section>
  )
}
