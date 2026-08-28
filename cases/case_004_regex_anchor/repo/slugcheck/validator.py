"""Slug validation for the publishing platform.

A valid slug:
- contains only lowercase a-z, digits 0-9 and hyphens,
- has no leading/trailing hyphen and no consecutive hyphens,
- is 1-64 characters long.
"""
import re

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*")


def is_valid_slug(slug: str) -> bool:
    """True when `slug` is a valid slug."""
    if not isinstance(slug, str) or not slug:
        return False
    if len(slug) > 64:
        return False
    return bool(_SLUG_RE.match(slug))
