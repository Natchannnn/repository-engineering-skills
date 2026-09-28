# C2 run 1 (positive): colorama init/deinit regression test

- Operator: AI assistant (OpenCode session), guided by `repo-foundation` Continue + `repo-native-refactor` review.
- Target: `tartley/colorama` @ `841634e` (shallow clone, temp dir, no fork, no upstream PR).
- Date: 2026-09-28. Windows, Python 3.14. Baseline must run with
  `python -m pytest --import-mode=importlib` (installed colorama in site-packages
  shadows the clone otherwise — environment quirk, documented here).
- Honest labels: n=1, single operator (me), no blind judge.

## Baseline (before change)

`42 passed, 10 skipped` — green. (`InitTest` skips without a tty; pre-existing.)

## Task (foundation Continue, lightweight path)

Gap found by inspection: `deinit()` exists in `colorama/initialise.py` but no test
asserts the init → wrap → deinit → restore round-trip. Leaked wrapped streams are
exactly the resource-lifecycle class the skill cares about.

Change (`colorama/tests/initialise_test.py`, +12/-1, test-only, no production code):
`testInitDeinitRestoresOriginalStreams` — init under mocked win32, assert wrapped,
deinit, assert identity restored. Same decorators and assert helpers as siblings.

## Verification (all on the final state)

- Full suite after change: `42 passed, 11 skipped` (was 10 skipped; +1 is the new test,
  skipped here for the same pre-existing no-tty reason as its 11 siblings).
- Test logic executed directly (setUp tty-gate bypassed): `LOGIC-VERIFIED-PASS`.
- Negative control (deinit neutered in test namespace): fails as expected with
  `stdout should not be wrapped` — the test has teeth (`HAS-TEETH`).
- Refactor review of the diff: R1, test-only, matches file conventions
  (top-level import, same patches, same asserts). No cleanup warranted.

## Verdict: PASS with a documented caveat

The committed test runs green on tty CI like its siblings; in this no-tty environment
its logic was verified by direct execution + negative control instead. No production
contract touched, scope confined to one test file.
