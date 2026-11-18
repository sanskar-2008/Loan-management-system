import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'

const MAIN = [
  { to: '/dashboard', label: 'Dashboard', end: true },
  { to: '/organizations', label: 'Organizations' },
  { to: '/loans', label: 'Loans' },
  { to: '/emis', label: 'EMIs' },
  { to: '/payments', label: 'Repayments' },
]

export default function Sidebar({ open, overdueCount = 0, onNavigate }) {
  const { admin, logout } = useAuth()
  const isDemo = admin?.is_demo
  const navigate = useNavigate()

  function go(path) {
    onNavigate?.()
    navigate(path)
  }

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand">
        <div className="brand-mark">LM</div>
        <NavLink to="/dashboard" style={{ color: 'inherit', textDecoration: 'none' }} onClick={() => onNavigate?.()}>
          <div>Loan Tracker</div>
          <div className="brand-sub">Personal</div>
        </NavLink>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-group">
          <div className="nav-label">Operations</div>
          {MAIN.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => onNavigate?.()}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span>{item.label}</span>
              {item.to === '/emis' && overdueCount > 0 ? (
                <span className="nav-badge">{overdueCount}</span>
              ) : null}
            </NavLink>
          ))}
        </div>

        <div className="nav-group">
          <div className="nav-label">Analysis</div>
          <NavLink
            to="/reports"
            onClick={() => onNavigate?.()}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Reports
          </NavLink>
        </div>
      </nav>

      <div className="sidebar-footer">
        {!isDemo ? <NavLink
          to="/settings"
          onClick={() => onNavigate?.()}
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          Settings
        </NavLink> : null}
        <div className="nav-link" style={{ cursor: 'default' }}>
          {admin?.full_name || admin?.username || 'Admin'}
        </div>
        <button
          type="button"
          className="nav-link"
          onClick={() => {
            logout()
            go('/login')
          }}
        >
          Sign out
        </button>
      </div>
    </aside>
  )
}
