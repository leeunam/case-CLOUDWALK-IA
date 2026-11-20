export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const errorLabels: Record<number, string> = {
  401: 'Sua sessão expirou ou ainda não foi iniciada.',
  403: 'Esta operação não está disponível para a sua sessão.',
  404: 'O recurso não está disponível nesta sessão.',
  409: 'A API encontrou um conflito ao processar a solicitação.',
  422: 'Os dados enviados foram recusados pela API.',
}

export function accessLost(error: unknown) {
  return error instanceof ApiError && [401, 403, 404].includes(error.status)
}

export function deliveryUncertain(error: unknown) {
  return !(error instanceof ApiError) || error.status === 0 ||
    error.status >= 500 || error.code === 'invalid_response'
}

export async function request<T>(path: string, options: {
  method?: 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: object
  csrf?: string
  key?: string
  simulatorSessionId?: string
} = {}): Promise<T> {
  const headers = new Headers({ Accept: 'application/json' })
  if (options.body) headers.set('Content-Type', 'application/json')
  if (options.csrf) headers.set('X-CSRF-Token', options.csrf)
  if (options.key) headers.set('Idempotency-Key', options.key)
  if (options.simulatorSessionId) headers.set('X-Simulator-Session-Id', options.simulatorSessionId)

  let response: Response
  try {
    response = await fetch(`/api/v1${path}`, {
      method: options.method ?? 'GET',
      credentials: 'same-origin',
      cache: 'no-store',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'network_error', 'Não foi possível conectar à API. Confira a conexão e tente novamente.')
  }
  if (response.status === 204) return undefined as T

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const error = payload?.error
    throw new ApiError(response.status, typeof error?.code === 'string' ? error.code : 'http_error',
      typeof error?.message === 'string' ? error.message : errorLabels[response.status] ?? `A API retornou HTTP ${response.status}.`)
  }
  if (payload === null || typeof payload !== 'object') {
    throw new ApiError(response.status, 'invalid_response', 'A API retornou uma resposta inválida.')
  }
  return payload as T
}

export function query(path: string, params: Record<string, string | number | null | undefined>) {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') search.set(key, String(value))
  }
  return search.size ? `${path}?${search}` : path
}

export async function withFreshCsrf<T>(
  csrf: string,
  operation: (csrf: string) => Promise<T>,
  refreshCsrf: () => Promise<string>,
) {
  try {
    return await operation(csrf)
  } catch (failure) {
    if (!(failure instanceof ApiError) || failure.status !== 403 || failure.code !== 'csrf_rejected') throw failure
    return operation(await refreshCsrf())
  }
}
