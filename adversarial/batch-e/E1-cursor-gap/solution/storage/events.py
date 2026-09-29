# Copyright (c) 2026 Example Fixture. MIT License.
"""Event store. Membership is append-only; readers must respect snapshots."""

EVENTS = [
    {"id": 101, "ts": 1000},
    {"id": 102, "ts": 1000},
    {"id": 103, "ts": 1000},
    {"id": 104, "ts": 1000},
]

# Test seam: called at the start of every scan (fault injection in evaluator).
on_scan = None


def read(notify=True):
    if notify and on_scan is not None:
        on_scan()
    return list(EVENTS)


def insert(event):
    EVENTS.append(event)


def reset():
    global EVENTS, on_scan
    EVENTS = [dict(e) for e in _SEED]
    on_scan = None


_SEED = [dict(e) for e in EVENTS]
