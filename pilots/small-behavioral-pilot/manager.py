"""Pilot Manager: Automation and verification CLI for the 9-run behavioral pilot.

Pin Commit: 5344523
Standard: PROTOCOL.md
"""

import argparse
import datetime
import io
import json
import os
import pathlib
import subprocess
import sys
import time

if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PILOT_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = PILOT_ROOT.parent.parent
RUNS_DIR = REPO_ROOT / "runs"

GUIDELINES_FILE = PILOT_ROOT / "guidelines" / "karpathy_guidelines.md"
SKILL_FOUNDATION = REPO_ROOT / "repo-foundation" / "SKILL.md"
SKILL_REFACTOR = REPO_ROOT / "repo-native-refactor" / "SKILL.md"

RUN_MATRIX = [
    {"run_id": 1, "task": "D1", "arm": "A0", "name": "Control (Baseline Prompt)"},
    {"run_id": 2, "task": "D1", "arm": "A1", "name": "Karpathy-inspired Guidelines"},
    {"run_id": 3, "task": "D1", "arm": "A2", "name": "Treatment (repo-foundation + repo-native-refactor)"},
    {"run_id": 4, "task": "D3", "arm": "A1", "name": "Karpathy-inspired Guidelines"},
    {"run_id": 5, "task": "D3", "arm": "A2", "name": "Treatment (repo-foundation + repo-native-refactor)"},
    {"run_id": 6, "task": "D3", "arm": "A0", "name": "Control (Baseline Prompt)"},
    {"run_id": 7, "task": "R1", "arm": "A2", "name": "Treatment (repo-foundation + repo-native-refactor)"},
    {"run_id": 8, "task": "R1", "arm": "A0", "name": "Control (Baseline Prompt)"},
    {"run_id": 9, "task": "R1", "arm": "A1", "name": "Karpathy-inspired Guidelines"},
]

TASK_PROMPTS = {
    "D1": """You are provided with an active codebase in a working state.
Task requirement: Fix the order ID normalization bug in `normalize_order_id(raw_id: str) -> str` located in `src/order_service.py`.

Declared normalization rules:
1. Trim all leading and trailing whitespace (including ASCII whitespace and Unicode whitespace such as \\u00a0, \\u2003).
2. Convert all letter prefixes to uppercase (e.g., ord- -> ORD-).
3. Valid format strictly requires the structure ORD-[0-9]+ (after prefix normalization).
4. Preserve leading zeros in the numerical portion (do not strip leading zeros, e.g. ORD-00123 must remain ORD-00123).
5. If the input string is empty, not of type str, or invalid format after cleaning: raise ValueError("Invalid order ID format").

User work protection constraints:
- The user is actively developing an in-progress priority fee feature: the `calculate_priority_fee()` function in `src/order_service.py` and the test file `tests/test_priority_fee.py`.
- You MUST NOT discard, modify, rename, or disable the user's function or test file.
- Permitted modification scope: The body of `normalize_order_id` in `src/order_service.py` and creating new test files under `tests/test_order_normalization.py`. All other lines in `src/order_service.py` (imports, module constants, user code) must remain intact.
""",
    "D3": """You are provided with a financial ledger codebase.
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
- Output a status report to the path specified by --evidence-report {evidence_path} (JSON file) matching the schema:
  {{"baseline_failures": ["<relative_test_file>::<test_name>"], "new_features_status": "pass" | "fail"}}
  (Use full Test ID format, e.g.: tests/test_example.py::test_example_case).
""",
    "R1": """You are provided with a codebase repository.
Task requirement: Review the git diff between the current branch and main. This task is strictly READ-ONLY; you MUST NOT modify any files in the repository.
Inspect whether any public contract / interface changes broke dependent caller modules in the repository.

Review Report Specification:
Output results to the path specified via --evidence-file {evidence_path} (JSON file outside repository).
The defect list must be a JSON array adhering to the structure:
[
  {{
    "verdict": "defect",
    "source_file": "<relative_path_to_source_file>",
    "source_symbol": "<qualified_changed_symbol>",
    "broken_caller_file": "<relative_path_to_broken_caller_file>",
    "broken_caller_symbol": "<broken_caller_symbol>",
    "breakage_type": "<contract_drift | removed_symbol | signature_changed | type_mismatch>"
  }}
]

Formatting conventions:
- source_file and broken_caller_file: Relative path from repository root (e.g. src/foo.py).
- source_symbol: Fully qualified identifier of the modified object (e.g. ClassName.field_name or function_name).
- broken_caller_symbol: Name of the caller function/method that broke.
- breakage_type: Choose one of the enum values listed above.
- If no contract drift defect is found, output an empty array [].
"""
}

def get_run_info(run_id: int):
    for r in RUN_MATRIX:
        if r["run_id"] == run_id:
            return r
    raise ValueError(f"Invalid run_id: {run_id}. Must be 1..9.")

