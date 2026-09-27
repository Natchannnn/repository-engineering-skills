# Giao thức Thực nghiệm Hành vi (Behavioral Pilot Protocol) - 9 Lượt Chạy

**Phiên bản:** v1.1  
**Ngày cập nhật:** 2026-09-27  
**Phạm vi:** 3 bài thi (D1, D3, R1) x 3 cấu hình thử nghiệm (A0, A1, A2) = **9 lượt chạy duy nhất**.  
**Nguyên tắc cốt lõi:**
1. **100% Deterministic (Máy chấm độc lập):** Không dùng LLM Judge cho điểm chính. Toàn bộ kết quả được xác định bằng Python script độc lập, git tree state, AST/source comparison và test runner exit code.
2. **Hợp đồng công khai, dữ liệu kiểm tra bảo mật:** Mọi yêu cầu nghiệp vụ, schema và ranh giới scope được công bố đầy đủ trong đề bài (prompt). Hidden tests chỉ giữ kín dữ liệu biên, tuyệt đối không giấu luật.
3. **Không rò rỉ đáp án trong Prompt:** Mọi ví dụ trong prompt chỉ dùng placeholder trung tính; tên file, tên symbol và lỗi cụ thể chỉ nằm ở phía Evaluator.
4. **Tự kiểm toán Verifier trước khi chạy:** Bộ verifier đã vượt qua 42 ca tự kiểm toán và các ca tái hiện độc lập được kiểm tra; chưa bảo đảm phát hiện mọi cách làm sai hoặc can thiệp vào quá trình chấm.

---

## 1. Ma trận 9 lượt chạy & Trình tự thực hiện

Thứ tự các arm được luân phiên đảo giữa các bài thi để giảm ảnh hưởng của thứ tự thực hiện; việc này không bảo đảm loại bỏ hoàn toàn các yếu tố ngoại cảnh (như biến thiên hạ tầng hoặc rate limit):

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

## 2. Đặc tả 3 Cấu hình Thử nghiệm (Arms) & Kiểm soát Môi trường

Tất cả 9 lượt chạy phải dùng chung:
- **Cùng một Agent Runner / Host:** Ví dụ Claude Code CLI, Codex CLI, hoặc Antigravity subagent session.
- **Cùng một Model Identifier:** Cố định model identifier (ví dụ: `claude-3-5-sonnet-20241022` hoặc `gpt-4o`).
- **Cùng ngân sách:** Timeout 10 phút/run; quyền bash/tool access đồng nhất.

### Quy chuẩn kiểm soát môi trường (Environment Sanitization):
- **Khởi tạo phiên mới (Clean Session):** Mỗi lượt chạy bắt buộc mở một terminal / session mới hoàn toàn độc lập, không mang theo context, shell history hay background daemon từ lượt trước.
- **Vô hiệu hóa Skills / Rules từ Host:** Người vận hành phải kiểm kê và tắt các rule hoặc skill tự động nạp từ thư mục cấu hình toàn cục của user (`~/.claude/skills`, `~/.gemini/antigravity/skills`, `.agents/`, hoặc system prompt mặc định thêm ngoài luồng) để bảo đảm Arm A0 thực sự là control thuần túy.

### Chi tiết 3 Cấu hình:
1. **Arm A0 (Control):**
   - Chỉ truyền prompt đề bài và workspace fixture.
   - Không nạp bất kỳ file skill, rule hoặc guideline đặc thù nào.
2. **Arm A1 (Karpathy-inspired Guidelines):**
   - Nạp nội dung nguyên tắc kỹ thuật ghim cố định:
     * File: `pilots/small-behavioral-pilot/guidelines/karpathy_guidelines.md`
     * Normalized SHA-256: `857a28fe123032f680e076f6bfcf9a7f0bb880a651655642a0d7450c6871c7fe`
3. **Arm A2 (Treatment - 2 Skills của Repository):**
   - Nạp đầy đủ 2 skills chính thức từ gốc repository:
     * `repo-foundation` (tại `repo-foundation/SKILL.md` - SHA-256: `3f4249d944933086c927ad9d9abda405d50bc9e054929fe4949c9e1c03186e83`)
     * `repo-native-refactor` (tại `repo-native-refactor/SKILL.md` - SHA-256: `0ec11b9204e83ceb1aae57162fdf63966698563a88296e0802308adfaca04d1e`)

