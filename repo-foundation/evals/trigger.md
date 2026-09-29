# Trigger checklist: repo-foundation

Not an automated eval (no host auto-routes here). Manual review aid: read each
prompt, ask which skill a router should pick. Reviewed 2026-09-28: description
matches all 20 intents below. Re-check when the description changes.

## SHOULD trigger repo-foundation (10)

1. "add X to this project" — new feature on a working codebase.
2. "set up a new module" — greenfield with no tooling yet.
3. "change this schema" — contract migration with callers.
4. "continue where we left off" — resume across sessions.
5. "add JSON export to this CLI, keep the old commands working".
6. "migrate the database from v1 to v2 without losing rows".
7. "take over this repo, it has failing tests I did not write".
8. "split this module; the boundary changed".
9. "fix this bug and add a regression test".
10. "bootstrap a small service with one working endpoint".

## SHOULD NOT trigger repo-foundation (10)

1. "fix this typo" — no skill needed.
2. "review my changes" — repo-native-refactor (read-only review).
3. "check this diff for contract breaks" — repo-native-refactor.
4. "clean this up before I open a PR" — repo-native-refactor.
5. "is this refactor safe?" — repo-native-refactor (audit, not build).
6. "what does this function do?" — no skill, just read.
7. "rewrite this file in another language" — out of scope for both; ask first.
8. "reformat the whole repo" — mechanical tooling, not a skill.
9. "merge these two duplicate validators" — repo-native-refactor (consolidation judgment).
10. "is this comment accurate?" — repo-native-refactor (prose audit).
