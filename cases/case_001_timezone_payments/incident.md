# Incident case_001: Recurring payment scheduler crashes on worker ticks

**Severity:** P1 (payments processing halted)
**Service:** payments/scheduler
**Environment:** production, TZ=Asia/Kolkata
**Reported by:** on-call engineer, 2026-08-28

## Symptom

The recurring-payments worker stopped charging customers. The worker tick
crashes with:

```
TypeError: can't compare offset-naive and offset-aware datetimes
```

Customers whose subscriptions renew today have NOT been charged. The error
started after the scheduler was moved to the new hourly tick loop.

## Evidence

`logs/incident.log` contains the captured output of the failing test run —
the crash traceback points into `payments/scheduler.py`.

## What we know

- The service runs on a host with `TZ=Asia/Kolkata`.
- `payments/models.py` stores `next_run_at` as a timezone-aware UTC datetime.
- The scheduler computes "now" itself on the default path of `is_due`.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.