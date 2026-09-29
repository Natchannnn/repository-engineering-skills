# E2 run: live-state integrity vs durable file (Astra idea 2, built)

Symptom prompt (all arms get ONLY this): "stock report disagrees with itself after
a failed refresh."

- Fixture: `fixture/` — `refresh()` mutates the shared dict while input may still fail,
  disk write last. Contract in `fixture/docs/api.md`: failure preserves disk AND held
  views; success updates both; replacing the dict object is forbidden. Scope: service only.
- Evaluator: `evaluator/test_refresh.py` (OSError injected at replace seam; mid-iteration
  ValueError feed; `FIXTURE_DIR` selects variant, separate processes).
- Solution: `solution/` (stage all rows → save → clear+update in place, views stay live).

## Validation log

1. Broken: `test_replace_failure_preserves_state` + `test_iterator_error_preserves_state`
   FAIL with `expected live view {'sku': 1}, got {'sku': 2}`; file hash unchanged in both
   (the trap: disk looks fine, memory does not).
2. Solution: 4 passed.
3. Trap-fix (assign a NEW dict object, /tmp, deleted): `test_existing_view_observes_success`
   FAILs — held MappingProxyType views go stale. The view test kills the tempting fix.
4. Build fix note: first draft modeled rows as `{"sku": ..., "qty": ...}` while tests fed
   `{"sku": 2}` — everything failed including solution. Remodeled rows as `{key: value}`
   single-key dicts, re-ran all directions. Invalid-test class caught pre-arm again.

Arms protocol: A0 bare / A1 superpowers-4 / A2 ours (SKILL.md + shared-contracts +
evolution + migration-examples), least-privilege dirs, symptom prompt + fixture files.
Expected bare failure: declare victory from the intact file, add tmp cleanup or a catch,
miss memory + stale aliases. Verdict for candidate fixes: full suite green + no new-dict swap.
