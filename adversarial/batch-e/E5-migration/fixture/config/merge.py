# Copyright (c) 2026 Example Fixture. MIT License.
"""Layered merge: defaults -> project -> user. Later layers win, nulls included."""

def merge(*layers):
    out = {}
    for layer in layers:
        out.update(layer)
    return out
