"""Phase 2 Pilot Manager: Automation and verification CLI for the 27-run cohort.

Tasks:
- D2: Contract Migration & Multi-Caller Preservation
- R2A: Neutral Review Fixture A (Clean / Backward-compatible)
- R2B: Neutral Review Fixture B (Defect / Contract drift)

Arms:
- A0: Control (Bare Prompt)
- A1: Karpathy Guidelines
- A2: Treatment (repo-foundation + repo-native-refactor)

Cohort: 3 tasks x 3 arms x 3 independent repetitions = 27 runs.
"""

from __future__ import annotations

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

PHASE2_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = PHASE2_ROOT.parent.parent
RUNS_DIR = REPO_ROOT / "runs_phase2"

GUIDELINES_FILE = PHASE2_ROOT.parent / "small-behavioral-pilot" / "guidelines" / "karpathy_guidelines.md"
SKILL_FOUNDATION = REPO_ROOT / "repo-foundation" / "SKILL.md"
SKILL_REFACTOR = REPO_ROOT / "repo-native-refactor" / "SKILL.md"

# Rotate arm order across repetitions to balance positional bias:
# Repetition 1: A0 -> A1 -> A2
# Repetition 2: A1 -> A2 -> A0
# Repetition 3: A2 -> A0 -> A1
ARM_ROTATION = {
    1: ["A0", "A1", "A2"],
    2: ["A1", "A2", "A0"],
    3: ["A2", "A0", "A1"],
}
TASK_SEQUENCE = ["D2", "R2A", "R2B"]

RUN_MATRIX = []
run_idx = 1
for rep in [1, 2, 3]:
    arm_order = ARM_ROTATION[rep]
    for task in TASK_SEQUENCE:
        for arm in arm_order:
            arm_names = {
                "A0": "Control (Baseline Prompt)",
                "A1": "Karpathy Guidelines",
                "A2": "Treatment (2 Skills)",
            }
            RUN_MATRIX.append({
                "run_id": run_idx,
                "repetition": rep,
                "task": task,
                "arm": arm,
                "name": f"{arm_names[arm]} (Rep {rep})",
            })
            run_idx += 1

TASK_PROMPTS = {
    "D2": """You are provided with an e-commerce shipping and orders service codebase.
Task requirement: Upgrade the shipping fee calculation function `calculate_shipping(weight_kg: Decimal, destination: str, express: bool = False) -> ShippingQuote` in `src/shipping.py`.

Declared business rules:
1. Declare dataclass `ShippingQuote` in `src/shipping.py` with 3 attributes of type `Decimal`: `base_fee`, `express_fee`, `total_fee`.
2. Parameter `weight_kg` must strictly be of type `Decimal` and `> 0` (reject bool, float, str, or <= 0). If invalid: raise `ValueError("Invalid weight")`.
3. Parameter `destination` must belong to the list returned by `get_supported_destinations()`. If unsupported: raise `ValueError("Unsupported destination")`.
4. Parameter `express` must be of type `bool` (default `False`). If `True`: `express_fee = Decimal("12.50")`. If `False`: `express_fee = Decimal("0.00")`. If express is not a bool: raise `ValueError` or `TypeError`.
5. `base_fee = (weight_kg * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
   - DOMESTIC: `rate = Decimal("5.00")`
   - INTERNATIONAL: `rate = Decimal("15.00")`
   - EXPRESS_ZONE: `rate = Decimal("25.00")`
6. `total_fee = base_fee + express_fee`.
7. Return `ShippingQuote(base_fee=base_fee, express_fee=express_fee, total_fee=total_fee)`.

Compatibility & Migration constraints:
- Utility function `get_supported_destinations() -> list[str]` and constant `DEFAULT_RATE_PER_KG = Decimal("5.00")` in `src/shipping.py` are public APIs consumed by external systems; their names, types, and signatures MUST be strictly preserved.
- Function `calculate_shipping` is used internally across multiple modules in the repository. You MUST inspect and migrate all internal callers across the repository to the new contract so the entire system operates consistently and the entire test suite passes.
- Preserve all existing test files, except `tests/test_shipping.py` which may be updated for the new contract. Authoring new test files in `tests/` is permitted.
""",
    "R2A": """You are provided with a codebase repository.
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
- source_symbol: Fully qualified identifier of the modified object (e.g. ClassName.method_name or function_name).
- broken_caller_symbol: Name of the caller function/method that broke.
- breakage_type: Choose one of the enum values listed above.
- If no contract drift defect is found, output an empty array [].
""",
    "R2B": """You are provided with a codebase repository.
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
- source_symbol: Fully qualified identifier of the modified object (e.g. ClassName.method_name or function_name).
- broken_caller_symbol: Name of the caller function/method that broke.
- breakage_type: Choose one of the enum values listed above.
- If no contract drift defect is found, output an empty array [].
""",
}


def get_run_info(run_id: int) -> dict:
    for r in RUN_MATRIX:
        if r["run_id"] == run_id:
            return r
    raise ValueError(f"Unknown run_id: {run_id}")


def get_run_dir(run_id: int) -> pathlib.Path:
    r = get_run_info(run_id)
    folder_name = f"run_{run_id:02d}_{r['task']}_{r['arm']}_rep{r['repetition']}"
    return RUNS_DIR / folder_name


