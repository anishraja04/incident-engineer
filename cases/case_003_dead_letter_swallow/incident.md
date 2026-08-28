# Incident case_003: Order messages silently disappear

**Severity:** P1 (orders lost, no trace)
**Service:** queue/worker
**Reported by:** fulfilment operations, 2026-08-28

## Symptom

Some orders never reach fulfilment. The source system shows the order as
"sent to processing", but the warehouse never receives it. There is no error
anywhere in the logs — the message just vanishes. The dead-letter queue,
which should hold unprocessable messages, is empty.

## Evidence

`logs/incident.log` contains the failing test run of the drain loop.

## What we know

- The consumer `drain` pops messages and calls `process_message`.
- Valid messages are appended to the ledger.
- Some payloads carry a `corrupt` flag and raise `CorruptMessageError`.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.