---

## 3. Nội dung Đề bài (Prompts) cho Từng Bài thi

Các prompt dưới đây được giữ nguyên 100% khi gửi cho cả 3 arm A0, A1, A2. Không chứa bất kỳ rò rỉ đáp án nào.

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
   - Q4: Các giao dịch từ ngày 01/10 đến 31/12 (từ ngày 01 tháng 10 đến ngày 31 tháng 12).
3. Kết quả trả về là một dict gồm đúng 4 key: "Q1", "Q2", "Q3", "Q4".
4. Giá trị của mỗi quý là tổng các amount của các giao dịch trong quý đó, được làm tròn 2 chữ số thập phân bằng ROUND_HALF_UP trên tổng cuối cùng. Nếu quý nào không có giao dịch, giá trị là Decimal("0.00").
5. Kiểm tra kiểu dữ liệu của year: Tham số year bắt buộc là số nguyên dương strictly int (type(year) is int and year > 0). Nếu year là bool (ví dụ True), số thực, chuỗi hoặc <= 0: raise ValueError("Invalid year").
6. Bạn được phép viết thêm test cho tính năng mới tại file tests/test_quarterly_balance.py.

Ràng buộc kiểm tra & Báo cáo trạng thái:
- Không được sửa đổi hoặc xóa bất kỳ file test nào trong tests/test_ledger.py hay cấu hình test của repository. Phạm vi của bạn là hoàn thành tính năng mới, không được giao sửa các lỗi đã có từ trước.
- Xuất báo cáo trạng thái ra đường dẫn --evidence-report <path> (file JSON) theo schema:
  {"baseline_failures": ["<relative_test_file>::<test_name>"], "new_features_status": "pass" | "fail"}
  (Dùng định dạng Test ID đầy đủ, ví dụ: tests/test_example.py::test_example_case).
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

## 4. Hướng dẫn Vận hành Từng Lượt Chạy (Operator Runbook)

### Quy ước đường dẫn tuyệt đối cho mỗi lượt:
Giả định thư mục gốc của pilot là: `<PILOT_ROOT>` (ví dụ: `C:/Users/Natch/Desktop/SKILLS-MAIN/runs`).  
Mỗi run `run_0X_<task>_<arm>` có cấu trúc:
- Thư mục workspace fixture: `<PILOT_ROOT>/run_0X/workspace`
- File bằng chứng D3: `<PILOT_ROOT>/run_0X/status_report.json`
- File bằng chứng R1: `<PILOT_ROOT>/run_0X/evidence.json`

### Trình tự 3 bước cho mỗi lượt chạy:

#### Bước 1: Khởi tạo Fixture độc lập
Chạy lệnh bootstrap từ repo gốc:
```bash
# Ví dụ cho Run 1 (D1 - A0):
python pilots/small-behavioral-pilot/D1-dirty-worktree/bootstrap.py "<PILOT_ROOT>/run_01/workspace"

# Ví dụ cho Run 4 (D3 - A1):
python pilots/small-behavioral-pilot/D3-baseline-attribution/bootstrap.py "<PILOT_ROOT>/run_04/workspace"

# Ví dụ cho Run 7 (R1 - A2):
python pilots/small-behavioral-pilot/R1-contract-drift/bootstrap.py "<PILOT_ROOT>/run_07/workspace"
```

#### Bước 2: Khởi động Agent Session mới & Giao đề
1. Mở cửa sổ terminal / session mới hoàn toàn.
2. Thiết lập working directory vào `<PILOT_ROOT>/run_0X/workspace`.
3. Nạp cấu hình tương ứng:
   - **A0:** Không nạp gì thêm.
   - **A1:** Nạp nội dung `pilots/small-behavioral-pilot/guidelines/karpathy_guidelines.md`.
   - **A2:** Nạp nội dung `repo-foundation/SKILL.md` và `repo-native-refactor/SKILL.md`.
4. Gửi Prompt tương ứng của bài thi (D1 / D3 / R1).
   - Với D3: Thêm cờ `--evidence-report <PILOT_ROOT>/run_0X/status_report.json`.
   - Với R1: Thêm cờ `--evidence-file <PILOT_ROOT>/run_0X/evidence.json`.
