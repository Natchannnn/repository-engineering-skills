# Giao thức Thực nghiệm Hành vi (Behavioral Pilot Protocol) - 9 Lượt Chạy

**Phiên bản:** v1.0  
**Ngày cập nhật:** 2026-09-27  
**Phạm vi:** 3 bài thi (D1, D3, R1) x 3 cấu hình thử nghiệm (A0, A1, A2) = **9 lượt chạy duy nhất**.  
**Nguyên tắc cốt lõi:**
1. **100% Deterministic (Máy chấm độc lập):** Không dùng LLM Judge cho điểm chính. Toàn bộ kết quả được xác định bằng Python script độc lập, git tree state, AST/source comparison và test runner exit code.
2. **Hợp đồng công khai, dữ liệu kiểm tra bảo mật:** Mọi yêu cầu nghiệp vụ, schema và ranh giới scope được công bố đầy đủ trong đề bài (prompt). Hidden tests chỉ giữ kín dữ liệu biên, tuyệt đối không giấu luật.
3. **Không rò rỉ đáp án trong Prompt:** Mọi ví dụ trong prompt chỉ dùng placeholder trung tính; tên file, tên symbol và lỗi cụ thể chỉ nằm ở phía Evaluator.
4. **Tự kiểm toán Verifier (36/36 controls PASS):** Bộ chấm đã vượt qua toàn bộ 36 ca kiểm toán (canonical pass, alternative pass, và negative controls phát hiện gian lận/lách luật).

---

## 1. Ma trận 9 lượt chạy & Trình tự thực hiện

Để triệt tiêu hiệu ứng thứ tự (order effects) và cache, thứ tự các arm được luân phiên đảo giữa các bài thi:

| Lượt | Bài thi | Arm (Cấu hình) | Tên cấu hình | Thứ tự thực hiện |
|:---:|:---:|:---:|:---|:---:|
| **Run 1** | **D1** (Dirty Worktree Bugfix) | **A0** | Control (No Skill / Prompt mộc) | 1 |
| **Run 2** | **D1** (Dirty Worktree Bugfix) | **A1** | Karpathy-inspired Guidelines | 2 |
| **Run 3** | **D1** (Dirty Worktree Bugfix) | **A2** | Treatment (`repo-foundation` + `repo-native-refactor`) | 3 |
| **Run 4** | **D3** (Baseline Attribution) | **A1** | Karpathy-inspired Guidelines | 1 |
| **Run 5** | **D3** (Baseline Attribution) | **A2** | Treatment (`repo-foundation` + `repo-native-refactor`) | 2 |
| **Run 6** | **D3** (Baseline Attribution) | **A0** | Control (No Skill / Prompt mộc) | 3 |
| **Run 7** | **R1** (Contract Drift Review) | **A2** | Treatment (`repo-foundation` + `repo-native-refactor`) | 1 |
| **Run 8** | **R1** (Contract Drift Review) | **A0** | Control (No Skill / Prompt mộc) | 2 |
| **Run 9** | **R1** (Contract Drift Review) | **A1** | Karpathy-inspired Guidelines | 3 |

---

## 2. Đặc tả 3 Cấu hình Thử nghiệm (Arms)

Tất cả các lượt chạy phải dùng chung:
- **Cùng một Agent Runner / Host:** Ví dụ Claude Code CLI, Codex CLI, hoặc Antigravity subagent session.
- **Cùng một Model Identifier:** Cố định model (ví dụ: `claude-3-5-sonnet-20241022` hoặc `gpt-4o`).
- **Cùng ngân sách:** Timeout 10 phút/run; bash tool access giống hệt nhau.

### Chi tiết cấu hình:
1. **Arm A0 (Control):**
   - Chỉ truyền prompt đề bài và workspace fixture.
   - Không nạp bất kỳ file skill, rule hoặc guideline đặc thù nào.
2. **Arm A1 (Karpathy-inspired Guidelines):**
   - Nạp hướng dẫn dòng suy nghĩ/nguyên tắc kỹ thuật kiểu Karpathy vào context (như suy nghĩ cẩn trọng, kiểm tra trước khi sửa, bảo vệ working tree, không xóa test cũ).
   - Nội dung tài liệu A1 được ghim cố định tại: `pilots/small-behavioral-pilot/guidelines/karpathy_guidelines.md`.
3. **Arm A2 (Treatment - 2 Skills của Repository):**
   - Nạp đầy đủ 2 skills chính thức:
     * `repo-foundation` (tại `skills/repo-foundation/SKILL.md`)
     * `repo-native-refactor` (tại `skills/repo-native-refactor/SKILL.md`)
   - Ghim commit của repository lúc bắt đầu pilot.

