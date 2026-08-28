from datetime import datetime, timedelta, timezone

from payments.models import Payment
from payments.scheduler import advance, is_due


def build_payment() -> Payment:
    return Payment(
        payment_id="pay_042",
        customer_id="cust_007",
        amount_cents=999,
        interval_hours=24,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_recurring_payments_charged_on_schedule():
    """The worker must charge each payment exactly on its schedule.

    Simulates a worker tick right at each scheduled time: the payment is
    scheduled 1h ahead, so it must be charged at the first tick that reaches
    that time and then exactly every interval_hours afterwards.
    """
    p = build_payment()
    first_due = p.next_run_at
    ticks = [
        first_due - timedelta(hours=1),   # 1h before: not due
        first_due,                        # due: charge #1
        first_due + timedelta(hours=24),  # due: charge #2
        first_due + timedelta(hours=48),  # due: charge #3
    ]
    charged_at = []
    for t in ticks:
        if is_due(p, now=t):
            charged_at.append(t)
            advance(p)

    assert len(charged_at) == 3, f"expected 3 charges, got {len(charged_at)}"
    # First charge must happen exactly at the scheduled time, not hours later.
    assert charged_at[0] == first_due
    # Charges are exactly one interval apart.
    gaps = [b - a for a, b in zip(charged_at, charged_at[1:])]
    assert gaps == [timedelta(hours=24), timedelta(hours=24)]