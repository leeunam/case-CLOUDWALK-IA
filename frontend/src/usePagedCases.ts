import { useCallback, useState } from 'react'
import { readPages } from './api/pagination'
import type { Page } from './simulator/contract'
import { useResource } from './simulator/useResource'

export function usePagedCases<T extends { id: string }>(read: (cursor?: string) => Promise<Page<T>>, revision: number) {
  const [pages, setPages] = useState(1)
  const load = useCallback(() => readPages(read, pages), [read, pages])
  const resource = useResource(load, revision)
  return {
    ...resource,
    loadMore: () => setPages(previous => previous + 1),
  }
}
