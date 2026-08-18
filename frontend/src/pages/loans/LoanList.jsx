import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../api/client'
import { DataTable, FilterBar, Pagination } from '../../components/tables/DataTable'
import { Badge, EmptyState, PageHeader } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'

export default function LoanList() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [filters, setFilters] = useState({
    q: searchParams.get('q') || '',
    status: '',
    loan_type: '',
  })
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ items: [], total: 0, page_size: 25 })
  const [error, setError] = useState('')

  useEffect(() => {
    const q = searchParams.get('q')
    if (q != null) setFilters((f) => ({ ...f, q }))
  }, [searchParams])

  useEffect(() => {
    api
      .get('/loans', {
        params: {
          q: filters.q || undefined,
          status: filters.status || undefined,
          loan_type: filters.loan_type || undefined,
          page,
          page_size: 25,
        },
      })
      .then((res) => setData(res.data))
      .catch((err) => setError(errorMessage(err)))
  }, [filters, page])

  return (
    <div>
      <PageHeader
        title="Loans"
        subtitle="Loans you took from organizations"
        actions={<Link className="btn" to="/loans/new">New Loan</Link>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      <FilterBar>
        <input
          className="input"
          placeholder="Search loan # or organization…"
          value={filters.q}
          onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, q: e.target.value })) }}
        />
        <select className="select" value={filters.status} onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, status: e.target.value })) }}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="closed">Closed</option>
          <option value="defaulted">Defaulted</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select className="select" value={filters.loan_type} onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, loan_type: e.target.value })) }}>
          <option value="">All types</option>
          <option value="flat">Flat</option>
          <option value="compound">Compound</option>
        </select>
      </FilterBar>
      {!data.items.length ? (
        <EmptyState title="No loans" description="Record a loan you took from an organization." action={<Link className="btn" to="/loans/new">Create loan</Link>} />
      ) : (
        <>
          <DataTable
            columns={[
              { key: 'loan_number', label: 'Loan #' },
              { key: 'organization_name', label: 'Organization' },
              { key: 'loan_type', label: 'Type', render: (r) => <Badge status={r.loan_type} /> },
              { key: 'principal_amount', label: 'Taken', render: (r) => formatMoney(r.principal_amount) },
              { key: 'emi_amount', label: 'EMI', render: (r) => formatMoney(r.emi_amount) },
              {
                key: 'outstanding_balance',
                label: 'Remaining',
                render: (r) => <span className="amt-remain">{formatMoney(r.outstanding_balance)}</span>,
              },
              { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
              { key: 'disbursement_date', label: 'Taken on', render: (r) => formatDate(r.disbursement_date) },
            ]}
            rows={data.items}
            onRowClick={(row) => navigate(`/loans/${row.id}`)}
          />
          <Pagination page={page} pageSize={data.page_size} total={data.total} onChange={setPage} />
        </>
      )}
    </div>
  )
}
