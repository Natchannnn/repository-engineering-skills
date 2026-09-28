# Phase 2 Behavioral Evaluation Protocol: Distributed Contracts and Paired Review (Phase 2 Protocol)

This document establishes the experimental methodology, technical specifications, fixtures, and acceptance criteria for **Phase 2** of the autonomous agent behavioral evaluation campaign across Python codebases.

---

## 1. Objectives & Scientific Hypotheses

### 1.1. Context from Phase 1 (9-Run Pilot)
- Phase 1 confirmed that all three configurations (A0 Control, A1 Guidelines, A2 Two Skills) completed focused, single-file micro-tasks (D1: dirty worktree bugfix, R1: multi-module contract drift review). On task D3 (pre-existing baseline failure attribution), models across A1 and A2 understood the underlying defect but were scored FAIL due to strict string-matching on the Test ID format.
- Phase 1 conclusion: On localized, single-file tasks with explicit requirements, empirical data showed no observed additional advantage of the treatment over the baseline control across those three fixtures.

### 1.2. Phase 2 Research Hypotheses
- **Hypothesis H1 (Distributed Constraint Discovery — Task D2):** When a public contract is intentionally evolved without the prompt enumerating affected callers, does equipping the agent with engineering skills (`repo-foundation`) promote proactive repository-wide inspection, comprehensive caller discovery, and complete migration compared to a bare prompt baseline?
- **Hypothesis H2 (Precision and Anti-Hallucination in Review — Paired Tasks R2A & R2B):** In code review tasks, agents exhibiting guesswork or defect-seeking bias risk flagging clean code (false positives on R2A). Do refactoring skills (`repo-native-refactor`) instill discipline: correctly reporting real defects when contract drift occurs (R2B — Recall) while refraining from fabricating issues on clean diffs (R2A — Precision)?
- **Principle of Falsifiability:** This evaluation was designed impartially so that **it may conclude that Treatment (A2) provides no measurable advantage or introduces additional latency/overhead compared to Control (A0)**. Skills were strictly frozen prior to execution and were not modified during or after evaluation.

---

## 2. Task Design

Phase 2 comprises three independent tasks: one contract migration task (D2) and two paired review tasks (R2A & R2B).

### 2.1. Task D2: Intentional Contract Migration & Distributed Caller Preservation
- **Domain:** E-commerce shipping and checkout service.
- **Authorized Evolution Scope:**
  - Upgrade `calculate_shipping(weight_kg: Decimal, destination: str, express: bool = False) -> ShippingQuote` in `src/shipping.py`.
  - Legacy contract returned a raw `Decimal`.
  - Target contract returns a dataclass `ShippingQuote(base_fee: Decimal, express_fee: Decimal, total_fee: Decimal)`.
  - Add optional parameter `express: bool = False` (when `True`, express fee is `Decimal("12.50")`).
  - Strict input validation: `weight_kg` must be strictly `Decimal` and `> 0`; `destination` must belong to supported destinations (`DOMESTIC`, `INTERNATIONAL`, `EXPRESS_ZONE`). Invalid inputs raise `ValueError`.
- **Mandatory Compatibility Surface (Must remain untouched):**
  - Module constant: `DEFAULT_RATE_PER_KG: Decimal = Decimal("5.00")`.
  - Public utility: `get_supported_destinations() -> list[str]`.
  - These symbols are consumed by external systems; candidates **must not rename, alter signatures, or remove them**.
- **Internal Migration Scope:**
  - The task prompt **does not enumerate caller file names**. The candidate must search the repository:
    1. Caller 1: `src/checkout.py::process_checkout`
    2. Caller 2: `src/cart_summary.py::estimate_cart`
    3. Caller 3: `src/invoice.py::generate_invoice_line_items`
  - All callers must be migrated to consume `ShippingQuote` (accessing `.total_fee`).
  - All existing caller tests in `tests/` must pass after migration; neutering, emptying, or suppressing caller tests is strictly prohibited.

### 2.2. Task R2A: Paired Neutral Review — Clean Diff (Clean Fixture)
- **Candidate Display Name:** Neutral label `task_r2a`, branch `review/batch-sync-v2`. Contains zero leading keywords such as "clean", "pass", or "no-defect".
- **Technical Nature:** Branch refactors batch synchronization logic and comprehensively migrates all repository callers. Zero contract drift, zero broken signatures, zero type mismatches.
- **Expected Output:** Empty JSON array `[]`.
- **Measurement Purpose:** Measures **Precision / False Positive Rate** (resistance against defect-seeking hallucination).

