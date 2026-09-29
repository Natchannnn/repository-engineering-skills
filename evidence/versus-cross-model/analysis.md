# Cross-model round (Space Bunny via OpenCode, 2026-09-28)

Operator: repo author running a second model. Our SHA `789fe24`, opponent
`obra/superpowers@8ca22db`. Protocol: 9 fresh performer sessions in
least-privilege dirs (network isolated, reported), 1 fresh judge session on
X/Y/Z-anonymized outputs, mapping recorded separately and revealed after scoring.
Full record: `mapping.txt`, `prompts/`, `outputs/`, `judge/` in this directory.

## Outcomes (judge scores, mapping verified against raw files)

- V1: X/Y/Z all WRONG → **invalid-test**. The fixture's test passes on floats
  (`round(1000*1.1,2) == 1100.0 == 1100`), so the rubric premise was broken and all
  three FLOAT answers were correct responses to the fixture as written. Fixture
  discarded, not the skills. My own pre-run walkthrough made the same error.
- V2: all CORRECT → **uncontested**. Dashboard contract spelled out in the task;
  even the bare arm catches it. A2 cited the patched escalation rule (patch adoption
  visible), but with everyone correct there is no discrimination signal.
- V3: all CORRECT → **uncontested** on outcome (trivial bug); process differs per arm
  as predicted (A1 full pytest red-green, A2 boundary sweep, A0 direct).

## What this round is worth

No valid discrimination signal — and that is the honest headline. What it does
establish: (1) the cross-model blind protocol executes cleanly end to end
(mapping, byte-identical judge inputs, environment-aware performer notes);
(2) two fixture-design lessons (tests must genuinely fail pre-fix; leads must be
buried, not spelled out). Next round needs harder, genuinely discriminating fixtures
before any scoreboard claims.
