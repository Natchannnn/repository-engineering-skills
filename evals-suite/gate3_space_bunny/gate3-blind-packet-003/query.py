import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent


def _ledger_path() -> Path:
    configured_path = Path(LEDGER_FILE)
    if configured_path.is_absolute():
        return configured_path
    return _MODULE_DIR / configured_path


def _read_all() -> list[dict]:
    path = _ledger_path()
    try:
        with path.open("r", encoding="utf-8") as ledger:
            return [json.loads(line) for line in ledger if line.strip()]
    except FileNotFoundError:
        return []


def get_by_id(n: int) -> dict | None:
    for record in _read_all():
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None, tenant: str | None = None) -> list[dict]:
    records = _read_all()
    return [
        record
        for record in records
        if (kind is None or record.get("kind") == kind)
        and (tenant is None or record.get("tenant") == tenant)
    ]
