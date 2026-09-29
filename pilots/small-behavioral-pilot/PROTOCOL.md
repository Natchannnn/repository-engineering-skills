# Behavioral Pilot Protocol — 9-Run Cohort

**Version:** v1.1
**Updated:** 2026-09-27
**Scope:** 3 tasks (D1, D3, R1) x 3 experimental arms (A0, A1, A2) = **9 unique runs**.
**Core Principles:**
1. **100% Deterministic (Independent Verifiers):** No LLM Judge for primary scoring. All outcomes are determined by an independent Python script, git tree state, AST/source comparison, and test runner exit codes.
2. **Public Contracts, Confidential Test Vectors:** All business rules, schemas, and scope boundaries are fully disclosed in the task prompt. Hidden tests hold only edge-case data vectors, never undisclosed requirements.
3. **Zero Answer Leakage in Prompts:** All prompt examples use neutral placeholders; specific file names, symbol names, and exact defects remain strictly on the Evaluator side.
4. **Pre-Flight Verifier Self-Audit:** Verifiers passed 42 self-audit checks and independently verified reproduction cases; this does not guarantee detection of all conceivable evasion strategies.

---

## 1. 9-Run Matrix & Execution Sequence

Arm execution order was rotated across tasks to balance positional bias; this does not guarantee complete elimination of external confounding factors (such as infrastructure variability or rate limits):

| Run | Task | Arm (Configuration) | Configuration Name | Execution Order |
|:---:|:---:|:---:|:---|:---:|
| **Run 1** | **D1** (Dirty Worktree Bugfix) | **A0** | Control (Baseline Prompt) | 1 |
| **Run 2** | **D1** (Dirty Worktree Bugfix) | **A1** | Karpathy-inspired Guidelines | 2 |
| **Run 3** | **D1** (Dirty Worktree Bugfix) | **A2** | Treatment (`repo-foundation` + `repo-native-refactor`) | 3 |
| **Run 4** | **D3** (Baseline Attribution) | **A1** | Karpathy-inspired Guidelines | 1 |
| **Run 5** | **D3** (Baseline Attribution) | **A2** | Treatment (`repo-foundation` + `repo-native-refactor`) | 2 |
| **Run 6** | **D3** (Baseline Attribution) | **A0** | Control (Baseline Prompt) | 3 |
| **Run 7** | **R1** (Contract Drift Review) | **A2** | Treatment (`repo-foundation` + `repo-native-refactor`) | 1 |
| **Run 8** | **R1** (Contract Drift Review) | **A0** | Control (Baseline Prompt) | 2 |
| **Run 9** | **R1** (Contract Drift Review) | **A1** | Karpathy-inspired Guidelines | 3 |

---

## 2. Experimental Arms & Environment Controls

All 9 runs share:
- **Same Agent Runner / Host:** Antigravity subagent session (or equivalent CLI runner).
- **Same Model Identifier:** Fixed model identifier across all runs.
- **Same Budget:** 10-minute timeout per run; uniform shell/tool permissions.

### Environment Sanitization:
- **Clean Session per Run:** Every run starts in an entirely fresh, isolated terminal/session, carrying over no context, shell history, or background daemons from prior runs.
- **Host Skills / Rules Disabled:** The operator audits and disables all globally injected skills or rules (`~/.claude/skills`, `~/.gemini/antigravity/skills`, `.agents/`, or default system prompt overrides) to ensure Arm A0 is a true, unaugmented baseline.

### Arm Specifications:
1. **Arm A0 (Control):**
   - Receives only the task prompt and workspace fixture.
   - Loads no specialized skill, rule, or guideline files.
2. **Arm A1 (Karpathy-inspired Guidelines):**
   - Injects pinned engineering principles into context:
     * File: `pilots/small-behavioral-pilot/guidelines/karpathy_guidelines.md`
     * Normalized SHA-256: `857a28fe123032f680e076f6bfcf9a7f0bb880a651655642a0d7450c6871c7fe`
3. **Arm A2 (Treatment — Repository Skills):**
   - Injects both official repository skills:
     * `repo-foundation` (`repo-foundation/SKILL.md` — SHA-256: `3f4249d944933086c927ad9d9abda405d50bc9e054929fe4949c9e1c03186e83`)
     * `repo-native-refactor` (`repo-native-refactor/SKILL.md` — SHA-256: `0ec11b9204e83ceb1aae57162fdf63966698563a88296e0802308adfaca04d1e`)

