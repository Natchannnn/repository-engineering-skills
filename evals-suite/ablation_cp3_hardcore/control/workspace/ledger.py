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
    tenant = event.get("tenant")
    if not isinstance(tenant, str) or not tenant.strip():
        raise ValueError("event tenant must be a non-empty string")

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


def _needs_migration(record: dict) -> bool:
    """Return True if the record is missing a valid tenant value."""
    tenant = record.get("tenant")
    return not (isinstance(tenant, str) and tenant.strip())


def migrate() -> int:
    """Rewrite ledger.jsonl atomically, backfilling tenant="default" into
    records that are missing a valid tenant.

    Returns the number of records migrated. If ledger.jsonl does not exist,
    returns 0 without creating an empty file. Subsequent runs on an already
    fully-migrated ledger return 0.
    """
    if not LEDGER_FILE.exists():
        return 0

    records = read_all()
    migrated = 0
    new_records = []
    for record in records:
        if _needs_migration(record):
            record = {**record, "tenant": "default"}
            migrated += 1
        new_records.append(record)

    if migrated == 0:
        return 0

    lines = b"".join(
        (json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        for r in new_records
    )

    fd, temporary_name = tempfile.mkstemp(
        dir=LEDGER_FILE.parent,
        prefix=f".{LEDGER_FILE.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "wb") as temporary_file:
            temporary_file.write(lines)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, LEDGER_FILE)
    finally:
        temporary_path = Path(temporary_name)
        if temporary_path.exists():
            temporary_path.unlink()

    return migrated


def read_all() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []

    records = []
    with LEDGER_FILE.open("r", encoding="utf-8") as ledger_file:
        for line in ledger_file:
            if line.strip():
                records.append(json.loads(line))
    return records
