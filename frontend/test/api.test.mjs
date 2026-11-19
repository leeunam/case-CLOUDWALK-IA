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
      return Response.json({ user: { role: 'simulator' }, csrf_token: 'rotated' }, { status: 201 })
    }
    if (route === '/api/v1/simulator/cases' && !simulatorReady) return Response.json({}, { status: 401 })
    if (route === '/api/v1/simulator/cases') return Response.json({ items: [], next_cursor: null })
    if (route === '/api/v1/channels') {
      return url.searchParams.get('cursor') === 'second page+'
        ? Response.json({ items: channels.slice(1), next_cursor: null })
        : Response.json({ items: [channels[0]], next_cursor: 'second page+' })
    }
    assert.match(route, /^\/api\/v1\/simulator\/channels\/.+\/messages$/)
    assert.equal(options.headers.get('X-CSRF-Token'), 'rotated')
    assert.equal(options.headers.get('Idempotency-Key'), 'unique-key')
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
  t.mock.method(globalThis, 'fetch', async path => {
    const url = new URL(path, 'https://help.test')
    if (url.pathname.endsWith('/session')) {
      assert.equal(url.pathname, '/api/v1/session')
      return Response.json(session)
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
  await staff.updateOperation({ switch_target_brand_id: 'horizonte' }, login.csrf_token)
  await staff.listCases({ brand_id: 'aurora', status: 'waiting_resumption', assignee: 'me' }, 'next+page')
  await staff.command('active', { type: 'reply', expected_version: 7, text: 'Olá' }, login.csrf_token, 'reply')
  await staff.command('active', { type: 'wait_for_customer', expected_version: 8, text: 'Envie o comprovante' }, login.csrf_token, 'wait')
  await assert.rejects(staff.command('active', { type: 'resolve', expected_version: 9 }, login.csrf_token, 'conflict'),
    { name: 'ApiError', status: 409, code: 'version_conflict' })
  await staff.logout(login.csrf_token)
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
