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
