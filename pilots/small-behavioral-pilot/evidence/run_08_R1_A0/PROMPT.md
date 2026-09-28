You are provided with a codebase repository.
Task requirement: Review the git diff between the current branch and main. This task is strictly READ-ONLY; you MUST NOT modify any files in the repository.
Inspect whether any public contract / interface changes broke dependent caller modules in the repository.

Review Report Specification:
Output results to the path specified via --evidence-file <REPO_ROOT>/runs/run_08_R1_A0/evidence.json (JSON file outside repository).
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
