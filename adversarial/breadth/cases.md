# Breadth attacks (one per reference, v0.2.0)

Format per case: target → setup → walkthrough → verdict → patch (if any).
HOLDS = skill text decides correctly. AMBIGUOUS = text under-determines the answer.

## atk-01 bootstrap: junk that looks like precedent — AMBIGUOUS (P2)
Repo has `utils_v2_final/` full of workarounds plus empty scaffold dirs (`services/`, `handlers/`).
"Healthy precedent only + representative slice first" blocks adopting junk. HOLDS there.
Gap: "healthy" has no recognition test — a workaround with tests and docs passes every
written check. Patch P2: 3-line smell test (does any caller outside its author use it?
does it contradict docs? would you copy it to a new domain?).

## atk-02 continuity: stale notes vs new code, both plausible — HOLDS with note
Old handoff says "auth is stubbed, do not enforce"; new code enforces with tests.
Skill: don't auto-resolve, don't blind-rollback, reconcile + ask. Correct safe answer.
Note (no patch): no "what to do while blocked" beyond asking; acceptable.

## atk-03 evolution: two domains both claim ownership — AMBIGUOUS (P1)
`billing/` and `ledger/` both validate currency, each idiomatic in its domain.
"No premature homogenization" says don't unify; task says "consolidate validation".
Text gives no ownership test to decide WHO owns it. Patch P1: owner = whoever owns the
invariant's failure (who gets paged when it breaks) + reason-to-change check from DRY rule.

## atk-04 verification: green tests, missing acceptance — HOLDS
Feature ships, suite green, but acceptance requirement (CLI exit code) never asserted.
"Passing tests do not guarantee completeness" + requirement-bounded completion catch it.
Proven by the CP3 overreach note in our own history.

## atk-05 deterministic-tooling: two repo tools disagree — AMBIGUOUS (P2)
Linter A says dead code, scanner B (also repo-native) says it is a plugin entry point.
"Project tools first" gives no tiebreak. Patch P2: dynamic-import/plugin/generated
check wins over static scanners (already hinted in tooling doc — promote to rule).

## atk-06 error-reliability: unclear log owner — HOLDS with note
Retry/idempotency and fallback-vs-masking rules decide the standard cases.
Genuinely unclear ownership → "log at the boundary that detects it + say so" is the
documented fallback. No patch.

## atk-07 finding-taxonomy: cross-domain smell, two owners — AMBIGUOUS (P1)
Duplicated currency check across billing/ledger (same as atk-03 at finding level).
Taxonomy names consequence + owner per finding but not how to assign ONE owner across
domains. Same patch as atk-03 (single owner test), filed once.

## atk-08 repository-prose: invented ticket in the repo's real format — HOLDS with patch (P1)
Rule "never invent tickets" is absolute. Gap is procedural: no check step (search tracker?
ask author?). Patch P1: one line — "a reference you cannot click through to is fiction;
delete it." Add to prose examples.

## atk-09 rehabilitation: one domain mid-migration — HOLDS with note
"Verifiable batches" + stop-conditions cover sequencing; unstable domain goes last by
the failure-invariant logic. Implicit rather than stated — P2 clarity line at most.

## atk-10 semantic-risk: R2 extraction changes observable error text — AMBIGUOUS (P1)
Extracting a shared predicate alters error messages (observable contract) while staying
"structural". Neither R2 nor R3 claims it. Patch P1: any change to user/contract-visible
text escalates one band (R1→R2, R2→R3). Add to risk doc with example.

## atk-11 testing-integrity: repo-wide mock theatre as "precedent" — AMBIGUOUS (P1)
Whole repo mocks heavily; hierarchy's "healthy sibling" would bless mock theatre.
"Healthy" hole again (see atk-01). Patch P1: health test is outcome-based (would this test
fail if the behavior broke?), never popularity-based. One shared "healthy precedent" test
fixes atk-01 + atk-11 together — file under P1, single patch.
