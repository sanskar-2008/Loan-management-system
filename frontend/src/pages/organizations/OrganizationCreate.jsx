import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'
import { PageHeader } from '../../components/ui'
import { errorMessage } from '../../utils/format'

export default function OrganizationCreate() {
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    name: '',
    contact_phone: '',
    contact_email: '',
    notes: '',
    default_flat_rate: '',
    default_compound_rate: '',
  })

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/organizations', {
        name: form.name.trim(),
        contact_phone: form.contact_phone.trim() || null,
        contact_email: form.contact_email.trim() || null,
        notes: form.notes.trim() || null,
        default_flat_rate: form.default_flat_rate === '' ? null : form.default_flat_rate,
        default_compound_rate:
          form.default_compound_rate === '' ? null : form.default_compound_rate,
      })
      navigate(`/organizations/${data.id}`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader title="Add organization" subtitle="Bank, NBFC, co-op, or person you borrow from" />
      {error ? <div className="error-banner">{error}</div> : null}
      <form className="panel panel-pad" style={{ maxWidth: 560 }} onSubmit={onSubmit}>
        <div className="form-grid">
          <div className="field" style={{ gridColumn: '1 / -1' }}>
            <label className="label">Name</label>
            <input
              className="input"
              style={{ width: '100%' }}
              required
              minLength={2}
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
            />
          </div>
          <div className="field">
            <label className="label">Phone</label>
            <input
              className="input"
              style={{ width: '100%' }}
              value={form.contact_phone}
              onChange={(e) => set('contact_phone', e.target.value)}
            />
          </div>
          <div className="field">
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              style={{ width: '100%' }}
              value={form.contact_email}
              onChange={(e) => set('contact_email', e.target.value)}
            />
          </div>
          <div className="field">
            <label className="label">Default flat rate %</label>
            <input
              className="input"
              type="number"
              step="0.0001"
              min="0"
              style={{ width: '100%' }}
              value={form.default_flat_rate}
              onChange={(e) => set('default_flat_rate', e.target.value)}
              placeholder="Optional"
            />
          </div>
          <div className="field">
            <label className="label">Default compound rate %</label>
            <input
              className="input"
              type="number"
              step="0.0001"
              min="0"
              style={{ width: '100%' }}
              value={form.default_compound_rate}
              onChange={(e) => set('default_compound_rate', e.target.value)}
              placeholder="Optional"
            />
          </div>
          <div className="field" style={{ gridColumn: '1 / -1' }}>
            <label className="label">Notes</label>
            <textarea
              className="textarea"
              rows={3}
              style={{ width: '100%' }}
              value={form.notes}
              onChange={(e) => set('notes', e.target.value)}
            />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Saving…' : 'Save'}
          </button>
          <button className="btn btn-secondary" type="button" onClick={() => navigate(-1)}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
