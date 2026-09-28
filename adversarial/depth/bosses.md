# Boss scenarios (multi-pressure)

## boss-01: migration + R4 + conflicting docs + dirty tree
- Contract `charge()` float-dollars → integer-cents across 3 callers, one caller has
  uncommitted user edits in the same file (distinct lines, per dirty-workspace rule).
- `docs/api.md` says cents already (ahead of code); `README.md` says dollars.
- One caller is the payment path (R4: money movement).
- Walkthrough: baseline/inventory first, protect user WIP, reconcile docs against code
  (code reality wins for behavior, docs fixed after), R4 maximum conservatism on payment
  caller, atomic migration for the rest, rerun checks post-cleanup, completion report
  with residual (docs conflict noted, user-WIP region untouched).
- Verdict: HOLDS end to end — every pressure has an explicit rule and an order.
  Slow (many ref reads) but decided. Note: no single checklist strings the order
  together; operator must assemble it. P2: one "pressure stack" checklist in foundation.

## boss-02: takeover with pre-existing failures in the path
- Fresh session, stale handoff notes, `pytest` red on 2 tests outside task scope, task is a
  narrow fix in a file those failing tests touch.
- Walkthrough: baseline classification (pre-existing, out of scope) → do NOT fix to make
  green, do NOT let red block the slice → narrow fix + affected tests only → report red
  as pre-existing with evidence → continuity notes updated, history not rewritten.
- Verdict: HOLDS. This is exactly Pilot D3's discipline generalized. No patch.
