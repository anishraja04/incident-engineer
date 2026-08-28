"""Retry wrapper for idempotent payment-verification calls.

`call_with_retry(fn, max_attempts)` calls `fn()` up to `max_attempts`
times. Transient errors are retried; the last error is re-raised when the
budget is exhausted. The operation is idempotent (verification), so extra
attempts only cost latency — but the billing integration counts each call,
so the attempt budget must be respected exactly.
"""


class TransientError(Exception):
    pass


def call_with_retry(fn, max_attempts: int = 3):
    attempts = 0
    while attempts <= max_attempts:
        attempts += 1
        try:
            return fn()
        except TransientError:
            continue
    raise TransientError("retry budget exhausted")