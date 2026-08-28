# ServiceConfig

Runtime configuration service. Each service loads its own copy of the
shared config file and tunes thresholds without affecting other services.

- `config/loader.py` — loads and returns a service's config.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```