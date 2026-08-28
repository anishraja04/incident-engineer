from config.loader import load_config


def test_each_service_gets_its_own_name():
    a = load_config("checkout")
    b = load_config("payments")
    assert a["service"] == "checkout"
    assert b["service"] == "payments"


def test_tuning_thresholds_is_isolated():
    """Tuning one service's threshold must not change another service's
    thresholds, even after both have been loaded."""
    a = load_config("checkout")
    b = load_config("payments")
    a["thresholds"]["p90"] = 0.50
    assert b["thresholds"]["p90"] == 0.95


def test_alerts_config_is_isolated():
    a = load_config("checkout")
    b = load_config("payments")
    a["alerts"]["pager"] = True
    assert b["alerts"]["pager"] is False


def test_identical_defaults_each_load():
    a = load_config("checkout")
    b = load_config("payments")
    assert a["thresholds"] == b["thresholds"]
    assert a["alerts"] == b["alerts"]