import { useEffect, useState } from 'react'

export function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Ocorreu uma falha. Tente novamente.'
}

type Resource<T> = { data: T | null; loading: boolean; error: string | null }

export function useResource<T>(load: () => Promise<T>, revision: number) {
  const [resource, setResource] = useState<Resource<T>>({ data: null, loading: true, error: null })

  useEffect(() => {
    let active = true
    setResource(previous => ({ ...previous, loading: true }))
    async function request() {
      try {
        const data = await load()
        if (active) setResource({ data, loading: false, error: null })
      } catch (error) {
        if (active) setResource(previous => ({ ...previous, loading: false, error: errorMessage(error) }))
      }
    }
    queueMicrotask(() => {
      if (active) void request()
    })
    return () => { active = false }
  }, [load, revision])

  return resource
}
