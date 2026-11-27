import { useSyncExternalStore } from 'react'

function subscribe(notify: () => void) {
  window.addEventListener('online', notify)
  window.addEventListener('offline', notify)
  return () => {
    window.removeEventListener('online', notify)
    window.removeEventListener('offline', notify)
  }
}

export function ConnectionNotice() {
  const online = useSyncExternalStore(subscribe, () => navigator.onLine)
  return online ? null : <p className="warning" role="status">Sem conexão. Os dados serão atualizados quando a conexão voltar.</p>
}
