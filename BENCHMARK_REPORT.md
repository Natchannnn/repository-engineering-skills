# Empirical Benchmark Report: The Evolution, Failures, and Hardening of AI Engineering Skills

**Date:** 2026-09-26  
**Subject:** Empirical validation of `repo-foundation` and `repo-native-refactor`  
**Methodology:** Multi-phase longitudinal evaluation across 2 agent architectures, 2 evaluation harnesses, automated checks, and blind judge reviews.  

---

## 1. Executive Summary & Scientific Honesty

Most AI benchmarks suffer from selective reporting: authors tune prompts until their tool wins, reporting flattering numbers while hiding negative signals. 

This report documents the **complete, unvarnished trajectory** of developing, testing, and hardening two specialized agent engineering skills:
- **`repo-foundation`**: Lifecycle engineering (Bootstrap, Slice, Evolution, Continuity), living documentation, and contract type protection.
- **`repo-native-refactor`**: Evidence-based surgical refactoring, semantic DRY predicate consolidation, and code hygiene.

The evaluation traversed four distinct empirical phases:
1. **Phase 1 (Gate 3 Live Campaign — 32 Checkpoints):** Evaluated on **Space Bunny** (OpenCode) and judged blindly by **OpenAI Codex**. Result: 32/32 functional pass, but revealed 3 critical blindspots (raw models substituted `Path` for `str`, zero persistent test files authored, and premature refactoring on greenfield code caused Variant C/D to score lower than Baseline A).
2. **Phase 2 (Targeted Skill Hardening):** Applied three explicit, surgical patches: *Strict literal contract adherence*, *Proportionate test artifact authorship*, and the *Minimal Intervention & Evidence Gate*.
3. **Phase 3 (Frontier Model Stress Ablations — Claude Sonnet 4.6):** Tested whether the hardened skills solved the blindspots under strict head-to-head conditions:
   - **CP2 Greenfield Slice:** Control failed the type contract (`Path`, 19/24); Treatment scored **24/24**.
   - **CP3 Hardcore Enterprise Evolution:** Both passed runtime tests (25/25). Blind judge review awarded **4.00 / 4.00 (100%)** to Treatment vs **2.84 / 4.00 (71.0%)** to Control (+29.0 percentage points). Control failed the mandatory `documentation_synchronized` hard gate and duplicated validation logic.
4. **Phase 4 (Cryptographic Invariants):** 32 automated harness integrity tests executed and verified in 63.3s.

---

## 2. Phase 1: Gate 3 Live Campaign (Space Bunny & Codex)

### Cohort Setup
- **Tester Agent:** Space Bunny (OpenCode)
- **Blind Judge:** OpenAI Codex
- **Workload:** 32 checkpoints across 4 variants and 2 repeated runs (`rep01`, `rep02`):
  - **Variant A:** Baseline (No Skills)
  - **Variant B:** `repo-foundation`
  - **Variant C:** `repo-native-refactor`
  - **Variant D:** Combined (Foundation + Refactor)

### Raw Results

| Variant | Rep 01 Score | Rep 02 Score | Total Score (Max 192) | Functional Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| **A (Baseline)** | 56 | 64 | **120** | **8 / 8 (100%)** |
| **B (`repo-foundation`)** | 59 | 67 | **126 (Highest)** | **8 / 8 (100%)** |
| **C (`repo-native-refactor`)**| 59 | 55 | **114** | **8 / 8 (100%)** |
| **D (Both Skills)** | 59 | 56 | **115** | **8 / 8 (100%)** |

### The Brutal Truth: What Gate 3 Exposed
While **Variant B** scored higher than Baseline A (126 vs 120), **Variants C and D scored lower than Baseline A**. Codex's blind review revealed three distinct failure modes:
1. **The Literal Type Blindspot:** In 4 checkpoints, models spontaneously substituted `LEDGER_FILE: str` with `pathlib.Path(...)`. Functional checks passed, but the `contract_aligned` pass bar failed.
2. **The Missing Test Artifact Blindspot:** In all 32 checkpoints, `Test Quality` was scored **0**. Space Bunny performed extensive self-checks in memory and scratch commands, but never authored or committed test files (`test_*.py`) for the judge to inspect.
3. **Premature Refactoring Churn:** On clean greenfield code (CP1/CP2), `repo-native-refactor` lacked an evidence gate. It attempted to restructure code that was already minimal and correct, adding unnecessary diff churn that penalized Variants C and D.

