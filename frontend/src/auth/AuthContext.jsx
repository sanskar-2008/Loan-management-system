import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem('lms_token'))
  const [admin, setAdmin] = useState(null)
  const [loading, setLoading] = useState(!!sessionStorage.getItem('lms_token'))

  useEffect(() => {
    if (!token) {
      setAdmin(null)
      setLoading(false)
      return
    }
    setLoading(true)
    api
      .get('/auth/me')
      .then((res) => setAdmin(res.data))
      .catch(() => {
        sessionStorage.removeItem('lms_token')
        setToken(null)
        setAdmin(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const value = useMemo(
    () => ({
      token,
      admin,
      loading,
      async login(username, password) {
        const { data } = await api.post('/auth/login', { username, password })
        sessionStorage.setItem('lms_token', data.access_token)
        setToken(data.access_token)
        return data
      },
      logout() {
        sessionStorage.removeItem('lms_token')
        setToken(null)
        setAdmin(null)
      },
    }),
    [token, admin, loading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