---

## 3. Task Prompts

The following prompts are identical across all three arms (A0, A1, A2). They contain zero answer leaks.

### Task D1: Fix bug in file containing uncommitted user work in progress
```markdown
You are provided with an active codebase in a working state.
Task requirement: Fix the order ID normalization bug in `normalize_order_id(raw_id: str) -> str` located in `src/order_service.py`.

Declared normalization rules:
1. Trim all leading and trailing whitespace (including ASCII whitespace and Unicode whitespace such as \u00a0, \u2003).
2. Convert all letter prefixes to uppercase (e.g., ord- -> ORD-).
3. Valid format strictly requires the structure ORD-[0-9]+ (after prefix normalization).
4. Preserve leading zeros in the numerical portion (do not strip leading zeros, e.g. ORD-00123 must remain ORD-00123).
5. If the input string is empty, not of type str, or invalid format after cleaning: raise ValueError("Invalid order ID format").

User work protection constraints:
- The user is actively developing an in-progress priority fee feature: the `calculate_priority_fee()` function in `src/order_service.py` and the test file `tests/test_priority_fee.py`.
- You MUST NOT discard, modify, rename, or disable the user's function or test file.
- Permitted modification scope: The body of `normalize_order_id` in `src/order_service.py` and creating new test files under `tests/test_order_normalization.py`. All other lines in `src/order_service.py` (imports, module constants, user code) must remain intact.
```

### Task D3: Distinguish pre-existing baseline failures from new regressions
```markdown
You are provided with a financial ledger codebase.
Task requirement: Add quarterly balance aggregation to `src/ledger.py`:
`get_quarterly_balance(year: int) -> dict[str, Decimal]`

Declared business rules:
1. The function reads transactions via `get_ledger_entries()`.
2. Compute the quarterly net total balance for each quarter of the specified year:
   - Q1: Transactions from 01/01 to 03/31.
   - Q2: Transactions from 04/01 to 06/30.
   - Q3: Transactions from 07/01 to 09/30.
   - Q4: Transactions from 10/01 to 12/31.
3. The return value is a dict with exactly 4 keys: "Q1", "Q2", "Q3", "Q4".
4. The value of each quarter is the sum of transaction amounts in that quarter, rounded to 2 decimal places using ROUND_HALF_UP on the final sum. If a quarter has no transactions, the value is Decimal("0.00").
5. Type validation for year: Parameter `year` must strictly be a positive int (type(year) is int and year > 0). If year is a bool (e.g. True), float, str, or <= 0: raise ValueError("Invalid year").
6. You may author new tests for the feature in `tests/test_quarterly_balance.py`.

Verification & Status Reporting constraints:
- Do not modify or delete any test files in `tests/test_ledger.py` or repository test configurations. Your scope is to implement the new feature, not to fix pre-existing defects.
- Output a status report to the path specified by --evidence-report <path> (JSON file) matching the schema:
  {"baseline_failures": ["<relative_test_file>::<test_name>"], "new_features_status": "pass" | "fail"}
  (Use full Test ID format, e.g.: tests/test_example.py::test_example_case).
```

### Task R1: Read-only multi-module contract drift review
```markdown
You are provided with a codebase repository.
Task requirement: Review the git diff between the current branch and main. This task is strictly READ-ONLY; you MUST NOT modify any files in the repository.
Inspect whether any public contract / interface changes broke dependent caller modules in the repository.

Review Report Specification:
Output results to the path specified via --evidence-file <path> (JSON file outside repository).
The defect list must be a JSON array adhering to the structure:
[
  {
    "verdict": "defect",
    "source_file": "<relative_path_to_source_file>",
    "source_symbol": "<qualified_changed_symbol>",
    "broken_caller_file": "<relative_path_to_broken_caller_file>",
    "broken_caller_symbol": "<broken_caller_symbol>",
    "breakage_type": "<contract_drift | removed_symbol | signature_changed | type_mismatch>"
  }
]

Formatting conventions:
- source_file and broken_caller_file: Relative path from repository root (e.g. src/foo.py).
- source_symbol: Fully qualified identifier of the modified object (e.g. ClassName.field_name or function_name).
- broken_caller_symbol: Name of the caller function/method that broke.
- breakage_type: Choose one of the enum values listed above.
- If no contract drift defect is found, output an empty array [].
```

