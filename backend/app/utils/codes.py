from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def next_borrower_code(db: Session) -> str:
    from app.models.borrower import Borrower

    count = db.scalar(select(func.count()).select_from(Borrower)) or 0
    return f"BR-{count + 1:04d}"


def next_organization_code(db: Session) -> str:
    from app.models.organization import Organization, LEGACY_ORG_CODE

    # Skip ORG-0000 (legacy); sequence from non-legacy orgs
    codes = db.scalars(select(Organization.code).where(Organization.code != LEGACY_ORG_CODE)).all()
    max_n = 0
    for code in codes:
        try:
            if code.startswith("ORG-"):
                max_n = max(max_n, int(code.split("-", 1)[1]))
        except (ValueError, IndexError):
            continue
    return f"ORG-{max_n + 1:04d}"


def next_loan_number(db: Session) -> str:
    from app.models.loan import Loan

    today = date.today().strftime("%Y%m%d")
    prefix = f"LN-{today}-"
    count = db.scalar(
        select(func.count()).select_from(Loan).where(Loan.loan_number.like(f"{prefix}%"))
    ) or 0
    return f"{prefix}{count + 1:04d}"


def next_payment_number(db: Session) -> str:
    from app.models.payment import Payment

    today = date.today().strftime("%Y%m%d")
    prefix = f"PAY-{today}-"
    count = db.scalar(
        select(func.count()).select_from(Payment).where(Payment.payment_number.like(f"{prefix}%"))
    ) or 0
    return f"{prefix}{count + 1:04d}"
