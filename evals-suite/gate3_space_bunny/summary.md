# Gate 3 Live Campaign: 32-Checkpoint Empirical Cohort (V2)

**Tester Agent:** Space Bunny (via OpenCode)  
**Evaluator / Judge:** OpenAI Codex (Blind Judge)  
**Execution Environment:** Multi-checkpoint isolated containerized runs (`evals-foundation`)  
**Scope:** 32 checkpoints across 4 experimental variants  

---

## 1. Experimental Cohort Matrix

The cohort evaluated 4 distinct variants over repeated runs (`rep01`, `rep02`) across the 4 milestones (`CP1_BOOTSTRAP`, `CP2_SLICE`, `CP3_EVOLUTION`, `CP4_CONTINUITY`):

| Variant | Skill Assignment | Description |
| :--- | :--- | :--- |
| **A** | None (Baseline) | Raw model execution without engineering skills |
| **B** | `repo-foundation` | Lifecycle engineering, foundation baseline, living docs |
| **C** | `repo-native-refactor` | Post-implementation audit & refactoring |
| **D** | Both (Foundation + Refactor) | Combined companion coordination |

---

## 2. Quantitative Results & Scorecard

**Functional Acceptance:** **32 / 32 Checkpoints PASSED (100% Functional Pass Rate)**. All variants built working code that satisfied baseline functional checks.

### Qualitative Dimensional Scores (Judged by Codex)
*Evaluated across 6 core criteria (max 192 points per variant across repetitions; excluding checkpoint-specific CP3/CP4 extra criteria):*

| Variant | Rep 01 Score | Rep 02 Score | Total Score | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **A (Baseline)** | 56 | 64 | **120** | Strong raw functional coding, but high contract drift |
| **B (`repo-foundation`)** | 59 | 67 | **126 (Highest)** | Highest architectural coherence and continuity |
| **C (`repo-native-refactor`)**| 59 | 55 | **114** | Premature intervention on greenfield code |
| **D (Both Skills)** | 59 | 56 | **115** | Over-auditing on un-needed clean additive slices |

---

## 3. Critical Findings & The 3 Skill Blindspots

While Variant B showed the best overall qualitative signal (126 vs 120), Gate 3 surfaced three critical engineering defects that proved raw skills still had vulnerabilities:

1. **Type Contract Drift (`contract_aligned: NOT MET` in 4 Checkpoints):**
   - In CP1–CP2 of A/rep01 and C/rep02, the model spontaneously substituted a string literal `LEDGER_FILE = "ledger.jsonl"` with `pathlib.Path(...)`.
   - Functional checks still passed because Python path objects happen to resolve locally, but downstream callers and IPC schemas expecting literal `str` were broken.
2. **The "Zero Test Quality" Blindspot (`Test Quality = 0` in all 32 Checkpoints):**
   - Space Bunny performed numerous self-checks in memory and ephemeral scripts, but never authored or committed persistent test artifacts (e.g. `tests/test_*.py`) for the judge to inspect.
   - Without explicit instruction, LLMs default to ephemeral verification.
3. **Premature Refactoring Penalty (Why C and D scored lower than A):**
   - `repo-native-refactor` lacked a strict "Minimal Intervention & Evidence Gate". When applied to clean greenfield code (CP1/CP2), it attempted to refactor code that was already minimal and correct, adding churn and lowering maintainability scores.

---

## 4. The Engineering Remedy

These three empirical findings from Gate 3 formed the exact specification for the subsequent skill patches:
1. **Patch 1 (`Strict literal contract adherence`):** Forbids wrapping or substituting declared primitive types (`str`) with `Path` or custom wrappers unless explicitly instructed.
2. **Patch 2 (`Proportionate test artifact authorship`):** Mandates authoring persistent test files (`tests/test_<feature>.py`) when task scope permits, while respecting boundaries when single-file constraints apply.
3. **Patch 3 (`Minimal Intervention & Evidence Gate`):** Prohibits speculative restructuring on clean greenfield or additive slices; requires concrete evidence of code smell or regression before refactoring.

Subsequent isolated ablations (CP2 Greenfield Slice and CP3 Hardcore Evolution) confirmed that these three patches addressed and mitigated the blindspots identified in Gate 3.
