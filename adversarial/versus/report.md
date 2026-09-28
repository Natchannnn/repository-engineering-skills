# D-versus: us vs superpowers@8ca22db (frozen)

- Opponent: `obra/superpowers` @ `8ca22db`, A1 subset = `systematic-debugging` +
  `test-driven-development` + `verification-before-completion` (+ `finishing-a-development-branch`
  for scope hygiene). Read fresh from clone for these runs.
- A0 = bare prompt. A2 = our two skills v0.2.0.
- Operator for all 9 performances: me (repo author). Contamination is real — I know our
  skills by heart, so A0/A1 run "as faithfully as I can" but cannot un-know. Read this as a
  directional signal and a bug hunt, NOT a benchmark. Home advantage: ours.

## V1 — drift-01 (tests vs local convention)

- A0: keeps float dollars (local code wins by inertia), breaks or weakens the cents tests → MISS.
- A1: TDD keeps existing tests green as spec + requirements checklist → migrates to cents → HIT.
- A2: hierarchy tests(5) > local(6) → cents → HIT.
- Note: superpowers reaches our answer by a different road. No unique advantage for us here.

## V2 — error-text consolidation review

- A0: tests green, diff tidy → APPROVE → MISS (dashboard regex breaks).
- A1: TDD green, verification gate checks claims not judgment, debugging skill is for bugs
  not review → APPROVE → MISS.
- A2: hierarchy forces caller/docs check → finds `docs/support.md` dashboard → REJECT
  (conditional on reading docs; confidence medium — the atk-10 band-escalation patch would
  make this decisive instead of diligent). → HIT with caveat.
- Only fixture where A2 stands alone. Review judgment is our turf; theirs has no rule for it.

## V3 — planted `>` vs `>=` bug (their turf, executed for real)

- Repro before fix: `total(500) = 500.0`, HIDDEN-CHECK FAIL. After one-char fix: 475.0/100.0, PASS.
- A0/A1/A2 all fix it — outcome does not discriminate on a trivial bug.
- Process difference is the finding: A1 *requires* repro-first + red-green cycle;
  A2 has baseline discipline + final-state verify but NO reproduce-before-fix rule.
  Our text would accept a fix verified only after the fact. → process gap in OUR skill (P1).

## Scoreboard (directional only)

A0 1/3 · A1 2/3 · A2 3/3 (V2 conditional). The honest headline: sputtering A0 loses both
judgment fixtures; superpowers matches us where tests speak (V1) but has no review-judgment
rule (V2); we have no reproduce-first rule (V3) — steal that from them.