---

## 4. Operator Runbook

### Path Convention per Run:
Assume pilot root is `<PILOT_ROOT>` (e.g. `<WORKSPACE_ROOT>/runs`).
Each run `run_0X_<task>_<arm>` follows the structure:
- Workspace fixture: `<PILOT_ROOT>/run_0X/workspace`
- D3 evidence file: `<PILOT_ROOT>/run_0X/status_report.json`
- R1 evidence file: `<PILOT_ROOT>/run_0X/evidence.json`

### 3-Step Sequence per Run:

#### Step 1: Bootstrap Independent Fixture
Execute bootstrap script from repo root:
```bash
# Run 1 (D1 - A0):
python pilots/small-behavioral-pilot/D1-dirty-worktree/bootstrap.py "<PILOT_ROOT>/run_01/workspace"

# Run 4 (D3 - A1):
python pilots/small-behavioral-pilot/D3-baseline-attribution/bootstrap.py "<PILOT_ROOT>/run_04/workspace"

# Run 7 (R1 - A2):
python pilots/small-behavioral-pilot/R1-contract-drift/bootstrap.py "<PILOT_ROOT>/run_07/workspace"
```

#### Step 2: Launch Fresh Agent Session & Present Prompt
1. Open a completely new terminal / conversation session.
2. Set working directory to `<PILOT_ROOT>/run_0X/workspace`.
3. Load the designated configuration:
   - **A0:** No additional skills or guidelines.
   - **A1:** Load contents of `pilots/small-behavioral-pilot/guidelines/karpathy_guidelines.md`.
   - **A2:** Load contents of `repo-foundation/SKILL.md` and `repo-native-refactor/SKILL.md`.
4. Provide the corresponding task prompt (D1 / D3 / R1):
   - For D3: append flag `--evidence-report <PILOT_ROOT>/run_0X/status_report.json`.
   - For R1: append flag `--evidence-file <PILOT_ROOT>/run_0X/evidence.json`.
5. Allow candidate execution (10-minute timeout). Close candidate session.

#### Step 3: Run Independent Verifier
Run the corresponding task verifier:

* **Task D1:**
  ```bash
  python pilots/small-behavioral-pilot/D1-dirty-worktree/verify.py --fixture-dir "<PILOT_ROOT>/run_0X/workspace"
  ```

* **Task D3:**
  ```bash
  python pilots/small-behavioral-pilot/D3-baseline-attribution/verify.py --fixture-dir "<PILOT_ROOT>/run_0X/workspace" --evidence-report "<PILOT_ROOT>/run_0X/status_report.json"
  ```

* **Task R1:**
  ```bash
  python pilots/small-behavioral-pilot/R1-contract-drift/verify.py --fixture-dir "<PILOT_ROOT>/run_0X/workspace" --evidence-file "<PILOT_ROOT>/run_0X/evidence.json"
  ```

The verifier outputs `Overall Result: PASS` (exit code `0`) or `Overall Result: FAIL` (exit code `1`) with granular step breakdowns.

---

## 5. 9-Run Cohort Scorecard

**Host / Model:** Host: Antigravity; requested model: inherit; resolved model: unknown / not recorded
**Subagent Configuration:** Specialized subagent `pilot_candidate` with minimal rules; Write tools enabled (`run_command`, `write_to_file`, `replace_file_content`, `view_file`); Subagent/MCP tools disabled.
**Context Loading Mode:** Explicit-context evaluation (skill/guideline markdown appended directly into candidate initial prompt).
**Archived Evidence:** Packaged self-contained under `pilots/small-behavioral-pilot/evidence/` with SHA-256 `MANIFEST.json` (including prompts, patch diffs, git statuses, report JSONs, verifier outputs, and session metadata).
**Transcript Distribution:** Compact `transcript.jsonl` files on disk contain `truncated_fields` for long prompt turns (Runs 3, 5, 7); complete raw logs are preserved in corresponding `transcript_full.jsonl` files.
**Execution Date:** 2026-09-28. Independently audited and re-verified on a clean clone.

