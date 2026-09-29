# Copyright (c) 2026 Example Fixture. MIT License.
"""Feature flag store with TTL expiry."""

FLAGS = {}


def add(name, enabled=True, expires_at=None):
    FLAGS[name] = {"enabled": bool(enabled), "expires_at": expires_at}


def is_active(name, now):
    rec = FLAGS.get(name)
    if rec is None:
        return False
    if not rec["enabled"]:
        return False
    exp = rec["expires_at"]
    return exp is None or now < exp


def purge_expired(now):
    dead = [
        name
        for name, rec in FLAGS.items()
        if rec["expires_at"] is not None and now >= rec["expires_at"]
    ]
    for name in dead:
        del FLAGS[name]
    return len(dead)


def reset():
    FLAGS.clear()
