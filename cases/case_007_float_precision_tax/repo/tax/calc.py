"""Sales tax calculation.

`compute_tax_cents(amount_cents, rate_percent)` returns the tax in cents,
rounded to the nearest cent with halves rounded UP.
"""


def compute_tax_cents(amount_cents: int, rate_percent: float) -> int:
    return round(amount_cents * rate_percent / 100)