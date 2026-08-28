# Incident case_002: Sales aggregation reports inflated totals

**Severity:** P1 (incorrect revenue reports)
**Service:** sales/aggregator
**Reported by:** finance team, 2026-08-28

## Symptom

The daily sales report shows inflated unit totals for some products. Numbers
for the same product grow across the day even when nothing was sold. Finance
cannot reconcile the report against the order system.

## Evidence

`logs/incident.log` contains the failing test run. The aggregation endpoint
is called once per request with that day's sales events.

## What we know

- The endpoint handler is supposed to be stateless.
- The report only becomes wrong after a product has appeared in an earlier
  request during the same process lifetime.
- A fresh process serves the first request correctly.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.