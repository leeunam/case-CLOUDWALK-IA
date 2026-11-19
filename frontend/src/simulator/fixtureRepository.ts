import type {
  Channel, Message, SimulatorCase, SimulatorMessage, SimulatorReceipt, SimulatorRepository,
} from './contract'
import fixtures from './fixtures.json'

type PendingReply = { due: number; resolves: boolean }
type CaseRecord = {
  detail: SimulatorCase
  correlationId: string
  messages: Message[]
  replies: PendingReply[]
}
type FixtureState = {
  cases: CaseRecord[]
  sent: Record<string, { fingerprint: string; receipt: SimulatorReceipt }>
}

const channels = fixtures.channels.items as Channel[]
const demoChannels: Channel[] = [
  ...channels,
  { ...channels[0], brand_id: fixtures.brands[1].id, id: '00000000-0000-4000-8000-000000000914' },
  { ...channels[1], brand_id: fixtures.brands[0].id, id: '00000000-0000-4000-8000-000000000915' },
  { ...channels[2], brand_id: fixtures.brands[0].id, id: '00000000-0000-4000-8000-000000000916' },
]

function initialState(empty: boolean): FixtureState {
  return {
    cases: empty ? [] : [
      {
        detail: structuredClone(fixtures.recoveredCase) as SimulatorCase,
        correlationId: fixtures.recoveredReceipt.correlation_id,
        messages: structuredClone(fixtures.handoffMessages.items) as Message[],
        replies: [],
      },
      {
        detail: {
          ...fixtures.resolvedCase,
          status: 'resolved',
          external_conversation_id: fixtures.resolvedConversationId,
        },
        correlationId: '00000000-0000-4000-8000-000000000200',
        messages: structuredClone(fixtures.resolvedMessages.items) as Message[],
        replies: [],
      },
    ],
    sent: {},
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

function settleReplies(state: FixtureState, now: number) {
  for (const record of state.cases) {
    for (const reply of record.replies) {
      if (reply.due > now) break
      const text = reply.resolves
        ? 'Recebi o complemento. Vou encerrar este atendimento simulado.'
        : 'Recebi a sua mensagem. Pode contar um pouco mais sobre o que aconteceu?'
      appendMessage(record, 'ai', text, Math.max(reply.due, Date.parse(record.detail.updated_at)))
      if (reply.resolves) record.detail.status = 'resolved'
    }
    record.replies = record.replies.filter(reply => reply.due > now)
  }
}

export function createFixtureRepository(scenario: string | null = null): SimulatorRepository {
  const empty = scenario === 'empty'
  const storageKey = empty ? 'cloudwalk.simulator.v1.empty' : 'cloudwalk.simulator.v1'
  let failFirstHistoryRead = scenario === 'error'

  async function access<T>(readOrWrite: (state: FixtureState) => T): Promise<T> {
    await new Promise(resolve => window.setTimeout(resolve, 320))
    if (!navigator.onLine) throw new Error('Conexão indisponível. Verifique a rede e tente novamente.')

    const stored = window.localStorage.getItem(storageKey)
    const state: FixtureState = stored ? JSON.parse(stored) : initialState(empty)
    const before = JSON.stringify(state)
    settleReplies(state, Date.now())
    const result = readOrWrite(state)
    const after = JSON.stringify(state)
    if (stored === null || after !== before) window.localStorage.setItem(storageKey, after)
    return result
  }

  function findCase(state: FixtureState, id: string) {
    const record = state.cases.find(item => item.detail.id === id)
    if (!record) throw new Error('Atendimento indisponível nesta simulação.')
    return record
  }

  return {
    listBrands: () => access(() => fixtures.brands),
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
    getCase: id => access(state => findCase(state, id).detail),
    listMessages: id => access(state => ({ items: findCase(state, id).messages, next_after_sequence: null })),
    sendMessage: (channelId, message, idempotencyKey) => access(state => {
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

      const now = Date.now()
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
          replies: [],
        }
        state.cases.unshift(record)
      }

      appendMessage(record, 'customer', message.text, now)
      const customers = record.messages.filter(item => item.author.type === 'customer').length
      if (record.detail.status === 'ai_active' && customers <= 2) {
        const delay = channel.type === 'chat' ? 1000 : 3500
        const due = Math.max(now + delay, (record.replies.at(-1)?.due ?? 0) + 1)
        record.replies.push({ due, resolves: customers === 2 })
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
