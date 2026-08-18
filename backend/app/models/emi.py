import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class EmiSchedule(Base):
    __tablename__ = "emi_schedules"
    __table_args__ = (UniqueConstraint("loan_id", "installment_no"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    loan_id: Mapped[str] = mapped_column(String(36), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    installment_no: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_component: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_component: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    loan = relationship("Loan", back_populates="emis")
    allocations = relationship("PaymentAllocation", back_populates="emi")
