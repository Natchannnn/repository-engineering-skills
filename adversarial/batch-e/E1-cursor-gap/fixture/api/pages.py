# Copyright (c) 2026 Example Fixture. MIT License.
"""Paginated scan. The API returns at most PAGE_SIZE raw records per call."""

PAGE_SIZE = 2


def scan(store_events, after_id, limit=PAGE_SIZE):
    """Return (page, next_after). next_after is None when the store is exhausted.

    NOTE: this returns *raw* records. Filtering happens in the caller.
    """
    ids = sorted(e["id"] for e in store_events if e["id"] > after_id)
    window = ids[:limit]
    if not window:
        return [], None
    page = [e for e in store_events if e["id"] in window]
    page.sort(key=lambda e: e["id"])
    return page, window[-1]
