import { useEffect } from 'react'
import { subscribeToCase } from './api/cable'
import type { Audience } from './api/cable'

export function useCaseRefresh(caseId: string, audience: Audience | null, pollMs: number | null,
  loading: boolean, refresh: () => void) {
  useEffect(() => {
    if (!audience) return
    const url = new URL('/cable', window.location.href)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return subscribeToCase(url.toString(), caseId, audience, refresh)
  }, [caseId, audience, refresh])

  useEffect(() => {
    if (loading || pollMs === null) return
    const timer = window.setTimeout(refresh, pollMs)
    return () => window.clearTimeout(timer)
  }, [pollMs, loading, refresh])

  useEffect(() => {
    window.addEventListener('online', refresh)
    return () => window.removeEventListener('online', refresh)
  }, [refresh])
}