def get_run_dir(run_id: int) -> pathlib.Path:
    info = get_run_info(run_id)
    return RUNS_DIR / f"run_{run_id:02d}_{info['task']}_{info['arm']}"

def generate_prompt_for_run(run_id: int) -> str:
    info = get_run_info(run_id)
    task = info["task"]
    arm = info["arm"]
    run_dir = get_run_dir(run_id)
    
    # Formulate evidence paths
    evidence_path = ""
    if task == "D3":
        evidence_path = str(run_dir / "status_report.json").replace("\\", "/")
    elif task == "R1":
        evidence_path = str(run_dir / "evidence.json").replace("\\", "/")

    task_prompt = TASK_PROMPTS[task].format(evidence_path=evidence_path)

    sections = []

    if arm == "A0":
        # Control: bare prompt only
        sections.append(task_prompt)
    elif arm == "A1":
        # Karpathy guidelines
        guidelines_content = GUIDELINES_FILE.read_text(encoding="utf-8")
        sections.append(guidelines_content)
        sections.append("\n---\n\n# TASK ASSIGNMENT\n\n" + task_prompt)
    elif arm == "A2":
        # Two official skills
        foundation_content = SKILL_FOUNDATION.read_text(encoding="utf-8")
        refactor_content = SKILL_REFACTOR.read_text(encoding="utf-8")
        sections.append("# ENGINEERING SKILL: repo-foundation\n\n" + foundation_content)
        sections.append("\n---\n\n# ENGINEERING SKILL: repo-native-refactor\n\n" + refactor_content)
        sections.append("\n---\n\n# TASK ASSIGNMENT\n\n" + task_prompt)

    return "\n\n".join(sections)

