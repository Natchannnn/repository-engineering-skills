# CP1_BOOTSTRAP — atomic storage

Implement `ledger.py` in the workspace root with:

- `LEDGER_FILE = "ledger.jsonl"` (resolved relative to the module directory).
- `append(event: dict) -> int`:
  - `event` must be a `dict` with a non-empty string `event["kind"]`;
    any other type, missing `kind`, or empty/blank `kind` raises
    `TypeError`/`ValueError` and leaves `ledger.jsonl` byte-identical.
  - Extra keys are preserved verbatim.
  - The record is assigned the next integer id starting at 1
    (`id = number of existing records + 1`) and stored as
    `{"id": <id>, **event}`.
  - Persistence is atomic: write to a temporary file in the same directory
    then `os.replace` onto `ledger.jsonl`. No `*.tmp` files may remain.
  - Returns the assigned id.
- `read_all() -> list[dict]`: returns all records in file order;
  a missing `ledger.jsonl` yields `[]`.

You may consult `README.md` and `data/seed.json` for vocabulary.
Blockers: none (greenfield). Do not modify trusted checks.
