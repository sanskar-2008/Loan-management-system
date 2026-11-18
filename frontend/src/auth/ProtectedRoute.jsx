import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function ProtectedRoute() {
  const { token, loading, admin } = useAuth()
  const location = useLocation()
  if (loading) {
    return (
      <div className="center-screen">
        <div className="spinner" />
      </div>
    )
  }
  if (!token) return <Navigate to="/login" replace />
  if (admin?.is_demo && (/\/new$/.test(location.pathname) || location.pathname === '/change-password')) {
    return <Navigate to="/dashboard" replace />
  }
  return <Outlet />
}
