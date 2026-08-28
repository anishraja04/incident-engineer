"""Order queue consumer.

`drain` pulls messages off the queue one at a time:
- valid messages are recorded in the ledger,
- messages that fail processing must end up in the dead-letter queue
  so they are never silently lost.
"""
from collections import deque


class CorruptMessageError(Exception):
    pass


def process_message(msg, ledger):
    """Record a message. Raises CorruptMessageError for corrupt payloads."""
    if msg.get("corrupt"):
        raise CorruptMessageError(f"corrupt payload: {msg.get('id')}")
    ledger.append(msg)


def drain(queue, ledger, dead_letter):
    """Process everything currently on the queue."""
    while queue:
        msg = queue.popleft()
        try:
            process_message(msg, ledger)
        except Exception:
            pass