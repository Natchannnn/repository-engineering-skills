import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _decode_records(data: bytes) -> list[dict]:
    records = []
    for line in data.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _is_valid_tenant(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _write_atomically(path: Path, data: bytes) -> None:
    fd, temporary_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")

    kind = event.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        raise ValueError("event kind must be a non-empty string")

    tenant = event.get("tenant")
    if not _is_valid_tenant(tenant):
        raise ValueError("event tenant must be a non-empty string")

    path = _ledger_path()
    existing = path.read_bytes() if path.exists() else b""
    event_id = len(_decode_records(existing)) + 1
    record = {"id": event_id, **event}
    encoded_record = (json.dumps(record) + "\n").encode("utf-8")

    if existing and not existing.endswith(b"\n"):
        existing += b"\n"

    _write_atomically(path, existing + encoded_record)
    return event_id


def migrate() -> int:
    path = _ledger_path()
    if not path.exists():
        return 0

    records = _decode_records(path.read_bytes())
    migrated_count = 0
    for index, record in enumerate(records):
        if not _is_valid_tenant(record.get("tenant")):
            records[index] = {**record, "tenant": "default"}
            migrated_count += 1

    if migrated_count == 0:
        return 0

    data = b"".join(
        (json.dumps(record) + "\n").encode("utf-8") for record in records
    )
    _write_atomically(path, data)
    return migrated_count


def read_all() -> list[dict]:
    path = _ledger_path()
    if not path.exists():
        return []
    return _decode_records(path.read_bytes())
