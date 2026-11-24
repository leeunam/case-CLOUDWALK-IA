import type { Session } from '../api/contract'
import { Icon, type IconName } from '../Icon'
import { Identity } from '../Topbar'
import { viewLabels, type StaffView } from './navigation'

type Destination = { id: StaffView; icon: IconName }
const inbox: Destination = { id: 'inbox', icon: 'inbox' }
const mine: Destination = { id: 'mine', icon: 'chat' }
const supervision: Destination[] = [
  { id: 'review', icon: 'review' },
  { id: 'failed', icon: 'alert' },
  { id: 'configuration', icon: 'settings' },
]

export function StaffNavigation({ session, view, onView, busy, onLogout }: {
  session: Session; view: StaffView; onView: (view: StaffView) => void; busy: boolean; onLogout: () => void
}) {
  const supervisor = session.user?.role === 'supervisor'
  const groups = [{ label: 'Operação', items: supervisor ? [inbox] : [inbox, mine] }]
  if (supervisor) groups.push({ label: 'Supervisão', items: supervision })
  return <aside className="rail" aria-label="Área do analista">
    <Identity href="/analista" />
    <nav className="rail-nav" aria-label="Navegação da operação">
      {groups.map(group => <div className="rail-group" key={group.label}>
        <h2>{group.label}</h2>
        {group.items.map(item => <button key={item.id} type="button" aria-current={view === item.id ? 'page' : undefined}
          onClick={() => onView(item.id)}><Icon name={item.icon} />{viewLabels[item.id]}</button>)}
      </div>)}
    </nav>
    <label className="mobile-nav"><span className="sr-only">Área da operação</span>
      <select value={view} onChange={event => onView(event.target.value as StaffView)}>
        {groups.map(group => <optgroup key={group.label} label={group.label}>
          {group.items.map(item => <option key={item.id} value={item.id}>{viewLabels[item.id]}</option>)}
        </optgroup>)}
      </select>
    </label>
    <div className="rail-bottom">
      <a href="/"><Icon name="chat" />Simulador</a>
      <a href="/health"><Icon name="pulse" />Status da API</a>
      <div className="account">
        <div><strong>{session.user?.name}</strong><small>{supervisor ? 'Supervisor' : 'Analista'}</small></div>
        <button type="button" aria-label="Sair da operação" title="Sair da operação" disabled={busy} onClick={onLogout}><Icon name="logout" /></button>
      </div>
    </div>
  </aside>
}
