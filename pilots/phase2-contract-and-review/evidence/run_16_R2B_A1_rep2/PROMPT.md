Workspace directory for this task: <REPO_ROOT>/runs_phase2/run_16_R2B_A1_rep2/workspace

You must perform all code views and git commands within this workspace directory.
Do not modify or commit any files within the workspace repository.
The ONLY permitted file output is the review report specified by --evidence-file: <REPO_ROOT>/runs_phase2/run_16_R2B_A1_rep2/evidence.json
Do not access evaluator harnesses, snapshots, or data from other runs.

# CODING GUIDELINES

# Engineering Principles & Operational Guidelines (Karpathy-Inspired)

## Core Mindset
1. **Understand Before Editing:** Always read existing source code, imports, and tests before writing any code. Form a mental model of the codebase architecture and contracts.
2. **Minimal & Surgical Diffs:** Solve problems with the minimum necessary changes. Never perform drive-by formatting, unnecessary refactorings, or modifications outside the explicit task scope.
3. **Respect Existing Work:**
   - Never tamper with, overwrite, or delete uncommitted user work or user test files.
   - Do not modify or suppress existing repository tests to turn a red build green.
   - If an existing test fails, analyze whether it was already failing at baseline or caused by your changes.
4. **Strict Scope Discipline:** If a task is read-only review, do not touch or stage any files in the workspace. If a task authorizes editing specific functions, confine changes exclusively to those functions.
5. **Rigorous Verification:** Run tests before submitting. Ensure code handles edge cases, type constraints, boundary conditions, and respects established function signatures.


---

# TASK ASSIGNMENT

You are provided with a codebase repository.
Task requirement: Review the git diff between the current branch and main. This task is strictly READ-ONLY; you MUST NOT modify any files in the repository.
Inspect whether any public contract / interface changes broke dependent caller modules in the repository.

Review Report Specification:
Output results to the path specified via --evidence-file <REPO_ROOT>/runs_phase2/run_16_R2B_A1_rep2/evidence.json (JSON file outside repository).
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
- source_symbol: Fully qualified identifier of the modified object (e.g. ClassName.method_name or function_name).
- broken_caller_symbol: Name of the caller function/method that broke.
- breakage_type: Choose one of the enum values listed above.
- If no contract drift defect is found, output an empty array [].
