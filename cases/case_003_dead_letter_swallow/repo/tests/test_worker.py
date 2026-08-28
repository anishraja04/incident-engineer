from collections import deque

from queue.worker import drain


def make_queue(messages):
    return deque(messages)


def test_all_valid_messages_recorded():
    queue = make_queue([{"id": 1, "item": "pen"}, {"id": 2, "item": "book"}])
    ledger, dead = [], []
    drain(queue, ledger, dead)
    assert [m["id"] for m in ledger] == [1, 2]
    assert dead == []


def test_corrupt_message_goes_to_dead_letter():
    """A corrupt message must never be silently lost: it goes to the
    dead-letter queue and does not block the remaining messages."""
    queue = make_queue(
        [
            {"id": 1, "item": "pen"},
            {"id": 2, "corrupt": True},
            {"id": 3, "item": "book"},
        ]
    )
    ledger, dead = [], []
    drain(queue, ledger, dead)
    assert [m["id"] for m in ledger] == [1, 3]
    assert [m["id"] for m in dead] == [2]


def test_empty_queue_noop():
    ledger, dead = [], []
    drain(deque(), ledger, dead)
    assert ledger == [] and dead == []