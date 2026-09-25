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

    path = _ledger_path()
    existing = path.read_bytes() if path.exists() else b""
    event_id = len(_decode_records(existing)) + 1
    record = {"id": event_id, **event}
    encoded_record = (json.dumps(record) + "\n").encode("utf-8")

    if existing and not existing.endswith(b"\n"):
        existing += b"\n"

    _write_atomically(path, existing + encoded_record)
    return event_id


def read_all() -> list[dict]:
    path = _ledger_path()
    if not path.exists():
        return []
    return _decode_records(path.read_bytes())