> [!NOTE] Gate 3 Archive Provenance
> The raw candidate workspaces and verification logs for the 32 Gate 3 checkpoints are preserved under `evals-suite/gate3_space_bunny/`. Qualitative judge scoring logs are summarized in `summary.md` with a representative trajectory summary preserved at `gate3-manual-v2-results/A_rep01.md` (does not constitute a full underlying judge record).

---

## 3. Phase 2: Targeted Engineering Patches

Rather than rationalizing the Gate 3 scores, we treated the failure modes as precise engineering requirements. We added three non-negotiable rules across both skills:

1. **Strict Literal Contract Adherence (`repo-foundation` & `repo-native-refactor`):**
   > *"Preserve exact declared interface types across all public boundaries (function signatures, return types, public module constants, and exported parameters). If a contract or specification declares a primitive type such as `str`, never change or wrap the exposed interface in `pathlib.Path` or custom wrapper objects unless an architectural evolution is explicitly requested. Internal intermediate representations may use appropriate helpers, provided all exposed public contracts and types remain exact."*
2. **Proportionate Test Artifact Authorship (`repo-foundation`):**
   > *"When task scope permits, author persistent tests (`tests/test_<feature>.py`) asserting happy paths, boundary conditions, and regressions. When task scope restricts modifications to a single module, verify using localized scratch checks; do not pollute the workspace with unapproved files."*
3. **Minimal Intervention & Evidence Gate (`repo-native-refactor`):**
   > *"Refactor only when there is concrete evidence of divergence, defect, code smell, or operational risk. Consolidate shared validation or transformation logic into clean, reusable helpers or predicates only when implementations share ownership, invariants, semantic purpose, and reasons to change."*

---

## 4. Phase 3: Frontier Model Stress Ablations (Claude Sonnet 4.6)

To rigorously verify if the patches addressed the failure modes, we subjected the hardened skills to focused head-to-head ablation tests on **Anthropic Claude Sonnet 4.6**:

### Test 1: Smoke Verification (CP2 Greenfield)
- **Goal:** Verify if the "Test Quality = 0" failure was resolved.
- **Result:** Claude Sonnet 4.6 loaded the patched skills, autonomously authored **18 comprehensive unit tests** in `tests/test_query.py`, and scored **24 / 24 Full Marks**. Test Quality jumped from 0 to 4.

### Test 2: CP2 Greenfield Slice Ablation (Head-to-Head)
- **Setup:** Identical CP1 baseline, identical un-coached task prompt (`evals/tasks/CP2_SLICE.md`).
- **Control (No Skills):** Sonnet 4.6 spontaneously wrapped `LEDGER_FILE = Path(...)` $\to$ **Failed contract (`contract_aligned: NOT MET`, 19 / 24)**.
- **Treatment (With Skills):** Maintained `LEDGER_FILE = "ledger.jsonl"` (`str`), executed 24 localized verification checks $\to$ **Passed all bars (`contract_aligned: MET`, 24 / 24, Winner)**.

### Test 3: CP3 Hardcore Enterprise Evolution Ablation (Head-to-Head)
- **Setup:** Complex multi-tenant contract evolution: tenant validation (`ValueError` on missing/empty/blank/non-string), zero-mutation guarantee on failure, atomic idempotent migration (`migrate() -> int`), multi-filter conjunction querying (`find(kind, tenant)`), and living documentation synchronization.
- **Automated Test Battery (`verify_cp3.py`):** Both Control and Treatment achieved **25 / 25 (Full Pass)** on runtime execution.
- **Independent Architectural Review (Blind Judge with Post-Hoc Unblinding):**

| Dimension | Weight | Control (No Skills) | Treatment (With Skills) | Delta / Finding |
| :--- | :---: | :---: | :---: | :--- |
| **1. Functional Correctness & Contracts** | 25% | **4.0 / 4.0** | **4.0 / 4.0** | Parity on runtime execution |
| **2. Refactoring Craft & Code Economy** | 20% | **2.8 / 4.0** | **4.0 / 4.0** | **Treatment:** extracted affirmative predicate `_is_valid_tenant` (DRY). Control duplicated validation with inverted logic (`_needs_migration`). |
| **3. Repository Conformity & Living Docs**| 20% | **0.0 / 4.0** | **4.0 / 4.0** | **Treatment:** updated `README.md` with complete CP3 contracts. Control left docs in obsolete CP1 stub. |
| **4. Scope Control & Blast Radius** | 10% | **4.0 / 4.0** | **4.0 / 4.0** | Both maintained surgical boundaries |
| **5. Contract Alignment & Type Safety** | 10% | **4.0 / 4.0** | **4.0 / 4.0** | Both preserved `str` type |
| **6. Code Clarity & Clean Idioms** | 15% | **3.2 / 4.0** | **4.0 / 4.0** | Treatment used clean variable semantics (`count` vs `migrated`) |
| **Weighted Total** | **100%** | **2.84 / 4.00 (71.0%)** | **4.00 / 4.00 (100%)** | Treatment scored +29.0 percentage points (+1.16/4.00) |