### 2.3. Task R2B: Paired Neutral Review — Defect Diff (Defect Fixture)
- **Candidate Display Name:** Neutral label `task_r2b`, branch `review/auth-token-v2`. Contains zero leading keywords such as "defect", "fail", or "broken".
- **Technical Nature:** Branch updates session token generation in `src/auth_service.py` (altering parameter order or introducing mandatory parameters), while leaving a dependent caller in `src/api_gateway.py::handle_login` calling the old signature. Runtime execution reliably triggers `TypeError`.
- **Expected Output:** Precise JSON defect report adhering to schema.
- **Measurement Purpose:** Measures **Recall / True Positive Detection**.

---

## 3. Experimental Arms

Each task is evaluated across three configurations:
1. **Arm A0 (Control — Bare Prompt):** Receives raw task instructions with no external engineering guidelines or skills.
2. **Arm A1 (Karpathy Engineering Guidelines):** Receives task instructions plus Karpathy-inspired engineering principles (minimal diffs, understand before editing, respect caller boundaries and test suites).
3. **Arm A2 (Treatment — Two Skills):** Receives task instructions plus both official repository skills: `repo-foundation` and `repo-native-refactor`.

---

## 4. Cohort Scope & Execution Structure

- **Sample Size:** 3 tasks (`D2`, `R2A`, `R2B`) × 3 arms (`A0`, `A1`, `A2`) × 3 independent repetitions = **27 runs**.
- **Balanced Arm Rotation (Latin-square permutation):**
  - Arm sequence was systematically rotated across the 3 repetitions:
    - **Rep 1:** `A0 -> A1 -> A2`
    - **Rep 2:** `A1 -> A2 -> A0`
    - **Rep 3:** `A2 -> A0 -> A1`
  - Rotation balances positional bias and mitigates execution-order confounding factors across arms.
- **Scientific Significance of Repetitions:**
  - 3 repetitions per task measure **inter-run variance / non-determinism** for a given model and prompt.
  - 3 repetitions **do not represent problem domain diversity**. This 27-run evaluation constitutes an **exploratory cohort** and should not be used to make sweeping claims about general software engineering capabilities.

---

## 5. Experimental Environment & Execution Conditions

- **Host Platform:** Google Antigravity Advanced Agentic Coding Engine.
- **Model Metadata:**
  - `Host: Antigravity`
  - `Requested model: inherit`
  - `Resolved model: unknown / not recorded`
- **Subagent Specification:**
  - Fully isolated `pilot_candidate` subagent.
  - Enabled tools: Write/Edit tools (`view_file`, `write_to_file`, `replace_file_content`, `run_command`).
  - Disabled tools: Subagent tools, MCP tools, Web search.
- **Execution Mode & Batching:**
  - Runs within each repetition were spawned and executed **as concurrent triplets** on the host:
    - *Repetition 1 (Runs 01–09):* Spawned in order `A0 -> A1 -> A2` (e.g. Runs 01, 02, 03 spawned at 22:24:14Z).
    - *Repetition 2 (Runs 10–18):* Spawned in order `A1 -> A2 -> A0` (e.g. Runs 10, 11, 12 spawned at 22:32:14Z).
    - *Repetition 3 (Runs 19–27):* Spawned in order `A2 -> A0 -> A1` (e.g. Runs 19, 20, 21 spawned at 22:38:54Z).
  - *Infrastructure acknowledgment:* Due to concurrent execution within the same host session, subagents potentially shared compute resources (CPU, memory, I/O, network bandwidth) and experienced identical localized host infrastructure fluctuations.
- **Timing & Timeout Policy:**
  - *Nominal timeout:* 180 seconds.
  - *Transcript-measured elapsed time:* Measured from the first recorded entry to the final response in the subagent transcript (including final report transmission to host).
    - 25 of 27 runs finished in under 180s (ranging from 38s to 164s).
    - 2 runs (Run 03: 184s and Run 19: 182s) slightly exceeded the nominal 180s window.
    - *Enforcement & validity:* The host did not emit an abort signal; the independent verifier verified that workspace solutions were fully valid and correct. The verifier PASS was preserved, with the timing anomaly transparently documented in metadata.
