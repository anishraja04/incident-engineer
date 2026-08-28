# Incident Case Format

Each case under `cases/case_NNN_<slug>/` is a self-contained incident:

```
case_NNN_<slug>/
├── case.json          # metadata + verification spec (machine readable)
├── incident.md        # the incident report the agent receives (human readable)
├── repo/              # the buggy project (stdlib-only Python, self-contained)
│   ├── <package>/
│   ├── tests/
│   └── README.md
├── logs/
│   └── incident.log   # captured output of the failing run (evidence)
├── ground_truth.patch # the official minimal fix
└── build_incident.sh  # how the incident was produced (repro of the bug)
```

## Verification spec (case.json)

```json
{
  "id": "case_001",
  "slug": "short-name",
  "title": "...",
  "severity": "P1",
  "service": "which component broke",
  "description": "one-line symptom",
  "tags": ["timezone", "datetime"],
  "challenging": false,
  "budget_steps": 60,
  "check": {
    "test_files_immutable": ["tests/"],
    "must_pass": ["tests/test_payments.py"],
    "must_not_contain": ["# noqa", "pytest.skip", "except: pass"]
  }
}
```

The verifier:
1. copies `repo/` to a fresh workspace,
2. lets the agent modify it,
3. runs `pytest -q` in the workspace,
4. requires every test in `must_pass` to pass,
5. requires `test_files_immutable` dirs to be byte-identical to the original (no
   deleting/weakening tests), and
6. rejects fixes containing the `must_not_contain` markers (anti-cheat).

## Rules for a good case

- stdlib-only repo (no network at eval time), 2-8 source files.
- Bug is reproducible: running the test suite BEFORE the fix fails on `must_pass`.
- Ground truth patch is minimal and fixes only the bug.
- `incident.md` reads like a real on-call report: symptom, error excerpt, service,
  what the user saw. The agent must NOT be spoon-fed the root cause.
- Logs are the actual captured output (not fabricated).