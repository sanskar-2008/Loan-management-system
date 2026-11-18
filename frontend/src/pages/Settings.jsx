import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { PageHeader } from '../components/ui'
import { errorMessage } from '../utils/format'
import { useAuth } from '../auth/AuthContext'

export default function SettingsPage() {
  const { admin } = useAuth()
  const [form, setForm] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/settings').then((r) => setForm(r.data)).catch((e) => setError(errorMessage(e)))
  }, [])

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const { data } = await api.put('/settings', {
        company_name: form.company_name,
        company_address: form.company_address,
        company_phone: form.company_phone,
        logo_url: form.logo_url,
        currency_code: form.currency_code,
        currency_symbol: form.currency_symbol,
        default_flat_rate: form.default_flat_rate,
        default_compound_rate: form.default_compound_rate,
        late_fee_enabled: form.late_fee_enabled,
        late_fee_type: form.late_fee_type,
        late_fee_value: form.late_fee_value,
        overdue_alert_threshold_count: form.overdue_alert_threshold_count,
      })
      setForm(data)
      setMessage('Settings saved.')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (!form) return null

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Company profile and loan defaults"
        actions={!admin?.is_demo ? <Link className="btn btn-secondary" to="/change-password">Change password</Link> : null}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      {message ? <div className="success-banner">{message}</div> : null}
      <form className="card card-pad" style={{ maxWidth: 820 }} onSubmit={onSubmit}>
        <div className="form-grid">
          <div className="field"><label className="label">Company name</label><input className="input" style={{ width: '100%' }} value={form.company_name || ''} onChange={(e) => set('company_name', e.target.value)} /></div>
          <div className="field"><label className="label">Phone</label><input className="input" style={{ width: '100%' }} value={form.company_phone || ''} onChange={(e) => set('company_phone', e.target.value)} /></div>
          <div className="field"><label className="label">Currency code</label><input className="input" style={{ width: '100%' }} value={form.currency_code || ''} onChange={(e) => set('currency_code', e.target.value)} /></div>
          <div className="field"><label className="label">Currency symbol</label><input className="input" style={{ width: '100%' }} value={form.currency_symbol || ''} onChange={(e) => set('currency_symbol', e.target.value)} /></div>
          <div className="field"><label className="label">Default flat rate %</label><input className="input" style={{ width: '100%' }} value={form.default_flat_rate} onChange={(e) => set('default_flat_rate', e.target.value)} /></div>
          <div className="field"><label className="label">Default compound rate %</label><input className="input" style={{ width: '100%' }} value={form.default_compound_rate} onChange={(e) => set('default_compound_rate', e.target.value)} /></div>
        </div>
        <div className="field"><label className="label">Address</label><textarea className="textarea" value={form.company_address || ''} onChange={(e) => set('company_address', e.target.value)} /></div>
        <div className="form-actions">
          {!admin?.is_demo ? <button className="btn" disabled={loading}>{loading ? 'Saving…' : 'Save settings'}</button> : <p className="muted">Demo settings are read-only.</p>}
        </div>
      </form>
    </div>
  )
}
