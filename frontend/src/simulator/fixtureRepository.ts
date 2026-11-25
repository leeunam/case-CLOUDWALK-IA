import type {
  Channel, Message, SimulatorCase, SimulatorReceipt, SimulatorRepository,
} from './contract'
import fixtures from './fixtures.json' with { type: 'json' }

type PendingReply = { due: number; throughSequence: number; proposesResolution: boolean }
type CaseRecord = {
  detail: SimulatorCase
  correlationId: string
  messages: Message[]
  pendingReply: PendingReply | null
}
type FixtureState = {
  cases: CaseRecord[]
  sent: Record<string, { fingerprint: string; receipt: SimulatorReceipt }>
}
type LegacyCaseRecord = Omit<CaseRecord, 'pendingReply'> & {
  replies: Array<{ due: number; resolves: boolean }>
}
type StoredFixtureState = Omit<FixtureState, 'cases'> & {
  cases: Array<CaseRecord | LegacyCaseRecord>
}

const channels = fixtures.channels.items as Channel[]
const demoChannels: Channel[] = [
  ...channels,
  { ...channels[0], brand_id: fixtures.brands[1].id, brand_name: fixtures.brands[1].name, id: '00000000-0000-4000-8000-000000000914' },
  { ...channels[1], brand_id: fixtures.brands[0].id, brand_name: fixtures.brands[0].name, id: '00000000-0000-4000-8000-000000000915' },
  { ...channels[2], brand_id: fixtures.brands[0].id, brand_name: fixtures.brands[0].name, id: '00000000-0000-4000-8000-000000000916' },
]

function initialState(empty: boolean): FixtureState {
  return {
    cases: empty ? [] : [
      {
        detail: structuredClone(fixtures.recoveredCase) as SimulatorCase,
        correlationId: fixtures.recoveredReceipt.correlation_id,
        messages: structuredClone(fixtures.handoffMessages.items) as Message[],
        pendingReply: null,
      },
      {
        detail: {
          ...fixtures.resolvedCase,
          status: 'resolved',
          external_conversation_id: fixtures.resolvedConversationId,
        },
        correlationId: '00000000-0000-4000-8000-000000000200',
        messages: structuredClone(fixtures.resolvedMessages.items) as Message[],
        pendingReply: null,
      },
    ],
    sent: {},
  }
}

function restoreState(stored: string): FixtureState {
  const { cases, sent }: StoredFixtureState = JSON.parse(stored)
  return {
    sent,
    cases: cases.map(record => {
      if ('pendingReply' in record) return record

      const { replies, ...savedCase } = record
      const [reply] = replies
      // O formato anterior agendava a primeira e a segunda mensagem separadamente.
      const customers = savedCase.messages.filter(message => message.author.type === 'customer')
      const throughSequence = customers[reply?.resolves ? 1 : 0]?.sequence
      const pendingReply = savedCase.detail.status === 'ai_active' && reply && throughSequence !== undefined
        ? { due: reply.due, throughSequence, proposesResolution: reply.resolves }
        : null
      return { ...savedCase, pendingReply }
    }),
  }
}

function appendMessage(record: CaseRecord, type: 'customer' | 'ai', text: string, time: number) {
  const created_at = new Date(time).toISOString()
  record.messages.push({
    id: crypto.randomUUID(),
    sequence: (record.messages.at(-1)?.sequence ?? 0) + 1,
    author: { type, id: null },
    text,
    created_at,
  })
  record.detail.updated_at = created_at
}

function queueReply(record: CaseRecord, now: number, proposesResolution: boolean) {
  const channel = demoChannels.find(item => item.id === record.detail.channel_id)
  const delay = channel?.type === 'chat' ? 1000 : 3500
  record.pendingReply = {
    due: now + delay,
    throughSequence: record.messages.at(-1)?.sequence ?? 0,
    proposesResolution,
  }
}

