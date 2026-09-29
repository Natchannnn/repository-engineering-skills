# Benchmark notes: what worked, what didn't, what I fixed

**Date:** 2026-09-26
**Subject:** Testing `repo-foundation` and `repo-native-refactor`

How I tested: four rounds, two agents, two harnesses, automated checks plus a blind judge.

---

## 1. The short version

I tested both skills, found three problems, patched them, then tested again:
- **`repo-foundation`**: Project bootstrap, vertical slices, contract evolution, living documentation, and multi-session continuity.
- **`repo-native-refactor`**: Evidence-based scoped refactoring, semantic predicate consolidation (DRY), and change-set cleanup.

Four rounds below. Hash checks you can re-run locally; judge scores you cannot:
1. **Phase 1 (Gate 3 Live Campaign — 32 Checkpoints):** Evaluated on **Space Bunny** (OpenCode) and judged blindly by **OpenAI Codex**. Result: 32/32 functional pass, but revealed 3 critical blindspots (raw models substituted `Path` for `str`, zero persistent test files authored, and premature refactoring on greenfield code caused Variant C/D to score lower than Baseline A). Raw candidate workspaces are preserved under `evals-suite/gate3_space_bunny/`.
2. **Phase 2 (three small patches):** *Strict literal contract adherence*, *Proportionate test artifact authorship*, and the *Minimal intervention and evidence gate*.
3. **Phase 3 (retest with Claude Sonnet 4.6):** Checked whether the patched skills fixed the blind spots head-to-head:
   - **CP2 Greenfield Slice:** Control altered the type contract (`Path`, 19/24); Treatment scored **24/24**.
   - **CP3 multi-tenant migration (the hardest task):** Both passed runtime tests (25/25). Blind judge review awarded **4.00 / 4.00 (100%)** to Treatment vs **2.84 / 4.00 (71.0%)** to Control. Treatment 4.00/4.00, control 2.84/4.00. One run each, one judge, so treat it as a case study. Control failed the mandatory `documentation_synchronized` hard gate and duplicated validation logic.
4. **Phase 4 (harness self-tests):** 32 automated harness integrity tests executed and verified in 63.3s at commit `ae83651` (expanded to 33 tests at commit `200286c` with Windows 8.3 short-path resolution).

---

## 2. Phase 1: Gate 3 live campaign (Space Bunny and Codex)

### Cohort setup
- **Tester Agent:** Space Bunny (OpenCode)
- **Blind Judge:** OpenAI Codex
- **Workload:** 32 checkpoints across 4 variants and 2 repeated runs (`rep01`, `rep02`):
  - **Variant A:** Baseline (No Skills)
  - **Variant B:** `repo-foundation`
  - **Variant C:** `repo-native-refactor`
  - **Variant D:** Combined (Foundation + Refactor)

### Raw results

| Variant | Rep 01 Score | Rep 02 Score | Total Score (Max 192) | Functional Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| **A (Baseline)** | 56 | 64 | **120** | **8 / 8 (100%)** |
| **B (`repo-foundation`)** | 59 | 67 | **126 (Highest)** | **8 / 8 (100%)** |
| **C (`repo-native-refactor`)**| 59 | 55 | **114** | **8 / 8 (100%)** |
| **D (Both Skills)** | 59 | 56 | **115** | **8 / 8 (100%)** |

A scored 56 in one run and 64 in the other. B beat A by 6 in total, which is less than that swing.

### Observed failures: what Gate 3 exposed
While **Variant B** scored higher than Baseline A (126 vs 120), **Variants C and D scored lower than Baseline A**. Codex's blind review revealed three failure modes:
1. **The literal type blind spot:** In 4 checkpoints, models swapped `LEDGER_FILE: str` with `pathlib.Path(...)`. Functional checks passed, but the `contract_aligned` pass bar failed.
2. **The missing test artifact blind spot:** In all 32 checkpoints, `Test Quality` was scored **0**. Space Bunny ran extensive self-checks in memory and scratch commands, but never authored or committed test files (`test_*.py`) for the judge to inspect.
3. **Premature refactoring:** On clean greenfield code (CP1/CP2), `repo-native-refactor` lacked an evidence gate. It tried to restructure code that was already minimal and correct, adding diff churn that penalized Variants C and D.

The raw candidate workspaces and verification logs for the 32 Gate 3 checkpoints are preserved under `evals-suite/gate3_space_bunny/`. Judge scoring logs are summarized in `summary.md`, with one trajectory summary at `gate3-manual-v2-results/A_rep01.md` (not a full judge record).

