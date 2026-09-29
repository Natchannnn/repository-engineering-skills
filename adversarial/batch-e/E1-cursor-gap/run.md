# E1 run: cursor over filtered gap (Astra idea 1, built)

Symptom prompt (all arms get ONLY this, never the docs below): "resume export from
checkpoint sometimes misses data."

- Fixture: `fixture/` (broken: terminates on empty filtered page, cursor from last
  returned record, no snapshot). Normative repo convention in `fixture/docs/cursor-format.md`.
- Evaluator: `evaluator/test_resume.py`, `FIXTURE_DIR` selects variant, separate process each.
- Solution: `solution/` (snapshot cursor, scan to exhaustion, filter after). Shared
  `storage`/`query`/`docs` copied identical into solution.

## Validation log (all run, recorded here)

1. Broken: `test_filtered_gap` FAILs `expected [101, 104], got [101]`; other 2 pass.
2. Solution: 3 passed.
3. Trap-fix (rescan whole store, /tmp, deleted after): FAILs test 1 AND test 2
   (leaks 105) — the snapshot test kills the tempting wrong fix.
4. Build fix note: first draft had `ACCEPTED = {101, 104}`, so the filter itself
   excluded 105 and the snapshot bound was never exercised. Fixed to include 105;
   re-ran all directions. This is exactly the invalid-test class from V1 — caught
   before any arm runs.

Arms protocol for next round: A0 bare / A1 superpowers-4 / A2 ours, least-privilege
dirs (A2 gets SKILL.md + shared-contracts + evolution + migration-examples only),
symptom prompt + fixture files, outputs DECISION + reason. Expected bare failure:
terminate-on-empty-page or rescan (both caught above).
