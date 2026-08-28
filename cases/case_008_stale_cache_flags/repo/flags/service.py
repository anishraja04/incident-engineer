"""Feature-flag service.

Flags are stored in `store` (dict). Reads are cached in `_cache` to keep
hot reads fast. The release team toggles flags with `set_flag`.
"""
_cache = {}


def get_flag(name, store):
    if name not in _cache:
        _cache[name] = store.get(name)
    return _cache[name]


def set_flag(name, value, store):
    store[name] = value