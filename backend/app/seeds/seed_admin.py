from decimal import Decimal

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, engine, Base
from app.models import Admin, Organization, Settings  # noqa: F401 — ensure models registered
from app.utils.security import hash_password


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    db = SessionLocal()
    try:
        admin = db.scalar(select(Admin).where(Admin.username == settings.admin_username))
        if not admin:
            admin = db.scalar(select(Admin).where(Admin.email == settings.admin_email))
        if not admin:
            admin = Admin(
                username=settings.admin_username,
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                full_name=settings.admin_full_name,
                is_active=True,
            )
            db.add(admin)

        app_settings = db.get(Settings, 1)
        if not app_settings:
            db.add(
                Settings(
                    id=1,
                    company_name="Loan Management Co",
                    company_address="",
                    company_phone="",
                    currency_code="INR",
                    currency_symbol="₹",
                    default_flat_rate=Decimal("12.0000"),
                    default_compound_rate=Decimal("14.0000"),
                    late_fee_enabled=False,
                    late_fee_type="fixed",
                    late_fee_value=Decimal("0.00"),
                    overdue_alert_threshold_count=5,
                )
            )
        db.commit()
    finally:
        db.close()
