import assert from 'node:assert/strict'
import test from 'node:test'
import { subscribeToCase } from '../src/api/cable.ts'

function fakeCable(t, audience = 'staff') {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  const connections = []
  let refreshes = 0
  const stop = subscribeToCase('wss://desk.test/cable', 'case-uuid', audience, () => refreshes += 1, (url, protocol) => {
    assert.equal(url, 'wss://desk.test/cable')
    assert.equal(protocol, 'actioncable-v1-json')
    const socket = {
      frames: [],
      close() { this.onclose?.() },
      send(frame) { this.frames.push(JSON.parse(frame)) },
      receive(frame) { this.onmessage?.({ data: JSON.stringify(frame) }) },
    }
    connections.push(socket)
    return socket
  })
  t.after(stop)
  const identifier = JSON.stringify({ channel: 'CaseUpdatesChannel', case_id: 'case-uuid', audience })
  return { connections, identifier, stop, refreshes: () => refreshes }
}

test('Action Cable assina apenas o caso aberto, reconsulta na confirmação e recebe aviso isolado', t => {
  const { connections: [socket], identifier, refreshes } = fakeCable(t, 'simulator')
  socket.receive({ type: 'welcome' })
  assert.deepEqual(socket.frames, [{ command: 'subscribe', identifier }])
  const message = { type: 'case.updated', case_id: 'case-uuid' }
  socket.receive({ identifier, message })
  assert.equal(refreshes(), 0)
  socket.receive({ type: 'confirm_subscription', identifier })
  socket.receive({ identifier: 'other subscription', message })
  socket.receive({ identifier, message: { ...message, case_id: 'another case' } })
  socket.receive({ identifier, message })
  assert.equal(refreshes(), 2)
})

test('Action Cable reconecta após perda e reconsulta na nova confirmação', t => {
  const { connections, identifier, refreshes } = fakeCable(t)
  connections[0].receive({ type: 'confirm_subscription', identifier })
  connections[0].close()
  t.mock.timers.tick(500)
  assert.equal(connections.length, 2)
  connections[1].receive({ type: 'welcome' })
  assert.equal(connections[1].frames[0].identifier, identifier)
  connections[1].receive({ type: 'confirm_subscription', identifier })
  assert.equal(refreshes(), 2)
})

test('Action Cable para ao recusar a assinatura e ignora quadros posteriores', t => {
  const { connections, identifier, refreshes } = fakeCable(t)
  connections[0].receive({ type: 'reject_subscription', identifier })
  connections[0].receive({ type: 'confirm_subscription', identifier })
  t.mock.timers.tick(10000)
  assert.equal(connections.length, 1)
  assert.equal(refreshes(), 1)
})
