# Drift matrix: do the two skills agree with each other?

Method: pairwise comparison of overlapping rules + a divergence fixture wherever the
texts can produce opposite answers on identical facts. Checked 2026-09-28 against
skill v0.2.0 (post `shared-contracts.md` dedup).

| # | Pair | Verdict | Note |
|---|---|---|---|
| 1 | Contract rule: shared §1 vs `evolution.md` §1 vs refactor boundary protection | AGREE | All three defer to task-authorized change, preserve the rest. The old `str`/`Path` duplication is gone (canonical §1). |
| 2 | Evidence hierarchy: refactor 8-level vs evolution 5-level | **DIVERGE** | `drift-01`: tests rank 5th in one, unranked in the other. Opposite answers when sibling is silent. Patch proposed in `drift-01/case.md` (P1). |
| 3 | Verification: `verification.md` §4 vs `testing-integrity.md` | AGREE | Latter is a strict superset (tautology, mock theatre, coupling). "Update tests on contract change" in both, both demand explicit reporting. |
| 4 | Failure classification (4 kinds) vs error-reliability ownership | AGREE | Different axes (sorting failures vs owning errors), no contradiction found. |
| 5 | Prose: foundation bullets vs `repository-prose.md` surfaces | AGREE by inspection | Same delete/preserve line. Residual: 5-line vs 154-line depth gap means terse readers under-apply; P2 (add 2-line pointer, not a rule change). |
| 6 | Scope: "no out-of-scope cleanup" vs refactor's cleanup purpose | AGREE via gate | Companion coordination + evidence gate mediate explicitly. No case found where both authorize opposite actions. |

Net: 1 genuine divergence (pair 2), 0 contradictions in contracts/verification, 1 depth-gap note.
The dedup to `shared-contracts.md` held everywhere it was applied — the remaining drift is
exactly where dedup has not been applied yet (hierarchies). Lesson: finish the dedup.
