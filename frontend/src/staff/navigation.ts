import type { ListFilters } from '../api/contract'

export type InboxView = 'inbox' | 'mine' | 'review' | 'failed'
export type StaffView = InboxView | 'configuration'

export const viewLabels: Record<StaffView, string> = {
  inbox: 'Caixa de atendimento', mine: 'Meus casos', review: 'Em revisão', failed: 'Falhas da IA', configuration: 'Configuração operacional',
}

export function currentView(filters: ListFilters, supervisor: boolean): InboxView {
  if (supervisor && filters.integration_status === 'failed') return 'failed'
  if (supervisor && filters.status === 'classification_review') return 'review'
  if (!supervisor && filters.assignee === 'me') return 'mine'
  return 'inbox'
}

export function filtersForView(filters: ListFilters, view: InboxView): ListFilters {
  const next = { ...filters }
  delete next.integration_status
  delete next.status
  delete next.assignee
  if (view === 'mine') next.assignee = 'me'
  if (view === 'review') next.status = 'classification_review'
  if (view === 'failed') next.integration_status = 'failed'
  return next
}
