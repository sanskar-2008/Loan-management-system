from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_admin
from app.models.activity import ActivityLog
from app.models.admin import Admin
from app.schemas import ActivityOut
from app.utils.pagination import paginate

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("")
def list_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    total = db.scalar(select(func.count()).select_from(ActivityLog)) or 0
    items = db.scalars(
        select(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return paginate([ActivityOut.model_validate(i) for i in items], total, page, page_size)
