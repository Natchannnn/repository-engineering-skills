import json
from pathlib import Path

LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")


def get_by_id(n: int) -> dict | None:
    for record in _read_all():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None, tenant: str | None = None) -> list[dict]:
    return [
        record
        for record in _read_all()
        if (kind is None or record.get("kind") == kind)
        and (tenant is None or record.get("tenant") == tenant)
    ]


def _read_all() -> list[dict]:
    ledger_path = Path(LEDGER_FILE)
    try:
        with ledger_path.open("r", encoding="utf-8") as ledger_file:
            return [json.loads(line) for line in ledger_file if line.strip()]
    except FileNotFoundError:
        return []
