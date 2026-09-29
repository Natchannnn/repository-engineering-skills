# Copyright (c) 2026 Example Fixture. MIT License.
"""Filter policy: these event ids are exportable (105 arrives mid-export and
passes the filter — only the snapshot mark excludes it)."""

ACCEPTED = {101, 104, 105}


def keep(event):
    return event["id"] in ACCEPTED
