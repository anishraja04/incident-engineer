# Incident case_005: Catalog API skips the first product

**Severity:** P2 (products missing from listings)
**Service:** catalog/paginator
**Reported by:** storefront team, 2026-08-28

## Symptom

The catalog API returns wrong items on every page. The very first product
in the catalog never appears on page 1 — instead the listing starts with
the second product. Every page looks "shifted" by one position, and the
last page is missing its final item.

## Evidence

`logs/incident.log` contains the failing test run for the paginator.

## What we know

- Pagination is 1-based: page 1, per_page 4 should return items 1-4.
- The API computes `start` and `end` from `(page - 1) * per_page` inside
  `catalog/paginator.py`.
- A direct request for `page=1, per_page=10` with exactly 10 items returns
  only 9 items.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.