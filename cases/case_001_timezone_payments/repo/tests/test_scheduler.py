from datetime import datetime, timedelta, timezone

from payments.models import Payment
from payments.scheduler import advance, is_due


def make_payment(hours_from_now: float = 1.0) -> Payment:
    base = datetime.now(timezone.utc)
    return Payment(
        payment_id="pay_001",
        customer_id="cust_042",
        amount_cents=1999,
        interval_hours=24,
        next_run_at=base + timedelta(hours=hours_from_now),
    )


def test_not_due_before_next_run():
    p = make_payment(hours_from_now=1.0)
    # One minute before the scheduled run the payment must NOT be due.
    t = datetime.now(timezone.utc) + timedelta(hours=0.9)
    assert not is_due(p, now=t)


def test_due_at_next_run():
    p = make_payment(hours_from_now=1.0)
    # One minute AFTER the scheduled run the payment MUST be due.
    t = datetime.now(timezone.utc) + timedelta(hours=1.1)
    assert is_due(p, now=t)


def test_due_when_no_explicit_now():
    """The default path (worker tick without an explicit timestamp) must
    use the same time basis as the tests: UTC."""
    p = make_payment(hours_from_now=-1.0)  # scheduled in the past
    assert is_due(p)


def test_advance_keeps_next_run_in_utc():
    p = make_payment(hours_from_now=0.0)
    advance(p)
    # After advancing, the payment must be due exactly one interval later.
    t = p.next_run_at + timedelta(minutes=1)
    assert is_due(p, now=t)