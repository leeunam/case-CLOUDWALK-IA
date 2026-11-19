import { useEffect, useState } from 'react'

export function useOpenCase() {
  const [caseId, setCaseId] = useState(() => new URLSearchParams(window.location.search).get('case'))

  useEffect(() => {
    const url = new URL(window.location.href)
    if (caseId) url.searchParams.set('case', caseId)
    else url.searchParams.delete('case')
    window.history.replaceState(null, '', url)
  }, [caseId])

  return [caseId, setCaseId] as const
}