- **Retry Policy:**
  - Infrastructure crashes (host termination, socket drops) permitted 1 rerun with explicit metadata recording.
  - Candidate voluntary exits or failed solutions were preserved without retries.

---

## 6. Verifier Criteria & Decoupled Metrics

### 6.1. Criteria for Task D2
1. **Mandatory Snapshot:** Sidecar snapshot (`d2-snapshot.json`) is strictly required to validate `initial_head` and `manifest`. Missing, malformed, or incomplete snapshots result in immediate failure.
2. **Git Integrity & No Staged Churn:** `git rev-parse HEAD` must strictly match `initial_head`. Staging index must be clean.
3. **Baseline Caller Test Protection:** The three test files `tests/test_checkout.py`, `tests/test_cart_summary.py`, and `tests/test_invoice.py` must match their original SHA-256 byte hashes in manifest (CRLF -> LF normalized) and must contain runnable tests that pass. Modifying, emptying, or replacing them with trivial assertions (`assertTrue(True)`) triggers immediate failure.
4. **Compatibility Surface:** `DEFAULT_RATE_PER_KG` (strictly `Decimal("5.00")`) and `get_supported_destinations()` must exist with unaltered contracts.
5. **Hidden Acceptance Tests for New API:** Verifies `calculate_shipping` against base fees, express fees, total fees, express flag, frozen `ShippingQuote` dataclass, and exact exceptions (`ValueError("Invalid weight")`, `ValueError("Unsupported destination")`).
6. **Hidden Caller Migration Tests:** Independently invokes `process_checkout`, `estimate_cart`, and `generate_invoice_line_items` to confirm migration to `ShippingQuote.total_fee` and verified business outputs.
7. **Existing Test Suite:** All tests in `tests/` pass with an explicit `OK` banner (zero `SkipTest`).

### 6.2. Criteria for Tasks R2A & R2B
- **Mandatory Snapshot:** Sidecar snapshot (`r2a-snapshot.json` / `r2b-snapshot.json`) required to validate `feature_head` and `manifest`.
- **Absolute Read-Only Enforcement:**
  - `git rev-parse HEAD` must match `feature_head` (no code commits).
  - `git diff HEAD` and staged index must be 100% clean.
  - All tracked files in manifest must match original SHA-256 hashes (CRLF -> LF normalized).
  - Bytecode caches generated by test discovery (`__pycache__`, `.pyc`) are permitted.
- **Report Output:** JSON file outside repository specified via `--evidence-file`:
  ```json
  [
    {
      "verdict": "defect",
      "source_file": "<path_to_source>",
      "source_symbol": "<symbol_name>",
      "broken_caller_file": "<path_to_caller>",
      "broken_caller_symbol": "<caller_symbol_name>",
      "breakage_type": "contract_drift | removed_symbol | signature_changed | type_mismatch"
    }
  ]
  ```
- **Decoupled Evaluation Metrics:**
  - `TP` (True Positives): Correct detection of actual contract drift (accepting pre-declared valid aliases).
  - `FP` (False Positives): Fabricated defect reported on clean code.
  - `FN` (False Negatives): Real defect missed.
  - On the clean fixture (R2A): With zero ground-truth defects (denominator is 0), individual run metrics are reported as `Precision: N/A`, `Recall: N/A`, with the sole pass criterion being `FP == 0` (no hallucinated defects).
  - On the defect fixture (R2B): Requires `TP == 1` and `FP == 0` (Precision = 1.0, Recall = 1.0).
  - Aggregate Precision and Recall are computed across pooled R2A and R2B data.
- **Task R2A (Clean):** Requires `FP == 0` (empty array `[]`). Any finding is scored FAIL.
- **Task R2B (Defect):** Requires `TP == 1` and `FP == 0`. An empty array `[]` is scored FAIL.

---

## 7. Verifier Self-Audit Suite

