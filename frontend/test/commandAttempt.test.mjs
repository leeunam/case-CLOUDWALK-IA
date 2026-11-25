import assert from 'node:assert/strict'
import test from 'node:test'
import { beginCommandAttempt, SessionCommandAttempts } from '../src/staff/commandAttempt.ts'
import { ApiError } from '../src/api/http.ts'
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

test('ir à configuração durante o envio e abrir outro caso durante a confirmação preserva a tentativa', async t => {
  const inbox = new SessionCommandAttempts()
  const writes = []
  t.mock.method(globalThis, 'fetch', (path, { body, headers }) => {
    const response = Promise.withResolvers()
    writes.push({ path, body, key: headers.get('Idempotency-Key'), response })
    return response.promise
  })
  async function submit(attempt) {
    try {
      await staff.command('A', attempt.command, { csrf_token: 'sessão' }, attempt.key)
      inbox.settle('A', attempt)
    } catch (failure) {
      inbox.settle('A', attempt, { failure })
    }
  }

  const notices = []
  const closeA = inbox.subscribe('A', change => notices.push(change))
  const first = inbox.begin('A', 8, correction)
  const sending = submit(first)
  closeA() // Tela de configuração: nenhuma conversa montada.
  writes[0].response.resolve(Response.json({ error: { code: 'response_lost' } }, { status: 502 }))
  await sending
  assert.deepEqual(notices, ['changed'])
  assert.equal(inbox.get('A').status, 'uncertain')
  assert.equal(inbox.begin('A', 9, { ...correction, expected_version: 9 }), null)

  const retry = inbox.begin('A', 9)
  const confirming = submit(retry)
  const noticesB = []
  const closeB = inbox.subscribe('B', change => noticesB.push(change))
  assert.equal(inbox.get('B'), null)
  const commandB = inbox.begin('B', 7, transfer)
  closeB()
  const returned = []
  inbox.subscribe('A', change => returned.push(change))
  assert.equal(inbox.get('A').status, 'confirming')
  assert.equal(inbox.begin('A', 9), null)
  inbox.abandon('A')
  assert.equal(inbox.get('A'), retry)
  assert.equal(writes.length, 2)
  assert.deepEqual(writes.map(({ path, body, key }) => ({ path, body, key })), Array(2).fill({
    path: '/api/v1/cases/A/classification', body: writes[0].body, key: first.key,
  }))
  assert.deepEqual(JSON.parse(writes[1].body), {
    expected_version: 8, category: 'pix', priority: 'urgent', reason: 'Revisar impacto',
  })
  writes[1].response.resolve(Response.json({ id: 'A', version: 9 }))
  await confirming
  assert.deepEqual(returned, ['settled'])
  assert.deepEqual(noticesB, ['changed'])
  assert.equal(inbox.get('A'), null)
  assert.equal(inbox.get('B'), commandB)
})

test('uma sessão nova não herda comandos nem respostas tardias da conta anterior', () => {
  const former = new SessionCommandAttempts()
  const old = former.begin('A', 7, transfer)
  const current = new SessionCommandAttempts()
  assert.equal(current.get('A'), null)
  const fresh = current.begin('A', 8, correction)
  former.settle('A', old, { failure: new TypeError('conexão perdida') })
  assert.equal(current.get('A'), fresh)
  assert.notEqual(fresh.key, old.key)
  former.abandon('A')
  assert.equal(former.get('A'), null)
  assert.equal(current.get('A').command.type, 'classification')
})

test('perda de acesso durante a confirmação avisa a conversa remontada', () => {
  const inbox = new SessionCommandAttempts()
  const sent = inbox.begin('A', 7, transfer)
  inbox.settle('A', sent, { failure: new ApiError(502, 'response_lost', 'resposta perdida') })
  const retry = inbox.begin('A', 8)
  const events = []
  inbox.subscribe('A', change => events.push(change))
  inbox.settle('A', retry, { failure: new ApiError(404, 'not_found', 'caso indisponível') })
  assert.deepEqual(events, ['access_lost'])
  assert.equal(inbox.get('A').key, sent.key)
  assert.equal(inbox.get('A').status, 'uncertain')
  assert.equal(inbox.begin('A', 8, correction), null)
})
