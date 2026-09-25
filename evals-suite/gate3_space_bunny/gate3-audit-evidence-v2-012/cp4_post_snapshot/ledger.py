import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent


def _ledger_path() -> Path:
    return _MODULE_DIR / LEDGER_FILE


def _read_bytes() -> bytes:
    try:
        return _ledger_path().read_bytes()
    except FileNotFoundError:
        return b""


def _records_from_bytes(data: bytes) -> list[dict]:
    records = []
    for line in data.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def read_all() -> list[dict]:
    return _records_from_bytes(_read_bytes())


def _atomic_write(data: bytes) -> None:
    path = _ledger_path()
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if "kind" not in event:
        raise ValueError('event must contain a non-empty "kind"')
    kind = event["kind"]
    if not isinstance(kind, str):
        raise TypeError('event["kind"] must be a string')
    if not kind.strip():
        raise ValueError('event["kind"] must not be blank')
    if "tenant" not in event:
        raise ValueError('event must contain a non-empty "tenant"')
    tenant = event["tenant"]
    if not isinstance(tenant, str) or not tenant.strip():
        raise ValueError('event["tenant"] must be a non-empty string')

    data = _read_bytes()
    new_id = len(_records_from_bytes(data)) + 1
    record = {"id": new_id, **event}
    encoded_record = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    if data and not data.endswith(b"\n"):
        encoded_record = b"\n" + encoded_record

    _atomic_write(data + encoded_record)
    return new_id


def migrate() -> int:
    try:
        data = _ledger_path().read_bytes()
    except FileNotFoundError:
        return 0

    records = _records_from_bytes(data)
    migrated = 0
    for record in records:
        tenant = record.get("tenant")
        if not isinstance(tenant, str) or not tenant.strip():
            record["tenant"] = "default"
            migrated += 1

    if migrated == 0:
        return 0

    encoded_data = b"".join(
        (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
        for record in records
    )
    _atomic_write(encoded_data)
    return migrated
