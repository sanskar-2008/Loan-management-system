"""
Payment / repayment service.

Route and table names stay `payments` for backward compatibility; UI copy displays this as
"Repayment".

Payments now represent repayments we make toward EMIs we owe (not collections from a customer).
FIFO still means: apply to the oldest unpaid EMI first. Do not reinterpret this as inbound
collection logic.
"""

from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.emi import EmiSchedule
from app.models.loan import Loan
from app.models.payment import Payment, PaymentAllocation
from app.services.activity_service import log_activity
from app.services.interest import money
from app.utils.codes import next_payment_number


def _emi_remaining(emi: EmiSchedule) -> Decimal:
    return money(emi.total_due - emi.amount_paid)


def _set_emi_status(emi: EmiSchedule) -> None:
    remaining = _emi_remaining(emi)
    if remaining <= Decimal("0.00"):
        emi.status = "paid"
        emi.amount_paid = money(emi.total_due)
        emi.paid_at = datetime.utcnow()
    elif emi.amount_paid > Decimal("0.00"):
        emi.status = "overdue" if emi.due_date < date.today() else "partial"
        emi.paid_at = None
    else:
        emi.status = "overdue" if emi.due_date < date.today() else "pending"
        emi.paid_at = None


def _recompute_loan_balances(db: Session, loan: Loan) -> None:
    emis = db.scalars(
        select(EmiSchedule).where(EmiSchedule.loan_id == loan.id).order_by(EmiSchedule.installment_no)
    ).all()
    total_paid = Decimal("0.00")
    interest_paid = Decimal("0.00")

    payments = db.scalars(
        select(Payment)
        .options(joinedload(Payment.allocations))
        .where(Payment.loan_id == loan.id, Payment.is_voided.is_(False))
    ).unique().all()

    for payment in payments:
        total_paid += money(payment.amount)
        for alloc in payment.allocations:
            interest_paid += money(alloc.interest_portion)

    for emi in emis:
        emi.amount_paid = Decimal("0.00")

    for payment in payments:
        for alloc in payment.allocations:
            emi = next((e for e in emis if e.id == alloc.emi_schedule_id), None)
            if emi:
                emi.amount_paid = money(emi.amount_paid + alloc.amount)

    for emi in emis:
        _set_emi_status(emi)

    loan.total_paid = money(total_paid)
    loan.total_interest_paid = money(interest_paid)
    loan.outstanding_balance = money(loan.total_payable - total_paid)
    if loan.outstanding_balance < Decimal("0.00"):
        loan.outstanding_balance = Decimal("0.00")

    if loan.outstanding_balance == Decimal("0.00") and loan.status in ("active", "defaulted"):
        loan.status = "closed"
        loan.closed_at = datetime.utcnow()
    elif loan.status == "closed" and loan.outstanding_balance > Decimal("0.00"):
        loan.status = "active"
        loan.closed_at = None


def record_payment(
    db: Session,
    *,
    loan_id: str,
    amount: Decimal,
    payment_date: date,
    payment_mode: str,
    reference_no: str | None,
    notes: str | None,
    emi_schedule_id: str | None,
    admin_id: str,
) -> Payment:
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status not in ("active", "defaulted"):
        raise HTTPException(status_code=400, detail="Payments allowed only on active or defaulted loans")
    if payment_date < loan.disbursement_date:
        raise HTTPException(status_code=400, detail="Payment date cannot be before disbursement date")

    amount = money(amount)
    if amount <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
    if amount > money(loan.outstanding_balance):
        raise HTTPException(status_code=400, detail="Amount exceeds outstanding balance")

    emis = db.scalars(
        select(EmiSchedule)
        .where(EmiSchedule.loan_id == loan_id)
        .order_by(EmiSchedule.installment_no)
    ).all()

    targets: list[EmiSchedule] = []
    if emi_schedule_id:
        target = next((e for e in emis if e.id == emi_schedule_id), None)
        if not target:
            raise HTTPException(status_code=400, detail="EMI does not belong to this loan")
        if target.status == "paid":
            raise HTTPException(status_code=400, detail="EMI is already paid")
        targets = [target] + [e for e in emis if e.id != target.id and e.status != "paid"]
    else:
        # FIFO: oldest unpaid EMI first (repayment toward EMIs we owe)
        targets = [e for e in emis if e.status != "paid"]

    remaining_to_allocate = amount
    allocations_data: list[tuple[EmiSchedule, Decimal, Decimal, Decimal]] = []

    for emi in targets:
        if remaining_to_allocate <= Decimal("0.00"):
            break
        emi_remaining = _emi_remaining(emi)
        if emi_remaining <= Decimal("0.00"):
            continue
        apply_amt = money(min(remaining_to_allocate, emi_remaining))

        paid_so_far = money(emi.amount_paid)
        if paid_so_far >= emi.interest_component:
            interest_remaining = Decimal("0.00")
        else:
            interest_remaining = money(emi.interest_component - paid_so_far)

        interest_portion = money(min(apply_amt, interest_remaining))
        principal_portion = money(apply_amt - interest_portion)

        allocations_data.append((emi, apply_amt, principal_portion, interest_portion))
        emi.amount_paid = money(emi.amount_paid + apply_amt)
        _set_emi_status(emi)
        remaining_to_allocate = money(remaining_to_allocate - apply_amt)

    if remaining_to_allocate > Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Unable to allocate full payment amount")

    payment = Payment(
        payment_number=next_payment_number(db),
        loan_id=loan_id,
        amount=amount,
        payment_date=payment_date,
        payment_mode=payment_mode,
        reference_no=reference_no,
        notes=notes,
        recorded_by=admin_id,
        is_voided=False,
    )
    db.add(payment)
    db.flush()

    for emi, apply_amt, principal_portion, interest_portion in allocations_data:
        db.add(
            PaymentAllocation(
                payment_id=payment.id,
                emi_schedule_id=emi.id,
                amount=apply_amt,
                principal_portion=principal_portion,
                interest_portion=interest_portion,
            )
        )

    _recompute_loan_balances(db, loan)

    log_activity(
        db,
        admin_id=admin_id,
        action="payment.recorded",
        entity_type="payment",
        entity_id=payment.id,
        summary=f"Recorded repayment {payment.payment_number} of {amount} on {loan.loan_number}",
    )
    db.commit()
    db.refresh(payment)
    return payment


def void_payment(db: Session, payment_id: str, reason: str, admin_id: str) -> Payment:
    payment = db.scalar(
        select(Payment)
        .options(joinedload(Payment.allocations), joinedload(Payment.loan))
        .where(Payment.id == payment_id)
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.is_voided:
        raise HTTPException(status_code=400, detail="Payment already voided")

    payment.is_voided = True
    payment.voided_at = datetime.utcnow()
    payment.void_reason = reason

    loan = payment.loan
    _recompute_loan_balances(db, loan)

    log_activity(
        db,
        admin_id=admin_id,
        action="payment.voided",
        entity_type="payment",
        entity_id=payment.id,
        summary=f"Voided repayment {payment.payment_number}: {reason}",
    )
    db.commit()
    db.refresh(payment)
    return payment
