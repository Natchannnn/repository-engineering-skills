# Copyright (c) 2026 Example Fixture. MIT License.
"""Batch refresh service. Scope for fixes: this file only."""

from catalog import persistence, state


def refresh(rows):
    for row in rows:  # BUG 1: mutates shared state while input may still fail
        for key, value in row.items():
            state.STATE[key] = value
    persistence.save(dict(state.STATE))  # BUG 2 (latent): disk write happens last,
    # so any earlier failure leaves memory ahead of disk with no rollback
