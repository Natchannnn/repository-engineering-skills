# Copyright (c) 2026 Example Fixture. MIT License.
"""Fixed refresh: stage + validate everything first, persist, then swap the shared
dictionary IN PLACE so held MappingProxyType views observe the update."""

from catalog import persistence, state


def refresh(rows):
    staged = {}
    for row in rows:
        staged.update(row)
    persistence.save(staged)
    state.STATE.clear()
    state.STATE.update(staged)
