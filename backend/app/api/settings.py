from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.admin import Admin
from app.models.settings import Settings
from app.schemas import SettingsOut, SettingsUpdate
from app.services.activity_service import log_activity

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    settings = db.get(Settings, 1)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.put("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
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
