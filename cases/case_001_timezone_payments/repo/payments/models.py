from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Payment:
    payment_id: str
    customer_id: str
    amount_cents: int
    interval_hours: int
    next_run_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "scheduled"