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

P1 (ambiguous — could go either way in real use):
1. Hierarchy drift (`drift-01`): add tests/callers rank to `evolution.md` §4.
2. "Healthy precedent" hole (`atk-01`, `atk-11`): one outcome-based health test, shared.
3. Ownership test (`atk-03`/`atk-07`): owner = whoever owns the failure.
4. Observable-text escalation (`atk-10`): visible text change escalates one risk band.
5. Prose verification step (`atk-08`): "unclickable reference is fiction".
6. Reproduce-before-fix (`versus V3`, stolen from superpowers): add to verification guidance + red-green for regression tests.

P2 (clarity/polish):
7. Tool-tiebreak (`atk-05`): dynamic-entry check beats static scanners.
8. Pressure-stack checklist (`boss-01`): one ordered list for multi-pressure tasks.
9. Terse-vs-deep prose gap (`drift-matrix` pair 5): pointer line only.

## Versus lesson

`obra/superpowers@8ca22db` matches us wherever maintained tests speak and beats our
process on bug fixing (reproduce-first + red-green as Iron Law). We stand alone only on
review judgment (contracts, risk bands, scope). Trade honestly: adopt their red-green
discipline (P1-6), keep our contract/risk machinery. That is the whole optimization
program for the next skill rev.
