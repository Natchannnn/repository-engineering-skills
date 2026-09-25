"""Read-only query helpers over the append-only event ledger.

The ledger location and the parsing rules mirror ``ledger.py`` so that records
written by ``append`` are observed here exactly as they were stored. Nothing in
this module writes to the ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
LEDGER_PATH = Path(__file__).resolve().parent / LEDGER_FILE


def _ledger_path() -> Path:
    return LEDGER_PATH


def _read_raw(path: Path) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except FileNotFoundError:
        return b""


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


def get_by_id(n: int) -> dict | None:
    """Return the first record whose ``id`` equals ``n``, or ``None``.

    A missing ledger, an out-of-range ``n`` and a non-integer ``n`` all yield
    ``None``. Records are scanned in file order, so no ordering assumption is
    made about the stored ids.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        return None
    for record in _parse(_read_raw(_ledger_path())):
        if record.get("id") == n:
            return record
    return None


def find(kind: str | None = None) -> list[dict]:
    """Return records in file order, keeping only those whose ``kind`` matches.

    ``kind=None`` returns every record. Matching is exact and case-sensitive;
    no stripping, folding or substring behaviour is applied.
    """
    records = _parse(_read_raw(_ledger_path()))
    if kind is None:
        return records
    return [record for record in records if record.get("kind") == kind]