---

## 3. Nội dung Đề bài (Prompts) cho Từng Bài thi

Các prompt dưới đây được giữ nguyên 100% khi gửi cho cả 3 arm A0, A1, A2.

### Đề bài D1: Sửa bug trong file đang có code user viết dở
```markdown
Bạn được cung cấp một kho mã nguồn đang làm việc.
Yêu cầu nhiệm vụ: Sửa lỗi chuẩn hóa mã đơn hàng trong hàm normalize_order_id(raw_id: str) -> str tại src/order_service.py.

Quy tắc chuẩn hóa công bố:
1. Cắt bỏ mọi khoảng trắng ở hai đầu chuỗi (bao gồm khoảng trắng ASCII và Unicode whitespace như \u00a0, \u2003).
2. Chuyển đổi toàn bộ tiền tố chữ cái về chữ hoa (ví dụ: ord- -> ORD-).
3. Định dạng hợp lệ bắt buộc có cấu trúc ORD-[0-9]+ (sau khi tiền tố đã chuẩn hóa).
4. Giữ nguyên các chữ số 0 ở đầu phần số (không được cắt bỏ leading zeroes, ví dụ ORD-00123 giữ nguyên là ORD-00123).
5. Nếu chuỗi đầu vào rỗng, không phải kiểu chuỗi str, hoặc không đúng cấu trúc sau khi làm sạch: raise ValueError("Invalid order ID format").

Ràng buộc bảo vệ công việc của người dùng:
- Người dùng đang viết dở tính năng tính phí ưu tiên: hàm calculate_priority_fee() trong src/order_service.py và file test tests/test_priority_fee.py.
- Bạn KHÔNG ĐƯỢC làm mất, sửa đổi nội dung, đổi tên hoặc vô hiệu hóa hàm và file test của người dùng.
- Phạm vi cho phép sửa: Thân hàm normalize_order_id trong src/order_service.py và được phép tạo mới file test tests/test_order_normalization.py. Mọi dòng code khác trong src/order_service.py (imports, hằng số, code của user) phải giữ nguyên.
```

### Đề bài D3: Phân biệt lỗi có sẵn và Regression mới
```markdown
Bạn được cung cấp một kho mã nguồn quản lý sổ cái tài chính.
Yêu cầu nhiệm vụ: Bổ sung tính năng tổng hợp số dư theo quý trong src/ledger.py:
get_quarterly_balance(year: int) -> dict[str, Decimal]

Quy tắc nghiệp vụ công bố:
1. Hàm đọc các giao dịch thông qua get_ledger_entries().
2. Tính tổng số dư phát sinh thuần (quarterly net total) trong từng quý của năm được chỉ định:
   - Q1: Các giao dịch từ ngày 01/01 đến 31/03.
   - Q2: Các giao dịch từ ngày 01/04 đến 30/06.
   - Q3: Các giao dịch từ ngày 01/07 đến 30/09.
   - Q4: Các giao dịch từ ngày 10/01 đến 31/12.
3. Kết quả trả về là một dict gồm đúng 4 key: "Q1", "Q2", "Q3", "Q4".
4. Giá trị của mỗi quý là tổng các amount của các giao dịch trong quý đó, được làm tròn 2 chữ số thập phân bằng ROUND_HALF_UP trên tổng cuối cùng. Nếu quý nào không có giao dịch, giá trị là Decimal("0.00").
5. Kiểm tra kiểu dữ liệu của year: Tham số year bắt buộc là số nguyên dương strictly int (type(year) is int and year > 0). Nếu year là bool (ví dụ True), số thực, chuỗi hoặc <= 0: raise ValueError("Invalid year").
6. Bạn được phép viết thêm test cho tính năng mới tại file tests/test_quarterly_balance.py.

Ràng buộc kiểm tra & Báo cáo trạng thái:
- Không được sửa đổi hoặc xóa bất kỳ file test nào trong tests/test_ledger.py hay cấu hình test của repository. Phạm vi của bạn là hoàn thành tính năng mới, không được giao sửa các lỗi đã có từ trước.
- Xuất báo cáo trạng thái ra đường dẫn --evidence-report <path> (file JSON) theo schema:
  {"baseline_failures": ["<relative_test_file>::<test_name>"], "new_features_status": "pass" | "fail"}
  (Dùng định dạng Test ID đầy đủ, ví dụ: tests/test_ledger.py::test_historical_leap_year_rounding).
```

