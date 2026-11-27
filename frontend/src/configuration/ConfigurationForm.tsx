import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { errorMessage } from '../hooks/useResource'

export function ConfigurationForm({ children, submit, onSave, onSaved }: {
  children: ReactNode; submit: string
  onSave: (data: FormData) => Promise<unknown>; onSaved?: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    const form = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      await onSave(form)
      onSaved?.()
    } catch (failure) {
      setError(errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  return <form className="configuration-form" onSubmit={save}>
    <fieldset disabled={busy}>{children}</fieldset>
    {error && <p className="error" role="alert">{error}</p>}
    <button type="submit" className="primary" disabled={busy}>{busy ? 'Salvando…' : submit}</button>
  </form>
}

export function Checks({ legend, name, options, selected }: {
  legend: string; name: string; options: Array<{ id: string; name: string }>; selected: string[]
}) {
  return <fieldset className="configuration-checks">
    <legend>{legend}</legend>
    {options.map(option => <label key={option.id}>
      <input type="checkbox" name={name} value={option.id} defaultChecked={selected.includes(option.id)} />
      {option.name}
    </label>)}
    {!options.length && <p className="muted">Nenhuma opção disponível.</p>}
  </fieldset>
}