---

## 3. Phase 2: the three patches

Instead of explaining away the Gate 3 scores, I treated the failure modes as engineering requirements. Three small rules went into both skills:

1. **Strict Literal Contract Adherence (`repo-foundation` & `repo-native-refactor`):**
   > *"Preserve exact declared interface types across all public boundaries (function signatures, return types, public module constants, and exported parameters). If a contract or specification declares a primitive type such as `str`, never change or wrap the exposed interface in `pathlib.Path` or custom wrapper objects unless an architectural evolution is explicitly authorized by the task. Internal intermediate representations may use appropriate helpers, provided all exposed public contracts and types remain exact."*
2. **Proportionate Test Artifact Authorship (`repo-foundation`):**
   > *"When task scope permits, author persistent tests (`tests/test_<feature>.py`) asserting happy paths, boundary conditions, and regressions. When task scope restricts modifications to a single module, verify using localized scratch checks; do not pollute the workspace with unapproved files."*
3. **Minimal Intervention & Evidence Gate (`repo-native-refactor`):**
   > *"Refactor only when there is concrete evidence of divergence, defect, code smell, or operational risk. Consolidate shared validation or transformation logic into clean, reusable helpers or predicates only when implementations share ownership, invariants, semantic purpose, and reasons to change."*

---

## 4. Phase 3: retest with Claude Sonnet 4.6

To check whether the patches fixed the failures, I reran the same milestones head-to-head on **Anthropic Claude Sonnet 4.6**:

### Test 1: smoke check (CP2 greenfield)
- **Goal:** check whether the "Test Quality = 0" failure was fixed.
- **Result:** Claude Sonnet 4.6 loaded the patched skills, wrote **18 unit tests** in `tests/test_query.py`, and scored **24 / 24**. Test Quality went from 0 to 4.

### Test 2: CP2 slice, head-to-head
- **Setup:** same CP1 baseline, same un-coached task prompt (`evals/tasks/CP2_SLICE.md`).
- **Control (no skills):** Sonnet 4.6 wrapped `LEDGER_FILE` in `Path(...)` and failed the contract check (19 / 24).
- **Treatment (with skills):** kept `LEDGER_FILE = "ledger.jsonl"` (`str`), ran 24 local verification checks, passed everything (24 / 24).

### Test 3: CP3 migration, head-to-head
- **Setup:** multi-tenant contract evolution. Tenant validation (`ValueError` on missing/empty/blank/non-string), zero-mutation guarantee on failure, atomic idempotent migration (`migrate() -> int`), multi-filter querying (`find(kind, tenant)`), and living documentation sync.
- **Automated tests (`verify_cp3.py`):** control and treatment both passed everything (25 / 25).
- **Blind judge review (unblinded after scoring):**

| Dimension | Weight | Control (No Skills) | Treatment (With Skills) | Delta / Finding |
| :--- | :---: | :---: | :---: | :--- |
| **1. Functional Correctness & Contracts** | 25% | **4.0 / 4.0** | **4.0 / 4.0** | Parity on runtime execution |
| **2. Refactoring Craft & Code Economy** | 20% | **2.8 / 4.0** | **4.0 / 4.0** | **Treatment:** extracted affirmative predicate `_is_valid_tenant` (DRY). Control duplicated validation with inverted logic (`_needs_migration`). |
| **3. Repository Conformity & Living Docs**| 20% | **0.0 / 4.0** | **4.0 / 4.0** | **Treatment:** updated `README.md` with complete CP3 contracts. Control left docs in obsolete CP1 stub. |
| **4. Scope control and blast radius** | 10% | **4.0 / 4.0** | **4.0 / 4.0** | Both kept tight boundaries |
| **5. Contract Alignment & Type Safety** | 10% | **4.0 / 4.0** | **4.0 / 4.0** | Both preserved `str` type |
| **6. Code Clarity & Clean Idioms** | 15% | **3.2 / 4.0** | **4.0 / 4.0** | Treatment used clean variable semantics (`count` vs `migrated`) |
| **Weighted Total** | **100%** | **2.84 / 4.00 (71.0%)** | **4.00 / 4.00 (100%)** | Treatment 4.00/4.00, control 2.84/4.00. One run each, one judge, so this is a case study, not a benchmark. |

Limits of this round: 8 trajectories across 4 variants (32 checkpoints) in one toy ledger repo for Gate 3. Phase 3 ran each arm once on CP2 and CP3. That validates the mechanism on these tasks. It says nothing general about other stacks.

