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
- **Chế độ thực thi & Thứ tự khởi tạo (Execution Mode & Batching):**
  - Các lượt chạy trong từng repetition được khởi tạo và thực thi **đồng thời theo nhóm ba (concurrent triplets)** trên host:
    - *Repetition 1 (Runs 01–09):* Khởi tạo theo thứ tự `A0 -> A1 -> A2` (ví dụ Runs 01, 02, 03 cùng spawn lúc 22:24:14Z).
    - *Repetition 2 (Runs 10–18):* Khởi tạo theo thứ tự `A1 -> A2 -> A0` (ví dụ Runs 10, 11, 12 cùng spawn lúc 22:32:14Z).
    - *Repetition 3 (Runs 19–27):* Khởi tạo theo thứ tự `A2 -> A0 -> A1` (ví dụ Runs 19, 20, 21 cùng spawn lúc 22:38:54Z).
  - *Thừa nhận hạ tầng:* Do chạy đồng thời theo nhóm ba trong cùng phiên host, các subagent có khả năng chia sẻ tài nguyên tính toán (CPU, bộ nhớ, I/O và băng thông mạng) hoặc cùng chịu các biến động hạ tầng cục bộ tại thời điểm chạy.
- **Thời gian & Cơ chế Timeout:**
  - *Ngưỡng danh định (nominal timeout):* 180 giây.
  - *Ghi nhận thực tế từ transcript:* Đo từ bản ghi đầu tiên đến phản hồi cuối cùng trong transcript của subagent (bao gồm cả pha gửi báo cáo kết thúc về host).
    - 25/27 lượt hoàn thành dưới 180 giây (thời gian dao động từ 38s đến 164s).
    - 2 lượt (Run 03: 184s và Run 19: 182s) ghi nhận khoảng thời gian từ bản ghi đầu đến phản hồi cuối trong transcript vượt nhẹ ngưỡng danh định 180s.
    - *Cơ chế cưỡng chế & tính hợp lệ:* Host không gửi tín hiệu hủy (abort) process subagent; verifier độc lập chấm và xác nhận giải pháp trong workspace hoàn toàn hợp lệ. Giữ nguyên kết quả PASS của verifier, đồng thời ghi nhận đầy đủ sai lệch quy trình đo thời gian này trong metadata và báo cáo mà không thay đổi quy tắc sau khi biết kết quả.
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

---

## 8. Kết Quả Thực Nghiệm & Scorecard 27 Lượt (Phase 2 Empirical Results)

Toàn bộ 27 lượt chạy của Phase 2 ($3 \text{ tasks} \times 3 \text{ arms} \times 3 \text{ repetitions}$) đã được thực thi và nghiệm thu thành công thông qua máy chấm độc lập tại commit `b9443ee`.

### 8.1. Bảng Kết Quả Chi Tiết 27 Runs (Kèm Số Bước & Thời Gian)

| Run | Task | Arm | Rep | Tên Arm | Kết quả | Steps | Transcript Time | Thời gian Verifier | Ghi chú Evidence |
|:---:|:---:|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---|
| 01 | D2 | A0 | 1 | Control (Prompt mộc) | **PASS** | 66 | 158.0s | 0.548s | Caller test hashes & public surface intact |
| 02 | D2 | A1 | 1 | Karpathy Guidelines | **PASS** | 72 | 150.0s | 0.550s | Caller test hashes & public surface intact |
| 03 | D2 | A2 | 1 | Treatment (2 Skills) | **PASS** | 90 | 184.0s* | 0.533s | Caller test hashes & public surface intact |
| 04 | R2A | A0 | 1 | Control (Prompt mộc) | **PASS** | 40 | 47.0s | 0.159s | `[]` (FP = 0, Read-only clean) |
| 05 | R2A | A1 | 1 | Karpathy Guidelines | **PASS** | 48 | 68.0s | 0.160s | `[]` (FP = 0, Read-only clean) |
| 06 | R2A | A2 | 1 | Treatment (2 Skills) | **PASS** | 48 | 67.0s | 0.159s | `[]` (FP = 0, Read-only clean) |
| 07 | R2B | A0 | 1 | Control (Prompt mộc) | **PASS** | 36 | 53.0s | 0.158s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 08 | R2B | A1 | 1 | Karpathy Guidelines | **PASS** | 44 | 54.0s | 0.172s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 09 | R2B | A2 | 1 | Treatment (2 Skills) | **PASS** | 48 | 120.0s | 0.171s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 10 | D2 | A1 | 2 | Karpathy Guidelines | **PASS** | 60 | 119.0s | 0.545s | Caller test hashes & public surface intact |
| 11 | D2 | A2 | 2 | Treatment (2 Skills) | **PASS** | 76 | 164.0s | 0.533s | Caller test hashes & public surface intact |
| 12 | D2 | A0 | 2 | Control (Prompt mộc) | **PASS** | 68 | 133.0s | 0.549s | Caller test hashes & public surface intact |
| 13 | R2A | A1 | 2 | Karpathy Guidelines | **PASS** | 46 | 63.0s | 0.155s | `[]` (FP = 0, Read-only clean) |
| 14 | R2A | A2 | 2 | Treatment (2 Skills) | **PASS** | 58 | 75.0s | 0.162s | `[]` (FP = 0, Read-only clean) |
| 15 | R2A | A0 | 2 | Control (Prompt mộc) | **PASS** | 58 | 72.0s | 0.151s | `[]` (FP = 0, Read-only clean) |
| 16 | R2B | A1 | 2 | Karpathy Guidelines | **PASS** | 44 | 90.0s | 0.154s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 17 | R2B | A2 | 2 | Treatment (2 Skills) | **PASS** | 32 | 62.0s | 0.151s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 18 | R2B | A0 | 2 | Control (Prompt mộc) | **PASS** | 30 | 38.0s | 0.151s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 19 | D2 | A2 | 3 | Treatment (2 Skills) | **PASS** | 94 | 182.0s* | 0.548s | Caller test hashes & public surface intact |
| 20 | D2 | A0 | 3 | Control (Prompt mộc) | **PASS** | 65 | 160.0s | 0.553s | Caller test hashes & public surface intact |
| 21 | D2 | A1 | 3 | Karpathy Guidelines | **PASS** | 75 | 152.0s | 0.542s | Caller test hashes & public surface intact |
| 22 | R2A | A2 | 3 | Treatment (2 Skills) | **PASS** | 50 | 106.0s | 0.171s | `[]` (FP = 0, Read-only clean) |
| 23 | R2A | A0 | 3 | Control (Prompt mộc) | **PASS** | 36 | 73.0s | 0.154s | `[]` (FP = 0, Read-only clean) |
| 24 | R2A | A1 | 3 | Karpathy Guidelines | **PASS** | 56 | 134.0s | 0.150s | `[]` (FP = 0, Read-only clean) |
| 25 | R2B | A2 | 3 | Treatment (2 Skills) | **PASS** | 42 | 73.0s | 0.166s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 26 | R2B | A0 | 3 | Control (Prompt mộc) | **PASS** | 40 | 58.0s | 0.159s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |
| 27 | R2B | A1 | 3 | Karpathy Guidelines | **PASS** | 40 | 59.0s | 0.157s | TP = 1, FP = 0 (`api_gateway.py::handle_login`) |

