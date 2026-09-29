# Copyright (c) 2026 Example Fixture. MIT License.
"""Fixed scan: cursor carries (snapshot, position). Empty filtered pages do NOT end
the job — only snapshot exhaustion returns None."""

from storage.events import read

PAGE_SIZE = 2


def start():
    snap = frozenset(e["id"] for e in read(notify=False))
    return {"snap": snap, "pos": 0}


def scan(cursor):
    evts = read()
    ids = sorted(
        e["id"] for e in evts if e["id"] in cursor["snap"] and e["id"] > cursor["pos"]
    )
    window = ids[:PAGE_SIZE]
    if not window:
        return [], None
    page = sorted((e for e in evts if e["id"] in window), key=lambda e: e["id"])
    return page, {"snap": cursor["snap"], "pos": window[-1]}
