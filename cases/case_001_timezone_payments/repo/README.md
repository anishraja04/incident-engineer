# RecurringPayments

Small internal service that schedules recurring payments for customers.

- `payments/scheduler.py` — decides whether a payment is due and computes the next run.
- `payments/models.py` — data model.
- `tests/` — unit tests.

Run tests with:

```bash
TZ=Asia/Kolkata python -m pytest -q
```