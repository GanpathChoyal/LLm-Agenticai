import { Outlet, NavLink, Link } from 'react-router-dom'
import './Layout.css'

export default function Layout() {
  return (
    <div className="app-layout">
      <header className="site-header">
        <div className="header-inner">
          <Link to="/" className="logo">
            <span className="logo-icon">❤️</span>
            <span className="logo-text">
              Cardiac <span className="logo-highlight">Emergency AI</span>
            </span>
          </Link>
          <nav className="site-nav">
            <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Dashboard
            </NavLink>
            <NavLink to="/upload" className="nav-link nav-cta">
              + New Patient
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="site-main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <p>Cardiac Emergency AI &copy; 2026 &mdash; For clinical use only. Always verify with qualified staff.</p>
      </footer>
    </div>
  )
}
