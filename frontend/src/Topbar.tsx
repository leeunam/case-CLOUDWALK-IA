export function Topbar({ staffPage = false, demo = false }: { staffPage?: boolean; demo?: boolean }) {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <a className="identity" href="/">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>Help desk</span>
        </a>
        <nav className="topbar-actions" aria-label="Navegação">
          {demo && <span className="mode"><i aria-hidden="true" />Demonstração</span>}
          <a href={staffPage ? '/' : '/analista'}>{staffPage ? 'Simulador' : 'Área do analista'}</a>
          <a href="/health">Status da API</a>
        </nav>
      </div>
    </header>
  )
}
