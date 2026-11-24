import type { CaseFilters, OperationUpdate, Session } from '../api/contract'

export function OperationControls({ operation, catalog, busy, updateOperation }: {
  operation: NonNullable<Session['operation']>; catalog: CaseFilters | null; busy: boolean
  updateOperation: (update: OperationUpdate) => Promise<void>
}) {
  return (
    <section className="operation" aria-label="Operação do analista">
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
  )
}
