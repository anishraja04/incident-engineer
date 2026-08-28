# TaxCalculator

Checkout service that computes sales tax on order amounts.

Business rule (from finance): tax is `amount * rate / 100`, rounded to the
nearest cent, **halves round up** (e.g. 8.5 cents -> 9 cents).

- `tax/calc.py` — the tax calculation.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```