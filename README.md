# Repository Engineering Skills: Code Review and Refactoring for AI Agents

Two agent skills for repository development, code review, and scoped refactoring. Includes tested Codex project installation commands using the Skills CLI, an atomic local installer, reproducible evaluation harnesses, 36 audited empirical pilot runs (Pilot 1 & Phase 2), and verified demonstration fixtures.

- **`repo-foundation`** guides project setup, feature implementation, public contract evolution, and multi-session continuity.
- **`repo-native-refactor`** conducts read-only diff audits and performs scoped cleanup while preserving required behavior and repository conventions.

[Install in a Codex project](docs/installation.md) · [Choose a skill](#choosing-a-skill) · [Reproducible demonstrations](#reproducible-demonstrations) · [Evaluation evidence & pilots](#evaluation-evidence--empirical-pilots) · [Verification commands](#verification-commands)

> **Governing Principle:** Respect scope. Preserve contracts. Verify changes.

Evaluation harnesses and historical comparison runs are included. The experiments cover a limited set of repository tasks; they do not establish consistent improvements across all models, languages, or projects.

---

## What the skills do

AI coding agents often introduce subtle regressions during multi-turn repository workflows:
- **Contract Drift:** Modifying public interface return types or schemas without updating dependent callers (e.g., swapping a declared `str` dictionary key or path with `Path` objects).
- **Scope Creep & Over-Refactoring:** Modifying healthy, unrelated modules or renaming files unnecessarily during narrow feature additions.
- **Unchecked Error Paths:** Neglecting edge-case invariants, leaving partial or dirty states on disk upon failure.
- **Documentation Drift:** Failing to synchronize living project documentation (`README.md`, CLI help) when capabilities change.

These skills provide structured engineering instructions that prompt agents to follow disciplined repository conventions, preserve public contracts, test changes proportionately, and respect explicit scope boundaries.

---

## Choosing a skill

You can use each skill independently. Routine edits such as fixing a typo, updating a comment, or isolated script modifications do not require activating either skill.

| Scenario | Recommended Skill | Reason |
| :--- | :--- | :--- |
| Starting a new repository or module from scratch | `repo-foundation` | Guides initial architecture, minimal dependencies, and early verification gates. |
| Implementing a new feature or additive capability | `repo-foundation` | Guides scope boundaries, living documentation sync, and behavior-driven tests. |
| Evolving an existing public contract or migrating schemas | `repo-foundation` | Manages atomic state migration, caller updates, and failure invariants. |
| Resuming work across sessions or taking over a codebase | `repo-foundation` | Reconciles discrepancies using an evidence hierarchy without rewriting history. |
| Reviewing a change set or PR diff without modifying code | `repo-native-refactor` | Conducts a read-only audit across semantic risk bands (R0–R4). |
| Cleaning up code smells, duplication, or dead weight in a diff | `repo-native-refactor` | Applies semantic DRY based on cost-benefit; leaves healthy code untouched. |

---

## Installation & distribution

### Option A: Install via Skills CLI (`npx skills`)

Requires Git and Node.js **22.20.0 or newer**, including npm/npx. Run from the project directory where you want to use the skills. The [Skills CLI](https://github.com/vercel-labs/skills) installs directly from this GitHub repository; there is no separate npm package for these two skills.

Preview available skills:
```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --list
```

Install both skills for **Codex in the current project**:
```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation repo-native-refactor --agent codex --copy -y
```

This writes to `.agents/skills/` and updates `skills-lock.json`. To select another agent interactively, omit `--agent codex`, `--copy`, and `-y`. Full configuration options are detailed in [the installation guide](docs/installation.md).

### Option B: Install from Local Clone (PowerShell)

If installing from a local clone into a target project:

```powershell
# Fresh install (stops safely if destination skill already exists):
pwsh -NoProfile -File ./scripts/install-skills.ps1 -TargetProject "C:\path\to\my-project"

# Safe update (backs up previous installation, replaces cleanly, and rolls back on failure):
pwsh -NoProfile -File ./scripts/install-skills.ps1 -TargetProject "C:\path\to\my-project" -Update
```

### Option C: Standalone Runtime Package (Offline ZIP)

Publishers building from a clean Git checkout can generate a verified standalone distribution ZIP:

```powershell
# Packages validated skills into a standalone distribution ZIP with manifest.json (requires clean Git checkout)
pwsh -NoProfile -File ./scripts/package-runtime.ps1 -OutputDir ./dist
```

Consumers receiving the release ZIP can unpack and use the skills directly without requiring Git or repository access. The archive contains verified skill payloads and MIT licenses, strictly excluding author evaluation files and ignored scratch artifacts.

---

## Reproducible demonstrations

To evaluate agent performance empirically without relying on marketing claims, this repository provides self-contained demo fixtures with independent verification scripts:

### Demo 1: Read-Only Contract Drift Review
- **Location:** [`examples/read-only-contract-review/`](examples/read-only-contract-review/)
- **Scenario:** A simulated pull request alters the return dictionary structure of `get_account_tier()` in `src/profile.py`, breaking an external consumer in `src/billing.py` with `KeyError: 'discount_pct'`.
- **Task:** Prompt an agent using `repo-native-refactor` to audit the diff in read-only mode and output a structured finding report.
- **Verification Gate:** `python examples/read-only-contract-review/verify.py` strictly checks:
  1. Complete finding schema (file, symbol, exception type `KeyError`, and broken caller).
  2. Affirmative finding verdict (rejecting negated or conditional statements).
  3. Protected state preservation (verifies that repository files and git tree state match the baseline at verification time; note that this check verifies state at audit time and does not observe intermediate writes that were subsequently undone within the session).

### Demo 2: Scoped Feature Development
- **Location:** [`examples/foundation-development/`](examples/foundation-development/)
- **Scenario:** An existing data-processing utility `metric_hub` requires a new `export-json` CLI command.
- **Task:** Prompt an agent using `repo-foundation` to implement the capability while preserving existing contracts (`summary`), authoring proportionate tests in `tests/`, and updating living documentation in `README.md`.
- **Verification Gate:** `python examples/foundation-development/verify.py` strictly checks:
  1. Correct execution of independent feature and regression test suites.
  2. Valid CLI JSON output contract conforming to schema specifications.
  3. Scope confinement: verifies that net modifications relative to `INITIAL_HEAD` across the working tree, index, and untracked files are confined strictly to authorized edit scope (does not claim to audit all intermediate commit history).

### Evidence Record Template
- **Location:** [`examples/template/`](examples/template/)
- Provides a canonical template and JSON Schema Draft 2020-12 contract ([`evidence-record.schema.json`](examples/template/evidence-record.schema.json)) for recording future empirical runs and demo experiments. The schema enforces structural validation of execution records (including ISO 8601 UTC timestamps, command exit codes, and explicit limitations); it does not independently attest to the factual execution of recorded metrics, nor does it claim that historical archived benchmarks retrospectively conform to this schema.

---

## Example prompts

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

## Evaluation evidence & empirical pilots

To maintain scientific honesty, our evaluation data is categorized into five distinct layers:

### A. Behavioral Pilot 1 (9-Run Cohort)
- **Scope & Protocol:** 3 repository tasks (`D1` dirty worktree preservation, `D3` baseline failure attribution, `R1` read-only contract drift audit) across 3 experimental arms (`A0` Baseline Control, `A1` Karpathy Guidelines, `A2` Skills).
- **Evaluation Mechanism:** 100% deterministic verifiers with 42 pre-flight self-audit checks. No LLM judge in primary scoring. All evidence self-contained under `pilots/small-behavioral-pilot/evidence/` with SHA-256 `MANIFEST.json`.
- **Outcome:** 9/9 PASS under independent audit. Full protocol and scorecards: [small-behavioral-pilot PROTOCOL.md](pilots/small-behavioral-pilot/PROTOCOL.md).

### B. Phase 2: Contract & Review Evaluation (27-Run Triplet Protocol)
- **Scope & Protocol:** 3 high-leverage tasks (`D2` shipping contract migration with caller AST verification, `R2A` clean refactor negative control, `R2B` subtle contract drift defect identification) across 3 arms (`A0`, `A1`, `A2`) replicated 3 times with rotated arm sequences to eliminate ordering bias (**27 unique runs**).
- **Evaluation Mechanism:** Independent Python verifiers enforcing workspace read-only integrity, snapshot hashes, caller test immutability, and hidden test suites (35 pre-flight self-audit checks). All evidence self-contained under `pilots/phase2-contract-and-review/evidence/` with SHA-256 `MANIFEST.json`.
- **Outcome:** 27/27 PASS under independent clone re-verification. Full protocol and scorecards: [phase2-contract-and-review PROTOCOL.md](pilots/phase2-contract-and-review/PROTOCOL.md).

### C. Harness & Demo Unit Test Suites
- **Harness Verification:** 59 unit tests (26 for `repo-foundation`, 33 for `repo-native-refactor`) verifying deterministic byte snapshots, atomic staging/rollback on I/O error, metaschema structural validation, exact rational scoring, and runner isolation.
- **Demo Acceptance Suite:** 41 tests in `scripts/test_demos.py` covering happy paths, negative control probes (path traversal rejection, schema violations, protected state tampering, prompt copy rejection, lockfile mutation, concurrent setup rejection, and substring tricks).

### D. Archive Integrity Verification
- **Archived Runs:** 31 independent verification packets in `evals-suite/`.
- **Integrity Guarantee:** All 31 packets pass `verify_hashes.py` with exact SHA-256 tree hash parity across Windows CRLF and Linux LF checkouts.

### E. Historical Case Studies (Observed Milestones)
- **Scope:** Evaluated on multi-turn milestones (CP1 Bootstrap, CP2 Query Slice, CP3 Multi-Tenant Evolution, CP4 Continuity) using a ledger repository domain.
- **Observations:** In CP2 tests, raw models spontaneously altered declared `str` module constants to `Path`, whereas agents with skill instructions preserved the declared string contract. In CP3 tests, agents with skill instructions updated living documentation and consolidated duplicate validation into affirmative predicates.
- **Known Limitations:**
  - **Task Domain:** These observations reflect specific repository workloads and do not prove universal superiority across different tech stacks or unconstrained tasks.
  - **Environment Scope:** Verified on Windows with Python 3.14; Linux/macOS behaviors rely on POSIX compatibility but have not undergone identical continuous auditing.
  - **Crash Invariants:** Safe replacement mechanisms have been verified against simulated I/O exceptions, but have not been tested against sudden system power loss or process `SIGKILL`.

For complete details, failure analyses, and trajectory notes, see [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md).

---

## Verification commands

To run all automated verification checks locally:

```bash
# 0. Install test runner dependencies:
python -m pip install jsonschema

# 1. Run refactor harness unit tests (33 tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run foundation harness unit tests (26 tests):
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets (10 schemas, rubric, policy):
python -B repo-foundation/evals/harness.py validate

# 4. Verify all 31 archived evidence packets (PowerShell):
pwsh -NoProfile -File ./scripts/verify-archive.ps1

# 5. Verify local installer with atomic rollback (PowerShell):
pwsh -NoProfile -File ./scripts/test-installer.ps1

# 6. Verify runtime package generator and Git commit parity (PowerShell):
pwsh -NoProfile -File ./scripts/test-package.ps1

# 7. Verify demo acceptance suite (PowerShell / Python 41 tests):
pwsh -NoProfile -File ./scripts/test-demos.ps1

# 8. Run Pilot 1 verifier self-audit suites (42 checks across D1, D3, R1):
python pilots/small-behavioral-pilot/D1-dirty-worktree/test_verifier.py
python pilots/small-behavioral-pilot/D3-baseline-attribution/test_verifier.py
python pilots/small-behavioral-pilot/R1-contract-drift/test_verifier.py

# 9. Run Phase 2 verifier self-audit suite (35 checks across D2, R2A, R2B):
python pilots/phase2-contract-and-review/test_all_phase2_verifiers.py
```

---

## Reporting issues, contributing & license

- **Reporting Issues:** Open an issue on GitHub. Include your agent host, model version, skill version, prompt, and unexpected behavior.
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md) for testing guidelines and pull request instructions.
- **License:** Released under the [MIT License](LICENSE).
