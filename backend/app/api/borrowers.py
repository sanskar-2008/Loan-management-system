from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.models.borrower import Borrower
from app.models.loan import Loan
from app.schemas import BorrowerCreate, BorrowerOut, BorrowerSummary, BorrowerUpdate, StatusUpdate
from app.services.activity_service import log_activity
from app.services.interest import money
from app.utils.codes import next_borrower_code
from app.utils.pagination import paginate

router = APIRouter(prefix="/borrowers", tags=["borrowers"])


@router.get("")
def list_borrowers(
    q: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: str = "created_at",
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = select(Borrower)
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(
                Borrower.full_name.ilike(like),
                Borrower.phone.ilike(like),
                Borrower.borrower_code.ilike(like),
                Borrower.email.ilike(like),
            )
        )
    if status:
        query = query.where(Borrower.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    sort_col = getattr(Borrower, sort, Borrower.created_at)
    items = db.scalars(
        query.order_by(sort_col.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return paginate([BorrowerOut.model_validate(i) for i in items], total, page, page_size)


@router.post("", response_model=BorrowerOut, status_code=201)
def create_borrower(
    body: BorrowerCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if db.scalar(select(Borrower).where(Borrower.phone == body.phone)):
        raise HTTPException(status_code=400, detail="Phone already exists")
    if body.email and db.scalar(select(Borrower).where(Borrower.email == str(body.email))):
        raise HTTPException(status_code=400, detail="Email already exists")
    borrower = Borrower(
        borrower_code=next_borrower_code(db),
        full_name=body.full_name,
        phone=body.phone,
        email=str(body.email) if body.email else None,
        address=body.address,
        id_proof_type=body.id_proof_type,
        id_proof_number=body.id_proof_number,
        notes=body.notes,
        status="active",
    )
    db.add(borrower)
    db.flush()
    log_activity(
        db,
        admin_id=admin.id,
        action="borrower.created",
        entity_type="borrower",
        entity_id=borrower.id,
        summary=f"Created borrower {borrower.borrower_code} — {borrower.full_name}",
    )
    db.commit()
    db.refresh(borrower)
    return borrower


@router.get("/{borrower_id}", response_model=BorrowerOut)
def get_borrower(
    borrower_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    borrower = db.get(Borrower, borrower_id)
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return borrower


@router.put("/{borrower_id}", response_model=BorrowerOut)
def update_borrower(
    borrower_id: str,
    body: BorrowerUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    borrower = db.get(Borrower, borrower_id)
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    existing_phone = db.scalar(
        select(Borrower).where(Borrower.phone == body.phone, Borrower.id != borrower_id)
    )
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone already exists")
    if body.email:
        existing_email = db.scalar(
            select(Borrower).where(Borrower.email == str(body.email), Borrower.id != borrower_id)
        )
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
    borrower.full_name = body.full_name
    borrower.phone = body.phone
    borrower.email = str(body.email) if body.email else None
    borrower.address = body.address
    borrower.id_proof_type = body.id_proof_type
    borrower.id_proof_number = body.id_proof_number
    borrower.notes = body.notes
    log_activity(
        db,
        admin_id=admin.id,
        action="borrower.updated",
        entity_type="borrower",
        entity_id=borrower.id,
        summary=f"Updated borrower {borrower.borrower_code}",
    )
    db.commit()
    db.refresh(borrower)
    return borrower


@router.patch("/{borrower_id}/status", response_model=BorrowerOut)
def update_status(
    borrower_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    borrower = db.get(Borrower, borrower_id)
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    if body.status == "inactive":
        active_loans = db.scalar(
            select(func.count())
            .select_from(Loan)
            .where(Loan.borrower_id == borrower_id, Loan.status == "active")
        ) or 0
        if active_loans:
            raise HTTPException(status_code=400, detail="Cannot deactivate borrower with active loans")
    borrower.status = body.status
    log_activity(
        db,
        admin_id=admin.id,
        action="borrower.deactivated" if body.status == "inactive" else "borrower.activated",
        entity_type="borrower",
        entity_id=borrower.id,
        summary=f"Borrower {borrower.borrower_code} set to {body.status}",
    )
    db.commit()
    db.refresh(borrower)
    return borrower


@router.get("/{borrower_id}/loans")
def borrower_loans(
    borrower_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if not db.get(Borrower, borrower_id):
        raise HTTPException(status_code=404, detail="Borrower not found")
    loans = db.scalars(select(Loan).where(Loan.borrower_id == borrower_id).order_by(Loan.created_at.desc())).all()
    return loans


@router.get("/{borrower_id}/summary", response_model=BorrowerSummary)
def borrower_summary(
    borrower_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if not db.get(Borrower, borrower_id):
        raise HTTPException(status_code=404, detail="Borrower not found")
    loans = db.scalars(select(Loan).where(Loan.borrower_id == borrower_id)).all()
    active = [l for l in loans if l.status == "active"]
    outstanding = money(sum((l.outstanding_balance for l in loans if l.status != "cancelled"), Decimal("0")))
    return BorrowerSummary(
        active_loans=len(active),
        total_loans=len(loans),
        outstanding_balance=outstanding,
    )
