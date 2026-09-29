# Copyright (c) 2026 Example Fixture. MIT License.
"""Flag queries."""

from flags import FLAGS, is_active


def active_flags(now):
    return sorted(n for n in FLAGS if is_active(n, now))
