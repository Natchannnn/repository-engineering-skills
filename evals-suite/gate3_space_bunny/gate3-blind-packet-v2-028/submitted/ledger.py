"""Append-only JSON-lines event ledger.

CP1 slice: durable appends and ordered reads. CP3 makes every event
multi-tenant and adds migrate() for ledgers written before that rule. The
ledger file is resolved relative to this module so callers are unaffected by
the working directory.
"""

import json
import os
import tempfile

LEDGER_FILE = "ledger.jsonl"
LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), LEDGER_FILE)

# Stands in for a tenant that a pre-CP3 record never carried, or carried
# unusable, so migrated records stay queryable by tenant.
DEFAULT_TENANT = "default"


def _load() -> tuple[bytes, list[dict]]:
    """Return the ledger's raw bytes plus its parsed records in file order."""
    try:
        with open(LEDGER_PATH, "rb") as handle:
            raw = handle.read()
    except FileNotFoundError:
        return b"", []
    records = [
        json.loads(line)
        for line in raw.decode("utf-8").splitlines()
        if line.strip()
    ]
    return raw, records


def read_all() -> list[dict]:
    """Return every stored record in file order; an absent ledger reads empty."""
    return _load()[1]


def append(event: dict) -> int:
    """Store one event and return its ledger ID.

    Both `kind` and `tenant` are required, and `tenant` must be a non-blank
    string: a record that cannot be attributed to a tenant is unusable for
    multi-tenant queries, so it is rejected rather than stored with a guess.

    Validation runs before any filesystem write, so a rejected event leaves
    ledger.jsonl byte-for-byte unchanged and no temp file behind.
    """
    if not isinstance(event, dict):
        raise TypeError(f"event must be a dict, got {type(event).__name__}")
    if "kind" not in event:
        raise ValueError("event must carry a 'kind' field")
    kind = event["kind"]
    if not isinstance(kind, str):
        raise TypeError(f"'kind' must be a str, got {type(kind).__name__}")
    if not kind.strip():
        raise ValueError("'kind' must not be empty or whitespace-only")
    if "tenant" not in event:
        raise ValueError("event must carry a 'tenant' field")
    tenant = event["tenant"]
    if not isinstance(tenant, str):
        raise ValueError(f"'tenant' must be a str, got {type(tenant).__name__}")
    if not tenant.strip():
        raise ValueError("'tenant' must not be empty or whitespace-only")

    raw, records = _load()
    event_id = len(records) + 1
    # An event carrying its own "id" key overrides the assigned one, per the
    # {"id": <id>, **event} record contract.
    record = {"id": event_id, **event}

    line = json.dumps(record).encode("utf-8") + b"\n"
    if raw and not raw.endswith(b"\n"):
        line = b"\n" + line
    _write_atomic(raw + line)
    return event_id


def migrate() -> int:
    """Give every tenant-less or unusable-tenant record a default tenant.

    Returns how many records were repaired. Records already carrying a
    non-empty string tenant are left untouched, so a ledger that needs no
    migration is not rewritten at all. IDs, record order, and every other key
    are preserved.
    """
    records = _load()[1]
    repaired = 0
    for record in records:
        tenant = record.get("tenant")
        if not isinstance(tenant, str) or tenant == "":
            record["tenant"] = DEFAULT_TENANT
            repaired += 1
    if repaired == 0:
        return 0
    payload = b"".join(
        json.dumps(record).encode("utf-8") + b"\n" for record in records
    )
    _write_atomic(payload)
    return repaired


def _write_atomic(payload: bytes) -> None:
    """Replace the ledger in a single step so no reader sees a partial file.

    Existing bytes are copied verbatim instead of re-serialized, which keeps
    records this module did not write at their original encoding.
    """
    directory = os.path.dirname(LEDGER_PATH)
    descriptor, temp_path = tempfile.mkstemp(
        dir=directory, prefix=LEDGER_FILE + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            # The rename is atomic for readers, but only a flushed file survives
            # an unclean shutdown.
            os.fsync(stream.fileno())
        os.replace(temp_path, LEDGER_PATH)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
