# Copyright (c) 2026 Example Fixture. MIT License.
"""Tiny TTL cache. Refactor-only review target."""

import time

_STORE = {}


def get(key, loader, ttl, clock=time.time):
    entry = _STORE.get(key)
    if entry is not None and entry["expires"] > clock():
        return entry["value"]
    value = loader()
    current = clock()
    _STORE[key] = {"value": value, "expires": current + ttl}
    return value


def reset():
    _STORE.clear()
