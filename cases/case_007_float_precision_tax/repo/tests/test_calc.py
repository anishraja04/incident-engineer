import pytest

from tax.calc import compute_tax_cents


@pytest.mark.parametrize(
    "amount_cents,rate_percent,expected",
    [
        (1999, 7.25, 145),
        (899, 18.0, 162),
        (149, 9.99, 15),
        (3456, 2.5, 86),
        (100, 10.0, 10),
        (131, 5.0, 7),
    ],
)
def test_tax_rounded_to_nearest_cent(amount_cents, rate_percent, expected):
    assert compute_tax_cents(amount_cents, rate_percent) == expected


@pytest.mark.parametrize(
    "amount_cents,rate_percent,expected",
    [
        (50, 1.0, 1),      # 0.5 cents -> rounds UP to 1
        (85, 10.0, 9),     # 8.5 cents -> rounds UP to 9
        (225, 10.0, 23),   # 22.5 cents -> rounds UP to 23
        (260, 2.5, 7),     # 6.5 cents -> rounds UP to 7
        (232, 6.25, 15),   # 14.5 cents -> rounds UP to 15
    ],
)
def test_half_cents_round_up(amount_cents, rate_percent, expected):
    """Finance rule: halves round UP, never to the nearest even number."""
    assert compute_tax_cents(amount_cents, rate_percent) == expected


def test_zero_tax():
    assert compute_tax_cents(0, 10.0) == 0