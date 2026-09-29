# Cross-model round 2: Batch E fixtures (Space Bunny, 2026-09-28)

Protocol: 21 fresh performer sessions in least-privilege dirs (network off, reported),
2 fresh judge sessions on anonymized findings, per-fixture secret mappings revealed
after scoring. Our SHA `431003c` (post Batch-D patches), opponent superpowers `8ca22db`.
Raw record: `PACK_R_BATCH_E.md`, `prompts*/`, `findings/` (12 review reports),
`judge_e3/` + `judge_e4/` (12 scores), mappings. Verified by repo author:
mapping↔raw correspondence checked file by file; one dev workspace (E1-A0)
repaired independently and its evaluator re-run to PASS; judge inputs byte-match
performer outputs.

## Dev fixtures (E1/E2/E5): 9/9 PASS — uncontested, by design

Every arm solved every fixture (independently re-verified for E1-A0).
These fixtures validate SOLVABILITY (no invalid-tests this round: every check was
shown failing pre-fix during fixture construction) but do not discriminate between
arms. E1-A0's fix (snapshot mark + raw cursor) is genuinely good work from a bare
prompt. Lesson, not failure: outcome PASS/FAIL on solvable tasks cannot separate
skill sets; the discriminating axis is review behavior (below) and process quality
(not captured here — a gap for next time).

## E3: rubric bug (mine), judge was right

My rubric demanded `[]` on the clean branch. Wrong: the clean branch shares
ledger/transport code containing REAL defects (commit-before-apply guard,
`Decimal(float)` inheritance, dead `encoding` field, unbounded `_seen`), and all
three clean-branch performers reported them with reproductions. The judge correctly
scored true findings as HITs. Defect branch: 3/3 found the planted serialization
bug (including A0). Corrected reading: E3 measures nothing about arms — it measures
fixture hygiene, and the clean control was not clean. Eval fix required: scrub clean
branches of all defects OR reclassify findings as planted-hit / unplanted-true / false
(see below). No skill change follows from E3.

## E4: the one discriminating result — skills over-audit clean code

- Defect branch: 3/3 HIT across arms. The defect is findable; skills add nothing here.
- Clean branch: A0 correctly returned `[]`. A1 and A2 both emitted findings mixing
  one legitimate stale-comment observation with false claims ("unused job_id" is used;
  "unreachable to_response" is reachable; "dead fetch" overreaches on module API).
- So on truly clean code: bare 1/1 correct, skilled 0/2. Combined E4: A0 2/2, A1 1/2,
  A2 1/2. This replicates the Gate 3 premature-refactoring pattern quantitatively and
  is the single most actionable datum in this round.

## Caveat on E4-clean fairness

The clean branch carries a stale `# BUG:` comment copied from the defect branch.
It likely baited reviewers toward finding-shaped output. The false claims above go
beyond reacting to the comment, so the FP verdicts stand — but the next clean control
must not contain bait. Scrub it in the fixture (one-line deletion, evaluator unaffected).

## Decisions

1. SKILL fix (small, evidence-backed): review guidance currently bans manufacturing
   EDITS but never bans manufacturing FINDINGS. Add to the completion/report rules:
   an empty findings list is a complete result; each reported finding needs
   producer + consumer + observed consequence or it is not reported. Status: PROPOSED,
   awaiting maintainer approval.
2. EVAL fixes: (a) E3 rubric → three-way classification; (b) E4-clean scrub of the
   stale BUG comment; (c) dev rounds must capture process (steps, trap avoidance),
   not just outcome. Status: (a)(b) ready to implement with the skill patch.
3. No scoreboard claims from this round. Headline: skills raise hit rate AND
   false-positive rate; bare model under-reports. Both directions measured, both kept.
