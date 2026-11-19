import type { Brand, Channel, Page, SimulatorCase, SimulatorReceipt, SimulatorRepository } from '../simulator/contract'
import type { Session } from './contract'
import { ApiError, query, request, withFreshCsrf } from './http.ts'
import { pageSize, readConversation } from './pagination.ts'
import { getSession } from './staff.ts'

const cases = '/simulator/cases'

export function brandsFromChannels(channels: Channel[]): Brand[] {
  const brands = new Map<string, string>()
  for (const { brand_id, brand_name } of channels) {
    if (typeof brand_name !== 'string' || !brand_name.trim()) {
      throw new ApiError(0, 'invalid_channel', 'A API não informou o nome da marca do canal.')
    }
    if (!brands.has(brand_id)) brands.set(brand_id, brand_name)
  }
  return [...brands].map(([id, name]) => ({ id, name }))
}

export function createSimulatorApi(): SimulatorRepository {
  let ready: Promise<string> | undefined
  // A renovação da sessão não muda a identidade dos envios já iniciados nesta aba.
  const sessionByAttempt = new Map<string, string>()

  async function prepare() {
    const session = await getSession()
    // O POST recupera a mesma identidade quando /session prioriza a sessão operacional.
    const simulator = session.user?.role === 'simulator' ? session : await withFreshCsrf(session.csrf_token,
      csrf => request<Session>('/simulator/session', { method: 'POST', csrf }),
      async () => (await getSession()).csrf_token)
    if (simulator.user?.role !== 'simulator' || !simulator.user.id || !simulator.csrf_token) {
      throw new ApiError(0, 'invalid_session', 'A API não confirmou a sessão de simulação.')
    }
    return simulator.user.id
  }

  async function withSession<T>(operation: (id: string) => Promise<T>) {
    ready ??= prepare().catch(failure => {
      ready = undefined
      throw failure
    })
    const prepared = ready
    const id = await prepared
    try {
      return await operation(id)
    } catch (failure) {
      if (ready === prepared && failure instanceof ApiError &&
        (failure.status === 401 || failure.code === 'simulator_session_changed')) ready = undefined
      throw failure
    }
  }

  return {
    listChannels: cursor => withSession(() =>
      request<Page<Channel>>(query('/channels', { audience: 'simulator', cursor, limit: pageSize }))),
    listCases: cursor => withSession(() =>
      request<Page<SimulatorCase>>(query(cases, { cursor, limit: pageSize }))),
    getConversation: id => withSession(() => readConversation<SimulatorCase>(`${cases}/${encodeURIComponent(id)}`)),
    sendMessage: (channelId, message, key) => withSession(async id => {
      const attempt = JSON.stringify([channelId, key])
      const simulatorSessionId = sessionByAttempt.get(attempt) ?? id
      sessionByAttempt.set(attempt, simulatorSessionId)
      const readCsrf = async () => (await getSession()).csrf_token
      return withFreshCsrf(await readCsrf(), csrf =>
        request<SimulatorReceipt>(`/simulator/channels/${encodeURIComponent(channelId)}/messages`, {
          method: 'POST', body: message, csrf, key, simulatorSessionId,
        }), readCsrf)
    }),
  }
}
