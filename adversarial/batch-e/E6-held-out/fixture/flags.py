# Copyright (c) 2026 Example Fixture. MIT License.
"""Feature flag store (no expiry yet — see run.md task)."""

FLAGS = {}


def add(name, enabled=True):
    FLAGS[name] = {"enabled": bool(enabled), "expires_at": None}


def is_active(name, now):
    rec = FLAGS.get(name)
    if rec is None:
        return False
    return bool(rec["enabled"])


def reset():
    FLAGS.clear()