function settleReplies(state: FixtureState, now: number) {
  for (const record of state.cases) {
    while (record.pendingReply && record.pendingReply.due <= now) {
      const { due, throughSequence, proposesResolution } = record.pendingReply
      const hasNewMessages = record.messages.some(message =>
        message.author.type === 'customer' && message.sequence > throughSequence,
      )
      const resolves = proposesResolution && !hasNewMessages
      const text = resolves
        ? 'Recebi o complemento. Vou encerrar este atendimento simulado.'
        : proposesResolution
          ? 'Recebi o complemento. Vou considerar as novas mensagens antes de encerrar.'
          : 'Recebi a sua mensagem. Pode contar um pouco mais sobre o que aconteceu?'
      const repliedAt = Math.max(due, Date.parse(record.detail.updated_at))
      appendMessage(record, 'ai', text, repliedAt)
      record.pendingReply = null
      if (resolves) record.detail.status = 'resolved'
      if (hasNewMessages) queueReply(record, repliedAt, true)
    }
  }
}

export function createFixtureRepository(scenario: string | null = null): SimulatorRepository {
  const empty = scenario === 'empty'
  const storageKey = empty ? 'cloudwalk.simulator.v1.empty' : 'cloudwalk.simulator.v1'
  let failFirstHistoryRead = scenario === 'error'

  async function access<T>(readOrWrite: (state: FixtureState, now: number) => T): Promise<T> {
    await new Promise(resolve => window.setTimeout(resolve, 320))
    if (!navigator.onLine) throw new Error('Conexão indisponível. Verifique a rede e tente novamente.')

    const stored = window.localStorage.getItem(storageKey)
    const state = stored ? restoreState(stored) : initialState(empty)
    const now = Date.now()
    settleReplies(state, now)
    const result = readOrWrite(state, now)
    const after = JSON.stringify(state)
    if (after !== stored) window.localStorage.setItem(storageKey, after)
    return result
  }

  function findCase(state: FixtureState, id: string) {
    const record = state.cases.find(item => item.detail.id === id)
    if (!record) throw new Error('Atendimento indisponível nesta simulação.')
    return record
  }

  return {
    listChannels: () => access(() => ({ items: demoChannels, next_cursor: null })),
    listCases: () => access(state => {
      if (failFirstHistoryRead) {
        failFirstHistoryRead = false
        throw new Error('O histórico está temporariamente indisponível.')
      }
      const items = state.cases.map(record => record.detail)
      items.sort((first, second) => Date.parse(second.updated_at) - Date.parse(first.updated_at))
      return { items, next_cursor: null }
    }),
    getConversation: id => access(state => {
      const { detail, messages } = findCase(state, id)
      return { detail, messages }
    }),
    sendMessage: (channelId, message, idempotencyKey) => access((state, now) => {
      if (!message.text.trim()) throw new Error(fixtures.invalidEnvelope.error.message)
      const channel = demoChannels.find(item => item.id === channelId)
      if (!channel) throw new Error('Canal indisponível nesta simulação.')

      const replayKey = JSON.stringify([channelId, idempotencyKey])
      const fingerprint = JSON.stringify([message.text, message.external_conversation_id, message.category, message.priority])
      const original = state.sent[replayKey]
      if (original) {
        if (original.fingerprint !== fingerprint) throw new Error('A chave de envio já identifica outra mensagem.')
        return original.receipt
      }

      let record = message.external_conversation_id
        ? state.cases.find(item => item.detail.channel_id === channelId &&
          item.detail.external_conversation_id === message.external_conversation_id)
        : undefined
      if (message.external_conversation_id && !record) {
        throw new Error('Conversa indisponível neste canal.')
      }

      if (!record || record.detail.status === 'resolved') {
        record = {
          detail: {
            id: crypto.randomUUID(),
            previous_case_id: record?.detail.id ?? null,
            channel_id: channelId,
            external_conversation_id: record?.detail.external_conversation_id ?? crypto.randomUUID(),
            status: message.category && message.priority ? 'ai_active' : 'classification_pending',
            updated_at: new Date(now).toISOString(),
          },
          correlationId: crypto.randomUUID(),
          messages: [],
          pendingReply: null,
        }
        state.cases.unshift(record)
      }

      appendMessage(record, 'customer', message.text, now)
      if (record.detail.status === 'ai_active' && !record.pendingReply) {
        const hasAiReply = record.messages.some(item => item.author.type === 'ai')
        queueReply(record, now, hasAiReply)
      }

      const receipt = {
        case_id: record.detail.id,
        correlation_id: record.correlationId,
        channel_id: record.detail.channel_id,
        external_conversation_id: record.detail.external_conversation_id,
      }
      state.sent[replayKey] = { fingerprint, receipt }
      return receipt
    }),
  }
}
