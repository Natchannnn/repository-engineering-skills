"""Read-only queries over the append-only JSON-lines event ledger.

CP2 slice: point lookup by ledger ID and filtering by event kind. The ledger
path is resolved relative to this module so callers are unaffected by the
working directory.
"""

from __future__ import annotations

import json
import os

LEDGER_FILE = "ledger.jsonl"
LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), LEDGER_FILE)


def _load() -> list[dict]:
    """Return every stored record in file order; an absent ledger reads empty."""
    try:
        with open(LEDGER_PATH, "rb") as handle:
            raw = handle.read()
    except FileNotFoundError:
        return []
    return [
        json.loads(line)
        for line in raw.decode("utf-8").splitlines()
        if line.strip()
    ]


def get_by_id(n: int) -> dict | None:
    """Return the record with ledger ID n, or None when no record has that ID."""
    for record in _load():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None, tenant: str | None = None) -> list[dict]:
    """Return records matching the supplied filters, in ledger file order.

    The kind and tenant filters are independent: each one supplied narrows the
    result, both supplied must both match, and neither supplied returns every
    record. Comparison is exact and case-sensitive, and an untrimmed filter
    value is never widened to match a stored value.
    """
    records = _load()
    if kind is not None:
        records = [record for record in records if record.get("kind") == kind]
    if tenant is not None:
        records = [record for record in records if record.get("tenant") == tenant]
    return records
