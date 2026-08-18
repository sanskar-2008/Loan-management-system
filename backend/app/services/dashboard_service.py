from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.activity import ActivityLog
from app.models.emi import EmiSchedule
from app.models.loan import Loan
from app.models.organization import Organization
from app.models.payment import Payment
from app.services.interest import money


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_month(d: date, n: int = 1) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def _filter_loans(db: Session, organization_id: str | None = None):
    q = select(Loan)
    if organization_id:
        q = q.where(Loan.organization_id == organization_id)
    return db.scalars(q).all()


def dashboard_summary(
    db: Session, period: str = "mtd", organization_id: str | None = None
) -> dict:
    today = date.today()
    if period == "today":
        start = today
    elif period == "ytd":
        start = date(today.year, 1, 1)
    elif period == "all":
        start = None
    else:
        start = _month_start(today)

    loans = _filter_loans(db, organization_id)
    active = [l for l in loans if l.status == "active"]
    closed = [l for l in loans if l.status == "closed"]
    defaulted = [l for l in loans if l.status == "defaulted"]
    cancelled = [l for l in loans if l.status == "cancelled"]
    flat = [l for l in loans if l.loan_type == "flat" and l.status != "cancelled"]
    compound = [l for l in loans if l.loan_type == "compound" and l.status != "cancelled"]
    book = [l for l in loans if l.status != "cancelled"]
    loan_ids = {l.id for l in book}

    outstanding = money(sum((l.outstanding_balance for l in book), Decimal("0")))
    principal_disbursed = money(sum((l.principal_amount for l in book), Decimal("0")))
    interest_earned = money(sum((l.total_interest_paid for l in book), Decimal("0")))
    portfolio_value = money(sum((l.outstanding_balance + l.total_paid for l in book), Decimal("0")))
    total_paid = money(sum((l.total_paid for l in book), Decimal("0")))

    pay_q = select(Payment).where(Payment.is_voided.is_(False))
    if organization_id:
        pay_q = pay_q.join(Loan).where(Loan.organization_id == organization_id)
    if start is not None:
        pay_q = pay_q.where(Payment.payment_date >= start)
    period_payments = db.scalars(pay_q).unique().all()
    period_collections = money(sum((p.amount for p in period_payments), Decimal("0")))

    today_q = select(Payment).where(Payment.is_voided.is_(False), Payment.payment_date == today)
    if organization_id:
        today_q = today_q.join(Loan).where(Loan.organization_id == organization_id)
    today_collections = money(
        sum((p.amount for p in db.scalars(today_q).unique().all()), Decimal("0"))
    )

    overdue_q = select(EmiSchedule).where(
        EmiSchedule.status.in_(["overdue", "partial", "pending"])
    )
    if organization_id:
        overdue_q = overdue_q.join(Loan).where(Loan.organization_id == organization_id)
    overdue_emis = db.scalars(overdue_q).unique().all()
    overdue_amount = Decimal("0")
    overdue_loan_ids = set()
    for emi in overdue_emis:
        if emi.loan_id not in loan_ids and organization_id:
            continue
        if emi.due_date < today and emi.status != "paid":
            overdue_amount += money(emi.total_due - emi.amount_paid)
            overdue_loan_ids.add(emi.loan_id)
    overdue_amount = money(overdue_amount)

    orgs_active = db.scalar(
        select(Organization).where(Organization.status == "active").limit(1)
    )
    from sqlalchemy import func

    orgs_total = db.scalar(select(func.count()).select_from(Organization)) or 0
    orgs_active_count = (
        db.scalar(select(func.count()).select_from(Organization).where(Organization.status == "active"))
        or 0
    )

    avg_loan = money(principal_disbursed / len(book)) if book else Decimal("0.00")
    if book and principal_disbursed:
        weighted = sum((l.principal_amount * l.annual_interest_rate for l in book), Decimal("0"))
        avg_rate = (weighted / principal_disbursed).quantize(Decimal("0.0001"))
    else:
        avg_rate = Decimal("0")

    by_organization = _by_organization(db)

    return {
        "portfolio_value": portfolio_value,
        "outstanding_balance": outstanding,
        "total_principal_disbursed": principal_disbursed,
        "total_interest_earned": interest_earned,
        "total_paid": total_paid,
        "period_collections": period_collections,
        "today_collections": today_collections,
        "monthly_collections": period_collections if period == "mtd" else money(
            sum(
                (
                    p.amount
                    for p in db.scalars(
                        select(Payment).where(
                            Payment.is_voided.is_(False),
                            Payment.payment_date >= _month_start(today),
                        )
                    ).all()
                ),
                Decimal("0"),
            )
        ),
        "active_loans": len(active),
        "closed_loans": len(closed),
        "overdue_loans": len(overdue_loan_ids),
        "overdue_amount": overdue_amount,
        "defaulted_loans": len(defaulted),
        "cancelled_loans": len(cancelled),
        "flat_loans": len(flat),
        "compound_loans": len(compound),
        "total_organizations": orgs_total,
        "active_organizations": orgs_active_count,
        "average_loan_amount": avg_loan,
        "average_interest_rate": avg_rate,
        "period": period,
        "organization_id": organization_id,
        "by_organization": by_organization,
    }


