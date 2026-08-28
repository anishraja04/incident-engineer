"""Raw telemetry ingestion. Lines look like:

    ts=1750000000 metric=cpu_usage value=42.5
"""
from dataclasses import dataclass


@dataclass
class Event:
    ts: int
    metric: str
    value: float


def parse_line(line: str) -> Event:
    parts = {}
    for token in line.strip().split():
        key, _, val = token.partition("=")
        parts[key] = val
    return Event(ts=int(parts["ts"]), metric=parts["metric"], value=float(parts["value"]))


def ingest(text: str) -> list[Event]:
    return [parse_line(line) for line in text.splitlines() if line.strip()]