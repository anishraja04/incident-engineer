# OrderQueue

Queue consumer that processes order messages. Valid messages must be
recorded in the ledger; messages that cannot be processed must be moved to
the dead-letter queue so an operator can inspect them.

- `queue/worker.py` — the drain loop.
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```