# Evaluation Harness & Archive Verification Guide

This document describes how to execute the evaluation harnesses, run verification checks, and verify historical benchmark archives.

---

## 1. Overview of Evaluation Components

The repository includes two independent evaluation harnesses:

| Component | Directory | Purpose |
| :--- | :--- | :--- |
| **Foundation Harness** | `repo-foundation/evals/` | Multi-checkpoint lifecycle verification, deterministic snapshots, exact rational scoring |
| **Refactor Harness** | `repo-native-refactor/evals/` | Cryptographic change evaluation, runner isolation, patch roundtrip integrity |
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
# 1. Foundation harness tests (26 unit tests):
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 2. Refactor harness tests (33 unit tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v
```

---

## 4. Verifying Historical Archive Evidence

The `evals-suite/` directory contains 31 sealed benchmark runs. Each packet contains a `verify_hashes.py` script that recalculates the SHA-256 tree hash of the workspace payload and verifies it against the sealed record.

### Running all 31 archive verifiers (PowerShell on Windows):

```powershell
$verifiers = @(Get-ChildItem -LiteralPath evals-suite -Recurse -Filter verify_hashes.py -File)
Write-Host "Found $($verifiers.Count) archive verifiers."

$passed = 0
foreach ($v in $verifiers) {
    python -B $v.FullName
    if ($LASTEXITCODE -eq 0) {
        $passed++
    } else {
        Write-Error "Verification failed for: $($v.FullName)"
    }
}
Write-Host "Results: $passed / $($verifiers.Count) passed."
```

All 31 verifiers must pass with exit code 0.
