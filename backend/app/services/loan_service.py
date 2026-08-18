from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.emi import EmiSchedule
from app.models.loan import Loan
from app.models.organization import Organization
from app.services.activity_service import log_activity
from app.services.interest import calculate_loan, money
from app.utils.codes import next_loan_number, next_organization_code


def preview_loan(
    *,
    loan_type: str,
    principal_amount: Decimal,
    annual_interest_rate: Decimal,
    tenure_months: int,
    disbursement_date: date,
):
    return calculate_loan(
        loan_type,
        principal_amount,
        annual_interest_rate,
        tenure_months,
        disbursement_date,
    )


def _resolve_organization(
    db: Session,
    *,
    organization_id: str | None = None,
    organization_name: str | None = None,
) -> Organization:
    if organization_id:
        org = db.get(Organization, organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        if org.status != "active":
            raise HTTPException(status_code=400, detail="Organization is inactive")
        return org

    name = (organization_name or "").strip()
    if not name:
        raise HTTPException(
            status_code=400,
            detail="organization_id or organization_name is required",
        )

    existing = db.scalar(select(Organization).where(Organization.name == name))
    if existing:
        if existing.status != "active":
            raise HTTPException(status_code=400, detail="Organization is inactive")
        return existing

    org = Organization(
        code=next_organization_code(db),
        name=name,
        status="active",
    )
    db.add(org)
    db.flush()
    return org


def create_loan(
    db: Session,
    *,
    organization_id: str | None = None,
    organization_name: str | None = None,
    loan_type: str,
    principal_amount: Decimal,
    annual_interest_rate: Decimal,
    tenure_months: int,
    disbursement_date: date,
    notes: str | None,
    admin_id: str,
) -> Loan:
    org = _resolve_organization(
        db,
        organization_id=organization_id,
        organization_name=organization_name,
    )

    calc = calculate_loan(
        loan_type,
        principal_amount,
        annual_interest_rate,
        tenure_months,
        disbursement_date,
    )

    loan = Loan(
        loan_number=next_loan_number(db),
        organization_id=org.id,
        borrower_id=None,
        loan_type=loan_type,
        principal_amount=money(principal_amount),
        annual_interest_rate=annual_interest_rate,
        tenure_months=tenure_months,
        disbursement_date=disbursement_date,
        emi_amount=calc.emi_amount,
        total_interest=calc.total_interest,
        total_payable=calc.total_payable,
        total_paid=Decimal("0.00"),
        total_interest_paid=Decimal("0.00"),
        outstanding_balance=calc.total_payable,
        status="active",
        notes=notes,
        created_by=admin_id,
    )
    db.add(loan)
    db.flush()

    for row in calc.schedule:
        db.add(
            EmiSchedule(
                loan_id=loan.id,
                installment_no=row.installment_no,
                due_date=row.due_date,
                principal_component=row.principal_component,
                interest_component=row.interest_component,
                total_due=row.total_due,
                amount_paid=Decimal("0.00"),
                status="pending",
            )
        )

    log_activity(
        db,
        admin_id=admin_id,
        action="loan.created",
        entity_type="loan",
        entity_id=loan.id,
        summary=f"Created loan {loan.loan_number} from {org.name}",
        metadata={"loan_type": loan_type, "principal": str(principal_amount), "organization_id": org.id},
    )
    db.commit()
    db.refresh(loan)
    return loan


def update_loan_status(db: Session, loan_id: str, new_status: str, admin_id: str) -> Loan:
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if new_status == "cancelled":
        if money(loan.total_paid) > Decimal("0.00"):
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel a loan with recorded (non-voided) payments",
            )
        if loan.status not in ("active",):
            raise HTTPException(status_code=400, detail="Only active loans can be cancelled")
    elif new_status == "defaulted":
        if loan.status not in ("active",):
            raise HTTPException(status_code=400, detail="Only active loans can be marked defaulted")
    else:
        raise HTTPException(status_code=400, detail="Invalid status transition")

    old = loan.status
    loan.status = new_status
    loan.updated_at = datetime.utcnow()
    log_activity(
        db,
        admin_id=admin_id,
        action="loan.status_changed",
        entity_type="loan",
        entity_id=loan.id,
        summary=f"Loan {loan.loan_number} status {old} → {new_status}",
    )
    db.commit()
    db.refresh(loan)
    return loan


def get_loan_detail(db: Session, loan_id: str) -> Loan:
    loan = db.scalar(
        select(Loan)
        .options(
            joinedload(Loan.organization),
            joinedload(Loan.emis),
            joinedload(Loan.payments),
        )
        .where(Loan.id == loan_id)
    )
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


def refresh_overdue_emis(db: Session) -> int:
    today = date.today()
    emis = db.scalars(
        select(EmiSchedule).where(
            EmiSchedule.status.in_(["pending", "partial", "overdue"]),
            EmiSchedule.due_date < today,
        )
    ).all()
    updated = 0
    for emi in emis:
        if emi.status != "paid" and emi.status != "overdue":
            remaining = money(emi.total_due - emi.amount_paid)
            if remaining > 0:
                emi.status = "overdue"
                updated += 1
        elif emi.status == "pending" and emi.due_date < today:
            emi.status = "overdue"
            updated += 1
    pending = db.scalars(
        select(EmiSchedule).where(EmiSchedule.status == "pending", EmiSchedule.due_date < today)
    ).all()
    for emi in pending:
        emi.status = "overdue"
        updated += 1
    db.commit()
    return updated
