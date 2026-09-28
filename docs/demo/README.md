# Demo runs (recorded)

Two self-contained fixtures. Each has an independent `verify.py` — no LLM judge.

## Demo 1: read-only contract drift

```sh
python examples/read-only-contract-review/verify.py
```

Breaks `get_account_tier()` return shape, expects a `KeyError: 'discount_pct'` finding with file + symbol + caller. Fails on negated verdicts, path traversal, or any worktree mutation.

## Demo 2: scoped feature dev

```sh
python examples/foundation-development/verify.py
```

Adds `export-json` to `metric_hub`, checks feature + regression suites, JSON schema, and scope confinement to `src/metric_hub/` + `tests/` + `README.md`.

## Recording

`demo-40s.gif` is intentionally not committed (keeps the repo lean). To reproduce for a release:

1. Fresh Windows Terminal, 120x30.
2. Run Demo 1 verify (expect FAIL finding format demo), then Demo 2 verify.
3. Export under 2MB to `docs/demo/demo-40s.gif` or link an unlisted video here.
