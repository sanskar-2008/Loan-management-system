import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../../api/client'
import { DataTable } from '../../components/tables/DataTable'
import { Badge, PageHeader, Spinner } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'
import { useAuth } from '../../auth/AuthContext'

export default function LoanDetail() {
  const { admin } = useAuth()
  const { id } = useParams()
  const [loan, setLoan] = useState(null)
  const [emis, setEmis] = useState([])
  const [payments, setPayments] = useState([])
  const [tab, setTab] = useState('overview')
  const [error, setError] = useState('')

  async function load() {
    const [l, e, p] = await Promise.all([
      api.get(`/loans/${id}`),
      api.get(`/loans/${id}/emis`),
      api.get(`/loans/${id}/payments`),
    ])
    setLoan(l.data)
    setEmis(e.data)
    setPayments(p.data)
  }

  useEffect(() => {
    load().catch((err) => setError(errorMessage(err)))
  }, [id])

  async function setStatus(status) {
    try {
      await api.patch(`/loans/${id}/status`, { status })
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (!loan) {
    return <div className="center-screen" style={{ minHeight: 240 }}><Spinner /></div>
  }

  return (
    <div>
      <PageHeader
        title={loan.loan_number}
        subtitle={`${loan.organization_name || 'Organization'} · ${loan.loan_type} interest`}
        actions={
          <>
            {!admin?.is_demo && (loan.status === 'active' || loan.status === 'defaulted') ? (
              <Link className="btn" to={`/payments/new?loan_id=${loan.id}`}>Record repayment</Link>
            ) : null}
            {loan.status === 'active' ? (
              <>
                {!admin?.is_demo ? <button className="btn btn-secondary" onClick={() => setStatus('defaulted')}>Mark Defaulted</button> : null}
                {!admin?.is_demo ? <button className="btn btn-danger" onClick={() => setStatus('cancelled')}>Cancel</button> : null}
              </>
            ) : null}
          </>
        }
      />
      {error ? <div className="error-banner">{error}</div> : null}

      <div className="kpi-grid">
        <div className="kpi"><div className="kpi-label">Status</div><div className="kpi-value"><Badge status={loan.status} /></div></div>
        <div className="kpi"><div className="kpi-label">Amount taken</div><div className="kpi-value">{formatMoney(loan.principal_amount)}</div></div>
        <div className="kpi"><div className="kpi-label">EMI</div><div className="kpi-value">{formatMoney(loan.emi_amount)}</div></div>
        <div className="kpi"><div className="kpi-label">Remaining</div><div className="kpi-value kpi-value--remain">{formatMoney(loan.outstanding_balance)}</div></div>
      </div>

      <div className="tabs">
        {['overview', 'emis', 'payments'].map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'emis' ? 'EMI Schedule' : t === 'payments' ? 'Repayments' : 'Overview'}
          </button>
        ))}
      </div>

      {tab === 'overview' ? (
        <div className="panel panel-pad">
          <div className="meta-grid">
            <div>
              <div className="muted">Organization</div>
              <div>
                {loan.organization_id ? (
                  <Link to={`/organizations/${loan.organization_id}`}>
                    {loan.organization_name || '—'}
                    {loan.organization_code ? ` · ${loan.organization_code}` : ''}
                  </Link>
                ) : (
                  loan.organization_name || '—'
                )}
              </div>
            </div>
            <div><div className="muted">Type</div><div><Badge status={loan.loan_type} /></div></div>
            <div><div className="muted">Rate</div><div>{loan.annual_interest_rate}%</div></div>
            <div><div className="muted">Tenure</div><div>{loan.tenure_months} months</div></div>
            <div><div className="muted">Date taken</div><div>{formatDate(loan.disbursement_date)}</div></div>
            <div><div className="muted">Total interest</div><div>{formatMoney(loan.total_interest)}</div></div>
            <div><div className="muted">Total payable</div><div>{formatMoney(loan.total_payable)}</div></div>
            <div><div className="muted">Total repaid</div><div className="amt-receive">{formatMoney(loan.total_paid)}</div></div>
            <div><div className="muted">Interest paid</div><div className="amt-receive">{formatMoney(loan.total_interest_paid)}</div></div>
            <div><div className="muted">Notes</div><div>{loan.notes || '—'}</div></div>
          </div>
        </div>
      ) : null}

      {tab === 'emis' ? (
        <DataTable
          columns={[
            { key: 'installment_no', label: '#' },
            { key: 'due_date', label: 'Due', render: (r) => formatDate(r.due_date) },
            { key: 'principal_component', label: 'Principal', render: (r) => formatMoney(r.principal_component) },
            { key: 'interest_component', label: 'Interest', render: (r) => formatMoney(r.interest_component) },
            { key: 'total_due', label: 'Due Amt', render: (r) => formatMoney(r.total_due) },
            { key: 'amount_paid', label: 'Paid', render: (r) => formatMoney(r.amount_paid) },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
          ]}
          rows={emis}
        />
      ) : null}

      {tab === 'payments' ? (
        <DataTable
          columns={[
            { key: 'payment_number', label: 'Payment #' },
            { key: 'payment_date', label: 'Date', render: (r) => formatDate(r.payment_date) },
            { key: 'amount', label: 'Amount', render: (r) => formatMoney(r.amount) },
            { key: 'payment_mode', label: 'Mode' },
            { key: 'is_voided', label: 'Voided', render: (r) => (r.is_voided ? 'Yes' : 'No') },
          ]}
          rows={payments}
          onRowClick={(row) => { window.location.href = `/payments/${row.id}` }}
        />
      ) : null}
    </div>
  )
}
