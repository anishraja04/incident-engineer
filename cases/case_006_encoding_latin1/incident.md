# Incident case_006: Warehouse import crashes on accented names

**Severity:** P1 (daily import blocked)
**Service:** importer/loader
**Reported by:** warehouse operations, 2026-08-28

## Symptom

The daily order import from the legacy mainframe fails every run:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 50:
invalid continuation byte
```

No orders are loaded today. The export side is unchanged — the mainframe
team verified the file opens fine in their tools.

## Evidence

`logs/incident.log` contains the failing test run. The export file is at
`importer/data/orders.csv` in the repository.

## What we know

- The mainframe writes ISO-8859-1 (latin-1); customer names contain
  accented characters like "José", "Müller", "López".
- The importer reads the CSV in `importer/loader.py`.
- The file itself is fine — the failure happens while decoding.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.