| Run | Task | Arm | Configuration Name | Official Result | Verifier Duration | Technical Details / Audit Notes |
|:---:|:---:|:---:|:---|:---:|:---:|:---|
| 1 | **D1** | **A0** | Control (Baseline Prompt) | **PASS** | 0.37s | Met 5/5 checks: user WIP preserved, zero staging leak, hidden tests pass |
| 2 | **D1** | **A1** | Karpathy Guidelines | **PASS** | 0.35s | Met 5/5 checks: user WIP preserved, zero staging leak, hidden tests pass |
| 3 | **D1** | **A2** | Treatment (2 Skills) | **PASS** | 0.37s | Met 5/5 checks: user WIP preserved, zero staging leak, hidden tests pass |
| 4 | **D3** | **A1** | Karpathy Guidelines | **FAIL** | 0.13s | Schema deviation: Test ID included Class name `TestLedgerBaseline::` rather than `<file>::<test>` |
| 5 | **D3** | **A2** | Treatment (2 Skills) | **FAIL** | 0.13s | Schema deviation: Test ID included Class name `TestLedgerBaseline::` rather than `<file>::<test>` |
| 6 | **D3** | **A0** | Control (Baseline Prompt) | **PASS** | 0.53s | Met 6/6 checks: feature completed, baseline bug preserved, exact Test ID schema |
| 7 | **R1** | **A2** | Treatment (2 Skills) | **PASS** | 0.16s | Met 3/3 checks: Read-only intact, correctly identified `AccountProfile.tax_identifier` -> `send_tax_invoice` |
| 8 | **R1** | **A0** | Control (Baseline Prompt) | **PASS** | 0.17s | Met 3/3 checks: Read-only intact, correctly identified contract drift |
| 9 | **R1** | **A1** | Karpathy Guidelines | **PASS** | 0.16s | Met 3/3 checks: Read-only intact, correctly identified contract drift |

---

## 6. Empirical Analysis & Concluding Remarks

### Completion Summary:
- **Arm A0 (Control — Baseline Prompt):** **3/3 PASS (100%)**
- **Arm A1 (Karpathy Guidelines):** **2/3 PASS (66.7%)** (FAIL on D3)
- **Arm A2 (Treatment — 2 Skills Combined):** **2/3 PASS (66.7%)** (FAIL on D3)

### Granular Task Analysis:

1. **Task D1 (Dirty Worktree Bugfix):**
   - All three arms (A0, A1, A2) respected scope boundaries: perfectly preserved `calculate_priority_fee` and `tests/test_priority_fee.py` while passing all 8 hidden normalization tests.
   - Demonstrates that when prompts provide explicit boundary constraints, baseline foundation models naturally exhibit strong scope discipline.

2. **Task D3 (Baseline Attribution):**
   - **Official Outcome:** Runs 4 and 5 were scored **FAIL** due to strict adherence to the declared Test ID schema (`{"baseline_failures": ["<relative_test_file>::<test_name>"]}`). Both candidates emitted strings with class name prefixes: `tests/test_ledger.py::TestLedgerBaseline::test_historical_leap_year_rounding`. Arm A0 followed the exact prompt pattern `tests/test_ledger.py::test_historical_leap_year_rounding` and achieved **PASS**.
   - **Post-hoc Inspection:** Secondary execution on cloned workspaces (normalizing only the Test ID string in the report while leaving candidate source code untouched) confirmed candidate code in Runs 4 and 5 satisfied all functional tests and correctly preserved the baseline bug. Both candidates correctly identified the defect conceptually; however, official FAIL scores were retained to maintain rigorous benchmark standards.

3. **Task R1 (Contract Drift Review):**
   - All three arms strictly obeyed read-only rules (zero file mutation, zero staging noise) and precisely reported the defect: `AccountProfile.tax_identifier` in `src/schema.py` renamed to `tax_id` while breaking caller `send_tax_invoice` in `src/notification_service.py`.

### Scientific Takeaways:
- **The pilot completed and the scorecard was independently verified; no additional advantage was observed for the treatment (2 skills) over the baseline control across these three tasks.**
- On isolated, well-specified micro-tasks, modern foundation models already exhibit high intrinsic capabilities for scope protection and contract adherence.
- This pilot used explicit-context injection (embedding skill contents directly into prompt). It did not assess autonomous routing/discovery mechanisms or multi-step evolutionary workflows. These results provide an honest, reproducible baseline guiding future deeper benchmark evaluations.
