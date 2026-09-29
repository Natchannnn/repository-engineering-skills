# Copyright (c) 2026 Example Fixture. MIT License.
"""Record store. Reads DATA_FILE dynamically so tests may redirect it."""

import json

import paths


def read_records():
    with open(paths.DATA_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def count():
    return len(read_records())
