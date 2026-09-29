# E8 run: double clock read (refactor-only target, built)

- Fixture: two single-file branches. Defect reads the clock on the expiry check
  AND again before stamping; clean captures once. No bait comments, no shared-code
  warts on clean (E3 lesson: a clean control must be actually clean).
- Evaluator: `evaluator/test_cache.py`, `BRANCH_DIR` selects variant. The stamp
  assertion is white-box on purpose (fixture-author oracle; `evaluator/` never
  ships to run dirs). The defect branch itself is the negative control —
  no separate mutant needed.

## Validation log

1. Defect: `test_single_capture_stamp` FAILs `expected stamp 110.0 (one clock read),
   got 210.0`; other 2 pass (basic hit/miss behavior intact).
2. Clean: 3 passed.
3. Build fix note: first draft measured a single get() on an empty store, where the
   `is not None` short-circuit skips the check-read — both branches stamped identically
   and the test passed on defect. Fixed by priming an expired entry first so the
   measured call actually takes the double-read path. Invalid-test class caught pre-arm.
4. Intended arms use: refactor-only (A2 = repo-native-refactor alone, no foundation)
   vs bare vs superpowers on both branches; E8 is plan item D.

Arms protocol (next round): least-privilege dirs (branch files only + arm skills),
neutral branch names, findings schema per E3/E4 (producer + consumer + consequence),
`[]` accepted on clean with reason. Expected bare failure: approve the tidy-looking
double read, or flag style instead of the stamp consequence.
