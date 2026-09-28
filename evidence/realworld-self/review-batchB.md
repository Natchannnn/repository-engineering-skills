# C1 self-dogfood: refactor review of Batch B diff

- Reviewer: AI assistant (OpenCode session), skill-guided by `repo-native-refactor` v0.2.0.
- Scope: `git diff a905103..176301d` — 8 files, +82/-2. Docs + manifests only, no executable code.
- Mode: read-only review first, then bounded cleanup of accepted findings.
- Honest labels: n=1, no blind judge, reviewer is also the author of the diff. This is a
  demonstration of the workflow, not independent evidence.

## Baseline

`a905103` (GIF on front page) → `176301d` (Batch B). Working tree clean before review.
No behavior change possible from these files (docs + JSON manifests); runtime payload
whitelist untouched. Verified: Skills CLI still discovers exactly 2 skills after the change.

## Findings

### F1 (R1): install-path sentence now misleading — ACCEPTED, FIXED
`README.md`: "This writes to `.agents/skills/`..." sits below the new multi-agent block
and the Claude marketplace block, but `claude-code` installs to `.claude/skills/`.
A Claude user following the page top-to-bottom gets the wrong path.
Fix: qualify per-agent paths in that sentence.

### F2 (R1): single-line JSON manifests — ACCEPTED, FIXED
`.claude-plugin/marketplace.json` + both `plugin.json` are one line each. Valid, but
unreviewable and guarantees noisy whole-file diffs on the next edit.
Fix: pretty-print 2-space indent. JSON semantics unchanged; re-ran
`claude plugin validate` on all three + Skills CLI `--list` after the change.

### F3 (R2): hardcoded `"version": "0.2.0"` will drift — REPORTED, DEFERRED
Both `plugin.json` pin a version string with no sync mechanism to `SKILL.md` metadata.
Next version bump will silently desync them. Not fixed here: needs a release-checklist
decision (single source vs script), which is a maintainer call, not a cleanup call.
Left as residual uncertainty.

## Deliberately left alone

- `docs/launch-kit.md` numbers (7/9, ceiling, 59) check out against evidence. No finding.
- `npx-install-verification.md` matrix disclaimers are accurate. No finding.
- No contract drift possible in this diff (no code, no schemas). Verified by inspection.

## Verification

- `claude plugin validate` on both skill dirs + marketplace root: 3/3 passed (before and after F2).
- `npx skills add <local> --list`: still exactly 2 skills after F2.
- No test suites affected (docs-only diff); `sync-shared --check` unaffected (no shared files touched).

## Result: Verified with caveats

F1+F2 fixed and re-validated. F3 deferred to maintainer. Same-agent self-review is not
independent review — treat this file as a worked example, not as evaluation evidence.
