"""Daily sales aggregation endpoint.

`aggregate_sales` is called once per request with the day's sales events and
returns per-product totals. The handler is intentionally stateless: each call
must produce totals for exactly the events it received.
"""


def aggregate_sales(events, totals={}):
    """Return a dict mapping product -> total units sold for `events`.

    Must reflect ONLY the events passed in this call.
    """
    for product, units in events:
        totals[product] = totals.get(product, 0) + units
    return totals
