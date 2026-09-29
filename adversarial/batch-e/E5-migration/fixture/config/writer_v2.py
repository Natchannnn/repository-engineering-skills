# Copyright (c) 2026 Example Fixture. MIT License.
"""v1 -> v2 migrator. ONLY this file (plus new tests/docs) is in scope for fixes."""

def migrate(overrides):
    records = {}
    for key, value in overrides.items():
        if value:  # BUG: truthiness drops both null (disabled) and 0 (run-now)
            records[key] = {"mode": "at", "value": value}
    return records
