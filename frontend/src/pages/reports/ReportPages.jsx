import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../../api/client'
import { DataTable } from '../../components/tables/DataTable'
import { Badge, PageHeader } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'

function downloadCsv(type, params = {}) {
  const qs = new URLSearchParams({ type, ...params }).toString()
  const token = sessionStorage.getItem('lms_token')
  return fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'}/reports/export?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((r) => r.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${type}_report.csv`
      a.click()
      URL.revokeObjectURL(url)
    })
}

export function PortfolioReport() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/reports/portfolio').then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)))
  }, [])
  return (
    <div>
      <PageHeader title="Portfolio Report" actions={<><Link className="btn btn-secondary" to="/reports">Back</Link><button className="btn" onClick={() => downloadCsv('portfolio')}>Export CSV</button></>} />
      {error ? <div className="error-banner">{error}</div> : null}
      {data ? (
        <DataTable
          columns={[
            { key: 'loan_number', label: 'Loan #' },
            { key: 'organization_name', label: 'Organization' },
            { key: 'loan_type', label: 'Type', render: (r) => <Badge status={r.loan_type} /> },
            { key: 'principal_amount', label: 'Taken', render: (r) => formatMoney(r.principal_amount) },
            {
              key: 'outstanding_balance',
              label: 'Remaining',
              render: (r) => <span className="amt-remain">{formatMoney(r.outstanding_balance)}</span>,
            },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            { key: 'disbursement_date', label: 'Taken on', render: (r) => formatDate(r.disbursement_date) },
          ]}
          rows={data.loans.map((l, i) => ({ ...l, id: i }))}
        />
      ) : null}
    </div>
  )
}

export function CollectionsReport() {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  function load() {
    api
      .get('/reports/collections', { params: { date_from: dateFrom || undefined, date_to: dateTo || undefined } })
      .then((r) => setData(r.data))
      .catch((e) => setError(errorMessage(e)))
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <PageHeader
        title="Repayments Report"
        subtitle={data ? `Total ${formatMoney(data.total)}` : ''}
        actions={<><Link className="btn btn-secondary" to="/reports">Back</Link><button className="btn" onClick={() => downloadCsv('collections', { date_from: dateFrom, date_to: dateTo })}>Export CSV</button></>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="filters">
        <input className="input" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <input className="input" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        <button className="btn btn-secondary" onClick={load}>Apply</button>
      </div>
      {data ? (
        <DataTable
          columns={[
            { key: 'payment_number', label: 'Repayment #' },
            { key: 'loan_number', label: 'Loan #' },
            {
              key: 'amount',
              label: 'Amount',
              render: (r) => <span className="amt-receive">{formatMoney(r.amount)}</span>,
            },
            { key: 'payment_date', label: 'Date', render: (r) => formatDate(r.payment_date) },
            { key: 'payment_mode', label: 'Mode' },
          ]}
          rows={data.payments.map((p, i) => ({ ...p, id: i }))}
        />
      ) : null}
    </div>
  )
}

export function OverdueReport() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/reports/overdue').then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)))
  }, [])
  const rows = data
    ? Object.entries(data.aging).flatMap(([bucket, items]) =>
        items.map((row, i) => ({ ...row, id: `${bucket}-${i}`, bucket }))
      )
    : []
  return (
    <div>
      <PageHeader title="Overdue Aging" actions={<><Link className="btn btn-secondary" to="/reports">Back</Link><button className="btn" onClick={() => downloadCsv('overdue')}>Export CSV</button></>} />
      {error ? <div className="error-banner">{error}</div> : null}
      {data ? (
        <div className="kpi-grid" style={{ marginBottom: 14 }}>
          <div className="kpi">
            <div className="kpi-label">Total overdue</div>
            <div className="kpi-value kpi-value--overdue">{formatMoney(data.total_overdue)}</div>
          </div>
        </div>
      ) : null}
      <DataTable
        columns={[
          { key: 'bucket', label: 'Bucket' },
          { key: 'loan_number', label: 'Loan #' },
          { key: 'organization_name', label: 'Organization' },
          { key: 'installment_no', label: '#' },
          { key: 'due_date', label: 'Due', render: (r) => formatDate(r.due_date) },
          { key: 'days_overdue', label: 'Days' },
          {
            key: 'remaining',
            label: 'Remaining',
            render: (r) => <span className="amt-overdue">{formatMoney(r.remaining)}</span>,
          },
        ]}
        rows={rows}
      />
    </div>
  )
}

