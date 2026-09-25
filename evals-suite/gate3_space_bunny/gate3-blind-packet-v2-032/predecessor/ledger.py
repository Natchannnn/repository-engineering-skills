"""Append-only JSON-lines event ledger.

The ledger file always lives next to this module, named by :data:`LEDGER_FILE`,
so reads and writes are independent of the process working directory.

Every record is multi-tenant: :func:`append` requires a usable ``tenant`` and
:func:`migrate` backfills the legacy records written before that rule existed.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

LEDGER_FILE = "ledger.jsonl"
LEDGER_PATH = Path(__file__).resolve().parent / LEDGER_FILE
DEFAULT_TENANT = "default"


def _ledger_path() -> Path:
    return LEDGER_PATH


def _is_usable_tenant(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_event(event: Any) -> None:
    if not isinstance(event, dict):
        raise TypeError(f"event must be a dict, got {type(event).__name__}")
    if "kind" not in event:
        raise ValueError("event must have a 'kind' key")
    kind = event["kind"]
    if not isinstance(kind, str):
        raise TypeError(f"event['kind'] must be a str, got {type(kind).__name__}")
    if not kind.strip():
        raise ValueError("event['kind'] must be a non-empty, non-whitespace string")
    if "tenant" not in event:
        raise ValueError("event must have a 'tenant' key")
    if not _is_usable_tenant(event["tenant"]):
        raise ValueError("event['tenant'] must be a non-empty, non-whitespace string")


def _parse(raw: bytes) -> list[dict]:
    records: list[dict] = []
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
    return records


def _read_raw(path: Path) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except FileNotFoundError:
        return b""


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _atomic_write(path: Path, payload: bytes) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f"{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        try:
            handle = open(fd, "wb")
        except BaseException:
            os.close(fd)
            raise
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        _unlink_quietly(tmp_path)
        raise


def append(event: dict) -> int:
    """Validate ``event``, append it to the ledger, and return its new integer id.

    ``event`` must carry a non-empty, non-whitespace ``kind`` string and a
    non-empty, non-whitespace ``tenant`` string. The id continues the existing
    numbering from 1. Extra keys are kept as given and the stored record is
    ``{"id": <id>, **event}``. Invalid input raises ``TypeError``/``ValueError``
    and leaves the ledger file untouched byte for byte.
    """
    _validate_event(event)

    path = _ledger_path()
    existing = _read_raw(path)

    new_id = len(_parse(existing)) + 1
    line = json.dumps({"id": new_id, **event}, ensure_ascii=False).encode("utf-8")

    payload = existing
    if payload and not payload.endswith(b"\n"):
        payload += b"\n"
    payload += line + b"\n"

    _atomic_write(path, payload)
    return new_id


def read_all() -> list[dict]:
    """Return every ledger record in file order, or ``[]`` if no ledger exists."""
    return _parse(_read_raw(_ledger_path()))


def migrate() -> int:
    """Backfill ``tenant`` on legacy records and return how many were repaired.

    A record is repaired when its ``tenant`` is absent, is not a string, or is an
    empty/whitespace-only string; it then receives ``DEFAULT_TENANT``. Record
    order, the existing ``id`` values and every other key are left untouched, so
    the rewrite goes out through the same atomic temp-file swap as :func:`append`.
    A ledger needing no repair is left byte for byte alone, and a missing ledger
    yields 0.
    """
    path = _ledger_path()
    records = _parse(_read_raw(path))
    if not records:
        return 0

    repaired = 0
    for record in records:
        if not _is_usable_tenant(record.get("tenant")):
            record["tenant"] = DEFAULT_TENANT
            repaired += 1

    if repaired == 0:
        return 0

    payload = b"".join(
        json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n" for record in records
    )
    _atomic_write(path, payload)
    return repaired
