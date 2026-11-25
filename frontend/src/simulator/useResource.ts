import { useCallback, useEffect, useRef, useState } from 'react'
import { accessLost } from '../api/http'

export function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Ocorreu uma falha. Tente novamente.'
}

type Resource<T> = { data: T | null; loading: boolean; error: string | null }

export function useResource<T>(load: () => Promise<T>, revision: number) {
  const [resource, setResource] = useState<Resource<T>>({ data: null, loading: true, error: null })
  const generation = useRef(0)

  useEffect(() => {
    const current = ++generation.current
    let active = true
    setResource(previous => ({ ...previous, loading: true }))
    async function request() {
      try {
        const data = await load()
        if (active && current === generation.current) setResource({ data, loading: false, error: null })
      } catch (error) {
        if (active && current === generation.current) setResource(previous => ({
          data: accessLost(error) ? null : previous.data, loading: false, error: errorMessage(error),
        }))
      }
    }
    queueMicrotask(() => {
      if (active) void request()
    })
    return () => { active = false }
  }, [load, revision])

  const replaceData = useCallback((data: T | null) => {
    generation.current += 1
    setResource({ data, loading: false, error: null })
  }, [])
  return { ...resource, replaceData }
}
