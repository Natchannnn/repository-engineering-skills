import json
import os
import tempfile
from pathlib import Path


LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    kind = event.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        raise ValueError("event kind must be a non-blank string")

    records = read_all()
    next_id = len(records) + 1
    record = {"id": next_id, **event}
    encoded = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )

    existing = LEDGER_FILE.read_bytes() if LEDGER_FILE.exists() else b""
    separator = b"\n" if existing and not existing.endswith(b"\n") else b""

    fd, temporary_name = tempfile.mkstemp(
        dir=LEDGER_FILE.parent,
        prefix=f".{LEDGER_FILE.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "wb") as temporary_file:
            temporary_file.write(existing)
            temporary_file.write(separator)
            temporary_file.write(encoded)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, LEDGER_FILE)
    finally:
        temporary_path = Path(temporary_name)
        if temporary_path.exists():
            temporary_path.unlink()

    return next_id


def read_all() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []

    records = []
    with LEDGER_FILE.open("r", encoding="utf-8") as ledger_file:
        for line in ledger_file:
            if line.strip():
                records.append(json.loads(line))
    return records
