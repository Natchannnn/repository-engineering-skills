# Contributing

Thanks for helping with the skills and harnesses.

---

## 1. Ground rules

- Never modify, reformat, or re-encode files inside `evals-suite/`. Those are sealed historical benchmarks with SHA-256 tree hashes.
- Any change to harness behavior or state machines needs matching regression unit tests.
- Keep changes bounded with a concrete reason, the way the skills themselves demand.

---

## 2. Local verification

Before opening a pull request, run the suites locally (Windows; Python per CI):

```bash
# 1. Run refactor harness unit tests:
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run foundation harness unit tests:
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets:
python -B repo-foundation/evals/harness.py validate

# 4. Verify all 31 archived evidence packets:
pwsh -NoProfile -File ./scripts/verify-archive.ps1
```

Check for whitespace errors before committing:
```bash
git diff --check
```

---

## 3. Reporting issues

When reporting a skill issue, include:
1. Skill name and version (e.g., `repo-foundation` v0.2.0).
2. Agent host and model.
3. The exact task prompt.
4. What the agent should have done per the skill.
5. What it actually did (transcripts or snippets).

Redact private paths and sensitive data.
