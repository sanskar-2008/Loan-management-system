import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../../api/client'
import { DataTable, FilterBar, Pagination } from '../../components/tables/DataTable'
import { EmptyState, PageHeader } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'

export default function PaymentList() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [mode, setMode] = useState('')
  const [data, setData] = useState({ items: [], total: 0, page_size: 25 })
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/payments', { params: { page, page_size: 25, mode: mode || undefined, include_voided: true } })
      .then((res) => setData(res.data))
      .catch((err) => setError(errorMessage(err)))
  }, [page, mode])

  return (
    <div>
      <PageHeader
        title="Repayments"
        subtitle="Payments you made toward loans"
        actions={<Link className="btn" to="/payments/new">Record repayment</Link>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      <FilterBar>
        <select className="select" value={mode} onChange={(e) => { setPage(1); setMode(e.target.value) }}>
          <option value="">All modes</option>
          <option value="cash">Cash</option>
          <option value="upi">UPI</option>
          <option value="bank_transfer">Bank transfer</option>
          <option value="cheque">Cheque</option>
          <option value="other">Other</option>
        </select>
      </FilterBar>
      {!data.items.length ? (
        <EmptyState
          title="No repayments"
          description="Record a repayment against an active loan."
          action={<Link className="btn" to="/payments/new">Record repayment</Link>}
        />
      ) : (
        <>
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
              { key: 'is_voided', label: 'Status', render: (r) => (r.is_voided ? 'Voided' : 'Posted') },
            ]}
            rows={data.items}
            onRowClick={(row) => navigate(`/payments/${row.id}`)}
          />
          <Pagination page={page} pageSize={data.page_size} total={data.total} onChange={setPage} />
        </>
      )}
    </div>
  )
}
