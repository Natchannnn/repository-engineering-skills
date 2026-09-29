# Copyright (c) 2026 Example Fixture. MIT License.
"""Lazy job descriptor. Stringifying performs storage I/O."""

class JobDesc:
    def __init__(self, job_id):
        self.job_id = job_id

    def __str__(self):
        from storage.jobs import fetch  # deferred import, still real I/O
        info = fetch(self.job_id)
        return f"job {self.job_id}: {info['title']}"
