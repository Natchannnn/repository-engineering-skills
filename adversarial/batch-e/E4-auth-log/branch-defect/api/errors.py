# Copyright (c) 2026 Example Fixture. MIT License.
"""Error mapping: storage errors become HTTP responses."""

class Denied(Exception):
    pass


def to_response(exc):
    if isinstance(exc, Denied):
        return (403, b"forbidden")
    if isinstance(exc, KeyError):
        return (404, b"not found")
    raise exc
