import assert from 'node:assert/strict'
import test from 'node:test'
import { ApiError } from '../src/api/http.ts'
import { readMessages, readPages } from '../src/api/pagination.ts'
import { canHandle } from '../src/api/permissions.ts'
import { brandsFromChannels, createSimulatorApi } from '../src/api/simulator.ts'
import { staff } from '../src/api/staff.ts'

const session = {
  user: { id: 'account', attendant_id: 'attendant', role: 'analyst', brand_ids: ['aurora'] },
  csrf_token: 'initial',
  operation: { active_brand_id: 'aurora', available: false, switch_target_brand_id: 'horizonte' },
}
const channels = [
  { id: 'channel-1', brand_id: 'aurora', brand_name: 'Nome vindo da API', type: 'chat' },
  { id: 'channel-2', brand_id: 'horizonte', brand_name: 'Outra marca autorizada', type: 'email' },
  { id: 'channel-3', brand_id: 'aurora', brand_name: 'Nome vindo da API', type: 'whatsapp' },
]
const message = sequence => ({ sequence, id: `message-${sequence}` })
const identityA = '00000000-0000-4000-8000-000000000001'
const identityB = '00000000-0000-4000-8000-000000000002'
const identityC = '00000000-0000-4000-8000-000000000003'
const simulatorSession = (id = identityA, csrf = 'rotated') =>
  Response.json({ user: { id, role: 'simulator' }, csrf_token: csrf }, { status: 201 })

test('simulador prepara uma sessão compartilhada entre leituras e usa CSRF rotacionado nos três canais', async t => {
  let simulatorReady = false
  let created = 0
  const sends = []
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(options.credentials, 'same-origin')
    const url = new URL(path, 'https://help.test')
    const route = url.pathname
    if (route === '/api/v1/session') {
      return Response.json({ ...session, csrf_token: simulatorReady ? 'rotated' : 'initial' })
    }
    if (route === '/api/v1/simulator/session') {
      assert.equal(options.method, 'POST')
      assert.equal(options.headers.get('X-CSRF-Token'), 'initial')
      assert.equal(options.body, undefined)
      created += 1
      simulatorReady = true
      return simulatorSession()
    }
    if (route === '/api/v1/simulator/cases' && !simulatorReady) return Response.json({}, { status: 401 })
    if (route === '/api/v1/simulator/cases') return Response.json({ items: [], next_cursor: null })
    if (route === '/api/v1/channels') {
      assert.equal(url.searchParams.get('audience'), 'simulator')
      return url.searchParams.get('cursor') === 'second page+'
        ? Response.json({ items: channels.slice(1), next_cursor: null })
        : Response.json({ items: [channels[0]], next_cursor: 'second page+' })
    }
    assert.match(route, /^\/api\/v1\/simulator\/channels\/.+\/messages$/)
    assert.equal(options.headers.get('X-CSRF-Token'), 'rotated')
    assert.equal(options.headers.get('Idempotency-Key'), 'unique-key')
    assert.equal(options.headers.get('X-Simulator-Session-Id'), identityA)
    sends.push([route.split('/')[5], JSON.parse(options.body)])
    return Response.json({ case_id: 'case', external_conversation_id: 'from-the-server' }, { status: 202 })
  })
  const api = createSimulatorApi()
  const [catalog] = await Promise.all([readPages(api.listChannels), api.listCases()])
  assert.equal(created, 1)
  assert.deepEqual(brandsFromChannels(catalog.items), [
    { id: 'aurora', name: 'Nome vindo da API' }, { id: 'horizonte', name: 'Outra marca autorizada' },
  ])
  for (const channel of channels) {
    const receipt = await api.sendMessage(channel.id, { text: channel.type }, 'unique-key')
    await api.sendMessage(channel.id, { text: 'Retorno', external_conversation_id: receipt.external_conversation_id }, 'unique-key')
  }
  assert.deepEqual(sends, channels.flatMap(channel => [
    [channel.id, { text: channel.type }], [channel.id, { text: 'Retorno', external_conversation_id: 'from-the-server' }],
  ]))
})

