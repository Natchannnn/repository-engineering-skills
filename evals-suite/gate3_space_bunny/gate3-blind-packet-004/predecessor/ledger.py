import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent


def _ledger_path() -> Path:
    configured_path = Path(LEDGER_FILE)
    if configured_path.is_absolute():
        return configured_path
    return _MODULE_DIR / configured_path


def read_all() -> list[dict]:
    path = _ledger_path()
    try:
        with path.open("r", encoding="utf-8") as ledger:
            return [json.loads(line) for line in ledger if line.strip()]
    except FileNotFoundError:
        return []


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(payload)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if "kind" not in event:
        raise ValueError("event must contain kind")
    kind = event["kind"]
    if not isinstance(kind, str):
        raise TypeError("event kind must be a string")
    if not kind.strip():
        raise ValueError("event kind must not be blank")
    tenant = event.get("tenant")
    if not isinstance(tenant, str) or not tenant.strip():
        raise ValueError("event tenant must be a non-empty string")

    next_id = len(read_all()) + 1
    record = {"id": next_id, **event}
    record["id"] = next_id
    record_bytes = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

    path = _ledger_path()
    existing_bytes = path.read_bytes() if path.exists() else b""
    payload = existing_bytes
    if existing_bytes and not existing_bytes.endswith((b"\n", b"\r")):
        payload += b"\n"
    payload += record_bytes
    _atomic_write(path, payload)

    return next_id


def migrate() -> int:
    path = _ledger_path()
    if not path.exists():
        return 0

    records = read_all()
    migrated_records = []
    changed = 0
    for record in records:
        tenant = record.get("tenant")
        if isinstance(tenant, str) and tenant.strip():
            migrated_records.append(record)
            continue
        migrated_record = dict(record)
        migrated_record["tenant"] = "default"
        migrated_records.append(migrated_record)
        changed += 1

    if changed:
        payload = b"".join(
            (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
            for record in migrated_records
        )
        _atomic_write(path, payload)

    return changed
