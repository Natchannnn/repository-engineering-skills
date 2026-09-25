import json
import os
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"

_ledger_path = Path(__file__).resolve().with_name(LEDGER_FILE)


def _read_all() -> list[dict]:
    if not _ledger_path.exists():
        return []
    records = []
    with _ledger_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def get_by_id(n: int) -> dict | None:
    """Return the record whose id == n, or None when absent.

    Returns None if ledger.jsonl does not exist.
    """
    for record in _read_all():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None, tenant: str | None = None) -> list[dict]:
    """Return records matching the given filters, or all records when both are None.

    Each non-None argument filters by exact match on the corresponding field.
    Both kind and tenant can be filtered simultaneously.
    Returns [] if ledger.jsonl does not exist.
    """
    records = _read_all()
    if kind is not None:
        records = [r for r in records if r.get("kind") == kind]
    if tenant is not None:
        records = [r for r in records if r.get("tenant") == tenant]
    return records