def _by_organization(db: Session) -> list[dict]:
    today = date.today()
    orgs = db.scalars(select(Organization).order_by(Organization.name)).all()
    loans = db.scalars(select(Loan)).all()
    emis = db.scalars(select(EmiSchedule).where(EmiSchedule.status != "paid")).all()
    by_org_loans: dict[str, list] = {}
    for l in loans:
        by_org_loans.setdefault(l.organization_id, []).append(l)

    overdue_by_loan: dict[str, Decimal] = {}
    for emi in emis:
        if emi.due_date < today:
            overdue_by_loan[emi.loan_id] = money(
                overdue_by_loan.get(emi.loan_id, Decimal("0")) + (emi.total_due - emi.amount_paid)
            )

    rows = []
    for org in orgs:
        ols = by_org_loans.get(org.id, [])
        book = [l for l in ols if l.status != "cancelled"]
        if not book and org.code == "ORG-0000":
            # still show legacy if empty? skip empty orgs except we may want all with loans
            pass
        outstanding = money(sum((l.outstanding_balance for l in book), Decimal("0")))
        paid = money(sum((l.total_paid for l in book), Decimal("0")))
        overdue = money(
            sum((overdue_by_loan.get(l.id, Decimal("0")) for l in book), Decimal("0"))
        )
        if not book:
            continue
        rows.append(
            {
                "organization_id": org.id,
                "organization_code": org.code,
                "organization_name": org.name,
                "loan_count": len(book),
                "active_loans": sum(1 for l in book if l.status == "active"),
                "outstanding_balance": outstanding,
                "total_paid": paid,
                "overdue_amount": overdue,
            }
        )
    rows.sort(key=lambda r: r["outstanding_balance"], reverse=True)
    return rows


