from catalog.paginator import get_page

ITEMS = [f"item-{i}" for i in range(1, 11)]  # 10 items


def test_first_page_returns_first_items():
    assert get_page(ITEMS, 1, 4) == ["item-1", "item-2", "item-3", "item-4"]


def test_second_page_returns_next_items():
    assert get_page(ITEMS, 2, 4) == ["item-5", "item-6", "item-7", "item-8"]


def test_last_page_returns_remainder():
    assert get_page(ITEMS, 3, 4) == ["item-9", "item-10"]


def test_all_items_covered_across_pages():
    seen = []
    page = 1
    while True:
        chunk = get_page(ITEMS, page, 4)
        if not chunk:
            break
        seen.extend(chunk)
        page += 1
    assert seen == ITEMS


def test_page_1_with_per_page_equal_to_length():
    assert get_page(ITEMS, 1, 10) == ITEMS