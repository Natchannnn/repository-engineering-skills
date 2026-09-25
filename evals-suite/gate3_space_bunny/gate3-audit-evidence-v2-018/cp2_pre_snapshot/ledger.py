import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def read_all() -> list[dict]:
    path = _ledger_path()
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    records = []
    for line in contents.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if "kind" not in event:
        raise ValueError("event must contain kind")
    kind = event["kind"]
    if not isinstance(kind, str):
        raise TypeError("event kind must be a string")
    if not kind.strip():
        raise ValueError("event kind must not be empty or whitespace")

    next_id = len(read_all()) + 1
    record = {"id": next_id, **event}
    encoded_record = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

    path = _ledger_path()
    try:
        existing = path.read_bytes()
    except FileNotFoundError:
        existing = b""
    if existing and not existing.endswith(b"\n"):
        existing += b"\n"
    replacement = existing + encoded_record

    directory = path.parent
    temporary_path = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{LEDGER_FILE}.",
            suffix=".tmp",
            dir=directory,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(replacement)
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

    return next_id
