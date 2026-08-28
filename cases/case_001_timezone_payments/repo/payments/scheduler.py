"""Recurring payment scheduler.

The worker loop calls `is_due(payment)` once per tick. When a payment is due
it is charged and `advance(payment)` computes the next run.
"""
from datetime import datetime, timedelta

from payments.models import Payment


def now_utc() -> datetime:
    """Current wall-clock time as naive UTC (as used by the rest of the
    codebase and by the database layer)."""
    return datetime.utcnow()


def is_due(payment: Payment, now: datetime | None = None) -> bool:
    """True when the payment's next run time has been reached."""
    current = now if now is not None else datetime.now()
    return current >= payment.next_run_at


def advance(payment: Payment) -> Payment:
    """Compute the next run time after a successful charge."""
    payment.next_run_at = payment.next_run_at + timedelta(hours=payment.interval_hours)
    return payment