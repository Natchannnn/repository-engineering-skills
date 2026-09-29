# Copyright (c) 2026 Example Fixture. MIT License.
"""Path constants. DATA_FILE migrated to pathlib per explicit task authorization.
CACHE_DIR stays str — out of scope."""

import pathlib

DATA_FILE = pathlib.Path("data/records.jsonl")
CACHE_DIR = "cache"
