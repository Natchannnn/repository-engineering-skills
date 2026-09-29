# Copyright (c) 2026 Example Fixture. MIT License.
"""Transport envelope: opaque bytes carrier. Never parses payload."""

def wrap(raw: bytes):
    return {"payload": raw, "encoding": "utf-8"}


def unwrap(env):
    return env["payload"]
