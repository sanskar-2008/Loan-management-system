import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Landing() {
  const { token } = useAuth()
  if (token) return <Navigate to="/dashboard" replace />

  return (
    <div className="landing">
      <header className="landing-nav">
        <Link to="/" className="landing-brand">
          <span className="brand-mark">LM</span>
          <span>Loan Tracker</span>
        </Link>
        <div className="landing-nav-actions">
          <Link className="btn btn-secondary" to="/login">
            Admin sign in
          </Link>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-copy">
          <p className="landing-eyebrow">Personal multi-org tracker</p>
          <h1>Loan Tracker</h1>
          <p className="landing-lead">
            Track loans you took from banks and other organizations — remaining balances,
            EMIs, and repayments in one place.
          </p>
          <div className="landing-cta">
            <Link className="btn" to="/login">
              Enter console
            </Link>
            <a className="btn btn-secondary" href="#capabilities">
              See capabilities
            </a>
          </div>
        </div>
        <div className="landing-hero-visual" aria-hidden="true">
          <div className="landing-stat-card">
            <div className="landing-stat-label">What you track</div>
            <div className="landing-stat-rows">
              <div><span>Organizations</span><span>Multiple lenders</span></div>
              <div><span>Loans</span><span>Flat &amp; compound</span></div>
              <div><span>Repayments</span><span>FIFO to EMIs</span></div>
              <div><span>Reports</span><span>Org statements</span></div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section" id="capabilities">
        <h2>Built for your own loan book</h2>
        <p className="landing-section-lead">
          One admin. No lending-out workflow. Manage how much you took, paid, and still owe —
          across organizations.
        </p>
        <div className="landing-grid">
          <article>
            <h3>Organizations</h3>
            <p>Add banks, co-ops, or people you borrow from, with optional default interest rates.</p>
          </article>
          <article>
            <h3>Repayments</h3>
            <p>Record full or partial repayments; allocation still applies to the oldest unpaid EMI first.</p>
          </article>
          <article>
            <h3>Dashboard</h3>
            <p>See overall totals and drill into each organization&apos;s outstanding, repaid, and overdue.</p>
          </article>
        </div>
      </section>

      <footer className="landing-footer">
        <span>Loan Tracker · Personal use</span>
        <Link to="/login">Sign in</Link>
      </footer>
    </div>
  )
}