Prior to running candidate evaluations, the Phase 2 verifier suite passed 35 positive and negative control unit tests:
1. **D2 Controls (15 tests):**
   - Canonical Solution (shipping updated + all 3 callers migrated) -> PASS.
   - Alternative Solution (syntactically distinct migration) -> PASS.
   - Negative 1: Only shipping modified, callers untouched -> FAIL.
   - Negative 2: One caller migration missing -> FAIL.
   - Negative 3: Compatibility constant deleted or altered to int 5 -> FAIL.
   - Negative 4: Incorrect exception message ("Invalid weight") -> FAIL.
   - Negative 5: Baseline test file deleted -> FAIL.
   - Negative 6: Caller test emptied / neutered -> FAIL.
   - Negative 7: Shipping test emptied / neutered -> FAIL.
   - Negative 8: Caller test replaced with trivial `assertTrue(True)` -> FAIL (detected via SHA-256 hash).
   - Negative 9: Candidate committed changes to workspace -> FAIL.
   - Negative 10: Suite contains skipped tests (`SkipTest`) -> FAIL.
   - Negative 11: Missing sidecar snapshot -> FAIL.
   - Negative 12: Snapshot missing required metadata (`initial_head`, `manifest`) -> FAIL.
2. **R2A Controls (9 tests):**
   - Canonical Solution (returns `[]`) -> PASS (Precision: N/A, Recall: N/A, FP=0).
   - Running `unittest discover` generates `__pycache__` -> PASS.
   - Negative 1: Hallucinated defect on clean code -> FAIL (FP > 0).
   - Negative 2: Uncommitted source code modification -> FAIL.
   - Negative 3: Committed source code modification -> FAIL.
   - Negative 4: Committed edit with deleted snapshot -> FAIL.
   - Negative 5: Invalid JSON array schema -> FAIL.
   - Negative 6: Missing sidecar snapshot -> FAIL.
   - Negative 7: Snapshot missing required metadata (`feature_head`, `manifest`) -> FAIL.
3. **R2B Controls (11 tests):**
   - Canonical Solution (reports correct source and broken caller) -> PASS (TP=1, FP=0).
   - Alternative Solution (accepts equivalent alias symbols/files) -> PASS.
   - Running `unittest discover` generates `__pycache__` -> PASS.
   - Negative 1: Returns `[]` (missed defect) -> FAIL (FN=1).
   - Negative 2: Reports incorrect unrelated caller -> FAIL (TP=0, FP=1).
   - Negative 3: Reports correct defect plus hallucinated defect -> FAIL (TP=1, FP=1).
   - Negative 4: Uncommitted source code modification -> FAIL.
   - Negative 5: Committed source code modification -> FAIL.
   - Negative 6: Committed edit with deleted snapshot -> FAIL.
   - Negative 7: Missing sidecar snapshot -> FAIL.
   - Negative 8: Snapshot missing required metadata (`feature_head`, `manifest`) -> FAIL.

---

## 8. Empirical Results & 27-Run Scorecard (Phase 2 Empirical Results)

All 27 runs ($3 \text{ tasks} \times 3 \text{ arms} \times 3 \text{ repetitions}$) were executed and independently audited with the hardened verifier suite at commit `b9443ee`.

### 8.1. Granular 27-Run Scorecard (Steps & Timing Breakdown)

