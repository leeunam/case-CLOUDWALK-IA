import assert from 'node:assert/strict'
import { test } from 'node:test'
import { currentView, filtersForView } from '../src/staff/navigation.ts'

test('abrir falhas mantém a marca, fila e classificação e remove o recorte anterior', () => {
  const selected = { brand_id: 'uma-marca', queue_id: 'uma-fila', priority: 'urgent', category: 'nova-categoria' }
  const review = { ...selected, status: 'classification_review' }
  const failed = filtersForView(review, 'failed')
  assert.deepEqual(failed, { ...selected, integration_status: 'failed' })
  assert.equal(currentView(failed, true), 'failed')
  assert.equal(currentView(review, true), 'review')
  assert.equal(currentView(review, false), 'inbox')
})

test('voltar à caixa mostra também casos de outros responsáveis e integrações', () => {
  const all = filtersForView({ brand_id: 'marca', integration_status: 'failed', assignee: 'unassigned' }, 'inbox')
  assert.deepEqual(all, { brand_id: 'marca' })
  const mine = filtersForView(all, 'mine')
  assert.deepEqual(mine, { brand_id: 'marca', assignee: 'me' })
  assert.equal(currentView(mine, false), 'mine')
  assert.equal(currentView(all, false), 'inbox')
})
