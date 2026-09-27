Workspace directory for this task: C:/Users/Natch/Desktop/SKILLS-MAIN/runs_phase2/run_18_R2B_A0_rep2/workspace

You must perform all code views and git commands within this workspace directory.
Do not modify or commit any files within the workspace repository.
The ONLY permitted file output is the review report specified by --evidence-file: C:/Users/Natch/Desktop/SKILLS-MAIN/runs_phase2/run_18_R2B_A0_rep2/evidence.json
Do not access evaluator harnesses, snapshots, or data from other runs.

Bạn được cung cấp một kho mã nguồn.
Yêu cầu nhiệm vụ: Review diff giữa branch hiện tại và main. Nhiệm vụ này là READ-ONLY, bạn KHÔNG ĐƯỢC sửa đổi bất kỳ file nào trong repository.
Hãy rà soát xem có thay đổi nào về giao diện/contract công khai gây gãy các module phụ thuộc (callers) trong repository hay không.

Quy chuẩn Báo cáo Review:
Xuất kết quả vào file được chỉ định qua cờ --evidence-file C:/Users/Natch/Desktop/SKILLS-MAIN/runs_phase2/run_18_R2B_A0_rep2/evidence.json (file JSON nằm ngoài repository).
Danh sách phát hiện lỗi là một mảng JSON tuân thủ đúng cấu trúc:
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

Quy ước định dạng:
- source_file và broken_caller_file: Đường dẫn tương đối từ gốc repository (ví dụ src/foo.py).
- source_symbol: Định danh đầy đủ của đối tượng bị thay đổi (ví dụ ClassName.method_name hoặc function_name).
- broken_caller_symbol: Tên hàm/phương thức của caller bị gãy.
- breakage_type: Chọn một trong các giá trị enum nêu trên.
- Nếu không phát hiện thấy lỗi contract drift nào, xuất mảng rỗng [].
