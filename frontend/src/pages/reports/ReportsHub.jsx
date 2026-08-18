import { Link } from 'react-router-dom'
import { PageHeader } from '../../components/ui'

const REPORTS = [
  { to: '/reports/portfolio', title: 'Portfolio', desc: 'Loans by status, type, amount taken and remaining' },
  { to: '/reports/collections', title: 'Repayments', desc: 'Repayments by date range and mode' },
  { to: '/reports/overdue', title: 'Overdue aging', desc: 'Aging buckets: 1–30, 31–60, 61–90, 90+' },
  { to: '/reports/interest', title: 'Interest paid', desc: 'Interest paid by loan' },
]

export default function ReportsHub() {
  return (
    <div>
      <PageHeader title="Reports" subtitle="Operational reports for your borrowed loans" />
      <div className="grid-2">
        {REPORTS.map((r) => (
          <Link key={r.to} to={r.to} className="panel panel-pad" style={{ textDecoration: 'none', color: 'inherit' }}>
            <h3 style={{ margin: '0 0 4px', fontSize: 14, fontWeight: 600 }}>{r.title}</h3>
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>{r.desc}</p>
          </Link>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 16, fontSize: 13 }}>
        Organization statements are available from each organization detail page.
      </p>
    </div>
  )
}
