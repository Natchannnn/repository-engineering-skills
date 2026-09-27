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
