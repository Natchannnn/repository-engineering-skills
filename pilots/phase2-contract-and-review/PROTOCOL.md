# Giao Thức Đánh Giá Hành Vi Đợt 2: Hợp Đồng Phân Tán và Kiểm Thử Đánh Giá Kép (Phase 2 Protocol)

Tài liệu này xác lập quy trình, đặc tả kỹ thuật, fixtures và tiêu chí nghiệm thu cho **Đợt 2 (Phase 2)** của chuỗi thử nghiệm hành vi agent trên kho mã nguồn Python.

---

## 1. Mục Tiêu & Giả Thuyết Khoa Học

### 1.1. Bối cảnh từ Đợt 1 (Pilot 9 lượt)
- Scorecard Đợt 1 xác nhận: Cả 3 cấu hình (A0 Control, A1 Guidelines, A2 Two Skills) đều hoàn thành xuất sắc các tác vụ vi mô đơn lẻ (D1: dirty worktree, R1: review contract drift). Ở bài D3 (lỗi baseline), mô hình ở A1 và A2 hiểu đúng bản chất nghiệp vụ nhưng bị trượt do định dạng chuỗi Test ID.
- Kết luận khoa học từ Đợt 1: Trên các tác vụ đơn lẻ, tập trung tại 1 file và có yêu cầu rõ ràng, dữ liệu thực nghiệm cho thấy chưa quan sát được ưu thế bổ sung của treatment so với control trên ba fixture đó.

### 1.2. Giả thuyết nghiên cứu Đợt 2
- **Giả thuyết H1 (Khám phá ràng buộc phân tán - Task D2):** Khi một hợp đồng công khai bị thay đổi có chủ đích mà đề bài **không liệt kê danh sách các caller phụ thuộc**, liệu việc trang bị kỹ năng (`repo-foundation`) có giúp agent chủ động rà soát toàn bộ repository, phát hiện đủ các caller phân tán và thực hiện di chuyển (migration) trọn vẹn hơn so với agent chỉ nhận prompt mộc?
- **Giả thuyết H2 (Độ chính xác và chống ảo giác trong Review - Paired Tasks R2A & R2B):** Trong bài toán đánh giá mã nguồn (code review), một agent có xu hướng đoán mò (guesswork) hoặc định kiến tìm lỗi (defect-seeking bias) sẽ dễ vu khống mã sạch (false positive trên R2A). Liệu kỹ năng (`repo-native-refactor`) có giúp duy trì kỷ luật: phát hiện đúng lỗi thật khi có contract drift (R2B - Recall) đồng thời kiềm chế không báo lỗi bậy khi diff an toàn (R2A - Precision)?
- **Nguyên tắc kiểm định trung thực (Falsifiability):** Đợt thử nghiệm này được thiết kế bình đẳng để **hoàn toàn có thể dẫn đến kết luận: Treatment (A2) không mang lại lợi thế vượt trội hoặc thậm chí làm tăng độ trễ/chi phí so với Control (A0)**. Không thay đổi nội dung skills giữa chừng để chạy theo kết quả.

---

## 2. Thiết Kế Bài Toán (Task Design)

Đợt 2 gồm 3 bài toán độc lập: 1 bài phát triển (D2) và 2 bài review đối ngẫu (R2A & R2B).

### 2.1. Task D2: Thay đổi Hợp đồng có Chủ đích & Di chuyển Callers Phân tán
- **Bối cảnh:** Kho mã nguồn dịch vụ vận chuyển và thanh toán thương mại điện tử.
- **Phần được phép thay đổi có chủ đích:**
  - Nâng cấp hàm `calculate_shipping(weight_kg: Decimal, destination: str, express: bool = False) -> ShippingQuote` tại `src/shipping.py`.
  - Hợp đồng cũ trả về một số `Decimal`.
  - Hợp đồng mới trả về một dataclass `ShippingQuote(base_fee: Decimal, express_fee: Decimal, total_fee: Decimal)`.
  - Bổ sung tham số tùy chọn `express: bool = False` (nếu `True`, tính thêm phí hỏa tốc 12.50).
  - Xác thực đầu vào chặt chẽ: `weight_kg` phải là `Decimal` và `> 0`; `destination` phải thuộc danh sách được hỗ trợ (`DOMESTIC`, `INTERNATIONAL`, `EXPRESS_ZONE`). Nếu sai, raise `ValueError`.
- **Bề mặt tương thích bắt buộc phải giữ nguyên (Compatibility Surface):**
  - Hằng số module: `DEFAULT_RATE_PER_KG: Decimal = Decimal("5.00")`.
  - Hàm tiện ích công khai: `get_supported_destinations() -> list[str]`.
  - Hai biểu tượng này đang được các hệ thống bên ngoài repo tiêu thụ; agent **không được phép đổi tên, sửa chữ ký hay xóa bỏ**.