test('simulador reaproveita a sessão coexistente com login e carrega as páginas da conversa', async t => {
  const sequences = []
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    const url = new URL(path, 'https://help.test')
    if (url.pathname === '/api/v1/session') return Response.json(session)
    if (url.pathname === '/api/v1/simulator/session') {
      assert.equal(options.method, 'POST')
      return simulatorSession()
    }
    if (url.pathname === '/api/v1/simulator/cases') return Response.json({ items: [], next_cursor: null })
    if (url.pathname.endsWith('/case')) {
      return Response.json({ channel_id: 'channel-2', external_conversation_id: 'persistent', status: 'waiting_customer' })
    }
    assert.equal(url.pathname, '/api/v1/simulator/cases/case/messages')
    const after = url.searchParams.get('after_sequence')
    sequences.push(after)
    return after === '0'
      ? Response.json({ items: [message(1), message(2)], next_after_sequence: 2 })
      : Response.json({ items: [message(3)], next_after_sequence: null })
  })
  const { detail, messages } = await createSimulatorApi().getConversation('case')
  assert.equal(detail.external_conversation_id, 'persistent')
  assert.deepEqual(sequences, ['0', '2'])
  assert.deepEqual(messages.map(item => item.sequence), [1, 2, 3])
})

test('catálogo exige identidade sintética mesmo após a sessão expirar com o analista conectado', async t => {
  let simulatorReady = true
  let created = 0
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    const url = new URL(path, 'https://help.test')
    if (url.pathname === '/api/v1/session') return Response.json(session)
    if (url.pathname === '/api/v1/simulator/session') {
      if (!simulatorReady) created += 1
      simulatorReady = true
      assert.equal(options.method, 'POST')
      return simulatorSession()
    }
    const unauthenticated = () => Response.json({ error: { code: 'unauthenticated' } }, { status: 401 })
    if (url.pathname === '/api/v1/simulator/cases') {
      return simulatorReady ? Response.json({ items: [], next_cursor: null }) : unauthenticated()
    }
    assert.equal(url.pathname, '/api/v1/channels')
    if (url.searchParams.get('audience') !== 'simulator') {
      return Response.json({ items: [{ ...channels[0], brand_id: 'staff', brand_name: 'Somente operação' }], next_cursor: null })
    }
    return simulatorReady ? Response.json({ items: channels, next_cursor: null }) : unauthenticated()
  })

  const api = createSimulatorApi()
  assert.deepEqual((await api.listChannels()).items, channels)
  assert.equal(created, 0)
  simulatorReady = false
  await assert.rejects(api.listChannels(), { status: 401, code: 'unauthenticated' })
  const [catalog] = await Promise.all([api.listChannels(), api.listCases()])
  assert.deepEqual(catalog.items, channels)
  assert.equal(created, 1)
})

test('abertura incerta repete o recibo original e nunca vira novo pedido em outra identidade', async t => {
  const receipts = new Map()
  const writes = []
  let currentId = identityA
  let switchAtWrite
  let loseReceipt = true
  const csrf = () => `csrf-${currentId}`
  const error = (status, code) => Response.json({ error: { code } }, { status })
  t.mock.method(globalThis, 'fetch', async (path, { headers, body }) => {
    const route = new URL(path, 'https://help.test').pathname
    if (route === '/api/v1/session') return Response.json({ ...session, csrf_token: csrf() })
    if (route === '/api/v1/simulator/session') return simulatorSession(currentId, csrf())
    if (route === '/api/v1/simulator/cases') {
      return currentId ? Response.json({ items: [], next_cursor: null }) : error(401, 'unauthenticated')
    }
    assert.match(route, /^\/api\/v1\/simulator\/channels\/.+\/messages$/)
    if (switchAtWrite) {
      currentId = switchAtWrite
      switchAtWrite = undefined
    }
    const expected = headers.get('X-Simulator-Session-Id')
    const key = headers.get('Idempotency-Key')
    writes.push({ currentId, expected, key, body, csrf: headers.get('X-CSRF-Token') })
    if (headers.get('X-CSRF-Token') !== csrf()) return error(403, 'csrf_rejected')
    if (expected !== currentId) return error(409, 'simulator_session_changed')
    const namespace = `${currentId}/${key}`
    if (!receipts.has(namespace)) receipts.set(namespace, { case_id: namespace })
    if (loseReceipt) {
      loseReceipt = false
      return error(502, 'bad_gateway')
    }
    return Response.json(receipts.get(namespace), { status: 202 })
  })

  const api = createSimulatorApi()
  const send = key => api.sendMessage('channel-1', { text: 'Abertura' }, key)
  await assert.rejects(send('repeat-in-a'), { status: 502 })
  assert.equal((await send('repeat-in-a')).case_id, `${identityA}/repeat-in-a`)
  assert.deepEqual(writes[1], writes[0])
  assert.equal(receipts.size, 1)

  loseReceipt = true
  await assert.rejects(send('lost-in-a'), { status: 502 })
  currentId = null
  await assert.rejects(api.listCases(), { status: 401 })
  currentId = identityB
  await assert.rejects(send('lost-in-a'), { status: 409, code: 'simulator_session_changed' })
  assert.deepEqual(writes[3], { ...writes[2], currentId: identityB, csrf: csrf() })
  assert.equal(receipts.size, 2)
  assert.equal((await send('new-in-b')).case_id, `${identityB}/new-in-b`)

  switchAtWrite = identityC
  await assert.rejects(send('race-b-c'), { status: 409, code: 'simulator_session_changed' })
  const [beforeRefresh, afterRefresh] = writes.slice(-2)
  assert.equal(beforeRefresh.expected, identityB)
  assert.equal(beforeRefresh.currentId, identityC)
  assert.deepEqual(afterRefresh, { ...beforeRefresh, csrf: csrf() })
  assert.equal(receipts.size, 3)
})

