---
name: repo-foundation
description: Add features, start modules, migrate contracts, or pick up half-finished work without breaking the public API. Use for "add X to this project", "set up a new module", "change this schema", "continue where we left off".
metadata:
  version: "0.2.0"
  license: "MIT"
---

# Repo Foundation

Build on a foundation that's just big enough, add features on top of it, and change the architecture only when requirements force it. Aim for the least total rework.

---

## Core Principles

- **No universal dogma:** Don't impose a layout, error pattern, or framework the project doesn't need. Plain standard library is fine.
- **Scope, baseline, and user work:**
  - Establish a clean baseline before mutating code: use the pre-existing revision/commit when Git exists; use a file inventory or snapshot when uninitialized or greenfield.
  - In a dirty workspace, protect pre-existing uncommitted user modifications. You may edit distinct parts of the same file as long as user work is preserved. Stop and ask only if there is an actual collision or ambiguous intent.
  - Never create commits or force Git initialization solely for handoff or tracking.
  - Reuse conventions only with healthy repository precedent. Don't treat accidental patterns or temporary workarounds as precedent, and don't expand into out-of-scope cleanup.
  - Don't push, publish, deploy, change branch protection, install system hooks, or buy anything unless the user asks.
- **Prose, naming, and restraint:**
  - Names reflect business domain concepts and ownership.
  - Add comments only for information code cannot express: grounded rationale, non-obvious invariants, units, rounding, ordering, protocol quirks, or compatibility.
  - Do not narrate syntax; do not invent tickets, incidents, owners, or production histories.
  - Treat error and CLI text as contract surface: check callers and parsers before rewording.
  - A ticket, PR, or incident reference you cannot click through to is fiction: delete it.
  - Do not strip valuable comments merely for cosmetic brevity; do not enforce arbitrary comment ratios.
  - Do not add abstractions, wrappers, or factory layers without concrete ownership, contract, or test seam needs.
- **Preserve consumed public contracts:** See `references/shared-contracts.md` §1 for the canonical rule. In short: preserve documented or consumed types/values/errors/serialization; only change a contract when the task clearly authorizes it, then update callers/tests/docs in scope.
- **Verification rigor & proportionate testing:**
  - Record baseline failures and distinguish: (1) pre-existing failures outside scope, (2) in-scope failures to fix, (3) regressions from current changes, and (4) environment errors.
  - Verify the final code state; never use pre-cleanup test results to certify modified code.
  - Add or update persistent tests when a change introduces behavior, fixes a defect, alters a contract, or exposes a meaningful coverage gap. Prefer the repository's existing test framework and structure. Do not add tests solely for file-count or coverage optics. For documentation-only or mechanically verified changes, use the relevant lightweight checks and explain any material verification gap.
  - Check every requirement before you say you're done. Say what you verified, what you only read, and what you assumed. A command that exits 0 doesn't count if the file it should make isn't there.
- **Failure invariants & state preservation:** If an operation can fail halfway, decide what must stay untouched. Validate inputs and ownership first, build the replacement on the side, keep the old state until the new one is ready. Test the failure boundary.

---

## Mode Selection

| Mode | Trigger | Core Actions | Exit Criteria |
|---|---|---|---|
| **Bootstrap** | New repository from scratch or an area lacking minimal foundation (no build/test/run commands, conventions, or boundaries). | Elicit critical constraints, choose just-enough design, set up minimal tooling/checks, implement and verify the first representative slice. Read [bootstrap](references/bootstrap.md). | Representative slice works and is verified; run/build commands are documented; repo is stable for subsequent work. |
| **Continue** | Adding a feature, bugfix, or improvement on an existing, fitting foundation. | Determine owning domain and boundary, implement changes, run proportionate checks, and review diff. Executable directly from core. | Task requirements are met; diff is reviewed; intentional contract changes are verified (or existing contracts preserved); remaining limitations are stated. |
| **Evolve** | New requirements alter core contracts, ownership, boundaries, or architecture; or adopting a repo with conflicting conventions. | Assess blast radius, execute controlled migration, update evidence, tests, and documentation. Read [evolution](references/evolution.md). | Transition is verified; new contracts are operational; instructions and documentation align with code. |

