# SlugValidator

Public-facing slug validation service used before content is published.
Slugs must contain only lowercase letters, digits and single hyphens
between parts.

- `slugcheck/validator.py` — validation logic.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```