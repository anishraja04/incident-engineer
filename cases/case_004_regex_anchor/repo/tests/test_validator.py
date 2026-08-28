from slugcheck.validator import is_valid_slug


def test_valid_slugs_accepted():
    for slug in ["hello", "hello-world", "a1-b2-c3", "x", "q" * 64]:
        assert is_valid_slug(slug), slug


def test_uppercase_rejected():
    assert not is_valid_slug("Hello")
    assert not is_valid_slug("HELLO-WORLD")


def test_special_characters_rejected():
    """Slugs with any character outside [a-z0-9-] must be rejected —
    a prefix match is not a valid slug."""
    assert not is_valid_slug("hello world")
    assert not is_valid_slug("hello!")
    assert not is_valid_slug("hello-world!")
    assert not is_valid_slug("hello@example.com")


def test_bad_hyphen_placement_rejected():
    assert not is_valid_slug("-hello")
    assert not is_valid_slug("hello-")
    assert not is_valid_slug("hello--world")


def test_too_long_rejected():
    assert not is_valid_slug("q" * 65)