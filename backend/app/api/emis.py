from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.models.emi import EmiSchedule
from app.models.loan import Loan
from app.services import loan_service
from app.utils.pagination import paginate

router = APIRouter(prefix="/emis", tags=["emis"])


@router.get("")
def list_emis(
    status: str | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    loan_id: str | None = None,
    organization_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = select(EmiSchedule).options(
        joinedload(EmiSchedule.loan).joinedload(Loan.organization)
    )
    if status:
        query = query.where(EmiSchedule.status == status)
    if due_from:
        query = query.where(EmiSchedule.due_date >= due_from)
    if due_to:
        query = query.where(EmiSchedule.due_date <= due_to)
    if loan_id:
        query = query.where(EmiSchedule.loan_id == loan_id)
    if organization_id:
        query = query.join(Loan).where(Loan.organization_id == organization_id)
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    items = db.scalars(
        query.order_by(EmiSchedule.due_date).offset((page - 1) * page_size).limit(page_size)
    ).unique().all()
    rows = [
        {
            "id": e.id,
            "loan_id": e.loan_id,
            "loan_number": e.loan.loan_number if e.loan else None,
            "organization_name": (
                e.loan.organization.name if e.loan and e.loan.organization else None
            ),
            "installment_no": e.installment_no,
            "due_date": e.due_date,
            "principal_component": e.principal_component,
            "interest_component": e.interest_component,
            "total_due": e.total_due,
            "amount_paid": e.amount_paid,
            "status": e.status,
            "paid_at": e.paid_at,
        }
        for e in items
    ]
    return paginate(rows, total, page, page_size)


@router.get("/{emi_id}")
def get_emi(
    emi_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    emi = db.get(EmiSchedule, emi_id)
    if not emi:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="EMI not found")
    return emi


@router.post("/refresh-overdue")
def refresh_overdue(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    updated = loan_service.refresh_overdue_emis(db)
    return {"updated": updated}