- **Phạm vi di chuyển nội bộ (Internal Migration Scope):**
  - Đề bài **không liệt kê tên file của các caller**. Agent phải tự tìm kiếm trong repo:
    1. Caller 1: `src/checkout.py::process_checkout`
    2. Caller 2: `src/cart_summary.py::estimate_cart`
    3. Caller 3: `src/invoice.py::generate_invoice_line_items`
  - Tất cả các caller này cần được di chuyển để tương thích với kiểu trả về `ShippingQuote` (sử dụng thuộc tính `.total_fee`).
  - Toàn bộ test suite của các caller trong `tests/` phải vượt qua sau khi di chuyển; nghiêm cấm việc sửa test để che giấu lỗi hoặc xóa bỏ test.

### 2.2. Task R2A: Review Đối ngẫu — Diff An toàn (Clean Fixture)
- **Tên hiển thị với Candidate:** Mã trung tính `task_r2a`, branch `review/batch-sync-v2`. Tuyệt đối không chứa từ ngữ gợi ý như "clean", "pass", "no-defect".
- **Bản chất kỹ thuật:** Branch thực hiện tái cấu trúc đồng bộ xử lý lô dữ liệu và đã di chuyển đầy đủ tất cả caller trong toàn repo. Không có contract drift, không có lỗi kiểu dữ liệu hay chữ ký bị gãy.
- **Kỳ vọng:** Agent kiểm tra và trả về mảng rỗng `[]`.
- **Mục đích:** Đo lường **Precision / False Positive Rate** (chống tật bịa lỗi / hallucinated defects).

### 2.3. Task R2B: Review Đối ngẫu — Diff Gãy Contract (Defect Fixture)
- **Tên hiển thị với Candidate:** Mã trung tính `task_r2b`, branch `review/auth-token-v2`. Tuyệt đối không chứa từ ngữ gợi ý như "defect", "fail", "broken".
- **Bản chất kỹ thuật:** Branch cập nhật hàm sinh token phiên trong `src/auth_service.py` (thay đổi thứ tự tham số hoặc bắt buộc thêm tham số mới), nhưng để sót một caller trong `src/api_gateway.py::handle_login` vẫn gọi theo chữ ký cũ. Khi chạy runtime, caller chắc chắn bị gãy (`TypeError`).
- **Kỳ vọng:** Agent phát hiện chính xác lỗi contract drift, báo cáo theo đúng JSON schema.
- **Mục đích:** Đo lường **Recall / True Positive Detection**.

---

## 3. Ba Nhóm So Sánh (Experimental Arms)

Mỗi bài toán được thử nghiệm độc lập trên 3 cấu hình:
1. **Arm A0 (Control - Bare Prompt):** Chỉ nhận mô tả nhiệm vụ kỹ thuật mộc, không kèm bất kỳ hướng dẫn hay kỹ năng kỹ thuật nào.
2. **Arm A1 (Karpathy Engineering Guidelines):** Nhận prompt nhiệm vụ kèm khối hướng dẫn kỹ thuật lấy cảm hứng từ Karpathy (kỷ luật diff nhỏ, đọc trước khi sửa, tôn trọng caller và test suite).
3. **Arm A2 (Treatment - Two Skills):** Nhận prompt nhiệm vụ kèm 2 kỹ năng chính thức của repository: `repo-foundation` và `repo-native-refactor`.

---

## 4. Quy Mô & Bản Chất của 27 Lượt Chạy (Cohorts)

- **Số lượng:** 3 bài (`D2`, `R2A`, `R2B`) × 3 cấu hình (`A0`, `A1`, `A2`) × 3 lần lặp độc lập = **27 runs**.
- **Cân bằng vị trí & Giảm ảnh hưởng thứ tự (Balanced Arm Rotation):**
  - Thứ tự các arm được hoán vị xoay vòng theo ma trận Latin-square qua 3 repetition:
    - **Rep 1:** `A0 -> A1 -> A2`
    - **Rep 2:** `A1 -> A2 -> A0`
    - **Rep 3:** `A2 -> A0 -> A1`
  - Cơ chế xoay vòng giúp cân bằng vị trí thực thi và giảm thiểu tác động của thứ tự chạy giữa các nhóm can thiệp.
- **Ý nghĩa khoa học của 3 lần lặp:**
  - 3 lần lặp trên cùng 1 bài toán nhằm đo lường **độ biến thiên ngẫu nhiên giữa các phiên chạy (inter-run variance / non-determinism)** của cùng một mô hình với cùng một prompt.
  - Ba lần lặp **không đại diện cho sự đa dạng của bài toán**. Do đó, kết quả 27 lượt này là một cuộc **khảo sát thăm dò (exploratory cohort)**, không dùng để đưa ra các tuyên bố khái quát hóa quy mô lớn về toàn bộ thế giới phần mềm.

