# D-versus re-run with patched text (2026-09-28)

Same operator, same fixtures, same frozen opponent (`obra/superpowers@8ca22db`).
Only our skill text changed (Batch D patches, commit `7772695`). A0/A1 texts unchanged,
so their answers are carried over — re-running them would be theater.

## V1 — drift-01: divergence closed

Patched `evolution.md` §4 now ranks tests/callers 5th, above local conventions 6th —
identical order to canonical §2. Both hierarchies answer INTEGER cents on the same facts.
A0 still FLOAT (miss), A1 still INTEGER (hit). Our internal contradiction is gone;
the external scoreboard is unchanged.

## V2 — error-text review: conditional → decisive

Before: A2 rejected only if the reviewer diligently read `docs/support.md`.
After the visible-text escalation rule (`semantic-risk.md`): the consolidation changes
user-visible text → R2 escalates to R3 → text treated as observable contract → REJECT
unless the dashboard is updated in scope. Same verdict, now forced by rule instead of
diligence. A0/A1 still APPROVE (their texts have no such rule).

## V3 — planted bug: full red-green under the new rule (executed)

`verification.md` §4 now demands reproduce-first + red-green. Ran it literally in temp:

1. repro: `total(500) = 500.0`, HIDDEN-CHECK FAIL (exit 1)
2. fix `>` → `>=`: 475.0/100.0, PASS (exit 0)
3. revert fix: FAIL again (exit 1) — regression check has teeth
4. restore fix: PASS (exit 0), temp dir removed

A2 process now matches A1's ritual on this axis. The stolen rule works.

## Scoreboard delta

First run: A0 1/3 · A1 2/3 · A2 3/3 (V2 conditional).
Re-run: A0 1/3 · A1 2/3 · A2 3/3 (V2 decisive, V3 red-green demonstrated).
Patches did not inflate our score — they converted two conditional wins into ruled wins
and closed one internal contradiction. That is what a patch is supposed to do.
