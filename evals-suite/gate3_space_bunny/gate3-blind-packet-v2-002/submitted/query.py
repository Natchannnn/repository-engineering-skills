import json
from pathlib import Path

LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")


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


def _read_all() -> list[dict]:
    ledger_path = Path(LEDGER_FILE)
    try:
        with ledger_path.open("r", encoding="utf-8") as ledger_file:
            return [json.loads(line) for line in ledger_file if line.strip()]
    except FileNotFoundError:
        return []
