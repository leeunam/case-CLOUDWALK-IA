import assert from 'node:assert/strict'
import { createSimulatorApi } from '/app/src/api/simulator.ts'
import { deliveryUncertain } from '/app/src/api/http.ts'
import { getSession, staff } from '/app/src/api/staff.ts'

const plan = JSON.parse(process.argv[2])
const nativeFetch = globalThis.fetch
const cookies = new Map()

// Node fornece a rede HTTP real. Esta adaptação conserva os cookies de uma aba
// isolada e resolve as URLs relativas usadas pelo cliente de produção.
globalThis.fetch = async (path, options) => {
  const headers = new Headers(options.headers)
  if (cookies.size) headers.set('Cookie', [...cookies.values()].join('; '))
  const response = await nativeFetch(new URL(path, 'http://fault:8080'), {
    ...options, headers, redirect: 'error', signal: AbortSignal.timeout(8000),
  })
  for (const value of response.headers.getSetCookie()) {
    const pair = value.split(';', 1)[0]
    const name = pair.slice(0, pair.indexOf('='))
    if (/;\s*max-age=0(?:;|$)/i.test(value) || pair.endsWith('=')) cookies.delete(name)
    else cookies.set(name, pair)
  }
  return response
}

async function attempt(callback) {
  try {
    return { receipt: await callback() }
  } catch (error) {
    return { status: error.status, code: error.code, uncertain: deliveryUncertain(error) }
  }
}

const api = createSimulatorApi()
const send = key => api.sendMessage(plan.channel, plan.message, key)
await api.listCases()
const identityA = (await getSession()).user
assert.equal(identityA.role, 'simulator')
const firstLost = await attempt(() => send(plan.same))
const repeated = await attempt(() => send(plan.same))
const secondLost = await attempt(() => send(plan.changed))
await staff.logout(await getSession())
// O cliente invalida seu cache ao receber a primeira recusa após logout.
const afterLogout = await attempt(() => api.listCases())
await api.listCases()
const identityB = (await getSession()).user
const switchedRetry = await attempt(() => send(plan.changed))
const newSend = await attempt(() => send(plan.fresh))

console.log(JSON.stringify({
  identityA: identityA.id, identityB: identityB.id, firstLost, repeated, secondLost,
  afterLogout, switchedRetry, newSend,
}))
