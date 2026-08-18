import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    payment_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    loan_id: Mapped[str] = mapped_column(String(36), ForeignKey("loans.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_no: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("admins.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    loan = relationship("Loan", back_populates="payments")
    recorded_by_admin = relationship("Admin", back_populates="payments")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    payment_id: Mapped[str] = mapped_column(String(36), ForeignKey("payments.id"), nullable=False)
    emi_schedule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("emi_schedules.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_portion: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    payment = relationship("Payment", back_populates="allocations")
    emi = relationship("EmiSchedule", back_populates="allocations")