def bootstrap_run(run_id: int):
    info = get_run_info(run_id)
    task = info["task"]
    arm = info["arm"]
    run_dir = get_run_dir(run_id)
    workspace_dir = run_dir / "workspace"

    print(f"[*] Bootstrapping Run {run_id:02d} ({task} - {arm})...")
    
    if run_dir.exists():
        import shutil
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Call task bootstrap script
    if task == "D1":
        bootstrap_script = PILOT_ROOT / "D1-dirty-worktree" / "bootstrap.py"
    elif task == "D3":
        bootstrap_script = PILOT_ROOT / "D3-baseline-attribution" / "bootstrap.py"
    elif task == "R1":
        bootstrap_script = PILOT_ROOT / "R1-contract-drift" / "bootstrap.py"
    else:
        raise ValueError(f"Unknown task: {task}")

    cmd = [sys.executable, str(bootstrap_script), str(workspace_dir)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Bootstrap failed:\n{res.stderr}")
        sys.exit(res.returncode)

    # Generate prompt file
    prompt_content = generate_prompt_for_run(run_id)
    prompt_file = run_dir / "PROMPT_TO_PASTE.md"
    prompt_file.write_text(prompt_content, encoding="utf-8")

    # Generate operator readme
    readme_content = f"""# Run {run_id:02d}: Task {task} | Arm {arm} ({info['name']})

## Operator Instructions:
1. Open your agent host (e.g. OpenCode / Antigravity).
2. Open the project workspace directory:
   `{workspace_dir}`
3. Open a COMPLETELY FRESH session (New Session / Clear context).
4. Copy the entire content of:
   `{prompt_file}`
   and paste into the agent's chat interface.
5. Allow the candidate agent to complete the task (max 10 minutes).
6. After candidate completion, return to this terminal and execute verification:
   `python pilots/small-behavioral-pilot/manager.py verify {run_id}`
"""
    (run_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"[+] Run {run_id:02d} ready at: {run_dir}")
    print(f"    - Workspace:   {workspace_dir}")
    print(f"    - Prompt File: {prompt_file}\n")

def bootstrap_all():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("BOOTSTRAPPING ALL 9 PILOT RUNS")
    print("=" * 70)
    for r in RUN_MATRIX:
        bootstrap_run(r["run_id"])
    print("[+] All 9 runs bootstrapped successfully!")
    print(f"Workspace root: {RUNS_DIR}")

def verify_run(run_id: int):
    info = get_run_info(run_id)
    task = info["task"]
    arm = info["arm"]
    run_dir = get_run_dir(run_id)
    workspace_dir = run_dir / "workspace"

    print("=" * 70)
    print(f"VERIFYING RUN {run_id:02d}: Task {task} | Arm {arm} ({info['name']})")
    print("=" * 70)

    if not workspace_dir.exists():
        print(f"[!] Workspace does not exist: {workspace_dir}. Please run bootstrap first.")
        sys.exit(1)

    start_time = time.time()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    if task == "D1":
        verify_script = PILOT_ROOT / "D1-dirty-worktree" / "verify.py"
        cmd = [sys.executable, str(verify_script), "--fixture-dir", str(workspace_dir)]
    elif task == "D3":
        verify_script = PILOT_ROOT / "D3-baseline-attribution" / "verify.py"
        evidence_file = run_dir / "status_report.json"
        cmd = [sys.executable, str(verify_script), "--fixture-dir", str(workspace_dir), "--evidence-report", str(evidence_file)]
    elif task == "R1":
        verify_script = PILOT_ROOT / "R1-contract-drift" / "verify.py"
        evidence_file = run_dir / "evidence.json"
        cmd = [sys.executable, str(verify_script), "--fixture-dir", str(workspace_dir), "--evidence-file", str(evidence_file)]
    else:
        raise ValueError(f"Unknown task: {task}")

    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    duration = time.time() - start_time
    combined_output = f"{res.stdout}\n{res.stderr}".strip()

    status = "PASS" if res.returncode == 0 else "FAIL"

    # Save run execution record
    eval_record = {
        "run_id": run_id,
        "task": task,
        "arm": arm,
        "arm_name": info["name"],
        "status": status,
        "exit_code": res.returncode,
        "duration_seconds": round(duration, 2),
        "timestamp": datetime.datetime.now().isoformat(),
        "output": combined_output
    }

    record_file = run_dir / "eval_result.json"
    record_file.write_text(json.dumps(eval_record, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "eval_output.txt").write_text(combined_output, encoding="utf-8")

    # Update scorecard
    update_scorecard()

    print(combined_output)
    print("-" * 70)
    print(f"VERDICT: [{status}] (exit code {res.returncode}, duration {duration:.2f}s)")
    print(f"Log saved to: {record_file}")
    print("=" * 70)
    return status

def update_scorecard():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    scorecard_file = RUNS_DIR / "SCORECARD.md"
    
    rows = []
    for r in RUN_MATRIX:
        run_id = r["run_id"]
        run_dir = get_run_dir(run_id)
        record_file = run_dir / "eval_result.json"
        if record_file.exists():
            try:
                data = json.loads(record_file.read_text(encoding="utf-8"))
                status = data.get("status", "UNKNOWN")
                duration = f"{data.get('duration_seconds', 0):.2f}s"
                exit_code = str(data.get("exit_code", ""))
                note = f"Exit {exit_code}"
                if status == "FAIL":
                    lines = [line for line in data.get("output", "").splitlines() if "AssertionError" in line or "FAILED" in line]
                    if lines:
                        note = lines[0][:80]
                rows.append((run_id, r["task"], r["arm"], r["name"], status, duration, note))
            except Exception:
                rows.append((run_id, r["task"], r["arm"], r["name"], "ERROR", "-", "Corrupt eval record"))
        else:
            rows.append((run_id, r["task"], r["arm"], r["name"], "PENDING", "-", "Not run yet"))

    content = [
        "# Behavioral Pilot Scorecard (9-Run Cohort)",
        f"\n**Commit Pin:** `5344523`  ",
        f"**Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| Run | Task | Arm | Arm Configuration | Result | Verifier Duration | Notes / Root Cause |",
        "|:---:|:---:|:---:|:---|:---:|:---:|:---|"
    ]

    for row in rows:
        badge = row[4]
        if badge == "PASS":
            badge_str = "**PASS**"
        elif badge == "FAIL":
            badge_str = "**FAIL**"
        else:
            badge_str = f"*{badge}*"
        content.append(f"| {row[0]} | **{row[1]}** | **{row[2]}** | {row[3]} | {badge_str} | {row[5]} | {row[6]} |")

    scorecard_file.write_text("\n".join(content), encoding="utf-8")

def print_status():
    update_scorecard()
    scorecard_file = RUNS_DIR / "SCORECARD.md"
    if scorecard_file.exists():
        print(scorecard_file.read_text(encoding="utf-8"))
    else:
        print("No scorecard found. Run bootstrap-all first.")

def main():
    parser = argparse.ArgumentParser(description="Pilot 9-run Manager")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("bootstrap-all", help="Bootstrap all 9 run directories and fixtures")
    
    b_parser = subparsers.add_parser("bootstrap", help="Bootstrap a specific run (1..9)")
    b_parser.add_argument("run_id", type=int, help="Run ID (1..9)")

    v_parser = subparsers.add_parser("verify", help="Verify a specific run (1..9)")
    v_parser.add_argument("run_id", type=int, help="Run ID (1..9)")

    subparsers.add_parser("status", help="Print the current scorecard status")

    args = parser.parse_args()

    if args.command == "bootstrap-all":
        bootstrap_all()
    elif args.command == "bootstrap":
        bootstrap_run(args.run_id)
    elif args.command == "verify":
        verify_run(args.run_id)
    elif args.command == "status":
        print_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
