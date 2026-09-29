# Copyright (c) 2026 Example Fixture. MIT License.
"""Worker consumes RESOLVED values only. Out of scope: do not touch to mask bugs."""

def describe(resolved):
    status, value = resolved
    if status == "disabled":
        return "disabled"
    return f"scheduled({value})"
