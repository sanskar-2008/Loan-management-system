export function Badge({ status }) {
  const key = String(status || '').toLowerCase().replace(/\s+/g, '-')
  return <span className={`badge badge-${key}`}>{status}</span>
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="empty panel">
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {actions ? <div className="topbar-actions">{actions}</div> : null}
    </div>
  )
}

export function Spinner() {
  return <div className="spinner" />
}
