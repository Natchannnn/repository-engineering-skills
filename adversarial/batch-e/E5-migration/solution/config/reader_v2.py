# Copyright (c) 2026 Example Fixture. MIT License.
"""v2 reader (fixed, out of scope for the task)."""

def resolve(key, records, defaults):
    rec = records.get(key)
    if rec is None or rec["mode"] == "inherit":
        return ("scheduled", defaults[key])
    if rec["mode"] == "disabled":
        return ("disabled", None)
    if rec["mode"] == "now":
        return ("scheduled", 0)
    return ("scheduled", rec["value"])
