import type { Brand, CaseStatus, Message, Priority } from '../simulator/contract'

export type Session = {
  user: {
    id: string
    name: string
    role: 'analyst' | 'supervisor' | 'simulator'
    brand_ids: string[]
    attendant_id: string | null
  } | null
  operation: {
    active_brand_id: string | null
    switch_target_brand_id: string | null
    available: boolean
    active_count: number
    portfolio_count: number
    portfolio_limit: number
    profile_version: number
  } | null
  csrf_token: string
}
export type OperationUpdate = { available?: boolean; switch_target_brand_id?: string | null }

type ClassificationSource = 'channel' | 'jev' | 'setfit' | 'supervisor'

export type StaffCase = {
  id: string
  brand_id: string
  queue_id: string
  channel_id: string
  status: CaseStatus
  integration_status: 'idle' | 'pending_delivery' | 'awaiting_result' | 'failed'
  version: number
  classification: {
    category: string | null
    priority: Priority | null
    category_source: ClassificationSource | null
    priority_source: ClassificationSource | null
  }
  assignee: { type: 'human' | 'ai'; id: string } | null
  handoff: { summary: string; message_ids: string[] } | null
  previous_case_id: string | null
  human_queue_since: string | null
  blocking_reason: string | null
  created_at: string
  updated_at: string
}

export type CaseFilters = { brands: Brand[]; queues: Array<{ id: string; brand_id: string; name: string }> }
export type ListFilters = {
  brand_id?: string
  queue_id?: string
  status?: CaseStatus | ''
  integration_status?: StaffCase['integration_status'] | ''
  priority?: Priority | ''
  category?: string
  assignee?: 'me' | 'unassigned' | ''
}
export type StaffCommand =
  | { type: 'reply' | 'wait_for_customer'; expected_version: number; text: string }
  | { type: 'resolve'; expected_version: number }
  | { type: 'classification'; expected_version: number; category: string; priority: Priority; reason: string }
  | { type: 'transfer'; expected_version: number; destination_queue_id: string; destination_assignee_id: string | null; reason: string }
  | { type: 'retry_agent'; expected_version: number; reason: string }
  | { type: 'force_handoff'; expected_version: number; reason: string; summary: string }
export type CaseAuditEvent = {
  id: string; occurred_at: string; type: string; reason: string | null
  routing?: { queue_id: string; rule_id: string | null; rule_version: number | null }
}
export type MessageList = { items: Message[]; next_after_sequence: number | null }
