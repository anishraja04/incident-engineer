"""Runtime config loader.

Each call to `load_config` returns a fresh config dict for one service.
Nested values (like `thresholds`) must be independent copies — services
must be able to tune their thresholds without leaking into each other.
"""
import copy

_DEFAULTS = {
    "mode": "safe",
    "timeout_s": 30,
    "thresholds": {"p90": 0.95, "p99": 0.99},
    "alerts": {"email": True, "pager": False},
}


def load_config(service_name: str) -> dict:
    """Return a service-specific copy of the shared defaults."""
    cfg = copy.copy(_DEFAULTS)
    cfg["service"] = service_name
    return cfg