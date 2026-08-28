import flags.service as svc


def test_initial_read():
    store = {"checkout_v2": False}
    assert svc.get_flag("checkout_v2", store) is False


def test_reads_reflect_latest_set():
    """After set_flag, readers must see the new value immediately."""
    store = {"checkout_v2": False}
    assert svc.get_flag("checkout_v2", store) is False
    svc.set_flag("checkout_v2", True, store)
    assert svc.get_flag("checkout_v2", store) is True


def test_toggle_back_and_forth():
    store = {"dark_mode": False}
    svc.get_flag("dark_mode", store)
    svc.set_flag("dark_mode", True, store)
    assert svc.get_flag("dark_mode", store) is True
    svc.set_flag("dark_mode", False, store)
    assert svc.get_flag("dark_mode", store) is False


def test_unknown_flag_returns_none():
    assert svc.get_flag("nope", {}) is None