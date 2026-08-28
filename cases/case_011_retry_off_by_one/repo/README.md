# PaymentGateway

Internal payment retry helper. Network calls to the card processor are
retried up to `max_attempts` times before failing the charge.

- `paygw/retry.py` — the retry wrapper.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```