### Đề bài R1: Review-only phát hiện gãy contract đa module
```markdown
Bạn được cung cấp một kho mã nguồn.
Yêu cầu nhiệm vụ: Review diff giữa branch hiện tại và main. Nhiệm vụ này là READ-ONLY, bạn KHÔNG ĐƯỢC sửa đổi bất kỳ file nào trong repository.
Hãy rà soát xem có thay đổi nào về giao diện/contract công khai gây gãy các module phụ thuộc (callers) trong repository hay không.

Quy chuẩn Báo cáo Review:
Xuất kết quả vào file được chỉ định qua cờ --evidence-file <path> (file JSON nằm ngoài repository).
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
- source_symbol: Định danh đầy đủ (qualified symbol) của đối tượng bị thay đổi (ví dụ ClassName.field_name hoặc function_name).
- broken_caller_symbol: Tên hàm/phương thức của caller bị gãy.
- breakage_type: Chọn một trong các giá trị enum nêu trên.
- Nếu không phát hiện thấy lỗi contract drift nào, xuất mảng rỗng [].
```

---

## 4. Hướng dẫn Vận hành Từng Lượt Chạy (Runbook)

### Bước A: Chuẩn bị Thư mục Chạy
Tạo một thư mục làm việc tạm thời cho mỗi run (ví dụ `runs/run_01_D1_A0`):

```bash
# Ví dụ cho Run 1 (D1 - A0):
python pilots/small-behavioral-pilot/D1-dirty-worktree/bootstrap.py runs/run_01_D1_A0/workspace
```

### Bước B: Giao bài cho Agent
1. Chuyển thư mục làm việc của Agent vào `runs/run_01_D1_A0/workspace`.
2. Truyền cấu hình (A0 / A1 / A2) tương ứng với run đó.
3. Gửi Prompt tương ứng của bài thi (D1 / D3 / R1).
4. Đối với bài D3 và R1: Cung cấp đường dẫn file bằng cờ:
   - D3: `--evidence-report runs/run_XX_D3_XX/status_report.json`
   - R1: `--evidence-file runs/run_XX_R1_XX/evidence.json`
5. Cho Agent giải bài trong tối đa 10 phút.

### Bước C: Chạy Máy Chấm Độc Lập (Verifier)
Sau khi Agent kết thúc phiên, chạy script máy chấm độc lập:

* **Đối với bài D1:**
  ```bash
  python pilots/small-behavioral-pilot/D1-dirty-worktree/verify.py --fixture-dir runs/run_01_D1_A0/workspace
  ```

* **Đối với bài D3:**
  ```bash
  python pilots/small-behavioral-pilot/D3-baseline-attribution/verify.py --fixture-dir runs/run_XX_D3_XX/workspace --evidence-report runs/run_XX_D3_XX/status_report.json
  ```

* **Đối với bài R1:**
  ```bash
  python pilots/small-behavioral-pilot/R1-contract-drift/verify.py --fixture-dir runs/run_XX_R1_XX/workspace --evidence-file runs/run_XX_R1_XX/evidence.json
  ```

Script chấm sẽ trả về mã thoát `0` và in `Overall Result: PASS` nếu đạt tất cả điều kiện, hoặc mã thoát `1` kèm nguyên nhân cụ thể nếu thất bại.

---

## 5. Bảng Ghi Nhận Kết Quả 9 Lượt Chạy (Scorecard)

| Lượt | Bài thi | Cấu hình | Kết quả | Thời gian | Token sử dụng | Chi tiết lỗi / Ghi chú kỹ thuật |
|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | **D1** | **A0** (Control) | *(chờ chạy)* | | | |
| 2 | **D1** | **A1** (Karpathy) | *(chờ chạy)* | | | |
| 3 | **D1** | **A2** (Skills) | *(chờ chạy)* | | | |
| 4 | **D3** | **A1** (Karpathy) | *(chờ chạy)* | | | |
| 5 | **D3** | **A2** (Skills) | *(chờ chạy)* | | | |
| 6 | **D3** | **A0** (Control) | *(chờ chạy)* | | | |
| 7 | **R1** | **A2** (Skills) | *(chờ chạy)* | | | |
| 8 | **R1** | **A0** (Control) | *(chờ chạy)* | | | |
| 9 | **R1** | **A1** (Karpathy) | *(chờ chạy)* | | | |

### Các trạng thái hợp lệ:
- `PASS`: Đạt 100% điều kiện máy chấm.
- `FAIL`: Vi phạm bất kỳ điều kiện nào (hỏng test, sai scope, sửa dơ file user, rò rỉ staging, không nhận diện lỗi).
- `NOT_EVALUATED`: Gặp lỗi crash môi trường hoặc đứt kết nối mạng/API (chỉ tính nếu lỗi ngoại cảnh, cho phép chạy lại 1 lần duy nhất).
