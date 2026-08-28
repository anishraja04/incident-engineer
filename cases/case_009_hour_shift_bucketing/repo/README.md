# TelemetryAggregator

Collects raw telemetry events from devices and produces hourly
per-metric reports for the ops dashboard.

Pipeline: `ingest` (parse raw lines) -> `bucket` (map event -> hour)
-> `report` (aggregate counts per hour).

- `telemetry/ingest.py`
- `telemetry/bucket.py`
- `telemetry/report.py`
- `tests/` — unit tests.

Run tests with:

```bash
python -m pytest -q
```