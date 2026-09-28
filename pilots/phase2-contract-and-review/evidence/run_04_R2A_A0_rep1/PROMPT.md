Workspace directory for this task: <REPO_ROOT>/runs_phase2/run_04_R2A_A0_rep1/workspace

You must perform all code views and git commands within this workspace directory.
Do not modify or commit any files within the workspace repository.
The ONLY permitted file output is the review report specified by --evidence-file: <REPO_ROOT>/runs_phase2/run_04_R2A_A0_rep1/evidence.json
Do not access evaluator harnesses, snapshots, or data from other runs.

You are provided with a codebase repository.
Task requirement: Review the git diff between the current branch and main. This task is strictly READ-ONLY; you MUST NOT modify any files in the repository.
Inspect whether any public contract / interface changes broke dependent caller modules in the repository.

Review Report Specification:
Output results to the path specified via --evidence-file <REPO_ROOT>/runs_phase2/run_04_R2A_A0_rep1/evidence.json (JSON file outside repository).
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
