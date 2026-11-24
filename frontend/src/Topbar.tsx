import { Icon } from './Icon'

export function Identity({ href = '/' }: { href?: string }) {
  return (
    <a className="identity" href={href}>
      <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
      <span>Help desk</span>
    </a>
  )
}

export function Topbar({ staffPage = false, demo = false }: { staffPage?: boolean; demo?: boolean }) {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Identity />
        <nav className="topbar-actions" aria-label="Navegação">
          {demo && <span className="mode"><i aria-hidden="true" />Dados locais</span>}
          <a href={staffPage ? '/' : '/analista'}>{staffPage ? 'Simulador' : 'Área do analista'}<Icon name="arrow" /></a>
          <a href="/health">Status da API</a>
        </nav>
      </div>
    </header>
  )
}
