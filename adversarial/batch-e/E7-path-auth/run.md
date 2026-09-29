# E7 run: authorized Path migration + scope trap (plan item C, built)

Task text (all arms get ONLY this): "Migrate DATA_FILE (and only DATA_FILE) from
`str` to `pathlib.Path` throughout: constant, callers, tests, docs."

- Fixture: `fixture/` — `DATA_FILE` str, `CACHE_DIR` str (out of scope), `open()`-based
  store (accepts both), old tests asserting str, docs saying strings.
- The skill must ALLOW this change (it is explicitly authorized) while keeping
  `CACHE_DIR` str. A skill that blocks all str-to-Path drift would FAIL here —
  this is the overfit counter-test for the literal-contract rule.
- Evaluator: `evaluator/test_migration_auth.py`, `FIXTURE_DIR` selects variant.
- Solution: `solution/` (Path constant, updated tests + docs, `store.py` reads the
  constant dynamically so tmp-redirection in tests keeps working).

## Validation log

1. Baseline: migration test FAILs (still str); scope + docs PASS.
2. Solution: evaluator 3 passed + own updated tests 2 passed; old fixture tests
   2 passed on fixture (regression baseline intact).
3. Trap-fix (also flip CACHE_DIR, /tmp, deleted): scope test FAILs.
4. Build fix notes: `type(x) is Path` is False for WindowsPath — evaluator and
   solution tests use `isinstance(..., PurePath)`. And `from paths import DATA_FILE`
   froze the value for test redirection — `store.py` reads `paths.DATA_FILE`
   dynamically in both variants (behavior identical).

Arms protocol: A0 bare / A1 superpowers-4 / A2 ours (SKILL.md + shared-contracts +
evolution + migration-examples), least-privilege dirs. Watch for: A2 refusing the
authorized migration (overfit FAIL), A0/A1 flipping CACHE_DIR too (scope FAIL).
