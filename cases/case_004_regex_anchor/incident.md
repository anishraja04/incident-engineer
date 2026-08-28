# Incident case_004: Slug validator accepts invalid slugs

**Severity:** P2 (bad URLs published)
**Service:** slugcheck/validator
**Reported by:** content platform team, 2026-08-28

## Symptom

Slugs that clearly violate the rules are being accepted and published:
`hello world`, `hello@example.com`, `hello-world!` all pass validation and
produce broken, unshareable URLs. The publish pipeline only rejects slugs
when validation says "invalid", so everything else goes live.

## Evidence

`logs/incident.log` contains the failing test run.

## What we know

- A valid slug: lowercase a-z, digits, single hyphens between parts, 1-64 chars.
- The failure only appears when a slug has an invalid character or a bad
  hyphen at the END of the string. Short valid slugs all pass.
- The validator is a single regex + length check in
  `slugcheck/validator.py`.

## Task

Fix the service so all tests in `tests/` pass. Do not modify the tests.