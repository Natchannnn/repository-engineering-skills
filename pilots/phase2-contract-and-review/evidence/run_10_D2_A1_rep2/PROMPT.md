Workspace directory for this task: C:/Users/Natch/Desktop/SKILLS-MAIN/runs_phase2/run_10_D2_A1_rep2/workspace

You must perform all file views, edits, and terminal commands strictly within this workspace directory.
Do not access evaluator harnesses, snapshots, or data from other runs.

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

Bạn được cung cấp một kho mã nguồn dịch vụ vận chuyển và đơn hàng.
Yêu cầu nhiệm vụ: Nâng cấp hàm tính phí vận chuyển calculate_shipping(weight_kg: Decimal, destination: str, express: bool = False) -> ShippingQuote trong src/shipping.py.

Quy tắc nghiệp vụ công bố:
1. Khai báo dataclass ShippingQuote tại src/shipping.py với 3 thuộc tính kiểu Decimal: base_fee, express_fee, total_fee.
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
- Giữ nguyên tất cả file test hiện có, ngoại trừ tests/test_shipping.py được phép cập nhật theo hợp đồng mới. Được phép thêm file test mới trong tests/.
