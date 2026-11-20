import type { Session } from './contract'
import { query, request } from './http.ts'
import { withStaffCsrf } from './staff.ts'
import type { CatalogCategory, Page, Priority } from '../simulator/contract'

export type BrandSettings = { id: string; name: string; default_queue_id: string; team_ids: string[]; version: number }
export type TeamSettings = { id: string; name: string; member_user_ids?: string[]; editable?: boolean; version: number }
export type QueueInput = { name: string; active: boolean; team_ids: string[] }
export type QueueSettings = QueueInput & { id: string; brand_id: string; version: number }
export type RuleInput = { active: boolean; position: number; queue_id: string; category: string | null; priority: Priority | null }
export type Rule = RuleInput & { id: string; brand_id: string; version: number }
export type { CatalogCategory } from '../simulator/contract'
export type Catalog = {
  brand_id: string
  version: number
  categories: CatalogCategory[]
  priorities: Array<{ key: Priority; name: string; description: string }>
}
export type AuditEvent = {
  id: string; brand_id: string; correlation_id: string; actor: { type: string; id: string | null }
  resource_type: string; resource_id: string; version: number; occurred_at: string
  before: object | null; after: object
}
export type Analyst = { user_id: string; attendant_id: string; name: string; brand_ids?: string[] }
export type ProfileInput = { portfolio_limit: number; alternatives: Array<Array<{ priority: Priority; category: string; limit: number }>> }
export type Profile = ProfileInput & { id: string; analyst_id: string; version: number }

const brandPath = (id: string) => `/brands/${encodeURIComponent(id)}`
const profilePath = (id: string) => `/analysts/${encodeURIComponent(id)}/capacity-profile`
const page = <T>(path: string, cursor?: string, filters: Record<string, string | undefined> = {}) =>
  request<Page<T>>(query(path, { ...filters, cursor, limit: 25 }))
const write = <T>(path: string, session: Session, body: object, method: 'POST' | 'PUT') =>
  withStaffCsrf(session, csrf => request<T>(path, { body, method, csrf }))

export const configuration = {
  brands: (cursor?: string) => page<BrandSettings>('/brands', cursor),
  teams: (cursor?: string) => page<TeamSettings>('/teams', cursor),
  queues: (brand: string, cursor?: string) => page<QueueSettings>(`${brandPath(brand)}/queues`, cursor),
  rules: (brand: string, cursor?: string) => page<Rule>(`${brandPath(brand)}/routing-rules`, cursor),
  audit: (brand: string, cursor?: string) => page<AuditEvent>(`${brandPath(brand)}/configuration-audit`, cursor),
  catalog: (brand: string) => request<Catalog>(`${brandPath(brand)}/catalog`),
  analysts: (brand: string, cursor?: string) => page<Analyst>('/analysts', cursor, { brand_id: brand }),
  queueAnalysts: (brand: string, queue: string, cursor?: string) =>
    page<Analyst>(`${brandPath(brand)}/queues/${encodeURIComponent(queue)}/analysts`, cursor),
  members: (cursor?: string) => page<Analyst>('/team-members', cursor),
  profile: (user: string) => request<Profile>(profilePath(user)),
  updateBrand: (session: Session, brand: BrandSettings, body: Pick<BrandSettings, 'name' | 'default_queue_id' | 'team_ids'>) =>
    write<BrandSettings>(brandPath(brand.id), session, { ...body, expected_version: brand.version }, 'PUT'),
  saveTeam: (session: Session, body: { name: string; member_user_ids: string[] }, id: string, team?: TeamSettings) =>
    team ? write<TeamSettings>(`/teams/${encodeURIComponent(team.id)}`, session, { ...body, expected_version: team.version }, 'PUT')
      : write<TeamSettings>('/teams', session, { ...body, brand_ids: [id] }, 'POST'),
  saveQueue: (session: Session, brand: string, body: QueueInput, queue?: QueueSettings) => {
    const path = `${brandPath(brand)}/queues`
    return queue ? write<QueueSettings>(`${path}/${queue.id}`, session, { ...body, expected_version: queue.version }, 'PUT')
      : write<QueueSettings>(path, session, body, 'POST')
  },
  saveRule: (session: Session, brand: string, body: RuleInput, rule?: Rule) => {
    const path = `${brandPath(brand)}/routing-rules`
    return rule ? write<Rule>(`${path}/${rule.id}`, session, { ...body, expected_version: rule.version }, 'PUT')
      : write<Rule>(path, session, body, 'POST')
  },
  saveCatalog: (session: Session, catalog: Catalog, categories: CatalogCategory[]) =>
    write<Catalog>(`${brandPath(catalog.brand_id)}/catalog`, session, { categories, expected_version: catalog.version }, 'PUT'),
  saveProfile: (session: Session, user: string, body: ProfileInput, profile?: Profile) =>
    profile ? write<Profile>(profilePath(user), session, { ...body, expected_version: profile.version }, 'PUT')
      : write<Profile>(profilePath(user), session, body, 'POST'),
}
