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

Bạn được cung cấp một kho mã nguồn quản lý sổ cái tài chính.
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
- Xuất báo cáo trạng thái ra đường dẫn --evidence-report C:/Users/Natch/Desktop/SKILLS-MAIN/runs/run_04_D3_A1/status_report.json (file JSON) theo schema:
  {"baseline_failures": ["<relative_test_file>::<test_name>"], "new_features_status": "pass" | "fail"}
  (Dùng định dạng Test ID đầy đủ, ví dụ: tests/test_example.py::test_example_case).