> [!NOTE] Evaluation Scope & Limitations
> - **Sample Size:** Gate 3 evaluated 8 longitudinal trajectories across 4 variants (32 total checkpoints) in the ledger repo domain. Phase 3 evaluated focused single-run head-to-head ablations per arm on the CP2 and CP3 milestones. These results demonstrate specific mechanism validation rather than large-scale statistical universality across arbitrary software stacks.
> - **Treatment Documentation Finding:** While Treatment synchronized `README.md` to reflect CP3 multi-tenant behavior, subsequent peer review audit identified a minor forward-looking overreach: the revised documentation referenced an aspirational CLI export not yet implemented in the codebase slice.

### Hard Gate Pass Bars

| Pass Bar | Control (No Skills) | Treatment (With Skills) | Impact |
| :--- | :---: | :---: | :--- |
| `functional_correctness` | **MET** | **MET** | Runtime correctness verified |
| `zero_mutation_guarantee` | **MET** | **MET** | Byte-exact file protection verified |
| `atomic_migration_idempotent` | **MET** | **MET** | Atomic fsync pattern confirmed via code inspection; migration idempotency verified at runtime (crash durability during power loss was not simulated) |
| `contract_literal_str_preserved`| **MET** | **MET** | `str` preserved in both |
| `documentation_synchronized` | <mark>**NOT MET (FAILED)**</mark> | **MET (PASSED)** | **Control disqualified on documentation drift** |

---

## 5. Phase 4: Test Harness Cryptographic Invariants (32 Tests)

The test harness in `repo-native-refactor/evals/` was verified across 32 deterministic cryptographic unit tests:
- **Command:** `python -B -m unittest discover -s repo-native-refactor/evals/tests -v`
- **Result:** `Ran 32 tests in 63.339s — OK` (32/32 Passed).
- **Invariants Verified:**
  - Strict SHA-256 tree hash computation over directory snapshots.
  - Rejection of post-collection tampering (patch alteration, task mutation, metadata edits).
  - Byte-exact roundtripping of binary data, non-UTF8 bytes, and CRLF line endings.
  - Scratch workspace isolation: baseline checks and test runners run in isolated disposable trees without mutating source trees.

---

## 6. Summary Comparison Table Across All Phases

| Benchmark Stage | Model & Agent | Control (No Skills) | Treatment (With Skills) | Measured Finding |
| :--- | :--- | :---: | :---: | :--- |
| **Phase 1: Gate 3 (32 Jobs)** | Space Bunny + Codex | 120 / 192 (A) | **126 / 192 (B)** | Foundation skill improved continuity; uncovered type drift & premature refactoring bugs. |
| **Phase 3: CP2 Greenfield** | Claude Sonnet 4.6 | 19 / 24 (Failed `str`) | **24 / 24 (Full Marks)** | Literal contract rule prevented model from breaking string API contract. |
| **Phase 3: CP3 Hardcore** | Claude Sonnet 4.6 | 2.84 / 4.00 (71.0%) | **4.00 / 4.00 (100%)** | Skills prevented logic duplication (DRY) and synchronized repository documentation. |
| **Phase 4: Harness Tests** | Deterministic Python | 32 / 32 Passed | 32 / 32 Passed | Cryptographic integrity and tamper-detection verified. |

---

## 7. How to Reproduce All Results

Clone the repository and run the test battery:

```bash
# 1. Run the 32 deterministic harness integrity unit tests:
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run the foundation evaluation harness unit tests:
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets (schemas, rubric, task specs):
python repo-foundation/evals/harness.py validate

# 4. Verify CP2 and CP3 solutions in temporary scratch workspaces:
python repo-foundation/evals/harness.py verify CP2_SLICE evals-suite/ablation_cp2/treatment/workspace
python repo-foundation/evals/harness.py verify CP3_EVOLUTION evals-suite/ablation_cp3_hardcore/treatment/workspace

# 5. Run the 7-trap CP3 hardcore runtime verification suite:
python evals-suite/ablation_cp3_hardcore/verify_cp3.py evals-suite/ablation_cp3_hardcore/treatment/workspace
```
