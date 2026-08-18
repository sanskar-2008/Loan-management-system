import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../../api/client'
import { DataTable } from '../../components/tables/DataTable'
import { PageHeader, Spinner } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'

export default function PaymentDetail() {
  const { id } = useParams()
  const [payment, setPayment] = useState(null)
  const [allocations, setAllocations] = useState([])
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function load() {
    const [p, a] = await Promise.all([
      api.get(`/payments/${id}`),
      api.get(`/payments/${id}/allocations`),
    ])
    setPayment(p.data)
    setAllocations(a.data)
  }

  useEffect(() => {
    load().catch((err) => setError(errorMessage(err)))
  }, [id])

  async function voidPayment() {
    try {
      await api.post(`/payments/${id}/void`, { reason })
      setMessage('Payment voided and balances recomputed.')
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (!payment) return <div className="center-screen" style={{ minHeight: 200 }}><Spinner /></div>

  return (
    <div>
      <PageHeader
        title={payment.payment_number}
        subtitle={`${payment.loan_number} · ${formatMoney(payment.amount)}`}
        actions={<Link className="btn btn-secondary" to={`/loans/${payment.loan_id}`}>View loan</Link>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      {message ? <div className="success-banner">{message}</div> : null}
      <div className="card card-pad" style={{ marginBottom: 14 }}>
        <div className="form-grid">
          <div><div className="muted">Date</div><div>{formatDate(payment.payment_date)}</div></div>
          <div><div className="muted">Mode</div><div>{payment.payment_mode}</div></div>
          <div><div className="muted">Reference</div><div>{payment.reference_no || '—'}</div></div>
          <div><div className="muted">Status</div><div>{payment.is_voided ? 'Voided' : 'Posted'}</div></div>
          <div><div className="muted">Notes</div><div>{payment.notes || '—'}</div></div>
          {payment.is_voided ? <div><div className="muted">Void reason</div><div>{payment.void_reason}</div></div> : null}
        </div>
      </div>
      <h3>Allocations</h3>
      <DataTable
        columns={[
          { key: 'emi_schedule_id', label: 'EMI ID' },
          { key: 'amount', label: 'Amount', render: (r) => formatMoney(r.amount) },
          { key: 'interest_portion', label: 'Interest', render: (r) => formatMoney(r.interest_portion) },
          { key: 'principal_portion', label: 'Principal', render: (r) => formatMoney(r.principal_portion) },
        ]}
        rows={allocations}
      />
      {!payment.is_voided ? (
        <div className="card card-pad" style={{ marginTop: 16, maxWidth: 560 }}>
          <h3 style={{ marginTop: 0 }}>Void payment</h3>
          <p className="muted">Creates a compensating reverse and recalculates EMI/loan balances.</p>
          <textarea className="textarea" placeholder="Reason (min 5 chars)" value={reason} onChange={(e) => setReason(e.target.value)} />
          <div className="form-actions">
            <button className="btn btn-danger" onClick={voidPayment}>Void payment</button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
