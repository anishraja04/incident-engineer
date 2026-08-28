# Incident case_009: Hourly telemetry report shifts daytime peaks by one hour

**Severity:** P1 (ops decisions based on wrong peaks)
**Service:** telemetry/reporting pipeline
**Reported by:** SRE team, 2026-08-28

## Symptom

The ops dashboard shows traffic peaks one hour later than they actually
happen. Night-time hours look correct; the shift only affects events
between 09:00 and 22:59 UTC. Capacity planning has already mis-scaled one
region because of it.

## Evidence

`logs/incident.log` contains the failing test run of the reporting pipeline.

## What we know

- Events carry a `ts` epoch; timestamps are UTC.
- The pipeline has three stages: `telemetry/ingest.py` (parse),
  `telemetry/bucket.py` (map event to hour), `telemetry/report.py`
  (aggregate).
- The report itself simply counts events per hour. 04:00 events are
  reported at 04:00; 15:00 events are reported at 16:00.
- A comment in `telemetry/bucket.py` mentions a "legacy daylight-saving
  adjustment inherited from the old analytics platform".

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.