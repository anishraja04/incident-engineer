"""Hourly report aggregation."""
from collections import Counter

from telemetry.bucket import hour_of


def hourly_counts(events) -> dict[int, int]:
    """Return {hour: number_of_events} for the given events (UTC hours)."""
    return dict(sorted(Counter(hour_of(e.ts) for e in events).items()))