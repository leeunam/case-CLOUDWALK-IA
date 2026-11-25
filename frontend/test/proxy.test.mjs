import assert from 'node:assert/strict'
import { once } from 'node:events'
import { createServer as createHttpServer } from 'node:http'
import { test } from 'node:test'
import { createServer as createViteServer } from 'vite'

test('proxy preserva a origem que o Rails valida em requisições do navegador', async t => {
  const backend = createHttpServer((req, res) => {
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ host: req.headers.host, origin: req.headers.origin }))
  })
  backend.listen(0, '127.0.0.1')
  t.after(() => new Promise(resolve => backend.close(resolve)))
  await once(backend, 'listening')

  const previousTarget = process.env.API_PROXY_TARGET
  process.env.API_PROXY_TARGET = `http://127.0.0.1:${backend.address().port}`
  t.after(() => {
    if (previousTarget === undefined) delete process.env.API_PROXY_TARGET
    else process.env.API_PROXY_TARGET = previousTarget
  })

  const vite = await createViteServer({ server: { host: '127.0.0.1', port: 0, ws: false } })
  t.after(() => vite.close())
  await vite.listen()

  const host = `127.0.0.1:${vite.httpServer.address().port}`
  const origin = `http://${host}`
  for (const path of ['/api/v1/session', '/webhooks/v1/probe', '/cable']) {
    const response = await fetch(`${origin}${path}`, { method: 'POST', headers: { Origin: origin } })
    assert.deepEqual(await response.json(), { host, origin })
  }
})
