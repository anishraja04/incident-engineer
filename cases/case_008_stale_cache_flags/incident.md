# Incident case_008: Feature flags serve stale values after toggles

**Severity:** P2 (deploys cannot be controlled)
**Service:** flags/service
**Reported by:** release engineering, 2026-08-28

## Symptom

We toggled `checkout_v2` ON to start a gradual rollout, but 20 minutes
later the services were still behaving as if the flag were OFF. Toggling
flags back and forth has no effect until a service process restarts. The
stored value in the database is correct — reads just return the old value.

## Evidence

`logs/incident.log` contains the failing test run of the flag service.

## What we know

- `set_flag` writes the new value to the store.
- Reads are served from a cache in `flags/service.py` so hot paths stay fast.
- A fresh process reads the correct value.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.