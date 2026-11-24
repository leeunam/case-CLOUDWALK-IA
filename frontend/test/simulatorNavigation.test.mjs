import assert from 'node:assert/strict'
import { test } from 'node:test'
import { focusAfterNavigation, navigate } from '../src/simulator/navigation.ts'

test('recibo liberado após abrir o histórico preserva o painel escolhido', async () => {
  let state = { caseId: 'aberto', showHistory: false }
  const { promise, resolve } = Promise.withResolvers()
  const delivered = promise.then(caseId => { state = navigate(state, { type: 'receipt', submittedFrom: 'aberto', caseId }) })
  state = navigate(state, { type: 'showHistory', visible: true })
  resolve('aberto')
  await delivered
  assert.deepEqual(state, { caseId: 'aberto', showHistory: true })
})

test('recibo de abertura atualiza o caso sem sair do histórico e respeita seleção posterior', () => {
  const history = { caseId: null, showHistory: true }
  const receipt = { type: 'receipt', submittedFrom: null, caseId: 'novo' }
  assert.deepEqual(navigate(history, receipt), { caseId: 'novo', showHistory: true })
  const selected = navigate(history, { type: 'open', caseId: 'outro' })
  assert.deepEqual(navigate(selected, receipt), { caseId: 'outro', showHistory: false })
})

test('novo atendimento abre o formulário e transfere o foco quando o botão sai da tela', () => {
  const before = { caseId: 'anterior', showHistory: true }
  const after = navigate(before, { type: 'open', caseId: null })
  assert.deepEqual(after, { caseId: null, showHistory: false })
  let focusCalls = 0
  const heading = { focus() { focusCalls++ } }
  focusAfterNavigation({ getClientRects: () => [] }, heading)
  assert.equal(focusCalls, 1)
  focusAfterNavigation({ getClientRects: () => [{}] }, heading)
  assert.equal(focusCalls, 1)
})
