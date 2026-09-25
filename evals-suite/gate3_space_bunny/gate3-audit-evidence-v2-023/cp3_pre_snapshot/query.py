import json
from pathlib import Path


LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")


def _read_all() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []

    records = []
    with LEDGER_FILE.open("r", encoding="utf-8") as ledger_file:
        for line in ledger_file:
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