*\*Ghi chú: Run 03 (184s) và Run 19 (182s) ghi nhận khoảng thời gian từ bản ghi đầu đến phản hồi cuối trong transcript vượt nhẹ ngưỡng danh định 180s. Không quan sát thấy tín hiệu ngắt (abort) từ host; verifier độc lập xác nhận lời giải đạt chuẩn và giữ nguyên kết quả PASS.*

---

### 8.2. Tổng Hợp Tỉ Lệ Đạt (Scorecard Summary)

| Arm | Mô tả | D2 (Contract Migration) | R2A (Clean Review) | R2B (Defect Review) | Tổng hợp | Tỉ lệ Đạt |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **A0** | Control (Prompt mộc) | 3/3 PASS | 3/3 PASS | 3/3 PASS | **9/9** | **100%** |
| **A1** | Karpathy Guidelines | 3/3 PASS | 3/3 PASS | 3/3 PASS | **9/9** | **100%** |
| **A2** | Treatment (2 Skills) | 3/3 PASS | 3/3 PASS | 3/3 PASS | **9/9** | **100%** |

---

### 8.3. Chỉ Số Review Tách Bạch (Precision, Recall & Specificity)

| Nhóm Arm | R2A (FP) | R2B (TP) | R2B (FN) | Precision ($TP / (TP+FP)$) | Recall ($TP / (TP+FN)$) | Specificity |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **A0 (Control)** | 0 / 3 | 3 / 3 | 0 / 3 | **100.0%** | **100.0%** | **100.0%** |
| **A1 (Guidelines)** | 0 / 3 | 3 / 3 | 0 / 3 | **100.0%** | **100.0%** | **100.0%** |
| **A2 (Treatment)** | 0 / 3 | 3 / 3 | 0 / 3 | **100.0%** | **100.0%** | **100.0%** |

---

### 8.4. Quan Sát Mô Tả Về Thực Thi & Dữ Liệu Transcript

Mặc dù kết quả chấm verifier đạt 100% trên cả ba arm, việc thống kê dữ liệu mô tả từ transcript và workspace cho thấy các số liệu cụ thể:

1. **Số bản ghi transcript (JSONL Records):**
   - Phép đếm này ghi nhận tổng số dòng JSONL trong transcript (gồm user input, planner response, tool calls, tool outputs, system messages).
   - **Tác vụ D2:** A0 trung bình 66.3 bản ghi; A1 trung bình 69.0 bản ghi; A2 trung bình 86.7 bản ghi.
   - **Tác vụ Review (R2A & R2B):** A0 trung bình 40.0 bản ghi; A1 trung bình 46.3 bản ghi; A2 trung bình 46.3 bản ghi.
   - **Toàn bộ 9 runs:** A0 trung bình **48.8 bản ghi/run**; A1 trung bình **53.9 bản ghi/run**; A2 trung bình **59.8 bản ghi/run** (+22.5% so với A0).
