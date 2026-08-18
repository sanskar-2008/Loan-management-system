import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../api/client'
import { PageHeader } from '../../components/ui'
import { errorMessage, formatMoney, toDisplayDate } from '../../utils/format'

function moneyNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

/** Mirror backend FIFO / targeted EMI allocation for live preview */
export function buildAllocationPreview(emis, amount, targetEmiId) {
  const amt = Math.round(moneyNum(amount) * 100) / 100
  if (!emis?.length || amt <= 0) return []

  const unpaid = emis
    .filter((e) => e.status !== 'paid')
    .slice()
    .sort((a, b) => a.installment_no - b.installment_no)

  let targets
  if (targetEmiId) {
    const target = unpaid.find((e) => e.id === targetEmiId)
    if (!target) return []
    targets = [target, ...unpaid.filter((e) => e.id !== targetEmiId)]
  } else {
    targets = unpaid
  }

  let remaining = amt
  const rows = []
  for (const emi of targets) {
    if (remaining <= 0) break
    const dueLeft = Math.round((moneyNum(emi.total_due) - moneyNum(emi.amount_paid)) * 100) / 100
    if (dueLeft <= 0) continue
    const apply = Math.min(remaining, dueLeft)
    rows.push({
      id: emi.id,
      installment_no: emi.installment_no,
      due_date: emi.due_date,
      remaining_before: dueLeft,
      applied: apply,
      status: emi.status,
    })
    remaining = Math.round((remaining - apply) * 100) / 100
  }
  return rows
}