Adopting an existing repository begins with mode selection; do not default to re-bootstrapping. If the repository already has working instructions, tooling, and conventions, reuse them. If a specific subsystem lacks a foundation, establish only what that subsystem requires.

---

## Continue Workflow (Core)

Routine feature work runs straight from the mode above plus core principles, no extra reference needed:

### 1. Scope and Baseline
Confirm the user's objective, observable consequences, affected boundaries, baseline revision/inventory, and any uncommitted user changes to preserve.

### 2. Implement Just Enough
- **Assumptions vs. product decisions:** Choose conventional, reversible defaults (directory layout, helper naming, standard library choices) autonomously. Bundle and ask product/architectural decisions (external dependencies, data schema changes, new auth schemes) before making breaking changes.
- **Intentional contract changes:** When a task explicitly requires changing a contract, verify that callers and tests reflect the new contract rather than forcing deprecated behavior.

### 3. Verify Proportionately
- **Lightweight path (Low risk):** For routine bug fixes, typos, formatting, or localized edits within established boundaries, keep scope tight, run relevant mechanical checks (syntax, linter, affected unit tests), and skip secondary review passes.
- **High-risk vigilance:** Single-line changes to authorization, permissions, data migrations, cryptography, persistence lifecycles, or concurrency carry critical risk. Read [verification](references/verification.md) when designing checks for critical boundaries.

### 4. Continuity and State
- **Implementation vs. requirements:** Existing code shows current behavior, not proof of meeting requirements. Passing tests do not guarantee completeness if acceptance requirements were omitted.
- **Reconciliation:** Use the evidence hierarchy to guide investigation, not to resolve material contradictions automatically. Reconcile conflicting requirements, documentation, callers, and tests before changing the affected contract. When task notes and code conflict, cross-check requirements and tests; do not default to editing notes to rubber-stamp code. If resuming across sessions or taking over a repo, read [continuity](references/continuity.md).
- **Tracking:** Reuse existing repository mechanisms (issue trackers, project notes). Do not create dedicated handoff files for routine features.

---

## Companion Coordination (`repo-native-refactor`)

Foundation builds; refactor audits and cleans up. After a finished feature, ask for one refactor pass if the host has it (see [references/companion.md](references/companion.md)). Rerun affected checks after its edits; same-agent self-review is not independent review.

---

## Reference Routing

Read supporting references only when the corresponding trigger occurs:

- **[references/bootstrap.md](references/bootstrap.md):** Read in **Bootstrap mode** to establish a new repository, set up minimal tooling, and build the first representative slice.
- **[references/evolution.md](references/evolution.md):** Read in **Evolve mode** to assess blast radius, handle breaking contract changes, or reconcile conflicting conventions.
- **[references/continuity.md](references/continuity.md):** Read when resuming work across sessions, taking over a repository, or reconciling stale notes with code reality.
- **[references/verification.md](references/verification.md):** Read when designing checks for greenfield code, high-risk boundaries (auth, data loss, concurrency), or weak test suites.
- **[references/shared-contracts.md](references/shared-contracts.md):** Canonical contract + evidence hierarchy + final-state rule. Read when touching any public interface, reconciling conflicting requirements, or certifying completion.
- **[references/migration-examples.md](references/migration-examples.md):** Atomic vs transitional migration patterns. Read in Evolve mode before mutating persisted state.
- **[references/companion.md](references/companion.md):** Full companion coordination (roles, handoff, loop limits). Read when planning a refactor pass with `repo-native-refactor`.

---

## When NOT to Use

- **Trivial edits:** Skip this skill for typos, isolated script adjustments, or formatting-only changes: the overhead is not worth it.
- **Ambiguous precedent:** When repository conventions are ambiguous or conflicting, preserve the dominant local pattern and document the choice in the completion report rather than speculating.
