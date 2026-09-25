# CP3_EVOLUTION — multi-tenant contract evolution (deliberate replacement)

The event contract evolves. Implement the replacement exactly:

- `ledger.append` now REQUIRES a non-empty string `event["tenant"]`.
  Appends without it (missing, empty, blank, or non-string) raise
  `ValueError` and leave `ledger.jsonl` byte-identical.
- `query.find` gains an optional filter: `find(kind=None, tenant=None)`.
  Each non-`None` argument filters by exact match; both `None` returns all.
- `ledger.migrate() -> int`: rewrites `ledger.jsonl` atomically, backfilling
  `"tenant": "default"` into records missing it (or holding a non-string /
  empty tenant). Preserves `id` order and all other keys. Returns the number
  of records migrated. A missing `ledger.jsonl` yields `0`.
- Backward compatibility that must NOT break: `append` with a tenant keeps
  sequential ids, atomicity, validation, and extra-key preservation;
  kind-only `find(kind=...)` keeps working.

This checkpoint deliberately replaces the CP2 query contract — adopt the new
contract while preserving every unaffected behavior.
Do not modify trusted checks.
