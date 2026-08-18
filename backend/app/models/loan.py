import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    loan_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )
    # Legacy column retained for SQLite migration compatibility; unused by product flows.
    borrower_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("borrowers.id"), nullable=True
    )
    loan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_interest_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    disbursement_date: Mapped[date] = mapped_column(Date, nullable=False)
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_interest: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_payable: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    total_interest_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("admins.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization = relationship("Organization", back_populates="loans")
    borrower = relationship("Borrower", back_populates="loans")
    created_by_admin = relationship("Admin", back_populates="loans")
    emis = relationship("EmiSchedule", back_populates="loan", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="loan")
