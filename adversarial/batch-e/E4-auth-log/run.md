# E4 run: logging side effect before auth (adversarial case 4, built)

Symptom prompt (review-only): "Review this diff." No mention of auth, logging order,
descriptors, or error mapping. Clean and defect branches differ ONLY in
`views/job_summary.py` (I/O descriptor vs data-only descriptor).

- Evaluator: `evaluator/test_denied.py`, `BRANCH_DIR` selects variant, separate processes.

## Validation log

1. Defect: both tests FAIL (`expected 403, got 404`; read-count assertion).
2. Clean: 2 passed — same log line + same auth order, safe because no I/O exists.
   This is the paired control that punishes placement-only flagging.
3. Trap-fix (catch KeyError, still 403): status test passes, read-count test FAILs
   `expected 0, got 2` — the oracle is not fooled by status-only repairs.
4. Review rubric: `REVIEW_RUBRIC.md` (location + I/O mechanism + 403/404 consequence
   required; `[]` on clean; `hash_tree.py` workspace check).

Arms protocol: A0 bare / A1 superpowers-4 / A2 ours (SKILL.md + shared-contracts +
semantic-risk + error-reliability), least-privilege dirs, neutral branch names.
Expected bare failure: read the log line, see no signature change, test unauthorized
with an EXISTING id only, declare clean — never exercising eager evaluation or mapping.
