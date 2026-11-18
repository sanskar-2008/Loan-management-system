import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../../api/client'
import { DataTable } from '../../components/tables/DataTable'
import { Badge, PageHeader, Spinner } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'
import { useAuth } from '../../auth/AuthContext'

export default function OrganizationDetail() {
  const { admin } = useAuth()
  const { id } = useParams()
  const navigate = useNavigate()
  const [org, setOrg] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loans, setLoans] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function load() {
    Promise.all([
      api.get(`/organizations/${id}`),
      api.get(`/organizations/${id}/summary`),
      api.get(`/organizations/${id}/loans`),
    ])
      .then(([o, s, l]) => {
        setOrg(o.data)
        setSummary(s.data)
        setLoans(l.data)
      })
      .catch((err) => setError(errorMessage(err)))
  }

  useEffect(() => {
    load()
  }, [id])

  async function toggleStatus() {
    if (!org) return
    const next = org.status === 'active' ? 'inactive' : 'active'
    setBusy(true)
    setError('')
    try {
      await api.patch(`/organizations/${id}/status`, { status: next })
      load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (!org || !summary) {
    return (
      <div>
        <PageHeader title="Organization" />
        {error ? <div className="error-banner">{error}</div> : <Spinner />}
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={org.name}
        subtitle={`${org.code} · ${org.status}`}
        actions={
          <>
            {!admin?.is_demo ? <Link className="btn" to={`/loans/new?organization_id=${org.id}`}>
              New loan
            </Link> : null}
            <Link className="btn btn-secondary" to={`/reports/organization/${org.id}`}>
              Statement
            </Link>
            {!admin?.is_demo ? <button className="btn btn-ghost" type="button" disabled={busy} onClick={toggleStatus}>
              {org.status === 'active' ? 'Deactivate' : 'Activate'}
            </button> : null}
          </>
        }
      />
      {error ? <div className="error-banner">{error}</div> : null}

      <div className="kpi-grid">
        <div className="kpi">
          <div className="kpi-label">Outstanding</div>
          <div className="kpi-value kpi-value--remain">{formatMoney(summary.outstanding_balance)}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Repaid</div>
          <div className="kpi-value kpi-value--receive">{formatMoney(summary.total_paid)}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Principal taken</div>
          <div className="kpi-value">{formatMoney(summary.principal_taken)}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Loans</div>
          <div className="kpi-value">
            {summary.active_loans} active · {summary.total_loans} total
          </div>
        </div>
      </div>

      <div className="panel panel-pad" style={{ marginBottom: 12 }}>
        <div className="meta-grid">
          <div>
            <div className="muted">Phone</div>
            <div>{org.contact_phone || '—'}</div>
          </div>
          <div>
            <div className="muted">Email</div>
            <div>{org.contact_email || '—'}</div>
          </div>
          <div>
            <div className="muted">Default flat</div>
            <div>{org.default_flat_rate != null ? `${org.default_flat_rate}%` : '—'}</div>
          </div>
          <div>
            <div className="muted">Default compound</div>
            <div>{org.default_compound_rate != null ? `${org.default_compound_rate}%` : '—'}</div>
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <div className="muted">Notes</div>
            <div>{org.notes || '—'}</div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Loans from this organization</h2>
        </div>
        <DataTable
          columns={[
            { key: 'loan_number', label: 'Loan #' },
            { key: 'loan_type', label: 'Type', render: (r) => <Badge status={r.loan_type} /> },
            {
              key: 'principal_amount',
              label: 'Taken',
              render: (r) => formatMoney(r.principal_amount),
            },
            {
              key: 'total_paid',
              label: 'Repaid',
              render: (r) => <span className="amt-receive">{formatMoney(r.total_paid)}</span>,
            },
            {
              key: 'outstanding_balance',
              label: 'Remaining',
              render: (r) => <span className="amt-remain">{formatMoney(r.outstanding_balance)}</span>,
            },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            {
              key: 'disbursement_date',
              label: 'Taken on',
              render: (r) => formatDate(r.disbursement_date),
            },
          ]}
          rows={loans}
          onRowClick={(row) => navigate(`/loans/${row.id}`)}
        />
      </div>
    </div>
  )
}
