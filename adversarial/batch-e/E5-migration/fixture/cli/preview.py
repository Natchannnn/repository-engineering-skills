# Copyright (c) 2026 Example Fixture. MIT License.
"""Pre-migration preview (uses the v1 reader — correct before migration)."""

from config import merge, reader_v1

DEFAULTS = {"interval": 30}


def preview(project, user):
    effective = merge.merge(DEFAULTS, project, user)
    status, value = reader_v1.resolve("interval", effective, DEFAULTS)
    if status == "disabled":
        return "disabled"
    return f"scheduled({value})"
