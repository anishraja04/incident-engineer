"""Catalog pagination.

`get_page(items, page, per_page)` returns the slice of `items` for a
1-based `page`. Every item must appear on exactly one page, and no page
may be empty while items remain.
"""


def get_page(items, page, per_page):
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = (page - 1) * per_page + 1
    end = start + per_page
    return items[start:end]