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

You are provided with an active codebase in a working state.
Task requirement: Fix the order ID normalization bug in `normalize_order_id(raw_id: str) -> str` located in `src/order_service.py`.

Declared normalization rules:
1. Trim all leading and trailing whitespace (including ASCII whitespace and Unicode whitespace such as \u00a0, \u2003).
2. Convert all letter prefixes to uppercase (e.g., ord- -> ORD-).
3. Valid format strictly requires the structure ORD-[0-9]+ (after prefix normalization).
4. Preserve leading zeros in the numerical portion (do not strip leading zeros, e.g. ORD-00123 must remain ORD-00123).
5. If the input string is empty, not of type str, or invalid format after cleaning: raise ValueError("Invalid order ID format").

User work protection constraints:
- The user is actively developing an in-progress priority fee feature: the `calculate_priority_fee()` function in `src/order_service.py` and the test file `tests/test_priority_fee.py`.
- You MUST NOT discard, modify, rename, or disable the user's function or test file.
- Permitted modification scope: The body of `normalize_order_id` in `src/order_service.py` and creating new test files under `tests/test_order_normalization.py`. All other lines in `src/order_service.py` (imports, module constants, user code) must remain intact.
