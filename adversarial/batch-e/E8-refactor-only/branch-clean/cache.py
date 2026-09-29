# Copyright (c) 2026 Example Fixture. MIT License.
"""Tiny TTL cache. Single clock capture per call — the control branch."""

import time

_STORE = {}


def get(key, loader, ttl, clock=time.time):
    now = clock()
    entry = _STORE.get(key)
    if entry is not None and entry["expires"] > now:
        return entry["value"]
    value = loader()
    _STORE[key] = {"value": value, "expires": now + ttl}
    return value


def reset():
    _STORE.clear()
