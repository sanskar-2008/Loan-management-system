from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(150), default="Loan Management Co")
    company_address: Mapped[str | None] = mapped_column(Text)
    company_phone: Mapped[str | None] = mapped_column(String(30))
    logo_url: Mapped[str | None] = mapped_column(String(255))
    currency_code: Mapped[str] = mapped_column(String(3), default="INR")
    currency_symbol: Mapped[str] = mapped_column(String(5), default="₹")
    default_flat_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("12.0000"))
    default_compound_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("14.0000"))
    late_fee_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    late_fee_type: Mapped[str | None] = mapped_column(String(20), default="fixed")
    late_fee_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    overdue_alert_threshold_count: Mapped[int | None] = mapped_column(Integer, default=5)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
