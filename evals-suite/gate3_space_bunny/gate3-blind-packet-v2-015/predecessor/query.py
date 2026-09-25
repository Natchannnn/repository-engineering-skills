import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _read_records() -> list[dict]:
    path = _ledger_path()
    if not path.exists():
        return []

    records = []
    for line in path.read_bytes().splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def get_by_id(n: int) -> dict | None:
    for record in _read_records():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None) -> list[dict]:
    records = _read_records()
    if kind is None:
        return records
    return [record for record in records if record.get("kind") == kind]
