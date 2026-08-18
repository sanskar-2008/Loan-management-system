from datetime import datetime

from sqlalchemy.orm import Session

from app.models.activity import ActivityLog


def log_activity(
    db: Session,
    *,
    admin_id: str | None,
    action: str,
    summary: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata_json=metadata,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    return entry
