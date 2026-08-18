import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import api from '../api/client'
import { Badge, PageHeader } from '../components/ui'
import { formatDate, formatMoney } from '../utils/format'

const COLORS = ['#0969da', '#1a7f37', '#9a6700', '#cf222e', '#656d76', '#8250df']

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid #d8dee4',
  fontSize: 12,
}

function useInView({ threshold = 0.35, rootMargin = '0px 0px -40px 0px' } = {}) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el || inView) return undefined
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          obs.disconnect()
        }
      },
      { threshold, rootMargin },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [inView, threshold, rootMargin])

  return [ref, inView]
}

function Kpi({ label, value, sub, tone }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value${tone ? ` kpi-value--${tone}` : ''}`}>{value}</div>
      {sub ? <div className="kpi-sub">{sub}</div> : null}
    </div>
  )
}

function Panel({ title, action, children, empty }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>{title}</h2>
        {action}
      </div>
      <div className="panel-body">
        {empty ? <div className="empty" style={{ padding: '28px 16px' }}>{empty}</div> : children}
      </div>
    </div>
  )
}

function ChartCard({ title, children, reveal, delay = 0 }) {
  const [ref, inView] = useInView()
  return (
    <div
      ref={ref}
      className={`panel chart-reveal${inView ? ' is-visible' : ''}`}
      style={{ '--reveal-delay': `${delay}ms` }}
    >
      <div className="panel-head">
        <h2>{title}</h2>
      </div>
      <div className="panel-pad" style={{ height: 280 }}>
        {reveal
          ? inView
            ? typeof children === 'function'
              ? children(true)
              : children
            : typeof children === 'function'
              ? children(false)
              : <div className="pie-placeholder" aria-hidden />
          : children}
      </div>
    </div>
  )
}

function AnimatedPie({
  data,
  colors = COLORS,
  donut = false,
  moneyTooltip = false,
  delay = 0,
  duration = 1400,
  active = true,
}) {
  if (!data.length) {
    return (
      <div className="muted" style={{ paddingTop: 80, textAlign: 'center' }}>
        No data
      </div>
    )
  }
  if (!active) return <div className="pie-placeholder" aria-hidden />

  return (
    <div className="pie-stage" style={{ width: '100%', height: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={donut ? 52 : 0}
            outerRadius={86}
            paddingAngle={donut ? 3 : 2}
            startAngle={90}
            endAngle={-270}
            isAnimationActive
            animationBegin={delay}
            animationDuration={duration}
            animationEasing="ease-out"
            stroke="#fff"
            strokeWidth={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={moneyTooltip ? (v) => formatMoney(v) : undefined}
          />
          <Legend verticalAlign="bottom" height={28} iconType="circle" />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const orgId = searchParams.get('org') || ''
  const [period, setPeriod] = useState('mtd')
  const [q, setQ] = useState('')
  const [summary, setSummary] = useState(null)
  const [charts, setCharts] = useState(null)
  const [widgets, setWidgets] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = { period }
    const chartParams = {}
    if (orgId) {
      params.organization_id = orgId
      chartParams.organization_id = orgId
    }
    Promise.all([
      api.get('/dashboard/summary', { params }),
      api.get('/dashboard/charts', { params: chartParams }),
      api.get('/dashboard/widgets', { params: chartParams }),
    ])
      .then(([s, c, w]) => {
        setSummary(s.data)
        setCharts(c.data)
        setWidgets(w.data)
      })
      .finally(() => setLoading(false))
  }, [period, orgId])

  const orgCards = summary?.by_organization || []
  const activeOrg = useMemo(
    () => orgCards.find((o) => o.organization_id === orgId),
    [orgCards, orgId],
  )

  function searchGo(e) {
    e.preventDefault()
    const term = q.trim()
    if (!term) return
    navigate(`/loans?q=${encodeURIComponent(term)}`)
  }

  if (loading || !summary || !charts || !widgets) {
    return (
      <div>
        <PageHeader title="Dashboard" subtitle="Your loans across organizations" />
        <div className="kpi-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <div className="kpi" key={i}>
              <div className="skeleton" style={{ width: '40%', marginBottom: 12 }} />
              <div className="skeleton" style={{ width: '70%', height: 22 }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const collectionsSeries = (charts.collections_vs_due?.collections || []).map((row, i) => ({
    month: row.month,
    collections: Number(row.amount),
    due: Number(charts.collections_vs_due.due[i]?.amount || 0),
  }))
  const outstandingSeries = (charts.outstanding_trend || []).map((d) => ({
    month: d.month,
    amount: Number(d.amount),
  }))
  const typeMix = (charts.loan_type_mix || []).filter((d) => Number(d.value) > 0)
  const statusMix = (charts.status_breakdown || []).filter((d) => Number(d.value) > 0)
  const orgMix = (charts.organization_mix || []).filter((d) => Number(d.value) > 0)
  const aging = (charts.overdue_aging || []).map((d) => ({
    name: d.name,
    amount: Number(d.amount),
  }))
  const modeMix = (charts.payment_mode_mix || []).filter((d) => Number(d.value) > 0)

  return (
    <div>
      <PageHeader
        title={activeOrg ? activeOrg.organization_name : 'Dashboard'}
        subtitle={
          activeOrg
            ? `Loans from ${activeOrg.organization_code}`
            : 'Personal multi-org loan tracker'
        }
        actions={
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <form onSubmit={searchGo} style={{ display: 'flex', gap: 6 }}>
              <input
                className="input"
                placeholder="Search loans / orgs…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                aria-label="Search"
              />
            </form>
            {orgId ? (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setSearchParams({})}
              >
                All organizations
              </button>
            ) : null}
            <select
              className="select"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              aria-label="Period"
            >
              <option value="today">Today</option>
              <option value="mtd">Month to date</option>
              <option value="ytd">Year to date</option>
              <option value="all">All time</option>
            </select>
          </div>
        }
      />

      {summary.overdue_loans > 0 ? (
        <div className="alert-warning alert" style={{ marginBottom: 16 }}>
          {summary.overdue_loans} loan{summary.overdue_loans === 1 ? '' : 's'} with overdue EMIs
          (<span className="amt-overdue"> {formatMoney(summary.overdue_amount)}</span>).{' '}
          <Link to="/reports/overdue">Review overdue report</Link>
        </div>
      ) : null}

      <div className="kpi-grid">
        <Kpi
          label="Outstanding"
          value={formatMoney(summary.outstanding_balance)}
          tone="remain"
        />
        <Kpi
          label="Repayments (period)"
          value={formatMoney(summary.period_collections)}
          sub={`Today ${formatMoney(summary.today_collections)}`}
          tone="receive"
        />
        <Kpi
          label="Overdue"
          value={formatMoney(summary.overdue_amount)}
          sub={`${summary.overdue_loans} loans`}
          tone="overdue"
        />
        <Kpi
          label="Active loans"
          value={summary.active_loans}
          sub={`${summary.closed_loans} closed · ${summary.defaulted_loans} defaulted`}
        />
        <Kpi label="Amount taken" value={formatMoney(summary.total_principal_disbursed)} />
        <Kpi
          label="Interest paid"
          value={formatMoney(summary.total_interest_earned)}
          tone="receive"
        />
        <Kpi
          label="Organizations"
          value={summary.active_organizations ?? summary.total_organizations}
          sub={`${summary.flat_loans} flat · ${summary.compound_loans} compound`}
        />
        <Kpi
          label="Avg loan size"
          value={formatMoney(summary.average_loan_amount)}
          sub={`Avg rate ${Number(summary.average_interest_rate || 0).toFixed(2)}%`}
        />
      </div>

      {!orgId && orgCards.length > 0 ? (
        <div style={{ marginBottom: 16 }}>
          <div className="panel-head" style={{ padding: '0 0 8px' }}>
            <h2 style={{ margin: 0, fontSize: 14 }}>By organization</h2>
          </div>
          <div className="org-card-grid">
            {orgCards.map((o) => (
              <button
                type="button"
                key={o.organization_id}
                className="org-card"
                onClick={() => setSearchParams({ org: o.organization_id })}
              >
                <div className="org-card-name">{o.organization_name}</div>
                <div className="muted" style={{ fontSize: 12 }}>{o.organization_code} · {o.loan_count} loans</div>
                <div className="org-card-metrics">
                  <div>
                    <div className="muted" style={{ fontSize: 11 }}>Remaining</div>
                    <strong className="amt-remain">{formatMoney(o.outstanding_balance)}</strong>
                  </div>
                  <div>
                    <div className="muted" style={{ fontSize: 11 }}>Repaid</div>
                    <strong className="amt-receive">{formatMoney(o.total_paid)}</strong>
                  </div>
                  <div>
                    <div className="muted" style={{ fontSize: 11 }}>Overdue</div>
                    <strong className="amt-overdue">{formatMoney(o.overdue_amount)}</strong>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid-2" style={{ marginBottom: 12 }}>
        <ChartCard title="Repayments vs due">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={collectionsSeries}>
              <defs>
                <linearGradient id="colFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1a7f37" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#1a7f37" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#eaeef2" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatMoney(v)} />
              <Legend />
              <Area
                type="monotone"
                dataKey="collections"
                name="Repayments"
                stroke="#1a7f37"
                fill="url(#colFill)"
                strokeWidth={2}
                isAnimationActive
                animationDuration={900}
              />
              <Area
                type="monotone"
                dataKey="due"
                name="Due"
                stroke="#656d76"
                fill="transparent"
                strokeWidth={2}
                strokeDasharray="4 4"
                isAnimationActive
                animationDuration={900}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Outstanding trend">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={outstandingSeries}>
              <defs>
                <linearGradient id="outFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#cf222e" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#cf222e" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#eaeef2" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatMoney(v)} />
              <Area
                type="monotone"
                dataKey="amount"
                name="Outstanding"
                stroke="#cf222e"
                fill="url(#outFill)"
                strokeWidth={2}
                isAnimationActive
                animationDuration={1000}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid-3 pie-row" style={{ marginBottom: 12 }}>
        <ChartCard title="By organization" reveal delay={0}>
          {(active) =>
            orgMix.length === 0 ? (
              <div className="muted" style={{ paddingTop: 80, textAlign: 'center' }}>No data</div>
            ) : (
              <AnimatedPie data={orgMix} donut moneyTooltip delay={80} duration={1500} active={active} />
            )
          }
        </ChartCard>
        <ChartCard title="Loan status" reveal delay={140}>
          {(active) =>
            statusMix.length === 0 ? (
              <div className="muted" style={{ paddingTop: 80, textAlign: 'center' }}>No data</div>
            ) : (
              <AnimatedPie data={statusMix} delay={160} duration={1600} active={active} />
            )
          }
        </ChartCard>
        <ChartCard title="Loan type" reveal delay={240}>
          {(active) =>
            typeMix.length === 0 ? (
              <div className="muted" style={{ paddingTop: 80, textAlign: 'center' }}>No data</div>
            ) : (
              <AnimatedPie data={typeMix} donut delay={200} duration={1500} active={active} />
            )
          }
        </ChartCard>
      </div>

      <div style={{ marginBottom: 12 }}>
        <ChartCard title="Overdue aging">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={aging} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eaeef2" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={48} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatMoney(v)} />
              <Bar
                dataKey="amount"
                name="Overdue"
                fill="#9a6700"
                radius={[0, 4, 4, 0]}
                isAnimationActive
                animationDuration={900}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid-2" style={{ marginBottom: 12 }}>
        <Panel
          title="Due soon"
          action={<Link className="btn btn-sm btn-ghost" to="/emis">View all</Link>}
          empty={widgets.upcoming_emis.length === 0 ? 'No EMIs due in the next 30 days.' : null}
        >
          {widgets.upcoming_emis.map((e) => (
            <Link className="list-item" key={e.id} to={`/loans/${e.loan_id}`}>
              <div>
                <div style={{ fontWeight: 500 }}>{e.organization_name}</div>
                <div className="muted" style={{ fontSize: 12 }}>
                  {e.loan_number} · #{e.installment_no} · {formatDate(e.due_date)}
                </div>
              </div>
              <strong className="amt-remain">
                {formatMoney(Number(e.total_due) - Number(e.amount_paid))}
              </strong>
            </Link>
          ))}
        </Panel>

        <Panel
          title="Recent loans"
          action={<Link className="btn btn-sm btn-ghost" to="/loans">View all</Link>}
          empty={widgets.recent_loans.length === 0 ? 'No loans yet.' : null}
        >
          {widgets.recent_loans.map((l) => (
            <Link className="list-item" key={l.id} to={`/loans/${l.id}`}>
              <div>
                <div style={{ fontWeight: 500 }} className="mono">{l.loan_number}</div>
                <div className="muted" style={{ fontSize: 12 }}>
                  {l.organization_name} · <Badge status={l.loan_type} /> · <Badge status={l.status} />
                </div>
              </div>
              <strong className="amt-remain">{formatMoney(l.outstanding_balance)}</strong>
            </Link>
          ))}
        </Panel>
      </div>
    </div>
  )
}
