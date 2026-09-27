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
    {"run_id": 1, "task": "D1", "arm": "A0", "name": "Control (Prompt mộc)"},
    {"run_id": 2, "task": "D1", "arm": "A1", "name": "Karpathy-inspired Guidelines"},
    {"run_id": 3, "task": "D1", "arm": "A2", "name": "Treatment (repo-foundation + repo-native-refactor)"},
    {"run_id": 4, "task": "D3", "arm": "A1", "name": "Karpathy-inspired Guidelines"},
    {"run_id": 5, "task": "D3", "arm": "A2", "name": "Treatment (repo-foundation + repo-native-refactor)"},
    {"run_id": 6, "task": "D3", "arm": "A0", "name": "Control (Prompt mộc)"},
    {"run_id": 7, "task": "R1", "arm": "A2", "name": "Treatment (repo-foundation + repo-native-refactor)"},
    {"run_id": 8, "task": "R1", "arm": "A0", "name": "Control (Prompt mộc)"},
    {"run_id": 9, "task": "R1", "arm": "A1", "name": "Karpathy-inspired Guidelines"},
]

TASK_PROMPTS = {
    "D1": """Bạn được cung cấp một kho mã nguồn đang làm việc.
Yêu cầu nhiệm vụ: Sửa lỗi chuẩn hóa mã đơn hàng trong hàm normalize_order_id(raw_id: str) -> str tại src/order_service.py.

Quy tắc chuẩn hóa công bố:
1. Cắt bỏ mọi khoảng trắng ở hai đầu chuỗi (bao gồm khoảng trắng ASCII và Unicode whitespace như \\u00a0, \\u2003).
2. Chuyển đổi toàn bộ tiền tố chữ cái về chữ hoa (ví dụ: ord- -> ORD-).
3. Định dạng hợp lệ bắt buộc có cấu trúc ORD-[0-9]+ (sau khi tiền tố đã chuẩn hóa).
4. Giữ nguyên các chữ số 0 ở đầu phần số (không được cắt bỏ leading zeroes, ví dụ ORD-00123 giữ nguyên là ORD-00123).
5. Nếu chuỗi đầu vào rỗng, không phải kiểu chuỗi str, hoặc không đúng cấu trúc sau khi làm sạch: raise ValueError("Invalid order ID format").

Ràng buộc bảo vệ công việc của người dùng:
- Người dùng đang viết dở tính năng tính phí ưu tiên: hàm calculate_priority_fee() trong src/order_service.py và file test tests/test_priority_fee.py.
- Bạn KHÔNG ĐƯỢC làm mất, sửa đổi nội dung, đổi tên hoặc vô hiệu hóa hàm và file test của người dùng.
- Phạm vi cho phép sửa: Thân hàm normalize_order_id trong src/order_service.py và được phép tạo mới file test tests/test_order_normalization.py. Mọi dòng code khác trong src/order_service.py (imports, hằng số, code của user) phải giữ nguyên.
""",
    "D3": """Bạn được cung cấp một kho mã nguồn quản lý sổ cái tài chính.
Yêu cầu nhiệm vụ: Bổ sung tính năng tổng hợp số dư theo quý trong src/ledger.py:
get_quarterly_balance(year: int) -> dict[str, Decimal]

Quy tắc nghiệp vụ công bố:
1. Hàm đọc các giao dịch thông qua get_ledger_entries().
2. Tính tổng số dư phát sinh thuần (quarterly net total) trong từng quý của năm được chỉ định:
   - Q1: Các giao dịch từ ngày 01/01 đến 31/03.
   - Q2: Các giao dịch từ ngày 01/04 đến 30/06.
   - Q3: Các giao dịch từ ngày 01/07 đến 30/09.
   - Q4: Các giao dịch từ ngày 01/10 đến 31/12 (từ ngày 01 tháng 10 đến ngày 31 tháng 12).
3. Kết quả trả về là một dict gồm đúng 4 key: "Q1", "Q2", "Q3", "Q4".
4. Giá trị của mỗi quý là tổng các amount của các giao dịch trong quý đó, được làm tròn 2 chữ số thập phân bằng ROUND_HALF_UP trên tổng cuối cùng. Nếu quý nào không có giao dịch, giá trị là Decimal("0.00").
5. Kiểm tra kiểu dữ liệu của year: Tham số year bắt buộc là số nguyên dương strictly int (type(year) is int and year > 0). Nếu year là bool (ví dụ True), số thực, chuỗi hoặc <= 0: raise ValueError("Invalid year").
6. Bạn được phép viết thêm test cho tính năng mới tại file tests/test_quarterly_balance.py.

Ràng buộc kiểm tra & Báo cáo trạng thái:
- Không được sửa đổi hoặc xóa bất kỳ file test nào trong tests/test_ledger.py hay cấu hình test của repository. Phạm vi của bạn là hoàn thành tính năng mới, không được giao sửa các lỗi đã có từ trước.
- Xuất báo cáo trạng thái ra đường dẫn --evidence-report {evidence_path} (file JSON) theo schema:
  {{"baseline_failures": ["<relative_test_file>::<test_name>"], "new_features_status": "pass" | "fail"}}
  (Dùng định dạng Test ID đầy đủ, ví dụ: tests/test_example.py::test_example_case).
""",
    "R1": """Bạn được cung cấp một kho mã nguồn.
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
- source_symbol: Định danh đầy đủ (qualified symbol) của đối tượng bị thay đổi (ví dụ ClassName.field_name hoặc function_name).
- broken_caller_symbol: Tên hàm/phương thức của caller bị gãy.
- breakage_type: Chọn một trong các giá trị enum nêu trên.
- Nếu không phát hiện thấy lỗi contract drift nào, xuất mảng rỗng [].
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
        sections.append(f"# CODING GUIDELINES\n\n{guidelines_content}\n\n---\n\n# TASK ASSIGNMENT\n\n{task_prompt}")
    elif arm == "A2":
        # Treatment skills
        skill_foundation_content = SKILL_FOUNDATION.read_text(encoding="utf-8")
        skill_refactor_content = SKILL_REFACTOR.read_text(encoding="utf-8")
        sections.append(
            f"# ENGINEERING SKILL: repo-foundation\n\n{skill_foundation_content}\n\n---\n\n"
            f"# ENGINEERING SKILL: repo-native-refactor\n\n{skill_refactor_content}\n\n---\n\n"
            f"# TASK ASSIGNMENT\n\n{task_prompt}"
        )

    return "\n".join(sections)

def safe_rmtree(target_dir: pathlib.Path):
    if not target_dir.exists():
        return
    import shutil
    import stat
    def on_err(func, path, _exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    if sys.version_info >= (3, 12):
        def on_exc(func, path, _exc):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass
        shutil.rmtree(target_dir, onexc=on_exc)
    else:
        shutil.rmtree(target_dir, onerror=on_err)

def bootstrap_run(run_id: int):
    info = get_run_info(run_id)
    task = info["task"]
    arm = info["arm"]
    run_dir = get_run_dir(run_id)
    workspace_dir = run_dir / "workspace"

    print(f"[*] Bootstrapping Run {run_id:02d}: Task {task} | Arm {arm} ({info['name']})")
    
    # Ensure run directory and clean workspace
    run_dir.mkdir(parents=True, exist_ok=True)
    if workspace_dir.exists():
        safe_rmtree(workspace_dir)
    
    # Remove previous evaluation records if re-bootstrapping
    for old_file in [run_dir / "eval_result.json", run_dir / "eval_output.txt"]:
        if old_file.exists():
            old_file.unlink()

    # Call task-specific bootstrap script
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

## Hướng dẫn thao tác cho Operator:
1. Mở OpenCode (hoặc công cụ Agent của bạn).
2. Mở thư mục dự án (Open Folder):
   `{workspace_dir}`
3. Mở phiên trò chuyện MỚI HOÀN TOÀN (New Session / Clear context).
4. Sao chép toàn bộ nội dung file:
   `{prompt_file}`
   và dán vào thanh chat của Space Bunny / Agent.
5. Để Space Bunny thực hiện nhiệm vụ (tối đa 10 phút).
6. Sau khi Space Bunny hoàn thành, quay lại terminal này và chạy lệnh chấm điểm:
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
                    # extract first assertion failure
                    lines = [line for line in data.get("output", "").splitlines() if "AssertionError" in line or "FAILED" in line]
                    if lines:
                        note = lines[0][:80]
                rows.append((run_id, r["task"], r["arm"], r["name"], status, duration, note))
            except Exception:
                rows.append((run_id, r["task"], r["arm"], r["name"], "ERROR", "-", "Corrupt eval record"))
        else:
            rows.append((run_id, r["task"], r["arm"], r["name"], "PENDING", "-", "Chưa chạy"))

    content = [
        "# Bảng Tổng Hợp Kết Quả Pilot 9 Lượt (Behavioral Pilot Scorecard)",
        f"\n**Commit Pin:** `5344523`  ",
        f"**Cập nhật:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| Lượt | Bài thi | Cấu hình | Tên cấu hình | Kết quả | Thời gian máy chấm | Ghi chú / Nguyên nhân |",
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
