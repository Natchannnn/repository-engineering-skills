import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if "kind" not in event:
        raise ValueError("event must contain kind")
    if not isinstance(event["kind"], str):
        raise TypeError("event kind must be a string")
    if not event["kind"].strip():
        raise ValueError("event kind must not be blank")
    tenant = event.get("tenant")
    if not isinstance(tenant, str) or not tenant.strip():
        raise ValueError("event tenant must be a non-empty string")

    event_id = len(read_all()) + 1
    record = {"id": event_id, **event}
    serialized = json.dumps(
        record,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"

    ledger_path = Path(LEDGER_FILE)
    existing = ledger_path.read_bytes() if ledger_path.exists() else b""
    if existing and not existing.endswith(b"\n"):
        existing += b"\n"

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=ledger_path.parent,
            prefix=f".{ledger_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(existing)
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, ledger_path)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    return event_id


def migrate() -> int:
    records = read_all()
    migrated = 0
    for record in records:
        tenant = record.get("tenant")
        if not isinstance(tenant, str) or not tenant.strip():
            record["tenant"] = "default"
            migrated += 1

    if migrated == 0:
        return 0

    serialized = b"".join(
        json.dumps(
            record,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
        for record in records
    )
    ledger_path = Path(LEDGER_FILE)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=ledger_path.parent,
            prefix=f".{ledger_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, ledger_path)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    return migrated


def read_all() -> list[dict]:
    ledger_path = Path(LEDGER_FILE)
    try:
        with ledger_path.open("r", encoding="utf-8") as ledger_file:
            return [json.loads(line) for line in ledger_file if line.strip()]
    except FileNotFoundError:
        return []
