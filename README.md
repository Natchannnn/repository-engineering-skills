# Repository Engineering Skills

Two specialized skills for AI coding agents working in software repositories.

- **`repo-foundation`** guides project setup, feature implementation, contract evolution, and multi-session continuity.
- **`repo-native-refactor`** audits diffs and performs bounded, regression-free refactoring while preserving intended behavior and repository conventions.

Both skills emphasize bounded scope, proportionate verification, contract preservation, and explicit handling of uncertainty.

The repository includes evaluation harnesses and archived comparison runs from internal experiments. These results cover a small set of repository tasks; they do not establish consistent improvements across all models, languages, or projects.

---

## 1. What the Skills Do

AI coding agents often struggle with consistency across multi-turn repository workflows:
- Substituting declared interface types (e.g., swapping a declared `str` path with `pathlib.Path` wrapper objects).
- Over-refactoring clean greenfield code or refactoring without establishing operational consequences.
- Neglecting failure invariants during state-modifying operations.
- Omitting persistent verification tests or letting repository documentation drift.

These skills provide structured engineering instructions that prompt agents to follow disciplined repository conventions, preserve public contracts, test changes proportionately, and respect explicit boundaries.

---

## 2. Choosing Between the Skills

You can use each skill independently. Small tasks such as fixing a typo or updating a comment do not require activating either skill.

| Scenario | Recommended Skill | Reason |
| :--- | :--- | :--- |
| Starting a new repository or module from scratch | `repo-foundation` | Guides initial structure, minimal dependencies, and early verification. |
| Implementing a new feature or additive capability | `repo-foundation` | Enforces scope boundaries, living documentation sync, and behavior-driven tests. |
| Evolving an existing public contract or migrating schemas | `repo-foundation` | Manages atomic state migration, caller updates, and failure invariants. |
| Resuming work across sessions or taking over a codebase | `repo-foundation` | Reconciles discrepancies using an evidence hierarchy without modifying history. |
| Reviewing a change set or PR diff without modifying code | `repo-native-refactor` | Conducts a read-only audit across semantic risk bands (R0–R4). |
| Cleaning up code smells, duplication, or dead weight in a diff | `repo-native-refactor` | Applies semantic DRY based on cost-benefit; leaves healthy code untouched. |

---

## 3. Installation & Tested Environments

### Tested Environment
- **Operating System:** Windows (tested on Windows 11 with `core.autocrlf=true`)
- **Python Version:** 3.14.5 (harness and test suite verified)
- **Supported Hosts:** Any coding agent host that loads skill directories containing a `SKILL.md` file and optional `references/` folder (e.g., OpenAI Codex / Agent SDK, Claude Code, Cursor, Antigravity). Note that Markdown compatibility alone does not guarantee equivalent behavior across all agent hosts.

### Runtime Installation
To install the skills for an agent, copy only the runtime skill directories (`repo-foundation` and `repo-native-refactor`) into your project or user skills directory.

> [!IMPORTANT]
> Do **not** install or copy the `evals-suite/` directory into your project. That directory contains archived historical benchmark runs and frozen artifacts for evaluation, not runtime instructions.

#### Example: Installing into a project using `.agents/skills/` (Codex / Agent SDK)

```powershell
# Set path to this cloned repository and your target project:
$sourceRepo = "C:\path\to\repository-engineering-skills"
$targetProject = "C:\path\to\my-project"

$installDir = Join-Path $targetProject ".agents\skills"

foreach ($skill in @("repo-foundation", "repo-native-refactor")) {
    $dest = Join-Path $installDir $skill
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRepo "$skill\SKILL.md") -Destination $dest -Force
    Copy-Item -LiteralPath (Join-Path $sourceRepo "$skill\references") -Destination $dest -Recurse -Force
}
```

---

## 4. Example Prompts

Here are three concrete prompts demonstrating intended workflows:

### A. Feature Development with `repo-foundation`
```text
Use repo-foundation to add JSON export to this CLI tool.
Preserve the existing command interfaces, default behaviors, and error handling.
Author proportionate unit tests for the new export format and document the flag in README.md.
```

### B. Read-Only Review with `repo-native-refactor`
```text
Use repo-native-refactor to review the current diff against main.
Identify any contract drifts, unhandled error paths, or misplaced domain ownership.
Review only; do not edit any source files.
```

### C. Change-Set Cleanup with `repo-native-refactor`
```text
Use repo-native-refactor to clean up the current diff where a concrete maintenance or correctness
problem exists. Preserve the authorized behavior and avoid cosmetic churn.
Run affected verification checks after your edits.
```

---

## 5. Evaluation Evidence & Known Limitations

To maintain scientific honesty, we separate our evaluation data into three distinct categories:

### A. Harness Unit Test Suite
- **Purpose:** Verifies that the evaluation harnesses execute deterministically, preserve state safely, and correctly enforce boundaries.
- **Coverage:**
  - `repo-foundation` harness: **26 unit tests** (validates deterministic byte snapshots, atomic staging/rollback on I/O failure, metaschema structural checks, exact rational scoring, and unmanaged directory protection).
  - `repo-native-refactor` harness: **32 unit tests** (validates blind protocol invariants, runner isolation, patch round-tripping, and non-finite score rejection).
- **Result:** 58/58 unit tests pass consistently on Windows / Python 3.14.

### B. Archive Integrity Verification
- **Purpose:** Verifies that historical experimental evidence recorded in `evals-suite/` remains intact and bit-exact across checkouts.
- **Coverage:** 31 independent `verify_hashes.py` verification scripts.
- **Result:** 31/31 pass with exact SHA-256 tree hash parity, including fresh Git clones with CRLF normalization.

### C. Agent Behavioral Experiments (Observed Case Studies)
- **Scope:** Evaluated on specific multi-turn milestones (CP1 Bootstrap, CP2 Query Slice, CP3 Multi-Tenant Evolution, CP4 Continuity) using a ledger repository domain.
- **Observations:**
  - In CP2 tests, raw models spontaneously altered declared `str` module constants to `Path`, whereas agents with skill instructions preserved the declared string contract.
  - In CP3 tests, agents with skill instructions updated living documentation and consolidated duplicate validation into affirmative predicates, scoring higher in blind maintainer reviews than uninstructed controls.
- **Known Limitations:**
  - **Small Task Domain:** These observations reflect a specific ledger system workload and do not prove universal superiority across different tech stacks or tasks.
  - **Environment Scope:** Verified on Windows with Python 3.14; Linux/macOS behaviors rely on POSIX compatibility but have not undergone identical continuous auditing.
  - **Crash Invariants:** Safe replacement mechanisms have been verified against simulated I/O exceptions, but have not been tested against sudden system power loss or process `SIGKILL`.

For complete details, failure analyses, and trajectory notes, see [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md).

---

## 6. Verification Commands

To run all automated verification checks locally:

```bash
# 1. Run refactor harness unit tests (32 tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run foundation harness unit tests (26 tests):
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets:
python -B repo-foundation/evals/harness.py validate

# 4. Verify all 31 archive evidence packets (PowerShell):
pwsh -Command "Get-ChildItem -Recurse -Filter verify_hashes.py | ForEach-Object { python -B $_.FullName; if ($LASTEXITCODE -ne 0) { throw 'Hash mismatch' } }"
```

---

## 7. Reporting Issues, Contributing & License

- **Reporting Issues:** Please open an issue on GitHub. Include your agent host, model name, the skill version, the task prompt, and the unexpected behavior.
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md) for testing guidelines and pull request instructions.
- **License:** Released under the [MIT License](LICENSE).
