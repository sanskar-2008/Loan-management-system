import csv
import io
from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.emi import EmiSchedule
from app.models.loan import Loan
from app.models.organization import Organization
from app.models.payment import Payment
from app.services.interest import money


def portfolio_report(db: Session, organization_id: str | None = None) -> dict:
    q = select(Loan).options(joinedload(Loan.organization))
    if organization_id:
        q = q.where(Loan.organization_id == organization_id)
    loans = db.scalars(q).unique().all()
    by_status: dict[str, dict] = {}
    by_type: dict[str, dict] = {}
    for loan in loans:
        s = by_status.setdefault(
            loan.status, {"count": 0, "principal": Decimal("0"), "outstanding": Decimal("0")}
        )
        s["count"] += 1
        s["principal"] = money(s["principal"] + loan.principal_amount)
        s["outstanding"] = money(s["outstanding"] + loan.outstanding_balance)
        t = by_type.setdefault(
            loan.loan_type, {"count": 0, "principal": Decimal("0"), "outstanding": Decimal("0")}
        )
        t["count"] += 1
        t["principal"] = money(t["principal"] + loan.principal_amount)
        t["outstanding"] = money(t["outstanding"] + loan.outstanding_balance)
    return {
        "by_status": by_status,
        "by_type": by_type,
        "loans": [
            {
                "loan_number": l.loan_number,
                "organization_name": l.organization.name if l.organization else None,
                "loan_type": l.loan_type,
                "principal_amount": l.principal_amount,
                "outstanding_balance": l.outstanding_balance,
                "status": l.status,
                "disbursement_date": l.disbursement_date,
            }
            for l in loans
        ],
    }


def collections_report(
    db: Session,
    date_from: date | None,
    date_to: date | None,
    organization_id: str | None = None,
) -> dict:
    q = select(Payment).options(joinedload(Payment.loan)).where(Payment.is_voided.is_(False))
    if organization_id:
        q = q.join(Loan).where(Loan.organization_id == organization_id)
    if date_from:
        q = q.where(Payment.payment_date >= date_from)
    if date_to:
        q = q.where(Payment.payment_date <= date_to)
    payments = db.scalars(q.order_by(Payment.payment_date.desc())).unique().all()
    by_mode: dict[str, Decimal] = {}
    total = Decimal("0")
    rows = []
    for p in payments:
        by_mode[p.payment_mode] = money(by_mode.get(p.payment_mode, Decimal("0")) + p.amount)
        total += p.amount
        rows.append(
            {
                "payment_number": p.payment_number,
                "loan_number": p.loan.loan_number if p.loan else None,
                "amount": p.amount,
                "payment_date": p.payment_date,
                "payment_mode": p.payment_mode,
                "reference_no": p.reference_no,
            }
        )
    return {"total": money(total), "by_mode": by_mode, "payments": rows}


def overdue_report(db: Session, organization_id: str | None = None) -> dict:
    today = date.today()
    q = (
        select(EmiSchedule)
        .options(joinedload(EmiSchedule.loan).joinedload(Loan.organization))
        .where(EmiSchedule.due_date < today, EmiSchedule.status != "paid")
    )
    if organization_id:
        q = q.join(Loan).where(Loan.organization_id == organization_id)
    emis = db.scalars(q).unique().all()
    aging: dict[str, list] = {"1-30": [], "31-60": [], "61-90": [], "90+": []}
    total = Decimal("0")
    for emi in emis:
        days = (today - emi.due_date).days
        rem = money(emi.total_due - emi.amount_paid)
        total += rem
        row = {
            "loan_number": emi.loan.loan_number if emi.loan else None,
            "organization_name": (
                emi.loan.organization.name if emi.loan and emi.loan.organization else None
            ),
            "installment_no": emi.installment_no,
            "due_date": emi.due_date,
            "days_overdue": days,
            "remaining": rem,
        }
        if days <= 30:
            aging["1-30"].append(row)
        elif days <= 60:
            aging["31-60"].append(row)
        elif days <= 90:
            aging["61-90"].append(row)
        else:
            aging["90+"].append(row)
    return {"total_overdue": money(total), "aging": aging}


