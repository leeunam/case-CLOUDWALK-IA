import { useEffect, useState } from 'react'

export function App() {
  const [status, setStatus] = useState('Conferindo conexão com a API…')

  useEffect(() => {
    const controller = new AbortController()

    async function checkApi() {
      try {
        const response = await fetch('/api/v1/health', { signal: controller.signal })
        if (!response.ok) throw new Error('API indisponível')

        const health = await response.json()
        if (health.status !== 'ok' || health.database !== 'ok') {
          throw new Error('Banco indisponível')
        }
        setStatus('API e banco conectados. Ambiente pronto para desenvolver.')
      } catch {
        if (!controller.signal.aborted) {
          setStatus('Falha na conexão. Confira os serviços com docker compose ps e recarregue a página.')
        }
      }
    }

    void checkApi()
    return () => controller.abort()
  }, [])

  return (
    <main>
      <h1>Help desk</h1>
      <p role="status">{status}</p>
      <a href="/api/v1/health">Consultar a saúde da API</a>
    </main>
  )
}
