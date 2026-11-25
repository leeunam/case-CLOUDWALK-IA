import type { CaseFilters, ListFilters } from '../api/contract'
import { Icon } from '../Icon'
import { categoryLabels, priorityLabels } from '../simulator/presentation'
import { staffCaseLabels } from './presentation'

export function CaseFilterControls({ filters, setFilters, catalog, analyst }: {
  filters: ListFilters; setFilters: (value: ListFilters) => void; catalog: CaseFilters | null; analyst: boolean
}) {
  const categories = new Map<string, string>()
  for (const brand of catalog?.brands ?? []) {
    if (filters.brand_id && brand.id !== filters.brand_id) continue
    const options = brand.categories ?? Object.entries(categoryLabels).map(([key, name]) => ({ key, name, active: true }))
    for (const option of options) if (!categories.has(option.key)) categories.set(option.key, option.name)
  }
  const filterCount = Object.values(filters).filter(Boolean).length
  return (
    <details className="filter-disclosure">
      <summary><Icon name="filter" />Filtros{filterCount > 0 && <span> · {filterCount}</span>}</summary>
      <div className="case-filters">
        <label>Marca
          <select value={filters.brand_id ?? ''} onChange={event => setFilters({ ...filters, brand_id: event.target.value, queue_id: '', category: '' })}>
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
            {analyst && <option value="me">Meus casos</option>}
            <option value="unassigned">Sem responsável</option>
          </select>
        </label>
        <label>Categoria
          <select value={filters.category ?? ''} onChange={event => setFilters({ ...filters, category: event.target.value })}>
            <option value="">Todas</option>
            {Array.from(categories, ([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
        <label>Prioridade
          <select value={filters.priority ?? ''} onChange={event => setFilters({ ...filters, priority: event.target.value as ListFilters['priority'] })}>
            <option value="">Todas</option>
            {Object.entries(priorityLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
      </div>
      {filterCount > 0 && <button type="button" className="text-button" onClick={() => setFilters({})}>Limpar filtros</button>}
    </details>
  )
}
