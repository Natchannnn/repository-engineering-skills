# E5 run: absent/null/0 migration semantics (adversarial case 5, built)

Symptom prompt (all arms get ONLY this): "preview before migration disagrees with
behavior after restart."

- Fixture: `fixture/` — truthiness migrator drops `null` and `0`; preview (v1 reader)
  stays correct, which hides the bug. Contract in `fixture/docs/migration.md`:
  absent = inherit, null = disabled, 0 = run now. Scope: migrator + new tests + guide.
- Evaluator: `evaluator/test_migration.py` (restart round-trip through JSON;
  `FIXTURE_DIR` selects variant, separate processes).
- Solution: `solution/` (presence and value handled as separate facts).

## Validation log

1. Broken: headline FAILs `expected disabled, got scheduled(30)` (+ matrix FAIL on 0).
2. Solution: 5 passed (matrix absent/null/0/positive, round-trip, later-default,
   preview-agrees, consumer-untouched).
3. Trap-fix (materialize absent keys with today's default, /tmp, deleted):
   `test_inherited_value_tracks_later_default` FAILs `expected 60, got scheduled(30)` —
   today's correct value rots on the next default change.
4. Simplification vs the idea, stated openly: the doc-code-block oracle (running a
   guide snippet through the checker) was dropped as fragile; the consumer-scope
   oracle (no v2/record/migrat tokens in consumer sources) covers the same trap
   deterministically.

Arms protocol: A0 bare / A1 superpowers-4 / A2 ours (SKILL.md + shared-contracts +
evolution + migration-examples), least-privilege dirs. Expected bare failure: fix one
null branch, keep losing 0, or freeze inherited values as fixed overrides.