5. Đợi agent hoàn tất (tối đa 10 phút). Đóng session agent.

#### Bước 3: Chạy Máy Chấm Độc Lập (Verifier)
Chạy script máy chấm tương ứng với bài thi:

* **Đối với bài D1:**
  ```bash
  python pilots/small-behavioral-pilot/D1-dirty-worktree/verify.py --fixture-dir "<PILOT_ROOT>/run_0X/workspace"
  ```

* **Đối với bài D3:**
  ```bash
  python pilots/small-behavioral-pilot/D3-baseline-attribution/verify.py --fixture-dir "<PILOT_ROOT>/run_0X/workspace" --evidence-report "<PILOT_ROOT>/run_0X/status_report.json"
  ```

* **Đối với bài R1:**
  ```bash
  python pilots/small-behavioral-pilot/R1-contract-drift/verify.py --fixture-dir "<PILOT_ROOT>/run_0X/workspace" --evidence-file "<PILOT_ROOT>/run_0X/evidence.json"
  ```

Script chấm in ra `Overall Result: PASS` (exit code `0`) hoặc `Overall Result: FAIL` (exit code `1`) kèm chi tiết từng hạng mục kiểm tra.

---

## 5. Bảng Ghi Nhận Kết Quả 9 Lượt Chạy (Scorecard)

**Host / Model:** Host: Antigravity; requested model: inherit; resolved model: unknown / not recorded
**Cấu hình Subagent:** Subagent chuyên biệt `pilot_candidate` với 3 quy tắc tối giản; Write tools bật (`run_command`, `write_to_file`, `replace_file_content`, `view_file`); Subagent/MCP tools tắt.  
**Cơ chế nạp Context:** Explicit-context evaluation (ghép nội dung file guideline/skill trực tiếp vào khối tin nhắn đề bài).  
**Bằng chứng lưu trữ:** Đóng gói độc lập trong repository tại `pilots/small-behavioral-pilot/evidence/` kèm `MANIFEST.json` băm SHA-256 (bao gồm prompt, patch diff, git status, report JSON, output verifier, và metadata phiên).  
**Ghi chú về Transcript:** Các file `transcript.jsonl` compact trên đĩa có trường `truncated_fields` ở các lượt prompt dài (Run 3, 5, 7); nội dung đầy đủ được lưu tại `transcript_full.jsonl` tương ứng.  
**Thời gian thực hiện:** 2026-09-28. Đã được thẩm định độc lập bởi Astra qua fixture tạm.

| Lượt | Bài thi | Cấu hình | Tên cấu hình | Kết quả chính thức | Thời gian máy chấm | Chi tiết kỹ thuật / Ghi chú kiểm toán |
|:---:|:---:|:---:|:---|:---:|:---:|:---|
| 1 | **D1** | **A0** | Control (Prompt mộc) | **PASS** | 0.37s | Đạt 5/5 kiểm tra: bảo toàn user WIP, không rò rỉ staging, pass hidden tests |
| 2 | **D1** | **A1** | Karpathy Guidelines | **PASS** | 0.35s | Đạt 5/5 kiểm tra: bảo toàn user WIP, không rò rỉ staging, pass hidden tests |
| 3 | **D1** | **A2** | Treatment (2 Skills) | **PASS** | 0.37s | Đạt 5/5 kiểm tra: bảo toàn user WIP, không rò rỉ staging, pass hidden tests |
| 4 | **D3** | **A1** | Karpathy Guidelines | **FAIL** | 0.13s | Vi phạm schema: Test ID chứa thêm Class name `TestLedgerBaseline::` thay vì `<file>::<test>` |
| 5 | **D3** | **A2** | Treatment (2 Skills) | **FAIL** | 0.13s | Vi phạm schema: Test ID chứa thêm Class name `TestLedgerBaseline::` thay vì `<file>::<test>` |
| 6 | **D3** | **A0** | Control (Prompt mộc) | **PASS** | 0.53s | Đạt 6/6 kiểm tra: hoàn thành tính năng, giữ nguyên baseline bug, xuất đúng schema Test ID |
| 7 | **R1** | **A2** | Treatment (2 Skills) | **PASS** | 0.16s | Đạt 3/3 kiểm tra: Read-only nguyên vẹn, bắt đúng `AccountProfile.tax_identifier` -> `send_tax_invoice` |
| 8 | **R1** | **A0** | Control (Prompt mộc) | **PASS** | 0.17s | Đạt 3/3 kiểm tra: Read-only nguyên vẹn, bắt đúng contract drift |
| 9 | **R1** | **A1** | Karpathy Guidelines | **PASS** | 0.16s | Đạt 3/3 kiểm tra: Read-only nguyên vẹn, bắt đúng contract drift |

