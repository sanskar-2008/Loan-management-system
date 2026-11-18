from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_admin, require_admin_write
from app.models.admin import Admin
from app.models.loan import Loan
from app.models.payment import Payment
from app.schemas import AllocationOut, PaymentCreate, PaymentOut, PaymentVoidRequest
from app.services import payment_service
from app.utils.pagination import paginate

router = APIRouter(prefix="/payments", tags=["payments"])


def _payment_out(payment: Payment) -> PaymentOut:
    out = PaymentOut.model_validate(payment)
    if payment.loan:
        out.loan_number = payment.loan.loan_number
    return out


@router.get("")
def list_payments(
    loan_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    mode: str | None = None,
    include_voided: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = select(Payment).options(joinedload(Payment.loan))
    if not include_voided:
        query = query.where(Payment.is_voided.is_(False))
    if loan_id:
        query = query.where(Payment.loan_id == loan_id)
    if date_from:
        query = query.where(Payment.payment_date >= date_from)
    if date_to:
        query = query.where(Payment.payment_date <= date_to)
    if mode:
        query = query.where(Payment.payment_mode == mode)
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    items = db.scalars(
        query.order_by(Payment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).unique().all()
    return paginate([_payment_out(i) for i in items], total, page, page_size)


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(
    body: PaymentCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_write),
):
    payment = payment_service.record_payment(
        db,
        loan_id=body.loan_id,
        amount=body.amount,
        payment_date=body.payment_date,
        payment_mode=body.payment_mode,
        reference_no=body.reference_no,
        notes=body.notes,
        emi_schedule_id=body.emi_schedule_id,
        admin_id=admin.id,
    )
    payment = db.scalar(
        select(Payment).options(joinedload(Payment.loan)).where(Payment.id == payment.id)
    )
    return _payment_out(payment)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    payment = db.scalar(
        select(Payment).options(joinedload(Payment.loan)).where(Payment.id == payment_id)
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _payment_out(payment)


@router.post("/{payment_id}/void", response_model=PaymentOut)
def void_payment(
    payment_id: str,
    body: PaymentVoidRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_write),
):
    payment = payment_service.void_payment(db, payment_id, body.reason, admin.id)
    payment = db.scalar(
        select(Payment).options(joinedload(Payment.loan)).where(Payment.id == payment.id)
    )
    return _payment_out(payment)


@router.get("/{payment_id}/allocations", response_model=list[AllocationOut])
def get_allocations(
    payment_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment.allocations