def interest_earned_report(db: Session, organization_id: str | None = None) -> dict:
    q = select(Loan)
    if organization_id:
        q = q.where(Loan.organization_id == organization_id)
    loans = db.scalars(q).all()
    total = money(sum((l.total_interest_paid for l in loans), Decimal("0")))
    return {
        "total_interest_earned": total,
        "by_loan": [
            {
                "loan_number": l.loan_number,
                "loan_type": l.loan_type,
                "total_interest": l.total_interest,
                "interest_paid": l.total_interest_paid,
            }
            for l in loans
            if money(l.total_interest_paid) > 0
        ],
    }


def organization_statement(db: Session, organization_id: str) -> dict:
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    loans = db.scalars(
        select(Loan)
        .options(joinedload(Loan.emis), joinedload(Loan.payments))
        .where(Loan.organization_id == organization_id)
        .order_by(Loan.created_at)
    ).unique().all()

    amount_taken = money(sum((l.principal_amount for l in loans), Decimal("0")))
    amount_repaid = money(sum((l.total_paid for l in loans), Decimal("0")))
    remaining = money(sum((l.outstanding_balance for l in loans), Decimal("0")))

    repayment_history = []
    for l in loans:
        for p in sorted(l.payments, key=lambda x: (x.payment_date, x.created_at)):
            repayment_history.append(
                {
                    "payment_number": p.payment_number,
                    "loan_number": l.loan_number,
                    "amount": p.amount,
                    "payment_date": p.payment_date,
                    "payment_mode": p.payment_mode,
                    "reference_no": p.reference_no,
                    "is_voided": p.is_voided,
                    "void_reason": p.void_reason,
                }
            )
    repayment_history.sort(key=lambda r: (r["payment_date"], r["payment_number"]))

    return {
        "organization": {
            "id": org.id,
            "code": org.code,
            "name": org.name,
            "contact_phone": org.contact_phone,
            "contact_email": org.contact_email,
            "notes": org.notes,
            "status": org.status,
        },
        "loans": [
            {
                "id": l.id,
                "loan_number": l.loan_number,
                "loan_type": l.loan_type,
                "principal_amount": l.principal_amount,
                "annual_interest_rate": l.annual_interest_rate,
                "tenure_months": l.tenure_months,
                "outstanding_balance": l.outstanding_balance,
                "total_paid": l.total_paid,
                "total_payable": l.total_payable,
                "status": l.status,
                "disbursement_date": l.disbursement_date,
            }
            for l in loans
        ],
        "repayment_history": repayment_history,
        "totals": {
            "amount_taken": amount_taken,
            "amount_repaid": amount_repaid,
            "remaining_outstanding": remaining,
            "loan_count": len(loans),
        },
    }


def export_csv(
    db: Session,
    report_type: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    if report_type == "portfolio":
        data = portfolio_report(db)
        writer.writerow(
            ["loan_number", "organization", "type", "principal", "outstanding", "status", "disbursement_date"]
        )
        for row in data["loans"]:
            writer.writerow(
                [
                    row["loan_number"],
                    row["organization_name"],
                    row["loan_type"],
                    row["principal_amount"],
                    row["outstanding_balance"],
                    row["status"],
                    row["disbursement_date"],
                ]
            )
    elif report_type == "collections":
        data = collections_report(db, date_from, date_to)
        writer.writerow(["payment_number", "loan_number", "amount", "date", "mode", "reference"])
        for row in data["payments"]:
            writer.writerow(
                [
                    row["payment_number"],
                    row["loan_number"],
                    row["amount"],
                    row["payment_date"],
                    row["payment_mode"],
                    row["reference_no"],
                ]
            )
    elif report_type == "overdue":
        data = overdue_report(db)
        writer.writerow(
            ["bucket", "loan_number", "organization", "installment", "due_date", "days", "remaining"]
        )
        for bucket, rows in data["aging"].items():
            for row in rows:
                writer.writerow(
                    [
                        bucket,
                        row["loan_number"],
                        row["organization_name"],
                        row["installment_no"],
                        row["due_date"],
                        row["days_overdue"],
                        row["remaining"],
                    ]
                )
    elif report_type == "interest":
        data = interest_earned_report(db)
        writer.writerow(["loan_number", "type", "total_interest", "interest_paid"])
        for row in data["by_loan"]:
            writer.writerow(
                [row["loan_number"], row["loan_type"], row["total_interest"], row["interest_paid"]]
            )
    else:
        raise HTTPException(status_code=400, detail="Unknown report type")
    return output.getvalue()
