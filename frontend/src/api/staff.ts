import type { Page, Message } from '../simulator/contract'
import type { CaseAuditEvent, CaseFilters, ListFilters, OperationUpdate, Session, StaffCase, StaffCommand } from './contract'
import { ApiError, query, request, withFreshCsrf } from './http.ts'
import { pageSize, readConversation } from './pagination.ts'

export function getSession() {
  return request<Session>('/session')
}

export function withStaffCsrf<T>(session: Session, operation: (csrf: string) => Promise<T>) {
  return withFreshCsrf(session.csrf_token, operation, async () => {
    const current = await getSession()
    if (!current.user || current.user.id !== session.user?.id || current.user.role !== session.user.role) {
      throw new ApiError(401, 'session_changed', 'A sessão da operação mudou. Confira a conta antes de repetir a ação.')
    }
    return current.csrf_token
  })
}

export const staff = {
  login: (email: string, password: string, csrf: string) =>
    withFreshCsrf(csrf, token => request<Session>('/session', {
      method: 'POST', body: { email, password }, csrf: token,
    }), async () => (await getSession()).csrf_token),
  logout: (session: Session) =>
    withStaffCsrf(session, csrf => request<void>('/session', { method: 'DELETE', csrf })),
  updateOperation: (body: OperationUpdate, session: Session) =>
    withStaffCsrf(session, csrf => request<Session>('/session/operation', { method: 'PATCH', body, csrf })),
  filters: () => request<CaseFilters>('/case-filters'),
  listCases: (filters: ListFilters, cursor?: string) =>
    request<Page<StaffCase>>(query('/cases', { ...filters, cursor, limit: pageSize })),
  getConversation: (id: string) => readConversation<StaffCase>(`/cases/${encodeURIComponent(id)}`),
  audit: (id: string, cursor?: string) =>
    request<Page<CaseAuditEvent>>(query(`/cases/${encodeURIComponent(id)}/audit`, { cursor, limit: pageSize })),
  command: (id: string, command: StaffCommand, session: Session, key: string) => withStaffCsrf(session, csrf => {
    const path = `/cases/${encodeURIComponent(id)}`
    if (command.type === 'reply') {
      const { expected_version, text } = command
      return request<{ case: StaffCase; message: Message }>(`${path}/messages`, {
        method: 'POST', body: { expected_version, text }, csrf, key,
      }).then(result => result.case)
    }
    if (command.type === 'classification') {
      const { expected_version, reason, category, priority } = command
      return request<StaffCase>(`${path}/classification`, {
        method: 'POST', body: { expected_version, reason, category, priority }, csrf, key,
      })
    }
    return request<StaffCase>(`${path}/actions`, { method: 'POST', body: command, csrf, key })
  }),
}
