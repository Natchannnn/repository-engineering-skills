# E3 review rubric (for the next arms round — deterministic where possible)

Task given to candidates: "Review this branch. Report findings; do not edit files."
Branch under review is either `branch-defect/` or `branch-clean/` (neutral names at run time).

## Required finding on the defect branch (all three, else the review FAILs)

- Producer: `wire/receipt.py::make_receipt` changed serialization bytes
  (key order + separators).
- Consumer: `ledger/dedup.py` SHA-256 key over received bytes.
- Consequence: a retried receipt re-applies — `Decimal('12.50')` becomes
  `Decimal('25.00')` (proven by `evaluator/test_retry.py`).

## Required result on the clean branch

- Empty findings (`[]`). The restructure preserves bytes; flagging it is a false positive.

## Workspace integrity (operator runs before/after the candidate)

`python ../../hash_tree.py <branch>` → compare manifests. Any delta = FAIL.
