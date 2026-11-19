export type ChannelType = 'chat' | 'whatsapp' | 'email'

export type Brand = { id: string; name: string }
export type Channel = { id: string; brand_id: string; brand_name: string; name: string; type: ChannelType }
export type Page<T> = { items: T[]; next_cursor: string | null }

export type CaseStatus =
  | 'classification_pending'
  | 'classification_review'
  | 'ai_active'
  | 'waiting_human'
  | 'human_active'
  | 'waiting_customer'
  | 'waiting_resumption'
  | 'resolved'

export type SimulatorCase = {
  id: string
  previous_case_id: string | null
  channel_id: string
  external_conversation_id: string
  status: CaseStatus
  updated_at: string
}

export type Category = 'pix' | 'payouts' | 'terminal'
export type Priority = 'basic' | 'intermediate' | 'advanced' | 'urgent'
export type SimulatorMessage = {
  text: string
  external_conversation_id?: string
  category?: Category
  priority?: Priority
}

export type SimulatorReceipt = {
  case_id: string
  correlation_id: string
  channel_id: string
  external_conversation_id: string
}

export type ActorType = 'system' | 'customer' | 'ai' | 'human' | 'supervisor'
export type Message = {
  id: string
  sequence: number
  author: { type: ActorType; id: string | null }
  text: string
  created_at: string
}
export type ConversationSnapshot = { detail: SimulatorCase; messages: Message[] }

export interface SimulatorRepository {
  listChannels(cursor?: string): Promise<Page<Channel>>
  listCases(cursor?: string): Promise<Page<SimulatorCase>>
  getConversation(id: string): Promise<ConversationSnapshot>
  sendMessage(channelId: string, message: SimulatorMessage, idempotencyKey: string): Promise<SimulatorReceipt>
}
