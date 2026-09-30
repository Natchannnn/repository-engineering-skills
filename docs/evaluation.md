# Evaluation harness and archive verification guide

This document describes how to execute the evaluation harnesses, run verification checks, and verify historical benchmark archives.

---

## 1. Overview of Evaluation Components

The repository includes two independent evaluation harnesses:

| Component | Directory | Purpose |
| :--- | :--- | :--- |
| **Foundation Harness** | `repo-foundation/evals/` | Multi-checkpoint lifecycle verification, deterministic snapshots, exact rational scoring |
| **Refactor Harness** | `repo-native-refactor/evals/` | Hash-checked change evaluation, runner isolation, patch roundtrip integrity |
| **Runtime Resource Checks** | `scripts/test_runtime_resources.py` | Skill-owned references resolve without the source repository or companion |
| **Runtime Polish Smoke** | `pilots/runtime-polish-smoke/` | Six bounded tasks with explicit skill invocation and independent outcome checks |
| **Bounded Rating Comparison** | `pilots/budget-rating-eval/` | Four audited review sessions with/without skills; usage, exclusions and limits recorded |
| **Behavioral Pilot 1** | `pilots/small-behavioral-pilot/` | 9-run behavioral evaluation (D1, D3, R1) with 42 self-audit checks |
| **Phase 2 Pilot** | `pilots/phase2-contract-and-review/` | 27-run contract drift and review evaluation (D2, R2A, R2B) with 35 self-audit checks |
| **Archive Evidence** | `evals-suite/` | 31 sealed historical evidence packets from experimental runs |

---

## 2. Running Foundation Harness Commands

The foundation evaluation harness is located at `repo-foundation/evals/harness.py`.

### A. Asset Validation
Validates that all JSON schemas, rubric definitions, scoring policies, and trusted check scripts compile cleanly:
```bash
python -B repo-foundation/evals/harness.py validate
```

### B. Taking a Deterministic Byte Snapshot
Creates a sealed, byte-exact snapshot bundle containing `snapshot.json` metadata and a `files/` payload with a SHA-256 tree hash:
```bash
# Export to a custom destination directory:
python -B repo-foundation/evals/harness.py snapshot /path/to/workspace --out /path/to/snapshot_bundle

# Export default persistent snapshot:
python -B repo-foundation/evals/harness.py snapshot /path/to/workspace
```

### C. Executing Checkpoint Verification
Executes trusted verification scripts bound to a specific milestone:
```bash
# Checkpoint IDs: CP1_BOOTSTRAP, CP2_SLICE, CP3_EVOLUTION, CP4_CONTINUITY
python -B repo-foundation/evals/harness.py verify CP2_SLICE /path/to/workspace
```

---

## 3. Running Unit Test Suites

Run both unit test suites from the repository root:

```bash
# 1. Foundation harness and example tests (30 tests):
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 2. Refactor harness and example tests (36 tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 3. Isolated skill resources (3 tests):
python -B scripts/test_runtime_resources.py
```

The six-case live smoke check uses installed runtime copies and explicit invocation;
see its [protocol and recorded limits](../pilots/runtime-polish-smoke/PROTOCOL.md).
It is not part of deterministic CI or proof of automatic skill selection.

The later [bounded comparison](../pilots/budget-rating-eval/RESULTS.md) records
four audited review sessions with an empty catalog versus both skills available
for implicit selection. Both repetitions in both arms passed, with equal graded
outcomes and higher measured context cost in the skill arm. Two migration
attempts were excluded after evidence loss, and remaining exclusion/mixed cases
were stopped for usage. It does not establish a universal 10/10 rating.

---

## 4. Verifying Historical Archive Evidence

The `evals-suite/` directory contains 31 sealed benchmark runs. Each packet contains a `verify_hashes.py` script that recalculates the SHA-256 tree hash of the workspace payload and verifies it against the sealed record.

### Running all 31 archive verifiers (PowerShell on Windows):

Run the unified archive verification script from the repository root:

```powershell
pwsh -NoProfile -File ./scripts/verify-archive.ps1
```

The script iterates through all 31 verifier scripts, checks that all 31 are present, executes them in isolated Python sub-processes, and confirms SHA-256 tree hash parity. All 31 verifiers must pass with exit code 0.

`scripts/verify_archive.py` is the same check as a Python script (Windows-verified 31/31). Sealed packet hashes encode Windows path ordering, so archive verification stays Windows-only by design; see `docs/reproduce.md`.

---

## 5. Running Pilot Verifier Self-Audit Suites

The pilots under `pilots/` include deterministic test verifiers and pre-flight self-audit suites:

```bash
# Pilot 1 self-audit suites (42 checks across D1, D3, R1):
python pilots/small-behavioral-pilot/D1-dirty-worktree/test_verifier.py
python pilots/small-behavioral-pilot/D3-baseline-attribution/test_verifier.py
python pilots/small-behavioral-pilot/R1-contract-drift/test_verifier.py

# Phase 2 self-audit suite (35 checks across D2, R2A, R2B):
python pilots/phase2-contract-and-review/test_all_phase2_verifiers.py
```
