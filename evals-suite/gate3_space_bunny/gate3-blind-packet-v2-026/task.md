# CP2_SLICE — query pipeline

Build on the CP1 `ledger.py` contract (do not change its behavior):

- Implement `query.py` in the workspace root with `LEDGER_FILE = "ledger.jsonl"`
  (resolved relative to the module directory):
  - `get_by_id(n: int) -> dict | None`: the record whose `id == n`,
    or `None` when absent. A missing `ledger.jsonl` yields `None`.
  - `find(kind: str | None = None) -> list[dict]`: records whose `kind`
    equals `kind`; `kind=None` returns all records in file order.
    A missing `ledger.jsonl` yields `[]`.
- Preserve the CP1 contract byte-for-byte: `append` keeps sequential ids,
  atomic persistence, input validation, and extra-key preservation.

Blockers: CP1 storage must keep working (regression-guarded).
Do not modify trusted checks.