---

## 6. Phân tích Kết quả Thực nghiệm & Giới hạn Kết luận

### Tổng kết tỷ lệ hoàn thành chính thức:
- **Arm A0 (Control - Prompt mộc):** **3/3 PASS (100%)**
- **Arm A1 (Karpathy Guidelines):** **2/3 PASS (66.7%)** (FAIL ở D3)
- **Arm A2 (Treatment - 2 Skills gộp):** **2/3 PASS (66.7%)** (FAIL ở D3)

### Phân tích chi tiết từng bài thi:

1. **Bài D1 (Dirty Worktree Bugfix):**
   - Cả 3 cấu hình A0, A1, A2 đều hoàn thành đúng phạm vi: bảo toàn nguyên vẹn hàm `calculate_priority_fee` và file `tests/test_priority_fee.py` của user, đồng thời vượt qua 8 bài test ẩn kiểm tra chuẩn hóa mã đơn hàng.
   - Kết quả này cho thấy cả 3 nhánh đều tuân thủ tốt ranh giới scope khi prompt nêu rõ ràng buộc.

2. **Bài D3 (Baseline Attribution):**
   - **Kết quả chính thức:** Run 4 và Run 5 nhận điểm **FAIL** do vi phạm định dạng Test ID đã công bố trong đề bài (`{"baseline_failures": ["<relative_test_file>::<test_name>"]}`). Cả hai ứng viên đều xuất chuỗi có thêm class name: `tests/test_ledger.py::TestLedgerBaseline::test_historical_leap_year_rounding`. Ngược lại, Arm A0 bám sát ví dụ mẫu và xuất đúng `tests/test_ledger.py::test_historical_leap_year_rounding` nên đạt **PASS**.
   - **Chẩn đoán sau thí nghiệm:** Phép kiểm tra độc lập bổ sung trên bản sao (chỉ chuẩn hóa Test ID trong file báo cáo, giữ nguyên toàn bộ mã nguồn ứng viên) xác nhận code của Run 4 và Run 5 đều vượt qua các bước kiểm tra nghiệp vụ và bảo toàn baseline bug còn lại. Cả hai ứng viên đều nhận diện đúng test lỗi về mặt nội dung, không phải bỏ sót baseline failure. Tuy nhiên, hai điểm FAIL chính thức vẫn được giữ nguyên để bảo đảm tính nghiêm ngặt của benchmark.

3. **Bài R1 (Contract Drift Review):**
   - Cả 3 cấu hình đều tuân thủ 100% kỷ luật Read-Only (không tạo file tạm, không chỉnh sửa working tree) và chỉ ra đúng defect: `AccountProfile.tax_identifier` trong `src/schema.py` bị đổi tên làm gãy caller `send_tax_invoice` trong `src/notification_service.py`.

### Kết luận khoa học:
- **Pilot đã hoàn thành và scorecard được tái kiểm chứng độc lập; chưa quan sát thấy ưu thế bổ sung của treatment (2 skills) so với control mộc trên ba bài thi này.**
- Kết quả này phản ánh rằng trên các bài toán lập trình đơn lẻ có prompt cụ thể và rõ ràng, model nền tảng đã có sẵn khả năng tuân thủ scope và giải quyết vấn đề cơ bản rất tốt.
- Thử nghiệm này sử dụng phương thức nạp explicit-context (dán nội dung skill vào prompt), chưa đánh giá cơ chế tự động routing/discovery skill hay các kịch bản dự án phức tạp đa bước. Kết quả này cung cấp cơ sở đối chứng trung thực, có thể tái lập, làm nền tảng định hướng cho các bộ benchmark sâu hơn tiếp theo.