One more honest note: treatment's updated `README.md` mentioned a CLI export that did not exist yet in that code slice. Aspirational docs are still docs drift.

### Hard gate pass bars

| Pass Bar | Control (No Skills) | Treatment (With Skills) | Impact |
| :--- | :---: | :---: | :--- |
| `functional_correctness` | **MET** | **MET** | Runtime correctness verified |
| `zero_mutation_guarantee` | **MET** | **MET** | Byte-exact file protection verified |
| `atomic_migration_idempotent` | **MET** | **MET** | Atomic fsync pattern confirmed via code inspection; migration idempotency verified at runtime (crash durability during power loss was not simulated) |
| `contract_literal_str_preserved`| **MET** | **MET** | `str` preserved in both |
| `documentation_synchronized` | <mark>**NOT MET (FAILED)**</mark> | **MET (PASSED)** | **Control disqualified on documentation drift** |

---

## 5. Phase 4: harness self-tests

The test harness in `repo-native-refactor/evals/` passed its deterministic self-tests:
- **Earlier run (commit `ae83651`):** `Ran 32 tests in 63.339s — OK` (32/32).
- **Current release (commit `200286c`):** `Ran 33 tests in 70.755s — OK` (33/33; added Windows 8.3 short-path resolution).
- **What the tests check:**
  - Strict SHA-256 tree hash computation over directory snapshots.
  - Rejection of post-collection tampering (patch alteration, task mutation, metadata edits).
  - Byte-exact roundtripping of binary data, non-UTF8 bytes, and CRLF line endings.
  - Scratch workspace isolation: baseline checks and test runners run in isolated disposable trees without mutating source trees.

---

## 6. Summary across phases

### Agent behavior

| Benchmark Stage | Model & Agent | Control (No Skills) | Treatment (With Skills) | What it showed |
| :--- | :--- | :---: | :---: | :--- |
| **Phase 1: Gate 3 (32 Jobs)** | Space Bunny + Codex | 120 / 192 (A) | **126 / 192 (B)** | Foundation skill improved continuity; uncovered type drift and premature refactoring issues. |
| **Phase 3: CP2 Greenfield** | Claude Sonnet 4.6 | 19 / 24 (swapped `str` for `Path`) | **24 / 24** | Literal contract rule kept the declared string API contract. |
| **Phase 3: CP3 migration** | Claude Sonnet 4.6 | 2.84 / 4.00 (71.0%) | **4.00 / 4.00 (100%)** | Skills consolidated the predicate (DRY) and synced the docs. |

### Harness tests and archive

| Test Target | Runner | Scope | Result | What it checks |
| :--- | :--- | :--- | :---: | :--- |
| **Refactor Harness Suite** | Python 3.14 `unittest` | 33 tests | **33 / 33 Passed** | Blind review protocol, patch round-tripping, non-finite score rejection, Windows 8.3 path resolution. |
| **Foundation Harness Suite** | Python 3.14 `unittest` | 26 tests | **26 / 26 Passed** | Byte snapshot determinism, atomic rollback on I/O failure, unmanaged target protection. |
| **Historical Archive Evidence** | `scripts/verify-archive.ps1` | 31 packets | **31 / 31 Passed** | Exact SHA-256 tree hash parity across fresh clones and line ending configurations. |

---

## 7. Verify it yourself

Run these locally. No network or API keys needed. (Rerunning the live agent runs needs model access; see Phase 1 and Phase 3 above.)

```bash
# 1. Run refactor harness unit tests (33 tests):
python -B -m unittest discover -s repo-native-refactor/evals/tests -v

# 2. Run foundation evaluation harness unit tests (26 tests):
python -B -m unittest discover -s repo-foundation/evals/tests -v

# 3. Validate foundation evaluation assets (schemas, rubric, task specs):
python -B repo-foundation/evals/harness.py validate

# 4. Verify all 31 archive evidence packets via unified script:
pwsh -NoProfile -File ./scripts/verify-archive.ps1

# 5. Verify CP2, CP3, and CP4 solutions in temporary scratch workspaces:
python -B repo-foundation/evals/harness.py verify CP2_SLICE evals-suite/ablation_cp2/treatment/workspace
python -B repo-foundation/evals/harness.py verify CP3_EVOLUTION evals-suite/ablation_cp3_hardcore/treatment/workspace
python -B repo-foundation/evals/harness.py verify CP4_CONTINUITY evals-suite/gate3_space_bunny/gate3-manual-v2-A-rep01
```
