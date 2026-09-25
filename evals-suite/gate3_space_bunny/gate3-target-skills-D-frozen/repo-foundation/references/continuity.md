# Continuity: Session Handover and State Reconciliation

Use this reference when resuming work in a new session, taking over a repository, or reconciling discrepancies between recorded notes and the actual codebase.

---

## 1. Reconciling Notes vs. Code Reality

When taking over an ongoing project, compare documented status with the actual state of the working tree:

- **Implementation vs. Requirements:** The current codebase and working tree show what the code is currently doing; they do *not* automatically prove that the implementation correctly satisfies the user's requirements or intended acceptance criteria.
- **Handling discrepancies:**
  - *Cross-check requirements and tests:* When notes/task trackers and code conflict, cross-check the user's original requirements, preserved contracts, and the actual test coverage.
  - *Passing tests are not a rubber stamp:* Existing tests passing is not sufficient to declare a feature complete if relevant acceptance criteria or edge cases were never tested. Do not default to editing notes or documentation just to legitimize whatever code happens to be present.
  - *Investigate before updating:* If notes say a feature is pending but code appears implemented, verify against the requirement and run/add acceptance checks. If the feature is truly complete and verified, update the task notes. If the code is partial or defective, address the implementation gap rather than rubber-stamping the notes.
  - *Never blind rollback:* Do not delete or revert working code solely because an unmaintained markdown note or task tracker does not mention it. If intent remains ambiguous, ask the user.

---

## 2. Working in Dirty or Uncommitted Workspaces

Users frequently invoke agents in workspaces containing uncommitted work:

- **Inventory before mutation:** Inspect `git status` (or directory state when not using Git) before modifying files.
- **Preserve user modifications:** Identify uncommitted changes belonging to the user. Do not discard or clobber these changes.
- **Editing files with user work:** Protecting user changes does *not* forbid editing the entire file. You may modify distinct, relevant parts of the same file as long as the user's uncommitted changes remain intact and functional. Only stop and ask if there is an actual conflict or if the user's intent cannot be determined.
- **Baseline definition:** The baseline for verification and diffing includes both the base commit and the pre-existing uncommitted modifications. Changes made by the current agent pass must be distinguishable from earlier user changes.
- **No forced commits:** Never execute `git commit`, `git stash`, or `git reset` automatically to create a clean slate unless the user explicitly commands it.

---

## 3. Session Handover Guidelines

When ending a session or preparing a handoff for another agent or developer:

- **Reuse existing channels:** Record state in existing project tracking mechanisms (e.g., project issue trackers, `TODO` lists, or brief handover notes). Do not create ad-hoc handoff files for routine features.
- **Concise handover contents:**
  - What was accomplished and verified in the current pass.
  - Current status of the working tree (modified files, running commands).
  - Specific remaining limitations, unverified edge cases, or next logical steps.
  - Verification commands executed and their outcomes.
- **Avoid instruction bloat:** Do not append ongoing session logs or raw conversation transcripts to permanent repository instruction files (like `AGENTS.md`). Keep instructions focused on lasting architecture and workflows.