---

## 5. Môi Trường Thực Nghiệm & Ghi Nhận Điều Kiện Chạy

- **Host Platform:** Google Antigravity Advanced Agentic Coding Engine.
- **Model Metadata:**
  - `Host: Antigravity`
  - `Requested model: inherit`
  - `Resolved model: unknown / not recorded`
- **Subagent Spec:**
  - `pilot_candidate` subagent cô lập hoàn toàn.
  - Công cụ cho phép: Write/Edit tools (`view_file`, `write_to_file`, `replace_file_content`, `run_command`).
  - Công cụ vô hiệu hóa: Subagent tools, MCP tools, Internet search.
- **Thời gian & Timeout:**
  - Timeout cho mỗi lượt chạy candidate: tối đa 180 giây.
  - Ghi nhận độc lập: thời gian thực thi của candidate subagent và thời gian chạy của verifier.
- **Xử lý lỗi môi trường (Retry Policy):**
  - Nếu subagent bị dừng do lỗi hạ tầng (host crash, ngắt kết nối process), được phép chạy lại 1 lần và ghi chú rõ trong metadata.
  - Nếu subagent tự ý kết thúc hoặc nộp bài không đạt, kết quả được giữ nguyên tuyệt đối, không retry.

---

## 6. Tiêu Chí Chấm Điểm & Đánh Giá Tách Bạch

### 6.1. Tiêu chí cho Task D2
1. **Bắt buộc Snapshot:** Sidecar snapshot (`d2-snapshot.json`) là bắt buộc để xác thực `initial_head` và `manifest`. Thiếu snapshot, snapshot hỏng hoặc thiếu metadata đều bị từ chối ngay lập tức.
2. **Toàn vẹn Git & Không commit bừa:** `git rev-parse HEAD` bắt buộc trùng khớp tuyệt đối với `initial_head`. Staging index phải sạch.
3. **Bảo vệ 3 Test Callers Gốc:** Ba file test `tests/test_checkout.py`, `tests/test_cart_summary.py`, và `tests/test_invoice.py` bắt buộc phải khớp byte-exact với SHA-256 gốc trong manifest (chuẩn hóa CRLF -> LF), đồng thời phải có test methods thực thi được và pass hoàn toàn. Mọi hành vi sửa đổi, làm rỗng, hay thay bằng `assertTrue(True)` đều bị từ chối.
4. **Bề mặt tương thích:** `DEFAULT_RATE_PER_KG` (kiểu strictly `Decimal("5.00")`) và `get_supported_destinations()` tồn tại và giữ nguyên hợp đồng.
5. **Hidden Tests cho API mới:** Kiểm tra `calculate_shipping` với các trường hợp: tính đúng `base_fee`, `express_fee`, `total_fee`; kiểm tra cờ `express`; trả về đúng frozen dataclass `ShippingQuote`; raise `ValueError("Invalid weight")` hoặc `ValueError("Unsupported destination")`.
6. **Hidden Tests cho 3 Callers:** Gọi độc lập `process_checkout`, `estimate_cart`, `generate_invoice_line_items` để xác nhận tất cả callers đều đã được di chuyển sang `ShippingQuote.total_fee` và trả về kết quả nghiệp vụ chính xác.
7. **Suite Test hiện có:** Toàn bộ test trong `tests/` chạy thành công với banner `OK` (không có `SkipTest`).

### 6.2. Tiêu chí cho Tasks R2A & R2B
- **Bắt buộc Snapshot:** Sidecar snapshot (`r2a-snapshot.json` / `r2b-snapshot.json`) là bắt buộc để xác thực `feature_head` và `manifest`. Thiếu snapshot hoặc metadata không đầy đủ đều bị từ chối với lỗi rõ ràng.
- **Bảo toàn Read-Only Tuyệt Đối:**
  - `git rev-parse HEAD` bắt buộc trùng khớp với `feature_head` ban đầu (không commit sửa mã).
  - `git diff HEAD` và staged index phải sạch hoàn toàn.
  - Toàn bộ file tracked trong manifest phải khớp SHA-256 nguyên bản (chuẩn hóa CRLF -> LF).
  - Cho phép bytecode sinh ra từ quá trình chạy test (`__pycache__`, `.pyc`).
- **Xuất kết quả:** File JSON ngoài repository theo cờ `--evidence-file`.
  ```json
  [
    {
      "verdict": "defect",
      "source_file": "<path_to_source>",
      "source_symbol": "<symbol_name>",
      "broken_caller_file": "<path_to_caller>",
      "broken_caller_symbol": "<caller_symbol_name>",
      "breakage_type": "contract_drift | removed_symbol | signature_changed | type_mismatch"
    }
  ]
  ```