2. **Khoảng thời gian transcript (Elapsed Seconds):**
   - Đo từ mốc thời gian của bản ghi đầu tiên đến bản ghi cuối cùng trong transcript.
   - **Tác vụ D2:** A0 trung bình 150.3s; A1 trung bình 140.3s; A2 trung bình 176.7s.
   - **Toàn bộ 9 runs:** A0 trung bình **88.0s/run**; A1 trung bình **98.8s/run**; A2 trung bình **114.8s/run** (+30.4% so với A0).
3. **Độ dài file patch đã lưu (Patch File Line Count trên D2):**
   - Phép đếm dòng dựa trên tệp `candidate_diff.patch` đã lưu (bao gồm header git diff và các dòng ngữ cảnh xung quanh; các file tạo mới được lưu tách biệt). Thước đo này không tách riêng dòng thêm/xóa và không phản ánh chất lượng hay mức độ tối giản của giải pháp.
   - **A1 (Guidelines):** Trung bình 252.0 dòng.
   - **A2 (Skills):** Trung bình 272.7 dòng.
   - **A0 (Control):** Trung bình 302.0 dòng.

---

### 8.5. Đánh Giá Biến Thiên Liên Lượt (Inter-Run Variance)

- **Về kết quả kiểm chứng:** Trên cả 3 lần lặp (Rep 1, Rep 2, Rep 3) cho cả 3 tác vụ, kết quả PASS/FAIL là bất biến tuyệt đối ($27/27$ PASS). Không có hiện tượng flakiness trong việc đạt tiêu chuẩn verifier.
- **Về hành vi thực thi:** Có sự biến thiên thực tế giữa các lượt chạy về thời gian (từ 38s đến 184s), số bản ghi transcript (từ 30 đến 94 bản ghi) và độ dài file patch đã lưu (từ 247 đến 343 dòng trên D2). Do các arm trong từng nhóm ba chạy đồng thời (concurrent triplets), sự biến động này có thể chịu ảnh hưởng từ chia sẻ tài nguyên hoặc biến động hạ tầng của host.

---

### 8.6. Nhận Định Khoa Học & Kết Luận Thực Nghiệm

> **Kết luận chính thức:** Trên ba fixture Phase 2, mỗi fixture được chạy ba lần cho mỗi arm, tất cả bài nộp vượt qua verifier. Chưa quan sát được khác biệt về tỷ lệ hoàn thành giữa control, guidelines và treatment. Thí nghiệm chưa xác định được lợi ích về chi phí, thời gian hoặc chất lượng ngoài các tiêu chí đã đo.

1. **Hiệu năng của mô hình nền tảng ở quy mô thử nghiệm hiện tại:**
   - Khi mục tiêu và ràng buộc tương thích được mô tả đầy đủ trong prompt, mô hình nền tảng ở nhóm Control (A0) tự thân đã đủ năng lực suy luận để hoàn thành đúng hợp đồng, bảo toàn các caller và phát hiện chính xác lỗi review mà không cần bổ sung guidelines hay skills.
   - Việc so sánh với Pilot 1 cho thấy: lỗi D3 ở đợt trước là do định dạng Test ID đã công bố được đối chiếu chuỗi; khi chuyển sang Phase 2 với verifier kiểm tra ngữ nghĩa AST và bảo vệ SHA-256 caller baseline test hash, cả ba nhóm đều vượt qua kiểm tra.
2. **Quan sát về các chỉ số mô tả:**
   - Trong 27 lượt chạy này, A2 có số bản ghi transcript trung bình cao hơn A0 khoảng 22,5% và khoảng thời gian từ bản ghi đầu đến bản ghi cuối dài hơn khoảng 30,4%. Đây là các chỉ số mô tả; thí nghiệm chưa đo token, chi phí hoặc tài nguyên tính toán và chưa tách được ảnh hưởng của chạy đồng thời. Cả ba arm đạt 9/9 theo verifier.
   - Cần giữ cùng một tiêu chuẩn chứng cứ cho cả hai chiều: Pilot này chưa chứng minh lợi ích bổ sung của hai skills so với control hay guidelines; nó cũng chưa chứng minh skills gây lãng phí tài nguyên theo nghĩa tổng quát.
3. **Đóng gói bằng chứng & Bản ghi chấm lại (Evidence Bundle & Re-verification Records):**
   - Toàn bộ 240 tệp bằng chứng của 27 lượt chạy được đóng gói tại `pilots/phase2-contract-and-review/evidence/` kèm `MANIFEST.json` mã hóa SHA-256 từng file, được khóa bằng cờ `-text -eol` trong `.gitattributes`.
   - Các tệp `verifier_execution_record.json` và `eval_result.json` là **bản ghi chấm lại độc lập sau phiên candidate** (thực hiện qua `manager.py verify`), ghi nhận chính xác lệnh verifier, mã thoát `exit_code: 0`, thời gian đo thực tế và output của verifier. Mốc thời gian (timestamp) trong các tệp này phản ánh thời điểm chấm lại sau phiên, không phải thời điểm chạy của candidate subagent.
