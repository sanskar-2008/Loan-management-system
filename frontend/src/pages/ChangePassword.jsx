import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { PageHeader } from '../components/ui'
import { errorMessage } from '../utils/format'

function EyeToggle({ show, onToggle }) {
  return (
    <button type="button" className="affix-btn" aria-label={show ? 'Hide password' : 'Show password'} onClick={onToggle}>
      {show ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
          <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
          <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
          <line x1="1" y1="1" x2="23" y2="23" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}
    </button>
  )
}

function PasswordField({ label, value, onChange, autoComplete, minLength }) {
  const [show, setShow] = useState(false)
  return (
    <div className="field">
      <label className="label">{label}</label>
      <div className="input-affix password-affix">
        <input
          className="input affix-input"
          type={show ? 'text' : 'password'}
          required
          minLength={minLength}
          autoComplete={autoComplete}
          value={value}
          onChange={onChange}
        />
        <EyeToggle show={show} onToggle={() => setShow((v) => !v)} />
      </div>
    </div>
  )
}

export default function ChangePassword() {
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setMessage('')
    try {
      await api.put('/auth/change-password', form)
      setMessage('Password updated successfully.')
      setForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title="Change password" actions={<Link className="btn btn-secondary" to="/settings">Back</Link>} />
      {error ? <div className="error-banner">{error}</div> : null}
      {message ? <div className="success-banner">{message}</div> : null}
      <form className="panel panel-pad" style={{ maxWidth: 480 }} onSubmit={onSubmit}>
        <PasswordField
          label="Current password"
          autoComplete="current-password"
          value={form.current_password}
          onChange={(e) => setForm({ ...form, current_password: e.target.value })}
        />
        <PasswordField
          label="New password"
          minLength={8}
          autoComplete="new-password"
          value={form.new_password}
          onChange={(e) => setForm({ ...form, new_password: e.target.value })}
        />
        <PasswordField
          label="Confirm password"
          minLength={8}
          autoComplete="new-password"
          value={form.confirm_password}
          onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
        />
        <div className="form-actions">
          <button className="btn" type="submit">Update password</button>
        </div>
      </form>
    </div>
  )
}
