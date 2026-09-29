# Copyright (c) 2026 Example Fixture. MIT License.
"""Checkpointed export job: keep calling scan() until next_cursor is None."""

from query.filtering import keep
from storage.events import read
from api.pages import scan


def run_export():
    out = []
    after = 0
    while True:
        page, after = scan(read(), after)
        kept = [e for e in page if keep(e)]
        out.extend(kept)
        if not kept:
            break  # BUG: an empty *filtered* page is not end-of-data
        after = kept[-1]["id"]  # BUG: cursor from last *returned* record
    return [e["id"] for e in out]
