# Incident case_007: Tax calculator undercharges on half-cent boundaries

**Severity:** P1 (revenue understatement)
**Service:** tax/calc
**Reported by:** finance team, 2026-08-28

## Symptom

Order totals do not reconcile. For a specific set of amounts and rates the
tax comes out one cent lower than finance's spreadsheet calculation. The
discrepancy only appears when the exact tax is a value like 8.5, 22.5 or
14.5 cents.

## Evidence

`logs/incident.log` contains the failing test run.

## What we know

- Finance rule (documented in the repo README): tax = amount * rate / 100,
  rounded to the nearest cent, **halves round up**.
- The failing cases all sit exactly on a half-cent boundary.
- The service computes tax in `tax/calc.py`.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.