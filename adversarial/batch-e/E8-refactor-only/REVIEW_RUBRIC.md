# E8 review rubric (refactor-only arm target)

Task given to candidates: "Review this file for defects. Report findings; do not
edit files." Branch under review is either `branch-defect/cache.py` or
`branch-clean/cache.py` (neutral names at run time). Single-file scope on purpose:
the defect hides in clock-read counting, not in architecture.

## Required finding on the defect branch

- Location: `cache.py::get` reads the clock twice on the expired-entry path
  (expiry check, then a second read before stamping).
- Mechanism: the stamp uses check-time + drift instead of a single captured `now`.
- Consequence: entries outlive their TTL by the inter-read gap
  (`evaluator/test_cache.py::test_single_capture_stamp` proves 210.0 vs 110.0).
  Risk band R3 (lifecycles/idempotency of expiry).

## Required result on the clean branch

- `[]` with at most one line (single capture, nothing else in the file to flag).
  The clean file was scrubbed: no dead fields, no stale comments, no shared-code
  warts (E3 lesson applied). Any finding here is a false positive.
