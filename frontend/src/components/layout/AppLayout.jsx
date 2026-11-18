import { Link, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Sidebar from './Sidebar'
import api from '../../api/client'
import { useAuth } from '../../auth/AuthContext'

const TITLES = {
  '/dashboard': 'Dashboard',
  '/loans': 'Loans',
  '/emis': 'EMIs',
  '/payments': 'Payments',
  '/reports': 'Reports',
  '/settings': 'Settings',
  '/change-password': 'Change password',
}

export default function AppLayout() {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [overdueCount, setOverdueCount] = useState(0)
  const { admin } = useAuth()
  const isDemo = admin?.is_demo

  useEffect(() => {
    setOpen(false)
    api
      .get('/dashboard/summary')
      .then((res) => setOverdueCount(res.data.overdue_loans || 0))
      .catch(() => {})
  }, [location.pathname])

  const base = '/' + (location.pathname.split('/')[1] || '')
  const title = TITLES[base] || TITLES[location.pathname] || 'Loan Manager'

  return (
    <div className="app-shell">
      <Sidebar open={open} overdueCount={overdueCount} onNavigate={() => setOpen(false)} />
      <div className="main-area">
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              type="button"
              className="btn btn-secondary menu-toggle"
              onClick={() => setOpen((v) => !v)}
            >
              Menu
            </button>
            <div className="topbar-title">{title}</div>
          </div>
          <div className="topbar-actions">
            {!isDemo ? <>
              <Link className="btn btn-secondary" to="/loans/new">New loan</Link>
              <Link className="btn" to="/payments/new">Record payment</Link>
            </> : <span className="demo-mode-badge">Demo · Read only</span>}
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
