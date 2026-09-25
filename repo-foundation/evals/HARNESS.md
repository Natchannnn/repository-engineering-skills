# Foundation Evaluation Harness

Multi-checkpoint repository lifecycle evaluation harness for `repo-foundation`.

Validates that an agent builds, extends, and evolves real repositories across multiple development phases while preserving architectural boundaries, data durability, and contract type safety.

---

## Capabilities & Architecture

The harness provides deterministic, zero-dependency Python verification for the four milestone checkpoints:

1. **CP1_BOOTSTRAP:**
   - Greenfield repository initialization from zero baseline.
   - Append-only event persistence with atomic durability (`tempfile` + `fsync` + `os.replace`).
   - Sequential 1-based IDs, UTF-8 line serialization, and input validation.
2. **CP2_SLICE:**
   - Greenfield additive query slice without mutating underlying storage contracts.
   - Strict interface literal type adherence (`LEDGER_FILE: str`, not wrapped in `pathlib.Path`).
   - Idempotent retrieval (`get_by_id`, `find`) and missing-file resilience.
3. **CP3_EVOLUTION:**
   - Deliberate breaking evolution of public contracts (multi-tenant validation).
   - Zero-mutation guarantee: rejected appends must leave disk bytes 100% untouched.
   - Atomic backfill migration (`migrate() -> int`), idempotency, and zero disk churn.
   - Conjunction querying (`kind` AND `tenant`) with backward compatibility for positional callers.
4. **CP4_CONTINUITY:**
   - Multi-session continuity, documentation synchronization, and regression resilience.

---

## Directory Structure

```text
evals/
├── HARNESS.md              # Technical manual and evaluation contracts
├── harness.py              # Unified CLI runner (validate, snapshot, verify, score)
├── core.py                 # Mathematical validation, SHA-256 tree hashing, schemas
├── byte_snapshot.py        # Byte-preserving snapshot and tree diff engine
├── rubric.json             # 8-dimension architectural scoring rubric
├── scoring_policy.json     # Hard gate policies and certification thresholds
├── tasks/                  # Unbiased milestone task specifications (CP1..CP4)
├── trusted_checks/         # Acceptance & regression verification scripts
└── schemas/                # JSON schemas for manifests, judgments, and scorecards
```

---

## CLI Usage

### 1. Validate Evaluation Assets
Validates internal JSON schemas, rubric weights, task specifications, and verification scripts:
```bash
python evals/harness.py validate
```

### 2. Deterministic Byte-Exact Snapshot
Takes a byte-level snapshot of a candidate workspace and computes its deterministic SHA-256 tree hash:
```bash
python evals/harness.py snapshot <workspace_path> [--out <snapshot.json>]
```

### 3. Verify a Checkpoint
Copies the candidate workspace into a temporary directory to avoid mutating the source workspace, adapts test boundaries, and executes all acceptance and regression checks:
```bash
python evals/harness.py verify CP1_BOOTSTRAP <workspace_path>
python evals/harness.py verify CP2_SLICE <workspace_path>
python evals/harness.py verify CP3_EVOLUTION <workspace_path>
python evals/harness.py verify CP4_CONTINUITY <workspace_path>
```

### 4. Score a Judgment
Computes weighted dimensional ratings and checks pass bars against `scoring_policy.json`:
```bash
python evals/harness.py score --judgment path/to/judgment.json
```

---

## Trust Boundaries & Environment Isolation

- **Host Privilege Inheritance:** Verification inherits the host environment. The harness copies candidate files into a temporary scratch directory before running checks to prevent in-place contamination of the original workspace, but it does **not** provide OS-level containerization, restrict network egress, or constrain subprocess capabilities. Execute checks only in an environment without sensitive credentials or production access.
- **Byte-Exact Immutability:** `byte_snapshot.py` enforces binary byte-level SHA-256 hashing, POSIX path normalization, and mode preservation to detect unauthorized workspace drift or post-run contamination.
- **Context Isolation:** Milestone specifications under `tasks/` contain raw functional contracts and interfaces without implementation hints, answers, or solution patterns.
- **Author vs. Runner Boundaries:** Author materials (`rubric.json`, `scoring_policy.json`, `trusted_checks/`) must remain outside runner visibility.
