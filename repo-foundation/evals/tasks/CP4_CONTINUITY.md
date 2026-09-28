# CP4_CONTINUITY — CLI export / handover (fresh session)

You are a fresh session taking over prior work with zero memory of it:
read the repository state (code, not chat history) and implement `export.py`:

- CLI: `python export.py --tenant T --format csv|json --out PATH`
  - Reads `ledger.jsonl` next to the module. A missing ledger is an error
    (exit code 2 with a message on stderr).
  - `--tenant` (required) filters records by exact tenant match.
    Unknown tenants export empty (csv: header only; json: `[]`), exit 0.
  - `--format csv`: writes header `id,kind,tenant,payload` then one row per
    record; `payload` is the JSON encoding of the record minus
    `id`/`kind`/`tenant`, with keys sorted and no spaces.
    Rows ordered by ascending `id`.
  - `--format json`: writes the filtered record list as JSON (file order).
  - `--summary`: also prints one `kind:<k> count:<n>` line per kind
    present in the FILTERED set, sorted by kind, to stdout.
  - Exit 0 on success (including empty exports).
- Do not change `ledger.py` / `query.py` behavior; all prior contracts stay green.

Note: this checkpoint runs in a fresh session with no prior conversation.
Do not modify trusted checks.