def dashboard_charts(db: Session, organization_id: str | None = None) -> dict:
    today = date.today()
    months = []
    start = _month_start(today)
    for i in range(11, -1, -1):
        m = _add_month(start, -i)
        months.append(m)

    loans = [l for l in _filter_loans(db, organization_id) if l.status != "cancelled"]
    loan_ids = {l.id for l in loans}

    pay_q = select(Payment).where(Payment.is_voided.is_(False))
    if organization_id:
        pay_q = pay_q.join(Loan).where(Loan.organization_id == organization_id)
    payments = db.scalars(pay_q).unique().all()

    emi_q = select(EmiSchedule)
    if organization_id:
        emi_q = emi_q.join(Loan).where(Loan.organization_id == organization_id)
    emis = db.scalars(emi_q).unique().all()

    disbursement = []
    collections = []
    due = []
    outstanding_trend = []

    for m in months:
        label = m.strftime("%Y-%m")
        next_m = _add_month(m, 1)
        disb = money(
            sum((l.principal_amount for l in loans if m <= l.disbursement_date < next_m), Decimal("0"))
        )
        coll = money(
            sum((p.amount for p in payments if m <= p.payment_date < next_m), Decimal("0"))
        )
        due_amt = money(
            sum((e.total_due for e in emis if m <= e.due_date < next_m), Decimal("0"))
        )
        paid_by = money(sum((p.amount for p in payments if p.payment_date < next_m), Decimal("0")))
        payable_by = money(
            sum((l.total_payable for l in loans if l.disbursement_date < next_m), Decimal("0"))
        )
        disbursement.append({"month": label, "amount": disb})
        collections.append({"month": label, "amount": coll})
        due.append({"month": label, "amount": due_amt})
        outstanding_trend.append({"month": label, "amount": money(max(payable_by - paid_by, Decimal("0")))})

    flat_count = sum(1 for l in loans if l.loan_type == "flat")
    compound_count = sum(1 for l in loans if l.loan_type == "compound")
    status_counts: dict[str, int] = {}
    for l in _filter_loans(db, organization_id):
        status_counts[l.status] = status_counts.get(l.status, 0) + 1

    aging = {"1-30": Decimal("0"), "31-60": Decimal("0"), "61-90": Decimal("0"), "90+": Decimal("0")}
    for emi in emis:
        if emi.status == "paid" or emi.due_date >= today:
            continue
        days = (today - emi.due_date).days
        rem = money(emi.total_due - emi.amount_paid)
        if days <= 30:
            aging["1-30"] += rem
        elif days <= 60:
            aging["31-60"] += rem
        elif days <= 90:
            aging["61-90"] += rem
        else:
            aging["90+"] += rem

    mtd_start = _month_start(today)
    mode_mix: dict[str, Decimal] = {}
    for p in payments:
        if p.payment_date >= mtd_start:
            mode_mix[p.payment_mode] = money(mode_mix.get(p.payment_mode, Decimal("0")) + p.amount)

    org_out: dict[str, Decimal] = {}
    org_names: dict[str, str] = {}
    orgs = {o.id: o for o in db.scalars(select(Organization)).all()}
    for l in loans:
        if l.status in ("active", "defaulted"):
            org_out[l.organization_id] = money(
                org_out.get(l.organization_id, Decimal("0")) + l.outstanding_balance
            )
    org_mix = [
        {"name": orgs[oid].name if oid in orgs else oid, "value": float(amt)}
        for oid, amt in sorted(org_out.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "disbursement_trend": disbursement,
        "collections_vs_due": {"collections": collections, "due": due},
        "outstanding_trend": outstanding_trend,
        "loan_type_mix": [
            {"name": "Flat", "value": flat_count},
            {"name": "Compound", "value": compound_count},
        ],
        "status_breakdown": [{"name": k, "value": v} for k, v in status_counts.items()],
        "overdue_aging": [{"name": k, "amount": money(v)} for k, v in aging.items()],
        "payment_mode_mix": [{"name": k, "value": v} for k, v in mode_mix.items()],
        "organization_mix": org_mix,
        "by_organization": _by_organization(db) if not organization_id else [],
    }


def dashboard_widgets(db: Session, organization_id: str | None = None) -> dict:
    today = date.today()
    loan_q = select(Loan).options(joinedload(Loan.organization)).order_by(Loan.created_at.desc())
    if organization_id:
        loan_q = loan_q.where(Loan.organization_id == organization_id)
    recent_loans = db.scalars(loan_q.limit(8)).unique().all()

    pay_q = (
        select(Payment)
        .options(joinedload(Payment.loan))
        .where(Payment.is_voided.is_(False))
        .order_by(Payment.created_at.desc())
    )
    if organization_id:
        pay_q = pay_q.join(Loan).where(Loan.organization_id == organization_id)
    recent_payments = db.scalars(pay_q.limit(8)).unique().all()

    up_q = (
        select(EmiSchedule)
        .options(joinedload(EmiSchedule.loan).joinedload(Loan.organization))
        .where(
            EmiSchedule.status.in_(["pending", "partial", "overdue"]),
            EmiSchedule.due_date >= today,
            EmiSchedule.due_date <= today + timedelta(days=30),
        )
        .order_by(EmiSchedule.due_date)
    )
    if organization_id:
        up_q = up_q.join(Loan).where(Loan.organization_id == organization_id)
    upcoming = db.scalars(up_q.limit(10)).unique().all()

    od_q = (
        select(EmiSchedule)
        .options(joinedload(EmiSchedule.loan).joinedload(Loan.organization))
        .where(EmiSchedule.due_date < today, EmiSchedule.status != "paid")
    )
    if organization_id:
        od_q = od_q.join(Loan).where(Loan.organization_id == organization_id)
    overdue_emis = db.scalars(od_q).unique().all()

    overdue_by_org: dict[str, dict] = {}
    for emi in overdue_emis:
        org = emi.loan.organization if emi.loan else None
        if not org:
            continue
        entry = overdue_by_org.setdefault(
            org.id,
            {
                "organization_id": org.id,
                "organization_name": org.name,
                "overdue_amount": Decimal("0"),
                "days": 0,
            },
        )
        rem = money(emi.total_due - emi.amount_paid)
        entry["overdue_amount"] = money(entry["overdue_amount"] + rem)
        entry["days"] = max(entry["days"], (today - emi.due_date).days)

    top_overdue = sorted(
        overdue_by_org.values(), key=lambda x: x["overdue_amount"], reverse=True
    )[:8]

    activities = db.scalars(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(12)
    ).all()

    return {
        "recent_loans": [
            {
                "id": l.id,
                "loan_number": l.loan_number,
                "organization_name": l.organization.name if l.organization else None,
                "principal_amount": l.principal_amount,
                "outstanding_balance": l.outstanding_balance,
                "total_paid": l.total_paid,
                "status": l.status,
                "loan_type": l.loan_type,
                "created_at": l.created_at,
            }
            for l in recent_loans
        ],
        "recent_payments": [
            {
                "id": p.id,
                "payment_number": p.payment_number,
                "loan_number": p.loan.loan_number if p.loan else None,
                "amount": p.amount,
                "payment_mode": p.payment_mode,
                "payment_date": p.payment_date,
            }
            for p in recent_payments
        ],
        "upcoming_emis": [
            {
                "id": e.id,
                "loan_id": e.loan_id,
                "loan_number": e.loan.loan_number if e.loan else None,
                "organization_name": (
                    e.loan.organization.name if e.loan and e.loan.organization else None
                ),
                "installment_no": e.installment_no,
                "due_date": e.due_date,
                "total_due": e.total_due,
                "amount_paid": e.amount_paid,
                "status": e.status,
            }
            for e in upcoming
        ],
        "top_overdue_organizations": top_overdue,
        "recent_activities": [
            {
                "id": a.id,
                "action": a.action,
                "summary": a.summary,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "created_at": a.created_at,
            }
            for a in activities
        ],
    }
