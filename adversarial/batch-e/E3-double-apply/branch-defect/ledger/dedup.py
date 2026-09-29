# Copyright (c) 2026 Example Fixture. MIT License.
"""Replay guard keyed on the SHA-256 of received BYTES (not parsed JSON)."""
import hashlib

_seen = set()


def already_applied(raw: bytes):
    h = hashlib.sha256(raw).hexdigest()
    if h in _seen:
        return True
    _seen.add(h)
    return False


def reset():
    _seen.clear()
