# Batch D attack report (2026-09-28)

Single operator (repo author), n=1 throughout, no blind judging. Fixtures deliberately
harder than real life. Expectation set in advance: some misses required — got them.

## Confirmed hits (keep as proof)

- drift reasoning beats bare prompts twice (V1: A0 keeps floats; V2: A0 approves blind).
- Boss-01/02 walkthroughs hold end to end (slow but decided).
- atk-02/04/06/09 hold; colorama/six evidence from Batch C unaffected.

## Misses → patch backlog

P0 (wrong behavior possible):
- (none found — no case produced actively wrong guidance, only under-determined ones.)

P1 — all applied 2026-09-28, re-verify with `sync-shared --check` + harness validate:
1. Hierarchy drift (`drift-01`): tests/callers rank added to `evolution.md` §4. DONE.
2. "Healthy precedent" hole (`atk-01`, `atk-11`): outcome-based health test in canonical §4, synced to both skills. DONE.
3. Ownership test (`atk-03`/`atk-07`): same canonical §4. DONE.
4. Observable-text escalation (`atk-10`): visible-text rule in `semantic-risk.md`. DONE.
5. Prose verification step (`atk-08`): click-through fiction rule in `repository-prose.md` + final-review checklist + 2-line inline twin in foundation. DONE.
6. Reproduce-before-fix (`versus V3`): added to `verification.md` §4 with red-green. DONE.

P2 — all applied 2026-09-28:
7. Tool-tiebreak (`atk-05`): dynamic-entry check wins, in `deterministic-tooling.md`. DONE.
8. Pressure-stack checklist (`boss-01`): new `evolution.md` §5. DONE.
9. Terse-vs-deep prose gap (`drift-matrix` pair 5): 2-line inline rule in foundation (not a cross-skill link — links break standalone installs). DONE.

## Versus lesson

`obra/superpowers@8ca22db` matches us wherever maintained tests speak and beats our
process on bug fixing (reproduce-first + red-green as Iron Law). We stand alone only on
review judgment (contracts, risk bands, scope). Trade honestly: adopt their red-green
discipline (P1-6), keep our contract/risk machinery. That is the whole optimization
program for the next skill rev.
