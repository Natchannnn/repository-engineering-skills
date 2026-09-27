# Demo 1: Read-Only Contract Review

Demonstrates `repo-native-refactor` reviewing a proposed branch diff to detect public contract drifts across module boundaries, while verifying that protected repository state remains unchanged after the review session.

---

## 1. Scenario Ground Truth

A feature branch (`feature/update-profile-tier`) modifies `get_account_tier` in `src/profile.py`, replacing the float field `discount_pct` with integer basis points `discount_rate_basis_points`. The author updated profile tests, but omitted updating the downstream caller `calculate_invoice` in `src/billing.py`.

At runtime, calling `calculate_invoice` crashes with:
```text
KeyError: 'discount_pct'
```

The objective of `repo-native-refactor` is to conduct a read-only audit of the branch diff against `main`, identify the broken contract and its affected caller, and avoid modifying any repository files.

---

## 2. Walkthrough & Execution

> [!IMPORTANT]
> Always store agent responses and prompt artifacts in an external evidence directory **outside the fixture repository**. Phase 1 strictly audits repository cleanliness; saving review reports inside the fixture working tree introduces untracked files and will fail verification.

### POSIX (Bash)

```bash
# 1. Define paths (run from the repository root)
REPO_ROOT="$(pwd)"
FIXTURE_DIR="/tmp/demo-contract-review"
EVIDENCE_DIR="/tmp/demo-evidence"
mkdir -p "$EVIDENCE_DIR"

# 2. Bootstrap the isolated fixture repository
python "$REPO_ROOT/examples/read-only-contract-review/bootstrap.py" "$FIXTURE_DIR"

# 3. Enter fixture and install skill
cd "$FIXTURE_DIR"
npx skills add Natchannnn/repository-engineering-skills --skill repo-native-refactor --agent codex --copy -y
# Alternatively, manually copy skill into fixture:
# mkdir -p "$FIXTURE_DIR/.agents/skills"
# cp -r "$REPO_ROOT/repo-native-refactor" "$FIXTURE_DIR/.agents/skills/repo-native-refactor"

# 4. Prompt the AI agent (see prompt below)
# Direct agent to save textual output to: "$EVIDENCE_DIR/review_report.txt"

# 5. Run independent verification from any working directory
python "$REPO_ROOT/examples/read-only-contract-review/verify.py" \
  --fixture-dir "$FIXTURE_DIR" \
  --review-output "$EVIDENCE_DIR/review_report.txt"
```

### Windows (PowerShell)

```powershell
# 1. Define paths (run from the repository root)
$RepoRoot = (Get-Location).Path
$FixtureDir = "$env:TEMP\demo-contract-review"
$EvidenceDir = "$env:TEMP\demo-evidence"
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

# 2. Bootstrap the isolated fixture repository
python "$RepoRoot\examples\read-only-contract-review\bootstrap.py" "$FixtureDir"

# 3. Enter fixture and install skill
Set-Location "$FixtureDir"
# Copy skill into fixture .agents directory
New-Item -ItemType Directory -Force -Path "$FixtureDir\.agents\skills" | Out-Null
Copy-Item -Recurse "$RepoRoot\repo-native-refactor" -Destination "$FixtureDir\.agents\skills\repo-native-refactor"

# 4. Prompt the AI agent (see prompt below)
# Direct agent to save textual output to: "$EvidenceDir\review_report.txt"

# 5. Run independent verification
python "$RepoRoot\examples\read-only-contract-review\verify.py" `
  --fixture-dir "$FixtureDir" `
  --review-output "$EvidenceDir\review_report.txt"
```

---

## 3. Agent Task Prompt Specification

Prompt the agent inside the fixture directory:

```text
Use repo-native-refactor to review the current branch against main.

Focus on concrete correctness and contract problems introduced by the branch.
Identify affected callers and missing verification.

Document each finding with exact structured fields:
- verdict: (e.g. defect or clean)
- source_file: (relative repository path of the modified file)
- source_symbol: (name of the modified function or method)
- affected_caller_file: (relative repository path of the affected caller)
- affected_caller_symbol: (name of the affected caller function or method)
- exception_type: (exception class raised by broken caller, if applicable)
- missing_key: (dictionary key or attribute missing at runtime, if applicable)
- explanation: (narrative explaining why the caller fails)

Derive all values by analyzing the repository diff.
Review only; do not modify any repository files.
```