- **Hệ số đánh giá tách bạch:**
  - `TP` (True Positives): Phát hiện đúng lỗi contract drift thực tế (chấp nhận danh sách alias hợp lệ được định nghĩa trước).
  - `FP` (False Positives): Báo lỗi ảo khi mã nguồn hoàn toàn an toàn.
  - `FN` (False Negatives): Bỏ sót lỗi thực tế.
  - Trên fixture sạch (R2A): Do không có lỗi thực tế (mẫu số bằng 0), kết quả đơn lẻ được ghi nhận là `Precision: N/A`, `Recall: N/A`, và tiêu chí PASS duy nhất là `FP == 0` (không báo lỗi sai).
  - Trên fixture có lỗi (R2B): Yêu cầu `TP == 1` và `FP == 0` (Precision = 1.0, Recall = 1.0).
  - Chỉ số Precision và Recall tổng hợp được tính chung trên dữ liệu gộp của cả hai bài R2A và R2B.
- **Task R2A (Clean):** Yêu cầu `FP == 0` (mảng rỗng `[]`). Bất kỳ finding nào đều tính là FAIL.
- **Task R2B (Defect):** Yêu cầu `TP == 1` và `FP == 0`. Báo cáo mảng rỗng `[]` tính là FAIL.

---

## 7. Quy Trình Nghiệm Thu Máy Chấm (Self-Audit)
Trước khi khởi chạy bất kỳ lượt candidate nào, bộ verifier của Phase 2 bắt buộc phải vượt qua toàn bộ 35 unit tests đối chứng (Positive & Negative Controls):
1. **D2 Controls (15 tests):**
   - Canonical Solution (sửa shipping + di chuyển cả 3 callers) -> PASS.
   - Alternative Solution (cú pháp di chuyển khác) -> PASS.
   - Negative 1: Chỉ sửa shipping, không sửa callers -> FAIL.
   - Negative 2: Di chuyển thiếu 1 caller -> FAIL.
   - Negative 3: Xóa hoặc đổi hằng số tương thích / gán int 5 -> FAIL.
   - Negative 4: Sai thông báo ngoại lệ ("Invalid weight") -> FAIL.
   - Negative 5: Xóa file test baseline -> FAIL.
   - Negative 6: Caller test bị làm rỗng / neutered -> FAIL.
   - Negative 7: Shipping test bị làm rỗng / neutered -> FAIL.
   - Negative 8: Caller test bị thay bằng assert tầm thường (`assertTrue(True)`) -> FAIL (phát hiện bằng SHA-256 manifest hash).
   - Negative 9: Candidate commit vào workspace -> FAIL.
   - Negative 10: Chứa test bị bỏ qua (`SkipTest`) -> FAIL.
   - Negative 11: Thiếu sidecar snapshot file -> FAIL.
   - Negative 12: Snapshot file thiếu metadata bắt buộc (`initial_head`, `manifest`) -> FAIL.
2. **R2A Controls (9 tests):**
   - Canonical Solution (trả `[]`) -> PASS (Precision: N/A (FP=0), Recall: N/A).
   - Chạy `unittest discover` sinh ra `__pycache__` -> PASS đúng.
   - Negative 1: Bịa lỗi trên mã sạch -> FAIL (FP > 0).
   - Negative 2: Chỉnh sửa mã nguồn chưa commit -> FAIL.
   - Negative 3: Sửa mã nguồn rồi commit -> FAIL.
   - Negative 4: Sửa mã nguồn, commit và xóa snapshot -> FAIL.
   - Negative 5: Sai schema JSON mảng -> FAIL.
   - Negative 6: Thiếu sidecar snapshot file -> FAIL.
   - Negative 7: Snapshot file thiếu metadata bắt buộc (`feature_head`, `manifest`) -> FAIL.
3. **R2B Controls (11 tests):**
   - Canonical Solution (báo đúng source & caller gãy) -> PASS (TP=1, FP=0).
   - Alternative Solution (chấp nhận alias symbol / file tương đương) -> PASS.
   - Chạy `unittest discover` sinh ra `__pycache__` -> PASS đúng.
   - Negative 1: Trả `[]` (bỏ sót lỗi) -> FAIL (FN=1).
   - Negative 2: Báo sai caller không liên quan -> FAIL (TP=0, FP=1).
   - Negative 3: Báo đúng lỗi kèm 1 lỗi ảo phụ -> FAIL (TP=1, FP=1).
   - Negative 4: Chỉnh sửa mã nguồn chưa commit -> FAIL.
   - Negative 5: Sửa mã nguồn rồi commit -> FAIL.
   - Negative 6: Sửa mã nguồn, commit và xóa snapshot -> FAIL.
   - Negative 7: Thiếu sidecar snapshot file -> FAIL.
   - Negative 8: Snapshot file thiếu metadata bắt buộc (`feature_head`, `manifest`) -> FAIL.
