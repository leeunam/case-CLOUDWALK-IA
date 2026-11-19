import { useCallback, useEffect, useState } from 'react'
import type { Brand, Channel, SimulatorReceipt, SimulatorRepository } from './contract'
import { Transcript } from '../Transcript'
import { useCaseRefresh } from '../useCaseRefresh'
import { Composer } from './Composer'
import { caseLabels, channelLabels } from './presentation'
import { useResource } from './useResource'

export function Conversation({
  id, latestCaseId, brands, channels, repository, demo, onHistoryChanged, onOpen,
}: {
  id: string
  latestCaseId?: string
  brands: Brand[]
  channels: Channel[]
  repository: SimulatorRepository
  demo: boolean
  onHistoryChanged: () => void
  onOpen: (id: string) => void
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
    onOpen(receipt.case_id)
  }

  return (
    <section className="panel workspace" aria-labelledby="conversation-heading">
      <div className="workspace-header">
        <div>
          {channel && <p className="context">{channelLabels[channel.type]}{brand && ` · ${brand.name}`}</p>}
          <h2 id="conversation-heading">Conversa</h2>
        </div>
        {detail && <span role="status" className={`case-status ${detail.status}`}>{caseLabels[detail.status]}</span>}
      </div>
      {previousCaseId && (
        <div className="previous-case">
          <button className="text-button" onClick={() => onOpen(previousCaseId)}>Ver atendimento anterior</button>
        </div>
      )}
      <div className="transcript">
        {!data && loading && <p role="status">Carregando conversa…</p>}
        {error && (
          <div className="notice" role="alert">
            <p>{error}</p>
            <button className="secondary" onClick={refresh} disabled={loading}>Tentar novamente</button>
          </div>
        )}
        {data && <Transcript messages={data.messages} />}
      </div>
      {latestCaseId ? (
        <div className="conversation-footer">
          <button className="secondary" onClick={() => onOpen(latestCaseId)}>Abrir atendimento mais recente</button>
        </div>
      ) : channel && detail && (
        <div className="conversation-footer">
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
          <Composer channel={channel} conversation={detail} repository={repository} onSent={handleSent} />
        </div>
      )}
    </section>
  )
}
