from decimal import Decimal
from datetime import date

from app.services.interest import calculate_flat, calculate_compound, money


def test_flat_interest_basic():
    calc = calculate_flat(Decimal("100000"), Decimal("12"), 12, date(2024, 1, 1))
    assert calc.total_interest == money("12000")
    assert calc.total_payable == money("112000")
    assert len(calc.schedule) == 12
    assert sum((r.total_due for r in calc.schedule), Decimal("0")) == calc.total_payable


def test_compound_interest_basic():
    calc = calculate_compound(Decimal("100000"), Decimal("12"), 12, date(2024, 1, 1))
    assert len(calc.schedule) == 12
    assert calc.emi_amount > 0
    assert calc.total_payable > Decimal("100000")
    # last outstanding should be cleared
    assert calc.schedule[-1].principal_component > 0


def test_zero_rate_compound():
    calc = calculate_compound(Decimal("12000"), Decimal("0"), 12, date(2024, 1, 1))
    assert calc.emi_amount == money("1000")
    assert calc.total_interest == money("0")
