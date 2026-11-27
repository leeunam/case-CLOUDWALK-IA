import { useState, type FormEvent } from 'react'
import type { Session } from '../api/contract'
import { staff } from '../api/staff'
import { Icon } from '../components/Icon'
import { errorMessage } from '../hooks/useResource'

export function Login({ session, onSession }: { session: Session; onSession: (session: Session) => void }) {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setError(null)
    setBusy(true)
    try {
      onSession(await staff.login(String(form.get('email')).trim(), String(form.get('password')), session.csrf_token))
    } catch (failure) {
      setError(errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="signin" onSubmit={login} aria-labelledby="login-heading">
      <span className="login-symbol"><Icon name="key" /></span>
      <div><h1 id="login-heading">Entrar na operação</h1>
        <p className="muted">Acesse a caixa de atendimento com seu e-mail e senha.</p>
      </div>
      <label>E-mail <input name="email" type="email" autoComplete="username" required /></label>
      <label>Senha <input name="password" type="password" autoComplete="current-password" required /></label>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="primary" disabled={busy} type="submit">{busy ? 'Entrando…' : 'Entrar'}</button>
    </form>
  )
}
