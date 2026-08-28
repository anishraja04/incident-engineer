# FeatureFlags

Internal feature-flag service. Services read flags via `get_flag`; the
release team toggles them with `set_flag`.

- `flags/service.py` — flag storage + reads.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```