test('falha HTTP, rede e catálogo fora do contrato são exibíveis e nunca acionam fixtures', async t => {
  const mocked = t.mock.method(globalThis, 'fetch', async () => Response.json({
    error: { code: 'unavailable', message: 'API indisponível.' },
  }, { status: 503 }))
  const api = createSimulatorApi()
  await assert.rejects(api.listCases(), { name: 'ApiError', status: 503, message: 'API indisponível.' })
  assert.equal(mocked.mock.callCount(), 1)
  mocked.mock.mockImplementation(() => Promise.reject(new TypeError('failed to fetch')))
  await assert.rejects(api.listCases(), { name: 'ApiError', status: 0, code: 'network_error' })
  assert.throws(() => brandsFromChannels([{ ...channels[0], brand_name: '' }]), { code: 'invalid_channel' })
})

test('cliente operacional envia sessão, filtro, ações versionadas e chaves corretas', async t => {
  const requests = []
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    requests.push({ path, ...options })
    if (options.method === 'DELETE') return new Response(null, { status: 204 })
    if (options.headers.get('Idempotency-Key') === 'conflict') {
      return Response.json({ error: { code: 'version_conflict', message: 'Retorne à versão atual.' } }, { status: 409 })
    }
    return Response.json({ ...session, case: { id: 'active' } })
  })
  const login = await staff.login('analyst@test', 'password', 'anonymous-token')
  await staff.updateOperation({ switch_target_brand_id: 'horizonte' }, login)
  await staff.listCases({ brand_id: 'aurora', status: 'waiting_resumption', assignee: 'me' }, 'next+page')
  await staff.command('active', { type: 'reply', expected_version: 7, text: 'Olá' }, login, 'reply')
  await staff.command('active', { type: 'wait_for_customer', expected_version: 8, text: 'Envie o comprovante' }, login, 'wait')
  await assert.rejects(staff.command('active', { type: 'resolve', expected_version: 9 }, login, 'conflict'),
    { name: 'ApiError', status: 409, code: 'version_conflict' })
  await staff.logout(login)
  assert.deepEqual(requests.map(req => [req.method, req.path, req.headers.get('X-CSRF-Token'), req.headers.get('Idempotency-Key')]), [
    ['POST', '/api/v1/session', 'anonymous-token', null],
    ['PATCH', '/api/v1/session/operation', 'initial', null],
    ['GET', '/api/v1/cases?brand_id=aurora&status=waiting_resumption&assignee=me&cursor=next%2Bpage&limit=25', null, null],
    ['POST', '/api/v1/cases/active/messages', 'initial', 'reply'],
    ['POST', '/api/v1/cases/active/actions', 'initial', 'wait'],
    ['POST', '/api/v1/cases/active/actions', 'initial', 'conflict'],
    ['DELETE', '/api/v1/session', 'initial', null],
  ])
  assert.deepEqual(JSON.parse(requests[3].body), { expected_version: 7, text: 'Olá' })
  assert.deepEqual(JSON.parse(requests[4].body), { type: 'wait_for_customer', expected_version: 8, text: 'Envie o comprovante' })
  assert.deepEqual(JSON.parse(requests[5].body), { type: 'resolve', expected_version: 9 })
})

