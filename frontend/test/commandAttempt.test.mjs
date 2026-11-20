import assert from 'node:assert/strict'
import test from 'node:test'
import { beginCommandAttempt } from '../src/staff/commandAttempt.ts'
import { staff } from '../src/api/staff.ts'

const transfer = {
  type: 'transfer', expected_version: 7, destination_queue_id: 'fila-original',
  destination_assignee_id: 'analista-da-fila', reason: 'Ajustar responsável',
}
const correction = {
  type: 'classification', expected_version: 8, category: 'pix', priority: 'urgent', reason: 'Revisar impacto',
}

test('o rascunho de transferência mantém a versão original após a troca concorrente de fila', () => {
  assert.equal(beginCommandAttempt(null, 8, transfer), null)
  const reviewed = { ...transfer, expected_version: 8, destination_queue_id: 'nova-fila', destination_assignee_id: null }
  assert.deepEqual(beginCommandAttempt(null, 8, reviewed)?.command, reviewed)
})

test('apenas a confirmação repete a ação incerta com o mesmo corpo, versão e chave', async t => {
  const requests = []
  t.mock.method(globalThis, 'fetch', async (path, { body, headers }) => {
    requests.push({ path, body, key: headers.get('Idempotency-Key') })
    if (requests.length === 1) throw new TypeError('conexão interrompida após o envio')
    if (path.endsWith('/classification')) return Response.json({ error: { code: 'version_conflict' } }, { status: 409 })
    return Response.json({ id: 'caso', version: 8 })
  })
  const send = attempt => staff.command('caso', attempt.command, { csrf_token: 'sessão' }, attempt.key)

  const draft = { ...transfer }
  const first = beginCommandAttempt(null, 7, draft)
  const sending = send(first)
  assert.equal(beginCommandAttempt(first, 7, draft), null)
  assert.equal(beginCommandAttempt(first, 8, correction), null)
  await assert.rejects(sending, { code: 'network_error' })
  const uncertain = { ...first, status: 'uncertain' }
  draft.destination_queue_id = 'segunda-fila'
  assert.equal(beginCommandAttempt(uncertain, 8, correction), null)

  const confirming = beginCommandAttempt(uncertain, 8)
  assert.equal(confirming.command, first.command)
  assert.equal(beginCommandAttempt(confirming, 8), null)
  assert.equal(beginCommandAttempt(confirming, 8, correction), null)
  await send(confirming)

  const next = beginCommandAttempt(null, 8, correction)
  await assert.rejects(send(next), { code: 'version_conflict' })
  assert.equal(requests.length, 3)
  assert.deepEqual(requests[0], requests[1])
  assert.deepEqual(JSON.parse(requests[1].body), transfer)
  assert.notEqual(requests[2].key, requests[0].key)
})
