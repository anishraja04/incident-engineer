from sales.aggregator import aggregate_sales


def test_single_batch_totals():
    events = [("pen", 3), ("notebook", 2), ("pen", 1)]
    result = aggregate_sales(events)
    assert result == {"pen": 4, "notebook": 2}


def test_each_call_is_stateless():
    """A second request must NOT see the first request's totals."""
    first = aggregate_sales([("pen", 10)])
    second = aggregate_sales([("notebook", 5)])
    assert first == {"pen": 10}
    assert second == {"notebook": 5}


def test_same_product_across_requests_isolated():
    """Totals for a product must reflect only the current request."""
    aggregate_sales([("mug", 7)])
    result = aggregate_sales([("mug", 2)])
    assert result == {"mug": 2}


def test_empty_batch_returns_empty():
    assert aggregate_sales([]) == {}