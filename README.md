# Repository Engineering Skills for Autonomous AI Agents

A pair of disciplined engineering skills designed to mitigate common failure modes in autonomous agent workflows: **spontaneous type-contract drift**, **premature or duplicated refactoring**, and **documentation decay**.

---

## The Skills

### 1. [`repo-foundation`](repo-foundation/SKILL.md)
Architectural lifecycle engine for autonomous agents:
- **Lifecycle Modes:** Bootstrap (greenfield setup), Continue (feature addition/bugfix), Evolve (controlled contract evolution), and Continuity (multi-session handover).
- **Strict Contract Adherence:** Prevents models from spontaneously swapping declared primitive types across public interfaces (e.g., swapping `str` with `pathlib.Path`).
- **Living Documentation:** Enforces synchronizing `README.md` and API specifications whenever contracts evolve.
- **Proportionate Verification:** Mandates persistent test authorship when scope permits without polluting bounded single-file tasks.

### 2. [`repo-native-refactor`](repo-native-refactor/SKILL.md)
Post-implementation audit and surgical code hygiene:
- **Evidence Gate:** Strictly prohibits speculative refactoring on clean greenfield code. Refactors only when concrete evidence of defect, smell, or divergence exists.
- **Semantic DRY (Single Source of Truth):** Enforces consolidating shared validation and transformation logic when implementations share ownership, invariants, and reasons to change, avoiding premature consolidation across separate boundaries.
- **Semantic Risk Bands:** Classifies changes from R0 (mechanical formatting) to R4 (critical boundaries: auth, crypto, data migration).
- **Prose Audit:** Strips syntax-narrating boilerplate while preserving critical operational invariants.

---

## Repository Layout

```text
SKILLS-MAIN/
├── repo-foundation/            # Foundation skill + internal evals suite
│   ├── SKILL.md                # Authoritative skill instructions
│   ├── references/             # Deep architectural references (bootstrap, evolution, etc.)
│   └── evals/                  # Multi-checkpoint evaluation harness & trusted checks
├── repo-native-refactor/       # Refactor skill + cryptographic audit harness
│   ├── SKILL.md                # Authoritative refactoring guidelines
│   ├── references/             # Risk classification and prose audit references
│   └── evals/                  # Cryptographic test harness (32 deterministic unit tests)
├── evals-suite/                # Unified experimental archive & benchmarks
│   ├── gate3_space_bunny/      # 32-checkpoint live campaign (Space Bunny + Codex)
│   ├── ablation_cp2/           # Head-to-head greenfield slice ablation
│   └── ablation_cp3_hardcore/  # Head-to-head multi-tenant enterprise evolution ablation
├── BENCHMARK_REPORT.md         # Full empirical benchmark report across all phases
└── README.md                   # This document
```

---

## Benchmark Highlights

Across a multi-phase evaluation spanning **Space Bunny (OpenCode)**, **Claude Sonnet 4.6**, **OpenAI Codex**, and blind judge reviews:

| Evaluation Phase | Metric | Raw Model (Control) | With Skills (Treatment) | Impact |
| :--- | :--- | :---: | :---: | :--- |
| **Harness Invariants** | Deterministic Unit Tests | 32 / 32 Passed | 32 / 32 Passed | Verified cryptographic tree hashing |
| **Gate 3 Cohort (32 Jobs)** | Functional Pass Rate | 100% | 100% | Baseline operational viability |
| **CP2 Greenfield Slice** | Contract Compliance | 19 / 24 (Failed `str`) | **24 / 24 (100%)** | Prevented string-to-Path type drift |
| **CP3 Enterprise Evolution** | Blind Architect Review | 2.84 / 4.00 (71%) | **4.00 / 4.00 (100%)** | Enforced DRY logic & living docs sync |
| **Living Documentation** | `README.md` Synchronized | ❌ Failed (Obsolete CP1 stub) | ⚠️ Passed with caveats | Updated to CP3 contracts; peer audit noted forward-looking reference to CLI export |

See [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md) for the complete data tables, failure analyses, and blind review verdicts.

---

## Reproducing the Verification Suite

Run all verification batteries directly from the repository root:

```bash
# 1. Run refactor harness integrity tests (32 unit tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run foundation evaluation harness tests:
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets:
python repo-foundation/evals/harness.py validate

# 4. Verify CP2 and CP3 solutions in temporary scratch workspaces:
python repo-foundation/evals/harness.py verify CP2_SLICE evals-suite/ablation_cp2/treatment/workspace
python repo-foundation/evals/harness.py verify CP3_EVOLUTION evals-suite/ablation_cp3_hardcore/treatment/workspace

# 5. Run the 7-trap CP3 hardcore runtime verification suite:
python evals-suite/ablation_cp3_hardcore/verify_cp3.py evals-suite/ablation_cp3_hardcore/treatment/workspace
```
