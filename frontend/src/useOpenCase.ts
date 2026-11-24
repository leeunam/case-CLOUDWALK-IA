import { useEffect, useState } from 'react'

export function caseIdFromUrl() {
  return new URLSearchParams(window.location.search).get('case')
}

export function useCaseUrl(caseId: string | null) {
  useEffect(() => {
    const url = new URL(window.location.href)
    if (caseId) url.searchParams.set('case', caseId)
    else url.searchParams.delete('case')
    window.history.replaceState(null, '', url)
  }, [caseId])
}

export function useOpenCase() {
  const [caseId, setCaseId] = useState(caseIdFromUrl)
  useCaseUrl(caseId)
  return [caseId, setCaseId] as const
}
