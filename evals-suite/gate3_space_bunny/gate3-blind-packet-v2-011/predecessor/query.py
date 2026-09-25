import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent


def _ledger_path() -> Path:
    return _MODULE_DIR / LEDGER_FILE


def _read_all() -> list[dict]:
    try:
        data = _ledger_path().read_bytes()
    except FileNotFoundError:
        return []

    records = []
    for line in data.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


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
