# Contributing to Repository Engineering Skills

Thank you for your interest in improving these skills and evaluation harnesses.

---

## 1. Ground Rules

- **Preserve the Evaluation Archive:** Never modify, reformat, or re-encode files inside `evals-suite/`. Those directories represent sealed historical benchmarks with cryptographic SHA-256 tree hashes.
- **Maintain Invariants:** Any modification to evaluation harness behavior or state machines must include corresponding regression unit tests.
- **Minimal Intervention:** Follow the same engineering principles that the skills prescribe: produce bounded, coherent changes with concrete justification.

---

## 2. Local Verification

Before submitting a pull request, ensure all verification suites pass locally on Windows with Python 3.14:

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

## 3. Reporting Issues

When reporting an issue with a skill, please provide:
1. **Skill Name & Version:** (e.g., `repo-foundation` v0.1.0)
2. **Agent Host & Model:** (e.g., Claude Code with Claude 3.7 Sonnet, Codex, Cursor, etc.)
3. **The Task Prompt:** The exact prompt given to the agent.
4. **Expected Behavior:** What the agent should have done according to the skill instructions.
5. **Observed Behavior:** What the agent actually did (transcripts or code snippets).

Feel free to redact private paths or sensitive project data.
