import { accessLost, deliveryUncertain } from '../api/http.ts'
import type { StaffCommand } from '../api/contract'

export type CommandAttempt = {
  status: 'sending' | 'uncertain' | 'confirming'
  command: Readonly<StaffCommand>
  key: string
}

export function beginCommandAttempt(previous: CommandAttempt | null, version: number | undefined,
  command?: StaffCommand): CommandAttempt | null {
  if (command) {
    if (previous || command.expected_version !== version) return null

    return { status: 'sending', command: { ...command }, key: crypto.randomUUID() }
  }

  return previous?.status === 'uncertain' ? { ...previous, status: 'confirming' } : null
}

type AttemptChange = 'changed' | 'settled' | 'access_lost'

// A caixa mantém as tentativas da sessão, inclusive quando a conversa sai da tela.
export class SessionCommandAttempts {
  private active = new Map<string, CommandAttempt>()
  private listeners = new Set<(id: string, change: AttemptChange) => void>()

  subscribe(caseId: string, listener: (change: AttemptChange) => void) {
    const onChange = (id: string, change: AttemptChange) => {
      if (id === caseId) listener(change)
    }
    this.listeners.add(onChange)
    return () => { this.listeners.delete(onChange) }
  }

  get(caseId: string) {
    return this.active.get(caseId) ?? null
  }

  begin(caseId: string, version: number | undefined, command?: StaffCommand) {
    const attempt = beginCommandAttempt(this.get(caseId), version, command)
    if (attempt) this.update(caseId, attempt)
    return attempt
  }

  settle(caseId: string, attempt: CommandAttempt, result?: { failure: unknown }) {
    if (this.get(caseId) !== attempt) return
    const denied = result && accessLost(result.failure)
    const uncertain = result && (deliveryUncertain(result.failure) || (attempt.status === 'confirming' && denied))
    this.update(caseId, uncertain ? { ...attempt, status: 'uncertain' } : null, denied ? 'access_lost' : 'settled')
  }

  abandon(caseId: string) {
    if (this.get(caseId)?.status === 'uncertain') this.update(caseId, null)
  }

  private update(caseId: string, attempt: CommandAttempt | null, change: AttemptChange = 'changed') {
    if (attempt) this.active.set(caseId, attempt)
    else this.active.delete(caseId)
    this.listeners.forEach(listener => listener(caseId, change))
  }
}