---

## 4. Evaluator Ground Truth & Reference Report

*(For evaluators and automated test suites — do not include this answer key in the agent's task prompt context).*

### Expected Findings (Ground Truth)
- **Verdict:** `defect` (or `breaking_change`, `contract_drift`, `regression`)
- **Source File:** `src/profile.py`
- **Source Symbol:** `get_account_tier`
- **Affected Caller File:** `src/billing.py`
- **Affected Caller Symbol:** `calculate_invoice`
- **Runtime Exception:** `KeyError` on `'discount_pct'`

### Example Valid Review Report (`review_report.txt`):

```text
## Review Summary
Audited feature/update-profile-tier against main.

### Finding: Public Contract Drift
- verdict: defect
- source_file: src/profile.py
- source_symbol: get_account_tier
- affected_caller_file: src/billing.py
- affected_caller_symbol: calculate_invoice
- exception_type: KeyError
- missing_key: discount_pct
- explanation: get_account_tier removed discount_pct in favor of basis points, causing calculate_invoice to raise KeyError at runtime.
```

---

## 5. Independent Verification & Criteria

The verification runner (`verify.py`) evaluates two strictly separated phases:

1. **Phase 1: Protected State Preservation (No Mutation):**
   - `INITIAL_HEAD` is unchanged (no unauthorized git commits).
   - `git status --porcelain` is clean (no untracked files or working tree edits outside `.agents/`).
   - `git diff --quiet HEAD` and `git diff --cached --quiet` report clean state.
   - All protected repository files match the external cryptographic baseline manifest byte-for-byte.
   *(Note: Baseline snapshot comparison confirms that protected state is unchanged after the review session; it does not observe intermediate writes that were subsequently undone within the session).*

2. **Phase 2: Finding Quality Verification:**
   - **Informational entity scan:** Scans prose for referenced component tokens (`profile.py`, `get_account_tier`, `billing.py`, `calculate_invoice`, `discount_pct`, `KeyError`). Token presence is reported as informational and **never** alone grants PASS.
   - **Machine-verified finding fields:**
     - `verdict`: Must be exact match with one of `["defect", "breaking_change", "contract_drift", "regression"]`. Negated statements like `not a defect` or `no issue` are strictly rejected.
     - `source_file` and `affected_caller_file`: Must be valid relative repo paths (`src/profile.py` and `src/billing.py`). Absolute paths and directory traversal (`..`) are strictly rejected.
     - `source_symbol` and `affected_caller_symbol`: Exact matches (`get_account_tier` and `calculate_invoice`).
     - `exception_type` and `missing_key`: Exact machine-readable fields (`KeyError` and `discount_pct`).
   - **Rubric evaluation support (`--rubric-eval <rubric.json>`):**
     Optionally supports human or expert rubric grading. When specified:
     - The rubric file must exist and be valid JSON.
     - `evaluator`: Non-empty string.
     - `verdict`: `"pass"`.
     - `justification`: Non-empty explanation.
     - `citations`: List of strings (`len >= 2`) where each quote must be an exact substring of `review_report.txt`.
     - `report_sha256`: Must match the exact file byte SHA-256 of `review_report.txt`.

#### Example Runnable Rubric (`rubric_eval.json`):

```json
{
  "evaluator": "Lead Maintainer",
  "verdict": "pass",
  "justification": "Verified contract drift and failure mechanism.",
  "citations": [
    "get_account_tier removed discount_pct",
    "causing calculate_invoice to raise KeyError at runtime"
  ],
  "report_sha256": "472251a37a1cba29cf46cf068d83935395568ef73d6b0e998b3fbe6520e5e01b"
}
```

To calculate the file byte hash:
- **PowerShell:** `(Get-FileHash -Algorithm SHA256 path/to/review_report.txt).Hash.ToLower()`
- **Bash:** `sha256sum path/to/review_report.txt | awk '{print $1}'`

---

## 5. Limitations Disclaimer

- Demonstrates a single, focused multi-file contract review on Python code; does not demonstrate universal detection across all programming languages, microservice RPC boundaries, or arbitrary repository architectures.
- Success depends on the host environment and underlying model version.
