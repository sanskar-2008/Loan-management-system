from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin, require_admin_write
from app.models.admin import Admin
from app.models.settings import Settings
from app.schemas import SettingsOut, SettingsUpdate
from app.services.activity_service import log_activity

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if getattr(admin, "is_demo", False):
        return SettingsOut(
            id=1,
            company_name="Loan Manager Demo",
            company_address="Sample workspace",
            company_phone=None,
            logo_url=None,
            currency_code="INR",
            currency_symbol="₹",
            default_flat_rate=12,
            default_compound_rate=14,
            late_fee_enabled=False,
            late_fee_type="fixed",
            late_fee_value=0,
            overdue_alert_threshold_count=5,
        )
    settings = db.get(Settings, 1)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.put("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_write),
):
    settings = db.get(Settings, 1)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(settings, key, value)
    settings.updated_at = datetime.utcnow()
    log_activity(
        db,
        admin_id=admin.id,
        action="settings.updated",
        entity_type="settings",
        entity_id="1",
        summary="Updated system settings",
    )
    db.commit()
    db.refresh(settings)
    return settings
