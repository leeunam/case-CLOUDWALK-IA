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
  let ready: Promise<void> | undefined

  async function prepare() {
    const session = await getSession()
    if (session.user?.role === 'simulator') return

    try {
      // Uma sessão operacional pode estar visível em /session e coexistir com a simulação.
      await request<Page<SimulatorCase>>(query(cases, { limit: 1 }))
    } catch (failure) {
      if (!(failure instanceof ApiError) || failure.status !== 401) throw failure
      const created = await withFreshCsrf(session.csrf_token,
        csrf => request<Session>('/simulator/session', { method: 'POST', csrf }),
        async () => (await getSession()).csrf_token)
      if (created.user?.role !== 'simulator' || !created.csrf_token) {
        throw new ApiError(0, 'invalid_session', 'A API não confirmou a sessão de simulação.')
      }
    }
  }

  async function withSession<T>(operation: () => Promise<T>) {
    ready ??= prepare().catch(failure => {
      ready = undefined
      throw failure
    })
    const prepared = ready
    await prepared
    try {
      return await operation()
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401 && ready === prepared) ready = undefined
      throw failure
    }
  }

  return {
    listChannels: cursor => withSession(() =>
      request<Page<Channel>>(query('/channels', { audience: 'simulator', cursor, limit: pageSize }))),
    listCases: cursor => withSession(() =>
      request<Page<SimulatorCase>>(query(cases, { cursor, limit: pageSize }))),
    getConversation: id => withSession(() => readConversation<SimulatorCase>(`${cases}/${encodeURIComponent(id)}`)),
    sendMessage: (channelId, message, key) => withSession(async () => {
      const session = await getSession()
      return request<SimulatorReceipt>(`/simulator/channels/${encodeURIComponent(channelId)}/messages`, {
        method: 'POST', body: message, csrf: session.csrf_token, key,
      })
    }),
  }
}
