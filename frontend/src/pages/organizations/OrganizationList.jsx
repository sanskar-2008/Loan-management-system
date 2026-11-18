import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../../api/client'
import { DataTable, FilterBar, Pagination } from '../../components/tables/DataTable'
import { Badge, EmptyState, PageHeader } from '../../components/ui'
import { errorMessage, formatMoney } from '../../utils/format'
import { useAuth } from '../../auth/AuthContext'

export default function OrganizationList() {
  const { admin } = useAuth()
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ q: '', status: '' })
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ items: [], total: 0, page_size: 25 })
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/organizations', {
        params: {
          q: filters.q || undefined,
          status: filters.status || undefined,
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
        title="Organizations"
        subtitle="Lenders you borrowed from"
        actions={!admin?.is_demo ? <Link className="btn" to="/organizations/new">Add organization</Link> : null}
      />
      {error ? <div className="error-banner">{error}</div> : null}
      <FilterBar>
        <input
          className="input"
          placeholder="Search name or code…"
          value={filters.q}
          onChange={(e) => {
            setPage(1)
            setFilters((f) => ({ ...f, q: e.target.value }))
          }}
        />
        <select
          className="select"
          value={filters.status}
          onChange={(e) => {
            setPage(1)
            setFilters((f) => ({ ...f, status: e.target.value }))
          }}
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </FilterBar>
      {!data.items.length ? (
        <EmptyState
          title="No organizations"
          description="Add a bank or lender, then record loans taken from them."
          action={!admin?.is_demo ? <Link className="btn" to="/organizations/new">Add organization</Link> : null}
        />
      ) : (
        <>
          <DataTable
            columns={[
              { key: 'code', label: 'Code', render: (r) => <span className="mono">{r.code}</span> },
              { key: 'name', label: 'Name' },
              { key: 'contact_phone', label: 'Phone', render: (r) => r.contact_phone || '—' },
              {
                key: 'default_flat_rate',
                label: 'Default flat',
                render: (r) => (r.default_flat_rate != null ? `${r.default_flat_rate}%` : '—'),
              },
              {
                key: 'default_compound_rate',
                label: 'Default compound',
                render: (r) => (r.default_compound_rate != null ? `${r.default_compound_rate}%` : '—'),
              },
              { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            ]}
            rows={data.items}
            onRowClick={(row) => navigate(`/organizations/${row.id}`)}
          />
          <Pagination page={page} pageSize={data.page_size} total={data.total} onChange={setPage} />
        </>
      )}
    </div>
  )
}
