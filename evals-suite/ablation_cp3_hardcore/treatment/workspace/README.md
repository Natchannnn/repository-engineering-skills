# Event Ledger (CP3)

Append-only JSON-lines event ledger with multi-tenant contracts, query, and CLI export.
See `tasks/cp1.md` … `tasks/cp4.md` for the milestone specs and `data/seed.json` for
sample vocabulary (kinds, tenants).

## Contracts

### `ledger.py`

- `append(event)` — Appends a record. Requires `event["kind"]` (non-blank string) and
  `event["tenant"]` (non-empty string); raises `ValueError` if either is missing, blank,
  or not a string. Write is atomic; `ledger.jsonl` is byte-identical on failure.
- `migrate() -> int` — Backfills `"tenant": "default"` into records missing a valid
  tenant. Rewrites `ledger.jsonl` atomically. Returns the count of records migrated.
  Missing file yields `0` without creating an empty file. Idempotent.
- `read_all() -> list[dict]` — Returns all records in file order.

### `query.py`

- `LEDGER_FILE = "ledger.jsonl"` — Path resolved relative to the module directory.
- `find(kind=None, tenant=None) -> list[dict]` — Returns records matching each non-`None`
  argument by exact match. Both `None` returns all records. Missing file yields `[]`.
- `get_by_id(n) -> dict | None` — Returns the record with `id == n`, or `None`.
