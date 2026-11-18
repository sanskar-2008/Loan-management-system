"""
Load sample multi-org loans and repayments for local UI / chart checks.

Run ONLY after migrate_to_orgs schema steps (organizations + rates + organization_id + backfill).

Usage (from backend/):
  PYTHONPATH=. .venv/bin/python -m app.seeds.migrate_to_orgs --seed
  # or after migration:
  PYTHONPATH=. .venv/bin/python -m app.seeds.seed_demo
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import secrets

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Admin, Loan, Organization
from app.models.emi import EmiSchedule
from app.models.organization import LEGACY_ORG_CODE
from app.seeds.seed_admin import init_db
from app.seeds.migrate_to_orgs import migrate_schema
from app.services import loan_service, payment_service
from app.utils.codes import next_organization_code
from app.utils.security import hash_password



def _months_ago(months: int, *, day: date | None = None) -> date:
    base = day or date.today()
    y, m = base.year, base.month - months
    while m <= 0:
        m += 12
        y -= 1
    for d in range(base.day, 0, -1):
        try:
            return date(y, m, d)
        except ValueError:
            continue
    return date(y, m, 1)


ORG_SPECS = [
    {
        "name": "Demo · HDFC Bank",
        "contact_phone": "1800100100",
        "default_flat_rate": Decimal("11.5000"),
        "default_compound_rate": Decimal("13.0000"),
    },
    {
        "name": "Demo · SBI",
        "contact_phone": "1800112211",
        "default_flat_rate": Decimal("10.0000"),
        "default_compound_rate": None,
    },
    {
        "name": "Demo · Local Co-op",
        "contact_phone": "9876500001",
        "default_flat_rate": None,
        "default_compound_rate": Decimal("14.5000"),
    },
    {
        "name": "Demo · Friend — Ramesh",
        "contact_phone": "9876500099",
        "default_flat_rate": Decimal("8.0000"),
        "default_compound_rate": Decimal("8.0000"),
    },
]


def _ensure_orgs(db) -> dict[str, Organization]:
    by_name: dict[str, Organization] = {}
    for spec in ORG_SPECS:
        org = db.scalar(select(Organization).where(Organization.name == spec["name"]))
        if not org:
            org = Organization(
                code=next_organization_code(db),
                name=spec["name"],
                contact_phone=spec["contact_phone"],
                default_flat_rate=spec["default_flat_rate"],
                default_compound_rate=spec["default_compound_rate"],
                status="active",
                notes="Sample organization for product tour.",
            )
            db.add(org)
            db.flush()
        else:
            org.notes = "Sample organization for product tour."
            org.default_flat_rate = spec["default_flat_rate"]
            org.default_compound_rate = spec["default_compound_rate"]
            org.status = "active"
        by_name[spec["name"]] = org
    db.commit()
    return by_name


LOAN_SAMPLES = [
    {
        "org": "Demo · HDFC Bank",
        "loan_type": "flat",
        "principal_amount": Decimal("150000.00"),
        "annual_interest_rate": Decimal("11.5000"),
        "tenure_months": 12,
        "disbursement_date": _months_ago(8),
        "pay_count": 6,
        "modes": ["upi", "cash", "bank_transfer", "upi", "cash", "upi"],
    },
    {
        "org": "Demo · SBI",
        "loan_type": "compound",
        "principal_amount": Decimal("250000.00"),
        "annual_interest_rate": Decimal("12.0000"),
        "tenure_months": 18,
        "disbursement_date": _months_ago(5),
        "pay_count": 3,
        "modes": ["bank_transfer", "upi", "cheque"],
    },
    {
        "org": "Demo · Local Co-op",
        "loan_type": "flat",
        "principal_amount": Decimal("80000.00"),
        "annual_interest_rate": Decimal("10.0000"),
        "tenure_months": 6,
        "disbursement_date": _months_ago(7),
        "pay_count": "all",
        "modes": ["cash", "upi", "cash", "bank_transfer", "upi", "cash"],
    },
    {
        "org": "Demo · Friend — Ramesh",
        "loan_type": "flat",
        "principal_amount": Decimal("50000.00"),
        "annual_interest_rate": Decimal("8.0000"),
        "tenure_months": 10,
        "disbursement_date": _months_ago(10),
        "pay_count": 2,
        "modes": ["cash", "other"],
        "defaulted": True,
    },
    {
        "org": "Demo · HDFC Bank",
        "loan_type": "compound",
        "principal_amount": Decimal("120000.00"),
        "annual_interest_rate": Decimal("13.0000"),
        "tenure_months": 12,
        "disbursement_date": _months_ago(2),
        "pay_count": 1,
        "modes": ["upi"],
    },
    {
        "org": "Demo · SBI",
        "loan_type": "flat",
        "principal_amount": Decimal("300000.00"),
        "annual_interest_rate": Decimal("10.0000"),
        "tenure_months": 24,
        "disbursement_date": _months_ago(1),
        "pay_count": 1,
        "modes": ["bank_transfer"],
    },
]


def _refresh_overdue(db) -> None:
    today = date.today()
    emis = db.scalars(
        select(EmiSchedule).where(
            EmiSchedule.status.in_(("pending", "partial")),
            EmiSchedule.due_date < today,
        )
    ).all()
    for emi in emis:
        emi.status = "overdue"


def seed_demo(*, force: bool = False) -> dict:
    init_db()
    migrate_schema()
    db = SessionLocal()
    db.info["demo_mode"] = True
    try:
        existing = db.scalar(
            select(func.count()).select_from(Loan).where(Loan.loan_number.like("DEMO-LN-%"))
        )
        if existing and not force:
            return {"skipped": True, "existing_demo_loans": int(existing)}

        admin = db.scalar(select(Admin).where(Admin.username == "demo-viewer"))
        if not admin:
            admin = Admin(
                username="demo-viewer",
                email="demo-viewer@loan-manager.invalid",
                password_hash=hash_password(secrets.token_urlsafe(48)),
                full_name="Demo Account",
                is_active=True,
            )
            db.add(admin)
            db.flush()

        orgs = _ensure_orgs(db)

        created_loans = 0
        created_payments = 0

        for raw in LOAN_SAMPLES:
            org = orgs[raw["org"]]
            loan = loan_service.create_loan(
                db,
                admin_id=admin.id,
                organization_id=org.id,
                loan_type=raw["loan_type"],
                principal_amount=raw["principal_amount"],
                annual_interest_rate=raw["annual_interest_rate"],
                tenure_months=raw["tenure_months"],
                disbursement_date=raw["disbursement_date"],
                notes="Sample loan for product tour.",
            )
            created_loans += 1

            emis = db.scalars(
                select(EmiSchedule)
                .where(EmiSchedule.loan_id == loan.id)
                .order_by(EmiSchedule.installment_no)
            ).all()

            pay_count = raw["pay_count"]
            modes = raw["modes"]
            n = len(emis) if pay_count == "all" else min(int(pay_count), len(emis))
            for i in range(n):
                emi = emis[i]
                pay_date = emi.due_date + timedelta(days=1)
                if pay_date > date.today():
                    pay_date = date.today()
                if pay_date < loan.disbursement_date:
                    pay_date = loan.disbursement_date

                payment_service.record_payment(
                    db,
                    loan_id=loan.id,
                    amount=emi.total_due,
                    payment_date=pay_date,
                    payment_mode=modes[i % len(modes)],
                    reference_no=f"DEMO-{loan.loan_number}-{i + 1}",
                    notes="Sample repayment for product tour.",
                    emi_schedule_id=None,
                    admin_id=admin.id,
                )
                created_payments += 1

            if raw.get("defaulted"):
                loan = db.get(Loan, loan.id)
                if loan and loan.status == "active":
                    loan.status = "defaulted"

        _refresh_overdue(db)
        db.commit()

        legacy = db.scalar(select(Organization).where(Organization.code == LEGACY_ORG_CODE))
        return {
            "skipped": False,
            "loans": created_loans,
            "payments": created_payments,
            "organizations": len(orgs),
            "legacy_org": legacy.name if legacy else None,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    force = "--force" in sys.argv
    result = seed_demo(force=force)
    if result.get("skipped"):
        print(
            f"Demo data already present ({result['existing_demo_loans']} loans). Use --force to re-add."
        )
    else:
        print(
            f"Seeded {result['organizations']} orgs, {result['loans']} loans, {result['payments']} repayments."
        )
