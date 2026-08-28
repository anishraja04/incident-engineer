from datetime import datetime, timezone

import pytest

from telemetry.bucket import hour_of
from telemetry.ingest import ingest
from telemetry.report import hourly_counts


def ts_for(hour: int, minute: int = 0) -> int:
    return int(datetime(2026, 8, 15, hour, minute, tzinfo=timezone.utc).timestamp())


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (0, 0, 0),
        (6, 30, 6),
        (8, 59, 8),
        (9, 0, 9),
        (12, 0, 12),
        (17, 30, 17),
        (22, 59, 22),
        (23, 0, 23),
    ],
)
def test_event_bucketed_into_its_utc_hour(hour, minute, expected):
    """Each event must be reported in the exact UTC hour it occurred."""
    assert hour_of(ts_for(hour, minute)) == expected


def test_end_to_end_hourly_report():
    text = "\n".join(
        [
            f"ts={ts_for(9, 10)} metric=cpu_usage value=42.0",
            f"ts={ts_for(9, 45)} metric=cpu_usage value=43.0",
            f"ts={ts_for(10, 5)} metric=cpu_usage value=41.0",
            f"ts={ts_for(23, 0)} metric=cpu_usage value=50.0",
            f"ts={ts_for(0, 30)} metric=cpu_usage value=39.0",
        ]
    )
    events = ingest(text)
    counts = hourly_counts(events)
    # Two events at 09:00 UTC, one at 10:00, one at 23:00, one at 00:00.
    assert counts == {0: 1, 9: 2, 10: 1, 23: 1}


def test_peak_hour_matches_source_timestamps():
    """The busiest hour in the report must be the busiest hour in the data."""
    text = "\n".join(
        [f"ts={ts_for(17, m)} metric=cpu_usage value=1.0" for m in range(0, 60, 5)]
    )
    events = ingest(text)
    counts = hourly_counts(events)
    assert counts == {17: 12}