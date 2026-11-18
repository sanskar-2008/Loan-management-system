from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_admin, require_admin_write
from app.models.admin import Admin
from app.models.loan import Loan
from app.models.organization import Organization
from app.schemas import (
    EmiOut,
    LoanCreate,
    LoanNotesUpdate,
    LoanOut,
    LoanPreviewRequest,
    LoanStatusUpdate,
    PaymentOut,
)
from app.services import loan_service
from app.utils.pagination import paginate

router = APIRouter(prefix="/loans", tags=["loans"])


def _loan_out(loan: Loan) -> LoanOut:
    data = LoanOut.model_validate(loan)
    if loan.organization:
        data.organization_name = loan.organization.name
        data.organization_code = loan.organization.code
    return data


@router.get("")
def list_loans(
    q: str | None = None,
    status: str | None = None,
    loan_type: str | None = None,
    organization_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = select(Loan).options(joinedload(Loan.organization))
    if status:
        query = query.where(Loan.status == status)
    if loan_type:
        query = query.where(Loan.loan_type == loan_type)
    if organization_id:
        query = query.where(Loan.organization_id == organization_id)
    if date_from:
        query = query.where(Loan.disbursement_date >= date_from)
    if date_to:
        query = query.where(Loan.disbursement_date <= date_to)
    if q:
        like = f"%{q}%"
        query = query.join(Organization).where(
            or_(
                Loan.loan_number.ilike(like),
                Organization.name.ilike(like),
                Organization.code.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    items = db.scalars(
        query.order_by(Loan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).unique().all()
    return paginate([_loan_out(i) for i in items], total, page, page_size)


@router.post("/preview")
def preview_loan(body: LoanPreviewRequest, admin: Admin = Depends(get_current_admin)):
    calc = loan_service.preview_loan(
        loan_type=body.loan_type,
        principal_amount=body.principal_amount,
        annual_interest_rate=body.annual_interest_rate,
        tenure_months=body.tenure_months,
        disbursement_date=body.disbursement_date,
    )
    return {
        "emi_amount": calc.emi_amount,
        "total_interest": calc.total_interest,
        "total_payable": calc.total_payable,
        "schedule": [
            {
                "installment_no": r.installment_no,
                "due_date": r.due_date,
                "principal_component": r.principal_component,
                "interest_component": r.interest_component,
                "total_due": r.total_due,
            }
            for r in calc.schedule
        ],
    }


@router.post("", response_model=LoanOut, status_code=201)
def create_loan(
    body: LoanCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_write),
):
    loan = loan_service.create_loan(
        db,
        organization_id=body.organization_id,
        organization_name=body.organization_name,
        loan_type=body.loan_type,
        principal_amount=body.principal_amount,
        annual_interest_rate=body.annual_interest_rate,
        tenure_months=body.tenure_months,
        disbursement_date=body.disbursement_date,
        notes=body.notes,
        admin_id=admin.id,
    )
    loan = db.scalar(
        select(Loan).options(joinedload(Loan.organization)).where(Loan.id == loan.id)
    )
    return _loan_out(loan)


@router.get("/{loan_id}", response_model=LoanOut)
def get_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    loan = db.scalar(
        select(Loan).options(joinedload(Loan.organization)).where(Loan.id == loan_id)
    )
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return _loan_out(loan)


@router.patch("/{loan_id}", response_model=LoanOut)
def update_notes(
    loan_id: str,
    body: LoanNotesUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_write),
):
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    loan.notes = body.notes
    db.commit()
    loan = db.scalar(
        select(Loan).options(joinedload(Loan.organization)).where(Loan.id == loan_id)
    )
    return _loan_out(loan)


@router.patch("/{loan_id}/status", response_model=LoanOut)
def update_status(
    loan_id: str,
    body: LoanStatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_write),
):
    loan = loan_service.update_loan_status(db, loan_id, body.status, admin.id)
    loan = db.scalar(
        select(Loan).options(joinedload(Loan.organization)).where(Loan.id == loan.id)
    )
    return _loan_out(loan)


@router.get("/{loan_id}/emis")
def loan_emis(
    loan_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    loan = loan_service.get_loan_detail(db, loan_id)
    return [EmiOut.model_validate(e) for e in sorted(loan.emis, key=lambda x: x.installment_no)]


@router.get("/{loan_id}/payments")
def loan_payments(
    loan_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    loan = loan_service.get_loan_detail(db, loan_id)
    out = []
    for p in sorted(loan.payments, key=lambda x: x.created_at, reverse=True):
        row = PaymentOut.model_validate(p)
        row.loan_number = loan.loan_number
        out.append(row)
    return out
