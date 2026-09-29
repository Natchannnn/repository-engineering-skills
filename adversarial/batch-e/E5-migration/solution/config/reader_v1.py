# Copyright (c) 2026 Example Fixture. MIT License.
"""v1 reader. Three states: absent key = inherit, null = disabled, 0 = run now."""

_MISSING = object()


def resolve(key, overrides, defaults):
    v = overrides.get(key, _MISSING)
    if v is _MISSING:
        return ("scheduled", defaults[key])
    if v is None:
        return ("disabled", None)
    return ("scheduled", v)
