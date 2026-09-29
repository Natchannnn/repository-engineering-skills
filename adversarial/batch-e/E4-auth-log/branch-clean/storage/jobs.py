# Copyright (c) 2026 Example Fixture. MIT License.
"""Job store. Counts every read (the oracle watches this counter)."""

JOBS = {"j1": {"title": "backup", "owner": "ops"}}
read_count = 0


def fetch(job_id):
    global read_count
    read_count += 1
    if job_id not in JOBS:
        raise KeyError(job_id)
    return JOBS[job_id]


def reset_count():
    global read_count
    read_count = 0
