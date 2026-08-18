from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


TWOPLACES = Decimal("0.01")


def money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def add_months(start: date, months: int) -> date:
    month = start.month - 1 + months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


@dataclass
class EmiRow:
    installment_no: int
    due_date: date
    principal_component: Decimal
    interest_component: Decimal
    total_due: Decimal


@dataclass
class LoanCalculation:
    emi_amount: Decimal
    total_interest: Decimal
    total_payable: Decimal
    schedule: list[EmiRow]


def calculate_flat(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    disbursement_date: date,
) -> LoanCalculation:
    principal = money(principal)
    annual_rate = Decimal(str(annual_rate))
    total_interest = money(principal * (annual_rate / Decimal("100")) * (Decimal(tenure_months) / Decimal("12")))
    total_payable = money(principal + total_interest)
    base_emi = money(total_payable / Decimal(tenure_months))

    interest_each = money(total_interest / Decimal(tenure_months))
    schedule: list[EmiRow] = []
    interest_allocated = Decimal("0.00")
    principal_allocated = Decimal("0.00")
    payable_allocated = Decimal("0.00")

    for i in range(1, tenure_months + 1):
        if i == tenure_months:
            interest_comp = money(total_interest - interest_allocated)
            total_due = money(total_payable - payable_allocated)
            principal_comp = money(total_due - interest_comp)
        else:
            interest_comp = interest_each
            total_due = base_emi
            principal_comp = money(total_due - interest_comp)
            interest_allocated += interest_comp
            principal_allocated += principal_comp
            payable_allocated += total_due

        schedule.append(
            EmiRow(
                installment_no=i,
                due_date=add_months(disbursement_date, i),
                principal_component=principal_comp,
                interest_component=interest_comp,
                total_due=total_due,
            )
        )

    return LoanCalculation(
        emi_amount=base_emi,
        total_interest=total_interest,
        total_payable=total_payable,
        schedule=schedule,
    )


def calculate_compound(
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    disbursement_date: date,
) -> LoanCalculation:
    principal = money(principal)
    annual_rate = Decimal(str(annual_rate))
    r = (annual_rate / Decimal("100")) / Decimal("12")
    n = tenure_months

    if r == 0:
        emi = money(principal / Decimal(n))
    else:
        factor = (Decimal("1") + r) ** n
        emi = money(principal * r * factor / (factor - Decimal("1")))

    schedule: list[EmiRow] = []
    outstanding = principal
    total_interest = Decimal("0.00")

    for i in range(1, n + 1):
        interest_comp = money(outstanding * r)
        if i == n:
            principal_comp = money(outstanding)
            total_due = money(principal_comp + interest_comp)
        else:
            principal_comp = money(emi - interest_comp)
            if principal_comp > outstanding:
                principal_comp = money(outstanding)
            total_due = money(principal_comp + interest_comp)

        outstanding = money(outstanding - principal_comp)
        if outstanding < Decimal("0.00"):
            outstanding = Decimal("0.00")
        total_interest += interest_comp

        schedule.append(
            EmiRow(
                installment_no=i,
                due_date=add_months(disbursement_date, i),
                principal_component=principal_comp,
                interest_component=interest_comp,
                total_due=total_due,
            )
        )

    total_payable = money(principal + total_interest)
    return LoanCalculation(
        emi_amount=emi,
        total_interest=money(total_interest),
        total_payable=total_payable,
        schedule=schedule,
    )


def calculate_loan(
    loan_type: str,
    principal: Decimal,
    annual_rate: Decimal,
    tenure_months: int,
    disbursement_date: date,
) -> LoanCalculation:
    if loan_type == "flat":
        return calculate_flat(principal, annual_rate, tenure_months, disbursement_date)
    if loan_type == "compound":
        return calculate_compound(principal, annual_rate, tenure_months, disbursement_date)
    raise ValueError("loan_type must be 'flat' or 'compound'")
