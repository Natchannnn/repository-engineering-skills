# Copyright (c) 2026 Example Fixture. MIT License.
"""Fixed export: snapshot once, scan to exhaustion, filter after."""

from api.pages import scan, start
from query.filtering import keep


def run_export():
    out = []
    cursor = start()
    while cursor is not None:
        page, cursor = scan(cursor)
        out.extend(e["id"] for e in page if keep(e))
    return out