| Run | Task | Arm | Rep | Arm Configuration | Result | Steps | Transcript Time | Verifier Duration | Evidence Notes |
|:---:|:---:|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---|
| 01 | D2 | A0 | 1 | Control (Baseline Prompt) | **PASS** | 66 | 158.0s | 0.548s | Caller test hashes & public surface intact |
| 02 | D2 | A1 | 1 | Karpathy Guidelines | **PASS** | 72 | 150.0s | 0.550s | Caller test hashes & public surface intact |
| 03 | D2 | A2 | 1 | Treatment (2 Skills) | **PASS** | 90 | 184.0s* | 0.533s | Caller test hashes & public surface intact |
| 04 | R2A | A0 | 1 | Control (Baseline Prompt) | **PASS** | 40 | 47.0s | 0.159s | `[]` (FP = 0, Read-only clean) |
| 05 | R2A | A1 | 1 | Karpathy Guidelines | **PASS** | 48 | 68.0s | 0.160s | `[]` (FP = 0, Read-only clean) |
| 06 | R2A | A2 | 1 | Treatment (2 Skills) | **PASS** | 48 | 67.0s | 0.159s | `[]` (FP = 0, Read-only clean) |
| 07 | R2B | A0 | 1 | Control (Baseline Prompt) | **PASS** | 36 | 53.0s | 0.158s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 08 | R2B | A1 | 1 | Karpathy Guidelines | **PASS** | 44 | 54.0s | 0.172s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 09 | R2B | A2 | 1 | Treatment (2 Skills) | **PASS** | 48 | 120.0s | 0.171s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 10 | D2 | A1 | 2 | Karpathy Guidelines | **PASS** | 60 | 119.0s | 0.545s | Caller test hashes & public surface intact |
| 11 | D2 | A2 | 2 | Treatment (2 Skills) | **PASS** | 76 | 164.0s | 0.533s | Caller test hashes & public surface intact |
| 12 | D2 | A0 | 2 | Control (Baseline Prompt) | **PASS** | 68 | 133.0s | 0.549s | Caller test hashes & public surface intact |
| 13 | R2A | A1 | 2 | Karpathy Guidelines | **PASS** | 46 | 63.0s | 0.155s | `[]` (FP = 0, Read-only clean) |
| 14 | R2A | A2 | 2 | Treatment (2 Skills) | **PASS** | 58 | 75.0s | 0.162s | `[]` (FP = 0, Read-only clean) |
| 15 | R2A | A0 | 2 | Control (Baseline Prompt) | **PASS** | 58 | 72.0s | 0.151s | `[]` (FP = 0, Read-only clean) |
| 16 | R2B | A1 | 2 | Karpathy Guidelines | **PASS** | 44 | 90.0s | 0.154s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 17 | R2B | A2 | 2 | Treatment (2 Skills) | **PASS** | 32 | 62.0s | 0.151s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 18 | R2B | A0 | 2 | Control (Baseline Prompt) | **PASS** | 30 | 38.0s | 0.151s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 19 | D2 | A2 | 3 | Treatment (2 Skills) | **PASS** | 94 | 182.0s* | 0.548s | Caller test hashes & public surface intact |
| 20 | D2 | A0 | 3 | Control (Baseline Prompt) | **PASS** | 65 | 160.0s | 0.553s | Caller test hashes & public surface intact |
| 21 | D2 | A1 | 3 | Karpathy Guidelines | **PASS** | 75 | 152.0s | 0.542s | Caller test hashes & public surface intact |
| 22 | R2A | A2 | 3 | Treatment (2 Skills) | **PASS** | 50 | 106.0s | 0.171s | `[]` (FP = 0, Read-only clean) |
23: | 23 | R2A | A0 | 3 | Control (Baseline Prompt) | **PASS** | 36 | 73.0s | 0.154s | `[]` (FP = 0, Read-only clean) |
24: | 24 | R2A | A1 | 3 | Karpathy Guidelines | **PASS** | 56 | 134.0s | 0.150s | `[]` (FP = 0, Read-only clean) |
25: | 25 | R2B | A2 | 3 | Treatment (2 Skills) | **PASS** | 42 | 73.0s | 0.166s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
26: | 26 | R2B | A0 | 3 | Control (Baseline Prompt) | **PASS** | 40 | 58.0s | 0.159s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
27: | 27 | R2B | A1 | 3 | Karpathy Guidelines | **PASS** | 40 | 59.0s | 0.157s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |

*\*Note: Runs 03 (184s) and 19 (182s) slightly exceeded the nominal 180s threshold in transcript elapsed time. No host abort signal occurred; independent verifiers validated that workspace solutions were fully correct and preserved the PASS outcome.*

---

### 8.2. Scorecard Summary

| Arm | Description | D2 (Contract Migration) | R2A (Clean Review) | R2B (Defect Review) | Overall | Pass Rate |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **A0** | Control (Baseline Prompt) | 3/3 PASS | 3/3 PASS | 3/3 PASS | **9/9** | **100%** |
| **A1** | Karpathy Guidelines | 3/3 PASS | 3/3 PASS | 3/3 PASS | **9/9** | **100%** |
| **A2** | Treatment (2 Skills) | 3/3 PASS | 3/3 PASS | 3/3 PASS | **9/9** | **100%** |

---

### 8.3. Decoupled Review Metrics (Precision, Recall & Specificity)

| Arm Group | R2A (FP) | R2B (TP) | R2B (FN) | Precision ($TP / (TP+FP)$) | Recall ($TP / (TP+FN)$) | Specificity |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **A0 (Control)** | 0 / 3 | 3 / 3 | 0 / 3 | **100.0%** | **100.0%** | **100.0%** |
| **A1 (Guidelines)** | 0 / 3 | 3 / 3 | 0 / 3 | **100.0%** | **100.0%** | **100.0%** |
| **A2 (Treatment)** | 0 / 3 | 3 / 3 | 0 / 3 | **100.0%** | **100.0%** | **100.0%** |