export default function PaymentCreate() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [loans, setLoans] = useState([])
  const [emis, setEmis] = useState([])
  const [outstanding, setOutstanding] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    loan_id: params.get('loan_id') || '',
    amount: '',
    payment_date: new Date().toISOString().slice(0, 10),
    payment_mode: 'cash',
    reference_no: '',
    notes: '',
    emi_schedule_id: '',
  })

  useEffect(() => {
    Promise.all([
      api.get('/loans', { params: { status: 'active', page_size: 100 } }),
      api.get('/loans', { params: { status: 'defaulted', page_size: 100 } }),
    ]).then(([a, d]) => setLoans([...a.data.items, ...d.data.items]))
  }, [])

  useEffect(() => {
    if (!form.loan_id) {
      setEmis([])
      setOutstanding(null)
      return
    }

    let cancelled = false
    Promise.all([
      api.get(`/loans/${form.loan_id}`),
      api.get(`/loans/${form.loan_id}/emis`),
    ]).then(([loanRes, emiRes]) => {
      if (cancelled) return
      setOutstanding(moneyNum(loanRes.data.outstanding_balance))
      setEmis(emiRes.data.filter((e) => e.status !== 'paid'))
    })

    return () => {
      cancelled = true
    }
  }, [form.loan_id])

  function set(key, value) {
    setForm((f) => {
      const next = { ...f, [key]: value }
      if (key === 'loan_id') {
        next.emi_schedule_id = ''
        next.amount = ''
      }
      return next
    })
  }

  const amountNum = moneyNum(form.amount)
  const amountExceeds =
    form.loan_id &&
    form.amount !== '' &&
    outstanding != null &&
    amountNum > outstanding
  const amountInvalid =
    form.amount !== '' && (amountNum <= 0 || Number.isNaN(Number(form.amount)))

  const canSubmit =
    Boolean(form.loan_id) &&
    Boolean(form.payment_date) &&
    Boolean(form.payment_mode) &&
    form.amount !== '' &&
    amountNum > 0 &&
    !amountExceeds &&
    !amountInvalid &&
    !loading

  const allocation = useMemo(
    () => buildAllocationPreview(emis, form.amount, form.emi_schedule_id || null),
    [emis, form.amount, form.emi_schedule_id]
  )

  async function onSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/payments', {
        loan_id: form.loan_id,
        amount: form.amount,
        payment_date: form.payment_date,
        payment_mode: form.payment_mode,
        emi_schedule_id: form.emi_schedule_id || null,
        reference_no: form.reference_no || null,
        notes: form.notes || null,
      })
      navigate(`/payments/${data.id}`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="form-page">
      <PageHeader
        title="Record repayment"
        subtitle="Allocate against unpaid EMIs (FIFO by default)"
      />
      {error ? <div className="error-banner">{error}</div> : null}

      <form className="panel payment-form" onSubmit={onSubmit}>
        <div className="payment-form-body">
          <div className="field">
            <label className="label">Loan</label>
            <select
              className="select"
              style={{ width: '100%' }}
              required
              value={form.loan_id}
              onChange={(e) => set('loan_id', e.target.value)}
            >
              <option value="">Select loan</option>
              {loans.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.loan_number} · {l.organization_name}
                </option>
              ))}
            </select>
            {form.loan_id && outstanding != null ? (
              <div className="loan-outstanding">
                Outstanding: <strong>{formatMoney(outstanding)}</strong>
              </div>
            ) : null}
          </div>

          <div className="form-grid">
            <div className="field">
              <label className="label">Amount</label>
              <div className={`input-affix ${amountExceeds || amountInvalid ? 'has-error' : ''}`}>
                <span className="affix" aria-hidden="true">₹</span>
                <input
                  className="input affix-input"
                  inputMode="decimal"
                  placeholder="0.00"
                  required
                  value={form.amount}
                  onChange={(e) => {
                    const v = e.target.value.replace(/[^\d.]/g, '')
                    set('amount', v)
                  }}
                />
              </div>
              {amountExceeds ? (
                <div className="field-error">
                  Amount exceeds outstanding balance of {formatMoney(outstanding)}.
                </div>
              ) : null}
              {amountInvalid && !amountExceeds ? (
                <div className="field-error">Enter an amount greater than zero.</div>
              ) : null}
            </div>

            <div className="field">
              <label className="label">
                Payment date <span className="label-hint">(DD/MM/YYYY)</span>
              </label>
              <input
                className="input"
                type="date"
                style={{ width: '100%' }}
                required
                value={form.payment_date}
                onChange={(e) => set('payment_date', e.target.value)}
              />
              {form.payment_date ? (
                <div className="help">Selected: {toDisplayDate(form.payment_date)}</div>
              ) : (
                <div className="help">Format shown as day / month / year</div>
              )}
            </div>

            <div className="field">
              <label className="label">Mode</label>
              <select
                className="select"
                style={{ width: '100%' }}
                required
                value={form.payment_mode}
                onChange={(e) => set('payment_mode', e.target.value)}
              >
                <option value="cash">Cash</option>
                <option value="upi">UPI</option>
                <option value="bank_transfer">Bank transfer</option>
                <option value="cheque">Cheque</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="field">
              <label className="label">Target EMI (optional)</label>
              <select
                className="select"
                style={{ width: '100%' }}
                value={form.emi_schedule_id}
                disabled={!form.loan_id}
                onChange={(e) => set('emi_schedule_id', e.target.value)}
              >
                {!form.loan_id ? (
                  <option value="">Select a loan first</option>
                ) : (
                  <>
                    <option value="">Auto FIFO (oldest unpaid first)</option>
                    {emis.map((e) => (
                      <option key={e.id} value={e.id}>
                        #{e.installment_no} · due {toDisplayDate(e.due_date)} · rem{' '}
                        {formatMoney(moneyNum(e.total_due) - moneyNum(e.amount_paid))}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            <div className="field">
              <label className="label">Reference (optional)</label>
              <input
                className="input"
                style={{ width: '100%' }}
                value={form.reference_no}
                onChange={(e) => set('reference_no', e.target.value)}
                placeholder="UTR / cheque no."
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

          <div className="allocation-preview">
            <div className="allocation-preview-title">Allocation preview</div>
            {!form.loan_id ? (
              <div className="muted">Select a loan to preview EMI allocation.</div>
            ) : amountNum <= 0 ? (
              <div className="muted">Enter an amount to see which EMIs will be paid.</div>
            ) : amountExceeds ? (
              <div className="muted">Fix the amount to see allocation.</div>
            ) : allocation.length === 0 ? (
              <div className="muted">No unpaid EMIs available for allocation.</div>
            ) : (
              <div className="table-wrap" style={{ boxShadow: 'none' }}>
                <table className="data">
                  <thead>
                    <tr>
                      <th>Installment</th>
                      <th>Due date</th>
                      <th className="num">Remaining</th>
                      <th className="num">Applied</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allocation.map((row) => (
                      <tr key={row.id} className="no-click">
                        <td>#{row.installment_no}</td>
                        <td>{toDisplayDate(row.due_date)}</td>
                        <td className="num">{formatMoney(row.remaining_before)}</td>
                        <td className="num">
                          <strong>{formatMoney(row.applied)}</strong>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {allocation.length > 0 && form.emi_schedule_id ? (
              <div className="help" style={{ marginTop: 8 }}>
                Targeted EMI first, then remaining amount continues FIFO.
              </div>
            ) : null}
          </div>
        </div>

        <div className="form-sticky-footer">
          <Link className="btn btn-secondary" to="/payments">
            Cancel
          </Link>
          <button className="btn" type="submit" disabled={!canSubmit}>
            {loading ? 'Saving…' : 'Save payment'}
          </button>
        </div>
      </form>
    </div>
  )
}
