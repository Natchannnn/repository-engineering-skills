# Copyright (c) 2026 Example Fixture. MIT License.
"""Fixed migrator: presence and value are separate facts. Never use truthiness."""

def migrate(overrides):
    records = {}
    for key, value in overrides.items():
        if value is None:
            records[key] = {"mode": "disabled"}
        elif isinstance(value, int) and not isinstance(value, bool) and value == 0:
            records[key] = {"mode": "now"}
        else:
            records[key] = {"mode": "at", "value": value}
    return records
