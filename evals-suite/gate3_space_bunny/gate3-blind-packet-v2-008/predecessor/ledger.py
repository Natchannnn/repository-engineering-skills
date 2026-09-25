import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _read_snapshot() -> tuple[list[dict], bytes]:
    path = _ledger_path()
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return [], b""

    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return records, raw


def _valid_tenant(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _atomic_replace(path: Path, payload: bytes) -> None:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=".ledger-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(payload)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def read_all() -> list[dict]:
    records, _ = _read_snapshot()
    return records


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if "kind" not in event:
        raise ValueError("event must contain kind")
    if not isinstance(event["kind"], str):
        raise TypeError("event kind must be a string")
    if not event["kind"].strip():
        raise ValueError("event kind must not be blank")
    if "tenant" not in event or not _valid_tenant(event["tenant"]):
        raise ValueError("event tenant must be a non-blank string")

    path = _ledger_path()
    records, existing = _read_snapshot()
    assigned_id = len(records) + 1
    record = {"id": assigned_id, **event}
    payload = existing
    if payload and not payload.endswith(b"\n"):
        payload += b"\n"
    payload += (json.dumps(record) + "\n").encode("utf-8")
    _atomic_replace(path, payload)

    return assigned_id


def migrate() -> int:
    path = _ledger_path()
    records, _ = _read_snapshot()
    if not records:
        return 0

    migrated_records = []
    migrated_count = 0
    for record in records:
        if _valid_tenant(record.get("tenant")):
            migrated_records.append(record)
            continue
        migrated_record = dict(record)
        migrated_record["tenant"] = "default"
        migrated_records.append(migrated_record)
        migrated_count += 1

    if migrated_count == 0:
        return 0

    payload = b"".join(
        (json.dumps(record) + "\n").encode("utf-8")
        for record in migrated_records
    )
    _atomic_replace(path, payload)
    return migrated_count
