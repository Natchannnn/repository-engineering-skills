import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _read_all() -> list[dict]:
    path = _ledger_path()
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []

    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def get_by_id(n: int) -> dict | None:
    for record in _read_all():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None) -> list[dict]:
    records = _read_all()
    if kind is None:
        return records
    return [record for record in records if record.get("kind") == kind]
