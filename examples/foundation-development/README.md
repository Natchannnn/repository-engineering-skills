# Demo 2: Foundation Feature Development

Demonstrates `repo-foundation` guiding an AI coding agent to implement an additive feature in an existing repository, preserving existing public contracts, authoring proportionate verification tests, respecting scope boundaries, and maintaining documentation continuity.

---

## 1. Scenario Specification

The target repository `metric_hub` is a data processing utility that reads CSV transaction records and outputs grouped metrics.
- **Current functionality:** `python -m src.metric_hub.cli summary samples/transactions.csv` outputs a human-readable text table.
- **Task:** Implement a new `export-json` command:
  ```bash
  python -m src.metric_hub.cli export-json <csv_path> --out <output_json_path>
  ```
- **Requirements:**
  1. Output valid JSON with `status`, `record_count` (integer), and all `categories` grouped with `count` (integer) and `total_amount` (numeric float/int).
     Example complete output for `samples/transactions.csv`:
     ```json
     {
       "status": "success",
       "record_count": 6,
       "categories": {
         "electronics": { "count": 3, "total_amount": 450.0 },
         "books": { "count": 2, "total_amount": 55.0 },
         "groceries": { "count": 1, "total_amount": 45.5 }
       }
     }
     ```
  2. Preserve all existing public contracts and the `summary` command without regression.
  3. Author proportionate unit tests for the new capability in `tests/`.
  4. Synchronize living documentation in `README.md`.
  5. Strictly confine edits to `src/metric_hub/`, `tests/`, and `README.md` (no unneeded third-party dependencies).

---

## 2. Walkthrough & Execution

### POSIX (Bash)

```bash
# 1. Define paths (run from repository root)
REPO_ROOT="$(pwd)"
FIXTURE_DIR="/tmp/demo-foundation-dev"

# 2. Bootstrap the isolated fixture repository
python "$REPO_ROOT/examples/foundation-development/bootstrap.py" "$FIXTURE_DIR"

# 3. Enter fixture and install skill
cd "$FIXTURE_DIR"
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation --agent codex --copy -y
# Alternatively, manually copy skill into fixture:
# mkdir -p "$FIXTURE_DIR/.agents/skills"
# cp -r "$REPO_ROOT/repo-foundation" "$FIXTURE_DIR/.agents/skills/repo-foundation"

# 4. Finalize setup before starting agent session (records pristine state & lockfile baseline)
python "$REPO_ROOT/examples/finalize_setup.py" "$FIXTURE_DIR"

# 5. Prompt the AI agent (see prompt below)

# 6. Run independent verification from any working directory
python "$REPO_ROOT/examples/foundation-development/verify.py" \
  --fixture-dir "$FIXTURE_DIR"
```

### Windows (PowerShell)

```powershell
# 1. Define paths (run from repository root)
$RepoRoot = (Get-Location).Path
$FixtureDir = "$env:TEMP\demo-foundation-dev"

# 2. Bootstrap the isolated fixture repository
python "$RepoRoot\examples\foundation-development\bootstrap.py" "$FixtureDir"

# 3. Enter fixture and install skill
Set-Location "$FixtureDir"
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation --agent codex --copy -y
# Alternatively, manually copy skill into fixture:
# New-Item -ItemType Directory -Force -Path "$FixtureDir\.agents\skills" | Out-Null
# Copy-Item -Recurse "$RepoRoot\repo-foundation" -Destination "$FixtureDir\.agents\skills\repo-foundation"

# 4. Finalize setup before starting agent session (records pristine state & lockfile baseline)
python "$RepoRoot\examples\finalize_setup.py" "$FixtureDir"

# 5. Prompt the AI agent (see prompt below)

# 6. Run independent verification
python "$RepoRoot\examples\foundation-development\verify.py" `
  --fixture-dir "$FixtureDir"
```

---

## 3. Agent Prompt Specification

Prompt the agent inside the fixture workspace:

```text
Use repo-foundation to add an 'export-json' command to metric_hub:
python -m src.metric_hub.cli export-json <csv_path> --out <output_json_path>

Requirements:
1. Export JSON with status, record_count (int), and all category totals (count as int and total_amount).
2. Return non-zero exit code if input CSV does not exist.
3. Preserve existing summary command and all public core functions without regression.
4. Author proportionate unit tests in tests/ covering normal export and error handling.
5. Update README.md with export-json usage instructions.
6. Confine edits to src/metric_hub/, tests/, and README.md; do not add dependencies.
```

---

## 4. Independent Verification & Criteria

Verification is evaluated by the author's independent test suite, separate from any tests authored by the agent:

```bash
python <path-to-repo>/examples/foundation-development/verify.py --fixture-dir <path-to-fixture>
```

### Acceptance Checks Performed

1. **Scope Boundary Check:** Inspects working tree diffs, staged index diffs, and untracked files against `INITIAL_HEAD` using NUL-delimited output. Only `src/metric_hub/`, `tests/`, and exact `README.md` are permitted.
2. **Author Regression Test Suite:** Executes author-provided tests on the unchanged baseline contracts (`compute_category_totals` and `summary` CLI) to verify zero regressions.
3. **Author Feature Acceptance Test Suite:** Invokes the new `export-json` capability with author-owned independent checks across the sample dataset and dynamic synthetic datasets, validating JSON schema, full category coverage, strict integer counts, and error exits on invalid paths.
4. **Documentation Synchronization:** Verifies that `README.md` documents `export-json`.
5. **Workspace Unit Tests:** Runs workspace unit tests and inspects whether test files under `tests/` were authored or modified.

---

## 5. Limitations Disclaimer

- Demonstrates additive feature development on a small Python CLI utility; does not establish performance across large multi-language monorepos or complex async distributed systems.
- Results vary based on host agent tool-calling capabilities and underlying foundation model.
