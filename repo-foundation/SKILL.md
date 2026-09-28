---
name: repo-foundation
description: Build features on a clean repo foundation without breaking public API. Use when starting a module, adding a feature, migrating a contract, or resuming work.
metadata:
  version: "0.2.0"
  license: "MIT"
---

# Repo Foundation

Build software products with an explicit, just-enough foundation, develop features on top of that foundation, and adapt architecture as requirements evolve.

Optimize for total effort: deliver changes that are correct, testable, and maintainable with minimal rework, review overhead, and coordination cost.

---

## Core Principles

- **No universal dogma:** Match complexity to current requirements and system boundaries, not to an enterprise ideal. Do not enforce an arbitrary directory layout, error pattern, or framework where plain standard library suffices.
- **Scope, baseline, and user work:**
  - Establish a clean baseline before mutating code: use the pre-existing revision/commit when Git exists; use a file inventory or snapshot when uninitialized or greenfield.
  - In a dirty workspace, protect pre-existing uncommitted user modifications. You may edit distinct parts of the same file as long as user work is preserved. Stop and ask only if there is an actual collision or ambiguous intent.
  - Never create commits or force Git initialization solely for handoff or tracking.
- **Conventions and precedents:** Reuse conventions only with healthy repository precedent. Do not treat accidental patterns or temporary workarounds as precedent, and do not expand tasks into out-of-scope cleanup.
- **Prose, naming, and restraint:**
  - Names reflect business domain concepts and ownership.
  - Add comments only for information code cannot express: grounded rationale, non-obvious invariants, units, rounding, ordering, protocol quirks, or compatibility.
  - Do not narrate syntax; do not invent tickets, incidents, owners, or production histories.
  - Do not strip valuable comments merely for cosmetic brevity; do not enforce arbitrary comment ratios.
  - Do not add abstractions, wrappers, or factory layers without concrete ownership, contract, or test seam needs.
- **Preserve consumed public contracts:** See `references/shared-contracts.md` §1 for the canonical rule. In short: preserve documented or consumed types/values/errors/serialization; only change a contract when the task clearly authorizes it, then update callers/tests/docs in scope.
- **Verification rigor & proportionate testing:**
  - Record baseline failures and distinguish: (1) pre-existing failures outside scope, (2) in-scope failures to fix, (3) regressions from current changes, and (4) environment errors.
  - Verify the final code state; never use pre-cleanup test results to certify modified code.
  - Add or update persistent tests when a change introduces behavior, fixes a defect, alters a contract, or exposes a meaningful coverage gap. Prefer the repository's existing test framework and structure. Do not add tests solely for file-count or coverage optics. For documentation-only or mechanically verified changes, use the relevant lightweight checks and explain any material verification gap.
- **Failure invariants & state preservation:** For operations that overwrite, delete, migrate, or publish state, define what must remain unchanged if the operation fails. Validate inputs and destination ownership before mutation, prepare replacement data separately where appropriate, and retain the last valid state until replacement succeeds. Test relevant failure boundaries proportionately to the risk.
- **Requirement-bounded completion:** Before completion, check each material acceptance requirement against the final implementation and available evidence. Distinguish verified behavior, inspection-only conclusions, and unverified assumptions. A successful command is insufficient when its intended artifact or observable effect is missing.
- **No speculative authority:** Do not assume permission to push, publish, deploy, modify branch protection, install system-wide hooks, or purchase external services.

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

Execute routine feature development and bug fixes on an existing foundation directly from core instructions:

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

- **Complementary roles:** Foundation builds, implements, and adapts; Refactor audits, tightens prose, removes residue, and aligns conventions within scope. Foundation does not reimplement refactor's taxonomy or risk bands; Refactor does not revert intentional, requested behavioral changes.
- **Discovery and fallback:** Locate companion through host-supported discovery only; do not hardcode paths, download, or assume mentioning the name triggers execution. Foundation operates fully without companion (report companion not used). Same-agent self-review is not independent review.
- **Invocation timing:** Invoke refactor at meaningful checkpoints (completed feature, bootstrap slice, architectural evolution, or explicit audit request). Do not invoke after minor edits or lightweight fixes.
- **Minimal handoff contract:** Transfer objective/scope/intentional changes, baseline & user changes, contracts & precedents, check status & limitations from existing context without creating handoff files.
- **Post-cleanup and loop limits:** Rerun affected checks on final code state after refactor edits. Perform at most one refactor pass per checkpoint by default; iterate only on concrete findings or failing checks. If a product decision is missing, ask the user; do not guess or unilaterally redesign.

---

## Reference Routing

Read supporting references only when the corresponding trigger occurs:

- **[references/bootstrap.md](references/bootstrap.md):** Read in **Bootstrap mode** to establish a new repository, set up minimal tooling, and build the first representative slice.
- **[references/evolution.md](references/evolution.md):** Read in **Evolve mode** to assess blast radius, handle breaking contract changes, or reconcile conflicting conventions.
- **[references/continuity.md](references/continuity.md):** Read when resuming work across sessions, taking over a repository, or reconciling stale notes with code reality.
- **[references/verification.md](references/verification.md):** Read when designing checks for greenfield code, high-risk boundaries (auth, data loss, concurrency), or weak test suites.
- **[references/shared-contracts.md](references/shared-contracts.md):** Canonical contract + evidence hierarchy + final-state rule. Read when touching any public interface, reconciling conflicting requirements, or certifying completion.
- **[references/migration-examples.md](references/migration-examples.md):** Atomic vs transitional migration patterns. Read in Evolve mode before mutating persisted state.

---

## When NOT to Use

- **Trivial edits:** Skip this skill for typos, isolated script adjustments, or formatting-only changes — the coordination overhead is not justified.
- **Ambiguous precedent:** When repository conventions are ambiguous or conflicting, preserve the dominant local pattern and document the choice in the completion report rather than speculating.
