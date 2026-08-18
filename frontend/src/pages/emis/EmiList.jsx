import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'
import { DataTable, FilterBar, Pagination } from '../../components/tables/DataTable'
import { Badge, PageHeader } from '../../components/ui'
import { errorMessage, formatDate, formatMoney } from '../../utils/format'

export default function EmiList() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ items: [], total: 0, page_size: 25 })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  function load() {
    return api
      .get('/emis', { params: { status: status || undefined, page, page_size: 25 } })
      .then((res) => setData(res.data))
  }

  useEffect(() => {
    load().catch((err) => setError(errorMessage(err)))
  }, [status, page])

  async function refreshOverdue() {
    try {
      const { data: res } = await api.post('/emis/refresh-overdue')
      setMessage(`Marked ${res.updated} EMI(s) overdue.`)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="EMI Schedule"
        subtitle="Global installment explorer"
        actions={<button className="btn btn-secondary" onClick={refreshOverdue}>Refresh overdue</button>}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      {message ? <div className="success-banner">{message}</div> : null}
      <FilterBar>
        <select className="select" value={status} onChange={(e) => { setPage(1); setStatus(e.target.value) }}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="partial">Partial</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
        </select>
      </FilterBar>
      <DataTable
        columns={[
          { key: 'loan_number', label: 'Loan #' },
          { key: 'organization_name', label: 'Organization' },
          { key: 'installment_no', label: '#' },
          { key: 'due_date', label: 'Due', render: (r) => formatDate(r.due_date) },
          { key: 'total_due', label: 'Due Amt', render: (r) => formatMoney(r.total_due) },
          {
            key: 'amount_paid',
            label: 'Paid',
            render: (r) => <span className="amt-receive">{formatMoney(r.amount_paid)}</span>,
          },
          { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
        ]}
        rows={data.items}
        onRowClick={(row) => navigate(`/loans/${row.loan_id}`)}
      />
      <Pagination page={page} pageSize={data.page_size} total={data.total} onChange={setPage} />
    </div>
  )
}
