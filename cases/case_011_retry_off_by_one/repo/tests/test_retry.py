import pytest

from paygw.retry import TransientError, call_with_retry


def test_success_on_first_call():
    calls = []
    result = call_with_retry(lambda: (calls.append(1), "ok")[1], max_attempts=3)
    assert result == "ok"
    assert len(calls) == 1


def test_retries_then_succeeds():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise TransientError("timeout")
        return "charged"

    assert call_with_retry(flaky, max_attempts=3) == "charged"
    assert len(calls) == 3


def test_exhausts_exactly_max_attempts_then_raises():
    """The budget must be respected exactly: max_attempts calls, no more."""
    calls = []

    def always_fails():
        calls.append(1)
        raise TransientError("down")

    with pytest.raises(TransientError):
        call_with_retry(always_fails, max_attempts=3)
    assert len(calls) == 3, f"expected exactly 3 attempts, got {len(calls)}"


def test_single_attempt_budget():
    calls = []

    def always_fails():
        calls.append(1)
        raise TransientError("down")

    with pytest.raises(TransientError):
        call_with_retry(always_fails, max_attempts=1)
    assert len(calls) == 1