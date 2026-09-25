import json
from pathlib import Path

LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")


def _read_all() -> list[dict]:
    """Return all records from the ledger, or [] when the file is absent."""
    if not LEDGER_FILE.exists():
        return []
    records = []
    with LEDGER_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records


def get_by_id(n: int) -> dict | None:
    """Return the record whose ``id == n``, or ``None`` when absent.

    A missing ledger.jsonl also yields ``None``.
    """
    for record in _read_all():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None) -> list[dict]:
    """Return records matching ``kind`` in file order.

    When ``kind`` is ``None``, all records are returned.
    A missing ledger.jsonl yields an empty list.
    """
    records = _read_all()
    if kind is None:
        return records
    return [r for r in records if r.get("kind") == kind]
