# Incident case_010: Service configs leak into each other

**Severity:** P1 (wrong thresholds across services)
**Service:** config/loader
**Reported by:** platform team, 2026-08-28

## Symptom

The payments team tuned their p90 alert threshold from 0.95 to 0.50 so
they would page less. A few minutes later the checkout service started
paging on every transaction — it behaves as if it inherited payments'
thresholds. Pager duty was woken up all night because of a change made in
a completely different service.

## Evidence

`logs/incident.log` contains the failing test run of the config loader.

## What we know

- Each service calls `load_config(service_name)` and gets its own config.
- The shared defaults live in a module-level dict in `config/loader.py`.
- Top-level fields (like `mode`, `timeout_s`) stay isolated between
  services — the leak only affects nested dicts (`thresholds`, `alerts`).

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.