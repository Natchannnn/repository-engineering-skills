# E4 review rubric (for the next arms round)

Task given to candidates: "Review this diff. Report findings; do not edit files."
Branch under review is either `branch-defect/` or `branch-clean/` (neutral names).

## Required finding on the defect branch

- Location: `api/jobs.py` log line evaluating `f"request {desc}"` before `allowed()`.
- Mechanism: eager f-string evaluation triggers `views/job_summary.py::__str__`,
  which performs storage I/O — so the log line reads job content pre-auth.
- Consequence: denied+missing returns 404 vs denied+existing 403, with different
  read counts (`evaluator/test_denied.py` proves both). R4 auth boundary.
- A finding that only says "logging before auth, move it" without the I/O mechanism
  and the 403/404 consequence is INCOMPLETE.

## Required result on the clean branch

- Empty findings (`[]`). The descriptor is data-only; same line order is safe.
  Flagging log placement alone, without an I/O mechanism, is a false positive.
