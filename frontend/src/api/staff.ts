import type { Page, Message } from '../simulator/contract'
import type { CaseFilters, ListFilters, OperationUpdate, Session, StaffCase, StaffCommand } from './contract'
import { query, request } from './http.ts'
import { pageSize, readConversation } from './pagination.ts'

export function getSession() {
  return request<Session>('/session')
}

export const staff = {
  login: (email: string, password: string, csrf: string) =>
    request<Session>('/session', { method: 'POST', body: { email, password }, csrf }),
  logout: (csrf: string) => request<void>('/session', { method: 'DELETE', csrf }),
  updateOperation: (body: OperationUpdate, csrf: string) =>
    request<Session>('/session/operation', { method: 'PATCH', body, csrf }),
  filters: () => request<CaseFilters>('/case-filters'),
  listCases: (filters: ListFilters, cursor?: string) =>
    request<Page<StaffCase>>(query('/cases', { ...filters, cursor, limit: pageSize })),
  getConversation: (id: string) => readConversation<StaffCase>(`/cases/${encodeURIComponent(id)}`),
  command: (id: string, command: StaffCommand, csrf: string, key: string) => {
    const path = `/cases/${encodeURIComponent(id)}`
    if (command.type === 'reply') {
      const { expected_version, text } = command
      return request<{ case: StaffCase; message: Message }>(`${path}/messages`, {
        method: 'POST', body: { expected_version, text }, csrf, key,
      }).then(result => result.case)
    }
    return request<StaffCase>(`${path}/actions`, { method: 'POST', body: command, csrf, key })
  },
}
