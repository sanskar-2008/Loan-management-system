from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/portfolio")
def portfolio(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return report_service.portfolio_report(db, organization_id)


@router.get("/collections")
def collections(
    date_from: date | None = None,
    date_to: date | None = None,
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return report_service.collections_report(db, date_from, date_to, organization_id)


@router.get("/overdue")
def overdue(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return report_service.overdue_report(db, organization_id)


@router.get("/interest-earned")
def interest_earned(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return report_service.interest_earned_report(db, organization_id)


@router.get("/organization-statement/{organization_id}")
def organization_statement(
    organization_id: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return report_service.organization_statement(db, organization_id)


@router.get("/export")
def export(
    type: str = Query(..., alias="type"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    content = report_service.export_csv(db, type, date_from, date_to)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{type}_report.csv"'},
    )