def build_prompt(run_id: int) -> str:
    r = get_run_info(run_id)
    task = r["task"]
    arm = r["arm"]
    run_dir = get_run_dir(run_id)
    workspace_dir = run_dir / "workspace"
    evidence_file = run_dir / "evidence.json"

    base_task_text = TASK_PROMPTS[task].format(
        evidence_path=str(evidence_file).replace("\\", "/")
    )

    ws_str = str(workspace_dir).replace('\\', '/')
    ev_str = str(evidence_file).replace('\\', '/')

    if task in ("R2A", "R2B"):
        header = (
            f"Workspace directory for this task: {ws_str}\n\n"
            "You must perform all code views and git commands within this workspace directory.\n"
            "Do not modify or commit any files within the workspace repository.\n"
            f"The ONLY permitted file output is the review report specified by --evidence-file: {ev_str}\n"
            "Do not access evaluator harnesses, snapshots, or data from other runs.\n\n"
        )
    else:
        header = (
            f"Workspace directory for this task: {ws_str}\n\n"
            "You must perform all file views, edits, and terminal commands strictly within this workspace directory.\n"
            "Do not access evaluator harnesses, snapshots, or data from other runs.\n\n"
        )

    if arm == "A0":
        return header + base_task_text

    if arm == "A1":
        guidelines = GUIDELINES_FILE.read_text(encoding="utf-8")
        return (
            header
            + "# CODING GUIDELINES\n\n"
            + guidelines
            + "\n\n---\n\n# TASK ASSIGNMENT\n\n"
            + base_task_text
        )

    if arm == "A2":
        f_skill = SKILL_FOUNDATION.read_text(encoding="utf-8")
        r_skill = SKILL_REFACTOR.read_text(encoding="utf-8")
        return (
            header
            + "# ENGINEERING SKILL: repo-foundation\n\n"
            + f_skill
            + "\n\n---\n\n# ENGINEERING SKILL: repo-native-refactor\n\n"
            + r_skill
            + "\n\n---\n\n# TASK ASSIGNMENT\n\n"
            + base_task_text
        )

    raise ValueError(f"Unknown arm: {arm}")


def setup_workspace(run_id: int) -> pathlib.Path:
    r = get_run_info(run_id)
    task = r["task"]
    run_dir = get_run_dir(run_id)
    workspace_dir = run_dir / "workspace"

    if workspace_dir.exists():
        import shutil
        shutil.rmtree(workspace_dir)

    run_dir.mkdir(parents=True, exist_ok=True)

    task_subdirs = {
        "D2": "D2-contract-migration",
        "R2A": "R2A-neutral-review",
        "R2B": "R2B-neutral-review",
    }
    bootstrap_script = PHASE2_ROOT / task_subdirs[task] / "bootstrap.py"

    subprocess.run(
        [sys.executable, str(bootstrap_script), "--target-dir", str(workspace_dir)],
        check=True,
    )

    # Save prompt file for auditing
    prompt_file = run_dir / "prompt.md"
    prompt_file.write_text(build_prompt(run_id), encoding="utf-8")

    return workspace_dir


def verify_run(run_id: int) -> dict:
    r = get_run_info(run_id)
    task = r["task"]
    run_dir = get_run_dir(run_id)
    workspace_dir = run_dir / "workspace"
    evidence_file = run_dir / "evidence.json"

    task_subdirs = {
        "D2": "D2-contract-migration",
        "R2A": "R2A-neutral-review",
        "R2B": "R2B-neutral-review",
    }
    verify_script = PHASE2_ROOT / task_subdirs[task] / "verify.py"

    cmd = [sys.executable, str(verify_script), "--fixture-dir", str(workspace_dir)]
    if task in ("R2A", "R2B"):
        cmd.extend(["--evidence-file", str(evidence_file)])

    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - t0

    result = "PASS" if res.returncode == 0 else "FAIL"

    output_log = run_dir / "verifier_output.log"
    output_log.write_text(f"STDOUT:\n{res.stdout}\n\nSTDERR:\n{res.stderr}", encoding="utf-8")

    exec_record = {
        "run_id": run_id,
        "task": task,
        "arm": r["arm"],
        "repetition": r["repetition"],
        "name": r["name"],
        "command": cmd,
        "exit_code": res.returncode,
        "status": result,
        "duration_sec": round(duration, 3),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stdout": res.stdout,
        "stderr": res.stderr,
    }
    record_file = run_dir / "verifier_execution_record.json"
    record_file.write_text(json.dumps(exec_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "run_id": run_id,
        "task": task,
        "arm": r["arm"],
        "name": r["name"],
        "result": result,
        "duration_sec": round(duration, 3),
        "returncode": res.returncode,
        "stdout": res.stdout,
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 2 Pilot Manager")
    parser.add_argument("action", choices=["setup", "prompt", "verify", "status"], help="Action to perform")
    parser.add_argument("--run-id", type=int, help="Specific run ID (1-27)")
    args = parser.parse_args()

    if args.action == "prompt":
        if args.run_id:
            print(build_prompt(args.run_id))
        else:
            print("Please specify --run-id (1-27) for prompt generation.")

    elif args.action == "setup":
        targets = [args.run_id] if args.run_id else [r["run_id"] for r in RUN_MATRIX]
        for rid in targets:
            print(f"Setting up Run {rid:02d}...")
            ws = setup_workspace(rid)
            print(f"  Initialized at: {ws}")

    elif args.action == "verify":
        targets = [args.run_id] if args.run_id else [r["run_id"] for r in RUN_MATRIX]
        for rid in targets:
            print(f"Verifying Run {rid:02d}...")
            res = verify_run(rid)
            print(f"  Result: {res['result']} ({res['duration_sec']}s)")

    elif args.action == "status":
        print("| Run | Task | Arm | Rep | Name |")
        print("|---|---|---|---|---|")
        for r in RUN_MATRIX:
            print(f"| {r['run_id']:02d} | {r['task']} | {r['arm']} | {r['repetition']} | {r['name']} |")


if __name__ == "__main__":
    main()
