from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(
    period: str = Query("mtd", pattern="^(today|mtd|ytd|all)$"),
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return dashboard_service.dashboard_summary(db, period, organization_id)


@router.get("/charts")
def charts(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return dashboard_service.dashboard_charts(db, organization_id)


@router.get("/widgets")
def widgets(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return dashboard_service.dashboard_widgets(db, organization_id)
