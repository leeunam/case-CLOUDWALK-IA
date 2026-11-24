import { useCallback } from 'react'
import type { CaseFilters, ListFilters } from '../api/contract'
import { staff } from '../api/staff'
import { categoryLabels, formatTimestamp, priorityLabels } from '../simulator/presentation'
import { usePagedCases } from '../usePagedCases'
import { staffCaseLabels } from './presentation'

export function CaseList({ filters, catalog, revision, caseId, onOpen }: {
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
          const brand = catalog?.brands.find(entry => entry.id === item.brand_id)
          const queue = catalog?.queues.find(entry => entry.id === item.queue_id)?.name
          const category = item.classification.category
          const name = brand?.categories?.find(entry => entry.key === category)?.name
          const priority = item.classification.priority
          const label = category ? name ?? categoryLabels[category as keyof typeof categoryLabels] ?? category : 'Atendimento'
          return (
            <li key={item.id}>
              <button type="button" onClick={() => onOpen(item.id)} aria-current={caseId === item.id ? 'true' : undefined}>
                <strong>{label}</strong>
                {(brand || queue) && <span>{[brand?.name, queue].filter(Boolean).join(' · ')}</span>}
                <time className="muted" dateTime={item.updated_at}>{formatTimestamp(item.updated_at)}</time>
                <span className="row-status"><span className={`case-status ${item.status}`}>{staffCaseLabels[item.status]}</span>
                  {priority && <span>{priorityLabels[priority]}</span>}</span>
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
