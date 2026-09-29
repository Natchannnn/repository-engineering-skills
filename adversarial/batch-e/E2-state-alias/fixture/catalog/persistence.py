# Copyright (c) 2026 Example Fixture. MIT License.
"""Durable catalog persistence: temp file + atomic replace."""

import json
import os

_replace = os.replace  # seam for fault injection
DATA_PATH = None  # set by caller/evaluator to a real file path


def save(data):
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    _replace(tmp, DATA_PATH)


def load():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)
