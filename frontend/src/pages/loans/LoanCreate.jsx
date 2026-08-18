import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../api/client'
import { PageHeader } from '../../components/ui'
import { errorMessage, formatMoney, toDisplayDate } from '../../utils/format'

function rateFromOrg(org, loanType, settings) {
  if (org) {
    if (loanType === 'compound' && org.default_compound_rate != null) {
      return String(org.default_compound_rate)
    }
    if (loanType === 'flat' && org.default_flat_rate != null) {
      return String(org.default_flat_rate)
    }
  }
  if (!settings) return loanType === 'compound' ? '14' : '12'
  return String(
    loanType === 'compound' ? settings.default_compound_rate : settings.default_flat_rate,
  )
}

export default function LoanCreate() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [settings, setSettings] = useState(null)
  const [orgs, setOrgs] = useState([])
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    organization_id: params.get('organization_id') || '',
    loan_type: 'flat',
    principal_amount: '',
    annual_interest_rate: '12',
    tenure_months: '12',
    disbursement_date: new Date().toISOString().slice(0, 10),
    notes: '',
  })

  useEffect(() => {
    Promise.all([
      api.get('/settings'),
      api.get('/organizations', { params: { status: 'active', page_size: 100 } }),
    ]).then(([s, o]) => {
      setSettings(s.data)
      setOrgs(o.data.items || [])
      const selected =
        (o.data.items || []).find((x) => x.id === params.get('organization_id')) || null
      setForm((f) => ({
        ...f,
        annual_interest_rate: rateFromOrg(selected, f.loan_type, s.data),
      }))
    })
  }, [params])

  useEffect(() => {
    if (!form.principal_amount || !form.tenure_months || !form.disbursement_date) return
    const t = setTimeout(() => {
      api
        .post('/loans/preview', {
          loan_type: form.loan_type,
          principal_amount: form.principal_amount,
          annual_interest_rate: form.annual_interest_rate,
          tenure_months: Number(form.tenure_months),
          disbursement_date: form.disbursement_date,
        })
        .then((res) => setPreview(res.data))
        .catch(() => setPreview(null))
    }, 300)
    return () => clearTimeout(t)
  }, [
    form.loan_type,
    form.principal_amount,
    form.annual_interest_rate,
    form.tenure_months,
    form.disbursement_date,
  ])

  function set(key, value) {
    setForm((f) => {
      const next = { ...f, [key]: value }
      if (key === 'loan_type' || key === 'organization_id') {
        const org = orgs.find((x) => x.id === (key === 'organization_id' ? value : next.organization_id))
        next.annual_interest_rate = rateFromOrg(
          org,
          key === 'loan_type' ? value : next.loan_type,
          settings,
        )
      }
      return next
    })
  }

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/loans', {
        organization_id: form.organization_id,
        loan_type: form.loan_type,
        principal_amount: form.principal_amount,
        annual_interest_rate: form.annual_interest_rate,
        tenure_months: Number(form.tenure_months),
        disbursement_date: form.disbursement_date,
        notes: form.notes || null,
      })
      navigate(`/loans/${data.id}`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const schedulePeek = useMemo(() => preview?.schedule?.slice(0, 3) || [], [preview])

  return (
    <div>
      <PageHeader
        title="New loan"
        subtitle="Record a loan you took from an organization — EMI schedule is generated automatically"
      />
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="grid-2">
        <form className="panel panel-pad" onSubmit={onSubmit}>
          <div className="form-grid">
            <div className="field" style={{ gridColumn: '1 / -1' }}>
              <label className="label">Organization</label>
              <select
                className="select"
                style={{ width: '100%' }}
                required
                value={form.organization_id}
                onChange={(e) => set('organization_id', e.target.value)}
              >
                <option value="">Select organization…</option>
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name} ({o.code})
                  </option>
                ))}
              </select>
              <div className="help">
                <Link to="/organizations/new">Add organization</Link> if it is not listed.
              </div>
            </div>
            <div className="field">
              <label className="label">Loan type</label>
              <select
                className="select"
                style={{ width: '100%' }}
                value={form.loan_type}
                onChange={(e) => set('loan_type', e.target.value)}
              >
                <option value="flat">Flat interest</option>
                <option value="compound">Compound interest</option>
              </select>
            </div>
            <div className="field">
              <label className="label">
                Date taken <span className="label-hint">(DD/MM/YYYY)</span>
              </label>
              <input
                className="input"
                style={{ width: '100%' }}
                type="date"
                required
                value={form.disbursement_date}
                onChange={(e) => set('disbursement_date', e.target.value)}
              />
              {form.disbursement_date ? (
                <div className="help">Selected: {toDisplayDate(form.disbursement_date)}</div>
              ) : null}
            </div>
            <div className="field">
              <label className="label">Amount taken</label>
              <div className="input-affix">
                <span className="affix">₹</span>
                <input
                  className="input affix-input"
                  required
                  inputMode="decimal"
                  value={form.principal_amount}
                  onChange={(e) => set('principal_amount', e.target.value.replace(/[^\d.]/g, ''))}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="field">
              <label className="label">Annual interest rate %</label>
              <input
                className="input"
                style={{ width: '100%' }}
                required
                value={form.annual_interest_rate}
                onChange={(e) => set('annual_interest_rate', e.target.value)}
              />
              <div className="help">Prefills from organization defaults when available.</div>
            </div>
            <div className="field">
              <label className="label">Tenure (months)</label>
              <input
                className="input"
                style={{ width: '100%' }}
                type="number"
                min="1"
                max="360"
                required
                value={form.tenure_months}
                onChange={(e) => set('tenure_months', e.target.value)}
              />
            </div>
          </div>
          <div className="field">
            <label className="label">Notes (optional)</label>
            <textarea
              className="textarea"
              value={form.notes}
              onChange={(e) => set('notes', e.target.value)}
            />
          </div>
          <div className="form-actions">
            <Link className="btn btn-secondary" to="/loans">
              Cancel
            </Link>
            <button className="btn" disabled={loading}>
              {loading ? 'Creating…' : 'Create loan'}
            </button>
          </div>
        </form>

        <div className="preview-panel">
          <h3 style={{ marginTop: 0, fontSize: 14, fontWeight: 600 }}>Schedule preview</h3>
          {!preview ? (
            <div className="muted">Enter amount, rate and tenure to calculate EMI.</div>
          ) : (
            <>
              <div className="stat-inline">
                <span className="muted">EMI amount</span>
                <strong>{formatMoney(preview.emi_amount)}</strong>
              </div>
              <div className="stat-inline">
                <span className="muted">Total interest</span>
                <strong>{formatMoney(preview.total_interest)}</strong>
              </div>
              <div className="stat-inline">
                <span className="muted">Total payable</span>
                <strong>{formatMoney(preview.total_payable)}</strong>
              </div>
              <div className="muted" style={{ marginTop: 14, marginBottom: 4, fontSize: 12 }}>
                First installments
              </div>
              {schedulePeek.map((row) => (
                <div className="stat-inline" key={row.installment_no}>
                  <span className="muted">
                    #{row.installment_no} · {toDisplayDate(row.due_date)}
                  </span>
                  <span>{formatMoney(row.total_due)}</span>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