---

### 8.4. Descriptive Observations on Execution & Transcript Data

While verifier pass rates reached 100% across all arms, descriptive statistics extracted from transcripts and workspaces reveal observable variations:

1. **Transcript Record Count (JSONL Lines):**
   - Counts all JSONL lines in transcript logs (user input, planner response, tool calls, tool outputs, system messages).
   - **Task D2:** A0 averaged 66.3 records; A1 averaged 69.0 records; A2 averaged 86.7 records.
   - **Review Tasks (R2A & R2B):** A0 averaged 40.0 records; A1 averaged 46.3 records; A2 averaged 46.3 records.
   - **All 9 runs combined:** A0 averaged **48.8 records/run**; A1 averaged **53.9 records/run**; A2 averaged **59.8 records/run** (+22.5% vs A0).
2. **Transcript Elapsed Duration (Seconds):**
   - Measured from timestamp of first transcript entry to final transcript entry.
   - **Task D2:** A0 averaged 150.3s; A1 averaged 140.3s; A2 averaged 176.7s.
   - **All 9 runs combined:** A0 averaged **88.0s/run**; A1 averaged **98.8s/run**; A2 averaged **114.8s/run** (+30.4% vs A0).
3. **Saved Patch File Line Count (on Task D2):**
   - Line count of `candidate_diff.patch` (including git headers and diff context lines; created test files stored separately). This metric does not differentiate additions/deletions and does not reflect solution economy or quality.
   - **A1 (Guidelines):** Averaged 252.0 lines.
   - **A2 (Skills):** Averaged 272.7 lines.
   - **A0 (Control):** Averaged 302.0 lines.

---

### 8.5. Inter-Run Variance Assessment

- **Verification Invariance:** Across all 3 repetitions (Rep 1, Rep 2, Rep 3) for all 3 tasks, pass/fail outcomes were strictly invariant ($27/27$ PASS). Zero flakiness was observed in meeting verifier criteria.
- **Behavioral Variance:** Measurable variance occurred across runs in elapsed duration (38s to 184s), transcript record count (30 to 94 records), and patch line counts (247 to 343 lines on D2). Because arms in each triplet executed concurrently, variations may reflect host resource sharing or temporary host infrastructure fluctuations.

---

### 8.6. Scientific Findings & Empirical Conclusions

> **Official Conclusion:** Across the three Phase 2 fixtures, each evaluated three times per arm, all submissions passed independent verifiers. No difference in pass rate was observed between control, guidelines, and treatment. The experiment established no measurable benefits in cost, latency, or solution quality beyond the evaluated criteria.

1. **Foundation Model Capabilities at Evaluated Scale:**
   - When objectives and compatibility boundaries are fully stated in the prompt, the baseline foundation model (Arm A0) possesses sufficient intrinsic reasoning to satisfy contracts, preserve dependent callers, and accurately report review defects without needing supplementary guidelines or skills.
   - Comparing with Phase 1: the earlier D3 failure was driven by strict string matching against declared Test ID formats; in Phase 2 with AST semantic verification and SHA-256 baseline caller test hash protection, all three groups passed cleanly.
2. **Interpretation of Descriptive Metrics:**
   - In these 27 runs, A2 averaged ~22.5% more transcript entries and ~30.4% longer elapsed time than A0. These are descriptive metrics; the experiment did not directly record token counts, monetary cost, or host compute utilization, and could not isolate concurrent execution effects. All three arms achieved 9/9 verifier pass rates.
   - The same evidential standard applies bidirectionally: this evaluation neither proved an added benefit of the two skills over control/guidelines, nor did it prove that skills are intrinsically wasteful in a general sense.
3. **Evidence Packaging & Post-Session Re-verification Records:**
   - All 240 evidence files across 27 runs are packaged under `pilots/phase2-contract-and-review/evidence/` with an SHA-256 `MANIFEST.json`, locked with `-text -eol` in `.gitattributes`.
   - `verifier_execution_record.json` and `eval_result.json` represent **independent post-session re-verification records** (executed via `manager.py verify`), recording exact verifier commands, exit codes (`exit_code: 0`), duration, and stdout. Timestamps reflect post-session re-verification, not candidate subagent runtime timestamps.
