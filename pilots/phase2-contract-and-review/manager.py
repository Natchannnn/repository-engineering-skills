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

# Generate 27 runs interleaved by repetition
RUN_MATRIX = []
run_idx = 1
for rep in range(1, 4):
    for task in ["D2", "R2A", "R2B"]:
        for arm in ["A0", "A1", "A2"]:
            arm_names = {
                "A0": "Control (Prompt mộc)",
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
    "D2": """Bạn được cung cấp một kho mã nguồn dịch vụ vận chuyển và đơn hàng.
Yêu cầu nhiệm vụ: Nâng cấp hàm tính phí vận chuyển calculate_shipping(weight_kg: Decimal, destination: str, express: bool = False) -> ShippingQuote trong src/shipping.py.

Quy tắc nghiệp vụ công bố:
1. Khai báo dataclass (hoặc class) ShippingQuote tại src/shipping.py với 3 thuộc tính kiểu Decimal: base_fee, express_fee, total_fee.
2. Tham số weight_kg bắt buộc là kiểu Decimal và strictly > 0 (không chấp nhận bool, float, str hoặc <= 0). Nếu sai: raise ValueError("Invalid weight").
3. Tham số destination bắt buộc phải thuộc danh sách được hỗ trợ bởi get_supported_destinations(). Nếu không thuộc danh sách: raise ValueError("Unsupported destination").
4. Tham số express bắt buộc là kiểu bool (mặc định False). Nếu True: express_fee = Decimal("12.50"). Nếu False: express_fee = Decimal("0.00"). Nếu express không phải bool: raise ValueError hoặc TypeError.
5. base_fee = (weight_kg * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).
   - DOMESTIC: rate = Decimal("5.00")
   - INTERNATIONAL: rate = Decimal("15.00")
   - EXPRESS_ZONE: rate = Decimal("25.00")
6. total_fee = base_fee + express_fee.
7. Hàm trả về đối tượng ShippingQuote(base_fee=base_fee, express_fee=express_fee, total_fee=total_fee).

Ràng buộc tương thích & di chuyển (Migration):
- Hàm tiện ích get_supported_destinations() -> list[str] và hằng số DEFAULT_RATE_PER_KG = Decimal("5.00") tại src/shipping.py là API công khai phục vụ hệ thống bên ngoài, BẮT BUỘC giữ nguyên tên, kiểu dữ liệu và chữ ký.
- Hàm calculate_shipping đã được sử dụng nội bộ bởi nhiều module khác nhau trong toàn bộ repository. Bạn CẦN TỰ RÀ SOÁT và di chuyển (migrate) tất cả các caller nội bộ trong repository sang hợp đồng mới để toàn bộ hệ thống hoạt động đồng bộ và toàn bộ test suite vượt qua.
- Không được xóa bỏ hoặc làm rỗng các bài test hiện có của các caller. Bạn được phép cập nhật các test hiện có hoặc thêm test mới tại tests/ để kiểm thử hợp đồng mới.
""",
    "R2A": """Bạn được cung cấp một kho mã nguồn.
Yêu cầu nhiệm vụ: Review diff giữa branch hiện tại và main. Nhiệm vụ này là READ-ONLY, bạn KHÔNG ĐƯỢC sửa đổi bất kỳ file nào trong repository.
Hãy rà soát xem có thay đổi nào về giao diện/contract công khai gây gãy các module phụ thuộc (callers) trong repository hay không.

Quy chuẩn Báo cáo Review:
Xuất kết quả vào file được chỉ định qua cờ --evidence-file {evidence_path} (file JSON nằm ngoài repository).
Danh sách phát hiện lỗi là một mảng JSON tuân thủ đúng cấu trúc:
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

Quy ước định dạng:
- source_file và broken_caller_file: Đường dẫn tương đối từ gốc repository (ví dụ src/foo.py).
- source_symbol: Định danh đầy đủ của đối tượng bị thay đổi (ví dụ ClassName.method_name hoặc function_name).
- broken_caller_symbol: Tên hàm/phương thức của caller bị gãy.
- breakage_type: Chọn một trong các giá trị enum nêu trên.
- Nếu không phát hiện thấy lỗi contract drift nào, xuất mảng rỗng [].
""",
    "R2B": """Bạn được cung cấp một kho mã nguồn.
Yêu cầu nhiệm vụ: Review diff giữa branch hiện tại và main. Nhiệm vụ này là READ-ONLY, bạn KHÔNG ĐƯỢC sửa đổi bất kỳ file nào trong repository.
Hãy rà soát xem có thay đổi nào về giao diện/contract công khai gây gãy các module phụ thuộc (callers) trong repository hay không.

Quy chuẩn Báo cáo Review:
Xuất kết quả vào file được chỉ định qua cờ --evidence-file {evidence_path} (file JSON nằm ngoài repository).
Danh sách phát hiện lỗi là một mảng JSON tuân thủ đúng cấu trúc:
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

Quy ước định dạng:
- source_file và broken_caller_file: Đường dẫn tương đối từ gốc repository (ví dụ src/foo.py).
- source_symbol: Định danh đầy đủ của đối tượng bị thay đổi (ví dụ ClassName.method_name hoặc function_name).
- broken_caller_symbol: Tên hàm/phương thức của caller bị gãy.
- breakage_type: Chọn một trong các giá trị enum nêu trên.
- Nếu không phát hiện thấy lỗi contract drift nào, xuất mảng rỗng [].
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

    header = f"Workspace directory for this task: {str(workspace_dir).replace('\\', '/')}\n\n"
    header += "You must perform all file views, edits, and terminal commands strictly within this workspace directory.\n\n"

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

    result = "PASS" if res.returncode == 0 and "Overall Result: PASS" in res.stdout else "FAIL"

    output_log = run_dir / "verifier_output.log"
    output_log.write_text(f"STDOUT:\n{res.stdout}\n\nSTDERR:\n{res.stderr}", encoding="utf-8")

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
