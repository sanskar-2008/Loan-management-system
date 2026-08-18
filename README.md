# Loan Tracker

Personal multi-organization loan tracker for one admin. Record loans **you took** from banks and other lenders, track EMIs, repayments, and remaining balances.

**Stack:** React (Vite) · FastAPI · SQLite

## Features

- Admin login (JWT)
- Organizations (lenders) with optional default flat/compound rates
- Flat & compound loans taken from organizations, with live EMI preview
- Automatic EMI schedule generation
- Repayments (API path still `/payments`) with FIFO allocation to oldest unpaid EMI, partials, and void
- Auto loan close when outstanding reaches zero
- Dashboard: overall KPIs + org cards + drill-down; green repaid / red outstanding / amber overdue
- Organization statement and operational reports (CSV export)
- App settings (currency, global rate fallbacks)

## Default credentials

- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

Change the password after first login via **Settings → Change password**.

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

SQLite database: `backend/data/loan_management.db`

Migration to organizations runs on startup. To migrate + load demo data:

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m app.seeds.migrate_to_orgs --seed
# or reseed only:
PYTHONPATH=. .venv/bin/python -m app.seeds.seed_demo --force
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173

Optional env (`frontend/.env`):

```
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

## Backup

Copy `backend/data/loan_management.db` while the app is stopped (or after a brief pause) for a consistent backup.
