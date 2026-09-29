# Copyright (c) 2026 Example Fixture. MIT License.
"""Access policy."""

ADMINS = {"root"}


def allowed(user, job_id):
    return user in ADMINS
