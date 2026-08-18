from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.models.loan import Loan
from app.models.organization import Organization
from app.schemas import (
    OrganizationCreate,
    OrganizationOut,
    OrganizationSummary,
    OrganizationUpdate,
    StatusUpdate,
)
from app.services.activity_service import log_activity
from app.services.interest import money
from app.utils.codes import next_organization_code
from app.utils.pagination import paginate

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("")
def list_organizations(
    q: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: str = "created_at",
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    query = select(Organization)
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(
                Organization.name.ilike(like),
                Organization.code.ilike(like),
                Organization.contact_phone.ilike(like),
                Organization.contact_email.ilike(like),
            )
        )
    if status:
        query = query.where(Organization.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    sort_col = getattr(Organization, sort, Organization.created_at)
    items = db.scalars(
        query.order_by(sort_col.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return paginate([OrganizationOut.model_validate(i) for i in items], total, page, page_size)


@router.post("", response_model=OrganizationOut, status_code=201)
def create_organization(
    body: OrganizationCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    org = Organization(
        code=next_organization_code(db),
        name=body.name.strip(),
        contact_phone=body.contact_phone,
        contact_email=str(body.contact_email) if body.contact_email else None,
        notes=body.notes,
        default_flat_rate=body.default_flat_rate,
        default_compound_rate=body.default_compound_rate,
        status="active",
    )
    db.add(org)
    db.flush()
    log_activity(
        db,
        admin_id=admin.id,
        action="organization.created",
        entity_type="organization",
        entity_id=org.id,
        summary=f"Created organization {org.code} — {org.name}",
    )
    db.commit()
    db.refresh(org)
    return org


@router.get("/{organization_id}", response_model=OrganizationOut)
def get_organization(
    organization_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/{organization_id}", response_model=OrganizationOut)
def update_organization(
    organization_id: str,
    body: OrganizationUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    new_status = body.status if body.status is not None else org.status
    if new_status == "inactive" and org.status != "inactive":
        active_outstanding = db.scalars(
            select(Loan).where(
                Loan.organization_id == organization_id,
                Loan.status == "active",
                Loan.outstanding_balance > 0,
            )
        ).first()
        if active_outstanding:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate — organization has active loans with outstanding balance",
            )

    org.name = body.name.strip()
    org.contact_phone = body.contact_phone
    org.contact_email = str(body.contact_email) if body.contact_email else None
    org.notes = body.notes
    org.default_flat_rate = body.default_flat_rate
    org.default_compound_rate = body.default_compound_rate
    if body.status is not None:
        org.status = body.status

    log_activity(
        db,
        admin_id=admin.id,
        action="organization.updated",
        entity_type="organization",
        entity_id=org.id,
        summary=f"Updated organization {org.code}",
    )
    db.commit()
    db.refresh(org)
    return org


@router.patch("/{organization_id}/status", response_model=OrganizationOut)
def update_organization_status(
    organization_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if body.status == "inactive":
        active_outstanding = db.scalars(
            select(Loan).where(
                Loan.organization_id == organization_id,
                Loan.status == "active",
                Loan.outstanding_balance > 0,
            )
        ).first()
        if active_outstanding:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate — organization has active loans with outstanding balance",
            )
    org.status = body.status
    log_activity(
        db,
        admin_id=admin.id,
        action="organization.deactivated" if body.status == "inactive" else "organization.activated",
        entity_type="organization",
        entity_id=org.id,
        summary=f"Organization {org.code} set to {body.status}",
    )
    db.commit()
    db.refresh(org)
    return org


@router.get("/{organization_id}/loans")
def organization_loans(
    organization_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if not db.get(Organization, organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    loans = db.scalars(
        select(Loan).where(Loan.organization_id == organization_id).order_by(Loan.created_at.desc())
    ).all()
    from app.api.loans import _loan_out

    return [_loan_out(l) for l in loans]


@router.get("/{organization_id}/summary", response_model=OrganizationSummary)
def organization_summary(
    organization_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if not db.get(Organization, organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    loans = db.scalars(select(Loan).where(Loan.organization_id == organization_id)).all()
    active = [l for l in loans if l.status == "active"]
    return OrganizationSummary(
        active_loans=len(active),
        total_loans=len(loans),
        outstanding_balance=money(sum((l.outstanding_balance for l in loans), Decimal("0"))),
        total_paid=money(sum((l.total_paid for l in loans), Decimal("0"))),
        principal_taken=money(sum((l.principal_amount for l in loans), Decimal("0"))),
    )
