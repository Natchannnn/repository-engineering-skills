# Demo runs (recorded)

![demo](demo-40s.gif)

Rendered directly from the test harness via `python scripts/render-demo-gif.py` (Pillow only, deterministic). Re-run that script to regenerate after verifier changes.

Two self-contained fixtures. Each has an independent `verify.py`, no LLM judge.

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

To re-record after verifier changes: `python scripts/render-demo-gif.py` (Pillow only, deterministic seed).
For a real screen capture instead: fresh Windows Terminal 120x30, run the two verifies above, export under 2MB with ScreenToGif and overwrite `demo-40s.gif`.