export function InterestReport() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api.get('/reports/interest-earned').then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)))
  }, [])
  return (
    <div>
      <PageHeader
        title="Interest paid"
        subtitle={data ? `Total ${formatMoney(data.total_interest_earned)}` : ''}
        actions={<><Link className="btn btn-secondary" to="/reports">Back</Link><button className="btn" onClick={() => downloadCsv('interest')}>Export CSV</button></>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      {data ? (
        <DataTable
          columns={[
            { key: 'loan_number', label: 'Loan #' },
            { key: 'loan_type', label: 'Type' },
            { key: 'total_interest', label: 'Scheduled Interest', render: (r) => formatMoney(r.total_interest) },
            {
              key: 'interest_paid',
              label: 'Interest Paid',
              render: (r) => <span className="amt-receive">{formatMoney(r.interest_paid)}</span>,
            },
          ]}
          rows={data.by_loan.map((r, i) => ({ ...r, id: i }))}
        />
      ) : null}
    </div>
  )
}

export function OrganizationStatement() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api
      .get(`/reports/organization-statement/${id}`)
      .then((r) => setData(r.data))
      .catch((e) => setError(errorMessage(e)))
  }, [id])

  if (!data && !error) {
    return (
      <div>
        <PageHeader title="Organization statement" />
      </div>
    )
  }

  const org = data?.organization
  const totals = data?.totals

  return (
    <div>
      <PageHeader
        title={org ? `${org.name} statement` : 'Organization statement'}
        subtitle={org ? org.code : ''}
        actions={<Link className="btn btn-secondary" to={org ? `/organizations/${org.id}` : '/reports'}>Back</Link>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      {data ? (
        <>
          <div className="panel panel-pad" style={{ marginBottom: 12 }}>
            <div className="meta-grid">
              <div><div className="muted">Phone</div><div>{org.contact_phone || '—'}</div></div>
              <div><div className="muted">Email</div><div>{org.contact_email || '—'}</div></div>
              <div><div className="muted">Status</div><div><Badge status={org.status} /></div></div>
              <div style={{ gridColumn: '1 / -1' }}><div className="muted">Notes</div><div>{org.notes || '—'}</div></div>
            </div>
          </div>
          <div className="kpi-grid">
            <div className="kpi">
              <div className="kpi-label">Amount taken</div>
              <div className="kpi-value">{formatMoney(totals.amount_taken)}</div>
            </div>
            <div className="kpi">
              <div className="kpi-label">Amount repaid</div>
              <div className="kpi-value kpi-value--receive">{formatMoney(totals.amount_repaid)}</div>
            </div>
            <div className="kpi">
              <div className="kpi-label">Remaining</div>
              <div className="kpi-value kpi-value--remain">{formatMoney(totals.remaining_outstanding)}</div>
            </div>
            <div className="kpi">
              <div className="kpi-label">Loans</div>
              <div className="kpi-value">{totals.loan_count}</div>
            </div>
          </div>
          <div className="panel" style={{ marginBottom: 12 }}>
            <div className="panel-head"><h2>Loans</h2></div>
            <DataTable
              columns={[
                { key: 'loan_number', label: 'Loan #' },
                { key: 'loan_type', label: 'Type', render: (r) => <Badge status={r.loan_type} /> },
                { key: 'principal_amount', label: 'Taken', render: (r) => formatMoney(r.principal_amount) },
                { key: 'annual_interest_rate', label: 'Rate', render: (r) => `${r.annual_interest_rate}%` },
                { key: 'tenure_months', label: 'Tenure' },
                { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
                {
                  key: 'outstanding_balance',
                  label: 'Remaining',
                  render: (r) => <span className="amt-remain">{formatMoney(r.outstanding_balance)}</span>,
                },
              ]}
              rows={data.loans}
            />
          </div>
          <div className="panel">
            <div className="panel-head"><h2>Repayment history</h2></div>
            <DataTable
              columns={[
                { key: 'payment_date', label: 'Date', render: (r) => formatDate(r.payment_date) },
                { key: 'payment_number', label: 'Repayment #' },
                { key: 'loan_number', label: 'Loan #' },
                {
                  key: 'amount',
                  label: 'Amount',
                  render: (r) => (
                    <span className={r.is_voided ? 'muted' : 'amt-receive'}>
                      {formatMoney(r.amount)}
                      {r.is_voided ? ' (void)' : ''}
                    </span>
                  ),
                },
                { key: 'payment_mode', label: 'Mode' },
                { key: 'reference_no', label: 'Reference', render: (r) => r.reference_no || '—' },
              ]}
              rows={data.repayment_history.map((r, i) => ({ ...r, id: i }))}
            />
          </div>
        </>
      ) : null}
    </div>
  )
}
