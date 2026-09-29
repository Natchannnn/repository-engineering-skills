# E3 run: same-JSON double-apply (adversarial case 3, built)

Symptom prompt (review-only, both branches get the same words): "Review this branch.
Report findings; do not edit files." No mention of ledger, hash, or retry.

- Defect branch: serializer emits sorted-key compact bytes; `json.loads` equality holds,
  suite-green illusion intact; retry of the historical receipt re-applies (12.50 → 25.00).
- Clean branch: genuine internal restructure (`_fields` + `_encode`), byte-identical
  output. Flagging it = false positive.
- Evaluator: `evaluator/test_retry.py`, `BRANCH_DIR` selects variant, separate processes.

## Validation log

1. Defect: FAILs `expected balance Decimal('12.50'), got Decimal('25.00')`.
2. Clean: 1 passed (byte identity holds through the restructure).
3. Negative control per idea spec (re-enable the serialization change while parsed
   objects stay equal) IS the defect branch itself — evaluator FAILs on it, so the
   oracle provably does not rely on `json.loads` equality.
4. Review rubric: `REVIEW_RUBRIC.md` (producer + consumer + consequence required;
   `[]` on clean; `hash_tree.py` workspace check for the round operator).

Arms protocol: A0 bare / A1 superpowers-4 / A2 ours (SKILL.md + shared-contracts +
semantic-risk + refactor-examples), least-privilege dirs, neutral branch names at run
time. Expected bare failure: compare parsed objects, see equality, return [].
