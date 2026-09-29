# Copyright (c) 2026 Example Fixture. MIT License.
"""Clean variant: descriptor carries only data it already has. Same logging line,
same auth order — but stringifying performs no I/O, so the denial contract holds."""

class JobDesc:
    def __init__(self, job_id):
        self.job_id = job_id

    def __str__(self):
        return f"job {self.job_id}"
