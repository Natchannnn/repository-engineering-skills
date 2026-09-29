# Trigger checklist: repo-native-refactor

Not an automated eval (no host auto-routes here). Manual review aid: read each
prompt, ask which skill a router should pick. Reviewed 2026-09-28: description
matches all 20 intents below. Re-check when the description changes.

## SHOULD trigger repo-native-refactor (10)

1. "review my changes" — read-only audit of a diff.
2. "check this diff for contract breaks" — contract-focused review.
3. "clean this up before I open a PR" — change-set cleanup.
4. "is this refactor safe?" — audit with risk bands.
5. "merge these two duplicate validators" — consolidation judgment.
6. "is this comment accurate?" — prose audit.
7. "this diff touches auth — what is the blast radius?" — R4 review.
8. "find dead code in this PR" — residue removal within scope.
9. "does this error message leak internals?" — observable-text review.
10. "review this PR without editing anything" — explicit read-only.

## SHOULD NOT trigger repo-native-refactor (10)

1. "add X to this project" — repo-foundation (build).
2. "set up a new module" — repo-foundation (bootstrap).
3. "change this schema" — repo-foundation (migration owns the change; refactor only reviews it after).
4. "continue where we left off" — repo-foundation (continuity).
5. "fix this typo" — no skill needed.
6. "migrate the database" — repo-foundation (refactor never migrates data).
7. "write the feature, then clean it" — foundation first; refactor at the checkpoint.
8. "redesign this module" — explicitly out of scope; neither skill redesigns alone.
9. "what does this function do?" — no skill, just read.
10. "reformat the whole repo" — mechanical tooling, not a skill.