test('login e escritas operacionais renovam CSRF rejeitado preservando corpo e chave', async t => {
  const requests = []
  t.mock.method(globalThis, 'fetch', async (path, { method, headers, body }) => {
    requests.push({ path, method, body, csrf: headers.get('X-CSRF-Token'), key: headers.get('Idempotency-Key') })
    if (method === 'GET') return Response.json({ ...session, csrf_token: 'rotated' })
    if (headers.get('X-CSRF-Token') === 'initial') {
      return Response.json({ error: { code: 'csrf_rejected' } }, { status: 403 })
    }
    assert.equal(headers.get('X-CSRF-Token'), 'rotated')
    if (method === 'DELETE') return new Response(null, { status: 204 })
    return Response.json({ ...session, case: { version: 8 } })
  })

  const actions = [
    () => staff.login('analyst@test', 'demo-password', 'initial'),
    () => staff.updateOperation({ available: false }, session),
    () => staff.command('active', { type: 'reply', expected_version: 7, text: 'Olá' }, session, 'reply-attempt'),
    () => staff.command('active', { type: 'wait_for_customer', expected_version: 7, text: 'Olá' }, session, 'wait-attempt'),
    () => staff.logout(session),
  ]
  for (const action of actions) {
    requests.length = 0
    await action()
    assert.equal(requests.length, 3)
    const [first, refresh, retry] = requests
    assert.deepEqual(refresh, { path: '/api/v1/session', method: 'GET', body: undefined, csrf: null, key: null })
    assert.deepEqual(retry, { ...first, csrf: 'rotated' })
  }
})

test('CSRF renovado não repete ações sob outra conta e a repetição é limitada a uma tentativa', async t => {
  let current = { ...session, user: { ...session.user, id: 'other-account' }, csrf_token: 'rotated' }
  let code = 'csrf_rejected'
  const mocked = t.mock.method(globalThis, 'fetch', async (_path, options) => {
    if (options.method === 'GET') return Response.json(current)
    return Response.json({ error: { code } }, { status: 403 })
  })
  const command = () => staff.command('active', { type: 'resolve', expected_version: 9 }, session, 'resolve-attempt')
  await assert.rejects(command(), { code: 'session_changed' })
  assert.equal(mocked.mock.callCount(), 2)

  mocked.mock.resetCalls()
  current = { ...session, csrf_token: 'rotated' }
  await assert.rejects(command(), { code: 'csrf_rejected' })
  assert.equal(mocked.mock.callCount(), 3)

  mocked.mock.resetCalls()
  code = 'forbidden'
  await assert.rejects(command(), { code: 'forbidden' })
  assert.equal(mocked.mock.callCount(), 1)
})

test('ações exigem identidade do atendente, marca em operação e caso humano ativo', () => {
  const detail = { status: 'human_active', brand_id: 'aurora', assignee: { type: 'human', id: 'attendant' } }
  assert.equal(canHandle(session, detail), true)
  assert.equal(canHandle(session, { ...detail, brand_id: 'horizonte' }), false)
  assert.equal(canHandle(session, { ...detail, assignee: { type: 'human', id: 'account' } }), false)
  assert.equal(canHandle(session, { ...detail, status: 'waiting_resumption' }), false)
  assert.equal(canHandle({ ...session, user: { ...session.user, role: 'supervisor' } }, detail), false)
})

test('paginação deduplica páginas sobrepostas e detecta cursores que não avançam', async () => {
  const result = await readPages(async cursor => cursor
    ? { items: [{ id: 'one' }, { id: 'two' }], next_cursor: null }
    : { items: [{ id: 'one' }], next_cursor: 'next' })
  assert.deepEqual(result.items.map(item => item.id), ['one', 'two'])
  await assert.rejects(readPages(async () => ({ items: [], next_cursor: 'same' })), ApiError)
  await assert.rejects(readMessages(async () => ({ items: [], next_after_sequence: 0 })), ApiError)
})
