# Copyright (c) 2026 Example Fixture. MIT License.
"""Job endpoint."""

from views.job_summary import JobDesc
from auth.policy import allowed
from api import errors

LOG = []


def handle(job_id, user):
    desc = JobDesc(job_id)
    LOG.append(f"request {desc}")  # BUG: f-string evaluates BEFORE the auth check
    if not allowed(user, job_id):
        raise errors.Denied()
    return {"ok": True}
