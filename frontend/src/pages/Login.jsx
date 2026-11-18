import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { errorMessage } from '../utils/format'

function EyeIcon({ open }) {
  // open = password currently visible → show "hide" (slashed) icon
  if (open) {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
        <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
        <line x1="1" y1="1" x2="23" y2="23" />
      </svg>
    )
  }
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

export default function Login() {
  const { login, loginDemo, token } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (token) return <Navigate to="/dashboard" replace />

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username.trim(), password)
      navigate('/dashboard')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function onDemo() {
    setError('')
    setLoading(true)
    try {
      await loginDemo()
      navigate('/dashboard')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel auth-panel-brand">
        <Link to="/" className="auth-brand">
          <span className="brand-mark">LM</span>
          <span>Loan Manager</span>
        </Link>
        <div className="auth-brand-copy">
          <h2>Operate your entire loan book from one desk.</h2>
          <p>
            Origination, EMI schedules, collections, and portfolio control — built for a single
            admin team that needs accuracy over noise.
          </p>
        </div>
        <ul className="auth-points">
          <li>Flat &amp; compound interest engines</li>
          <li>Automatic EMI generation</li>
          <li>Payment allocation &amp; voiding</li>
        </ul>
      </div>

      <div className="auth-panel auth-panel-form">
        <form className="auth-form" onSubmit={onSubmit}>
          <div className="auth-form-head">
            <h1>Admin sign in</h1>
            <p>Use your organization credentials to continue.</p>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          <div className="field">
            <label className="label" htmlFor="login-user">Username or email</label>
            <input
              id="login-user"
              className="input"
              style={{ width: '100%' }}
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label className="label" htmlFor="login-pass">Password</label>
            <div className="input-affix password-affix">
              <input
                id="login-pass"
                className="input affix-input"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="affix-btn"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={() => setShowPassword((v) => !v)}
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>

          <button className="btn auth-submit" type="submit" disabled={loading || !username || !password}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <div className="auth-divider"><span>or explore</span></div>
          <button className="btn btn-secondary auth-demo" type="button" onClick={onDemo} disabled={loading}>
            {loading ? 'Preparing demo…' : 'Try Demo Account'}
            <span aria-hidden="true">→</span>
          </button>
          <p className="auth-demo-note">Explore sample loans and reports in read-only mode.</p>

          <p className="auth-back">
            <Link to="/">← Back to home</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
