# Incident case_011: Payment retry makes one extra charge attempt

**Severity:** P1 (extra billable charge attempts)
**Service:** paygw/retry
**Reported by:** payments platform team, 2026-08-28

## Symptom

Every card-verification session that exhausts its retry budget bills ONE
extra charge attempt than configured. The processor's billing report
shows 4 attempts for a `max_attempts=3` configuration. Volume is high
enough that this shows up as a measurable cost increase in the monthly
statement.

## Evidence

`logs/incident.log` contains the failing test run of the retry wrapper.

## What we know

- `call_with_retry(fn, max_attempts)` is documented as calling `fn()` at
  most `max_attempts` times.
- When the call eventually succeeds after retries, the count is correct —
  the extra attempt only appears when the budget is exhausted.
- The verification call is idempotent, so no double-charges of customers
  occur — but every attempt is billed by the processor.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.