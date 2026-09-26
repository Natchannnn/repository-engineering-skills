# Repository Engineering Skills

Two specialized skills for AI coding agents working in software repositories.

- **`repo-foundation`** guides project setup, feature implementation, contract evolution, and multi-session continuity.
- **`repo-native-refactor`** reviews diffs and performs scoped cleanup while preserving the behavior the task requires.

Both skills emphasize repository evidence, contract preservation, and verification proportionate to the change.

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

### Install with npx

Requires Git and Node.js **22.20.0 or newer**, including npm/npx. Run from the project where you want to use the skills. The [Skills CLI](https://github.com/vercel-labs/skills) installs directly from this GitHub repository; there is no separate npm package for these two skills.

Preview the available skills without installing:

```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --list
```

Install both for **Codex in the current project**:

```sh
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation repo-native-refactor --agent codex --copy -y
```

This writes to `.agents/skills/` and creates or updates `skills-lock.json`. Re-running the command replaces the selected installed skills, including local edits inside them. Use a fresh project folder for a first trial. The version `1.7.0` pins the installer, not the skill source revision.

To select another agent interactively, omit `--agent codex`, `--copy`, and `-y`. Installation options, single-skill commands, updating and removal are in [the installation guide](docs/installation.md).

### Alternative: Install from local clone (PowerShell)

If installing from a local clone of this repository into a target project:

```powershell
# Fresh install (stops safely if destination skill already exists):
pwsh -NoProfile -File ./scripts/install-skills.ps1 -TargetProject "C:\path\to\my-project"

# Safe update (backs up previous installation, replaces cleanly, and rolls back on failure):
pwsh -NoProfile -File ./scripts/install-skills.ps1 -TargetProject "C:\path\to\my-project" -Update
```

### Check the installation and try a skill

```sh
npx skills@1.7.0 list --agent codex
```

Open the target project in Codex, start a new session and try the prompts below. Listing files confirms installation; verify that the host reads the intended skill before treating an example as a behavior test.

### Tested scope and installed files

- **Installation:** Windows, Node.js 24.16.0 and Skills CLI 1.7.0; discovery, project-local Codex copy installation, file comparison and reinstall tested. This does not establish automatic routing or behavior across hosts.
- **Local Installer Script:** Windows PowerShell / PowerShell 7; pre-flight validation of both skills, isolated staging, automatic backup creation, byte-exact post-deploy SHA-256 hash verification, and verified rollback on deployment failure.
- **Harness:** Windows / Python 3.14.5. Python is needed for the evaluation harness, not merely to load the Markdown skills.
- **Payload:** The CLI copies the selected skill directories, including their `evals/` harness files and supporting references. It does **not** install the repository-level `evals-suite/` archive. Harness files are copied, not run by this installation command. Each skill directory includes its MIT license for distribution.

See [the recorded installation checks](docs/npx-install-verification.md) for the source revision and limitations.

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
  - `repo-native-refactor` harness: **33 unit tests** (validates blind protocol invariants, runner isolation, patch round-tripping, non-finite score rejection, and Windows 8.3 path canonicalization).
- **Result:** 59/59 unit tests pass consistently on Windows / Python 3.14.

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
# 1. Run refactor harness unit tests (33 tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run foundation harness unit tests (26 tests):
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets:
python -B repo-foundation/evals/harness.py validate

# 4. Verify all 31 archive evidence packets (PowerShell):
pwsh -NoProfile -File ./scripts/verify-archive.ps1
```

---

## 7. Reporting Issues, Contributing & License

- **Reporting Issues:** Please open an issue on GitHub. Include your agent host, model name, the skill version, the task prompt, and the unexpected behavior.
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md) for testing guidelines and pull request instructions.
- **License:** Released under the [MIT License](LICENSE).
