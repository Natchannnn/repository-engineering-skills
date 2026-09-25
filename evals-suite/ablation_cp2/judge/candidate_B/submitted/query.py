import json
import os

LEDGER_FILE = "ledger.jsonl"

# Absolute path to the ledger, resolved once at import time relative to this
# module's directory so the file is found regardless of the working directory.
_LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), LEDGER_FILE)


def _read_all() -> list[dict]:
    """Return every record in the ledger, or [] when the file is absent."""
    if not os.path.exists(_LEDGER_PATH):
        return []
    records = []
    with open(_LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def get_by_id(n: int) -> dict | None:
    """Return the record whose id == n, or None when absent.

    A missing ledger.jsonl yields None.
    """
    for record in _read_all():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None) -> list[dict]:
    """Return records whose kind equals *kind*, preserving file order.

    kind=None returns all records. A missing ledger.jsonl yields [].
    """
    records = _read_all()
    if kind is None:
        return records
    return [r for r in records if r.get("kind") == kind]
