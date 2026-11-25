import type { Page } from '../simulator/contract'
import type { MessageList } from './contract'
import { ApiError, query, request } from './http.ts'

export const pageSize = 25

export async function readPages<T extends { id: string }>(
  read: (cursor?: string) => Promise<Page<T>>, count = Infinity,
): Promise<Page<T>> {
  const items = new Map<string, T>()
  const cursors = new Set<string>()
  let cursor: string | undefined
  for (let page = 0; page < count; page += 1) {
    const result = await read(cursor)
    for (const item of result.items) if (!items.has(item.id)) items.set(item.id, item)
    if (result.next_cursor === null) return { items: [...items.values()], next_cursor: null }
    if (!result.next_cursor || cursors.has(result.next_cursor)) {
      throw new ApiError(0, 'invalid_cursor', 'A API retornou uma paginação inválida.')
    }
    cursor = result.next_cursor
    cursors.add(cursor)
  }
  return { items: [...items.values()], next_cursor: cursor ?? null }
}

export async function readMessages(read: (after: number) => Promise<MessageList>) {
  const messages = new Map<number, MessageList['items'][number]>()
  let after = 0
  while (true) {
    const { items, next_after_sequence: next } = await read(after)
    for (const item of items) messages.set(item.sequence, item)
    if (next === null) return [...messages.values()].sort((a, b) => a.sequence - b.sequence)
    if (!Number.isSafeInteger(next) || next <= after) {
      throw new ApiError(0, 'invalid_sequence', 'A API retornou uma sequência de mensagens inválida.')
    }
    after = next
  }
}

export async function readConversation<T>(path: string) {
  const [detail, messages] = await Promise.all([
    request<T>(path),
    readMessages(after => request<MessageList>(query(`${path}/messages`, { after_sequence: after, limit: pageSize }))),
  ])
  return { detail, messages }
}
