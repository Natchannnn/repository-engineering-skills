Workspace directory for this task: <REPO_ROOT>/runs_phase2/run_17_R2B_A2_rep2/workspace

You must perform all code views and git commands within this workspace directory.
Do not modify or commit any files within the workspace repository.
The ONLY permitted file output is the review report specified by --evidence-file: <REPO_ROOT>/runs_phase2/run_17_R2B_A2_rep2/evidence.json
Do not access evaluator harnesses, snapshots, or data from other runs.

# ENGINEERING SKILL: repo-foundation

---
name: repo-foundation
description: Build software products on a clean, minimal foundation, develop new features or bug fixes, and adapt architecture as requirements evolve. Use when initializing a new codebase, adding features to an existing repository, or refactoring architectural boundaries and contracts.
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
- **Preserve consumed public contracts:** Preserve documented or demonstrably consumed public contracts, including declared types, values, errors, and serialization. A requested behavior change may authorize a contract change when that consequence is clear from the task; update affected callers, tests, and documentation within scope. Ask only when compatibility expectations or affected consumers remain materially ambiguous. Internal representations may differ when conversion preserves the public contract (for example, do not replace an exposed string path contract with `Path` objects in public module constants or function signatures merely because `Path` is preferred internally).
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


---

# ENGINEERING SKILL: repo-native-refactor

---
name: repo-native-refactor
description: Audit and refactor code changes to conform strictly to repository semantics, architecture, domain idioms, and reliability contracts. Use after implementation for surgical cleanup, behavior-preserving refactoring with verification, and review preparation without altering authorized behavior or introducing gratuitous modernization.
metadata:
  version: "1.2.1"
---

# Repo-Native Refactor

Produce the smallest coherent change that belongs naturally in the target repository.

Prioritize in order:
1. **Correctness and security:** Prevent regressions, avoid new security vulnerabilities, and handle boundary conditions.
2. **Semantic integrity:** Preserve existing invariants, state transitions, validation, and error boundaries.
3. **Strict contract adherence:** Preserve documented or demonstrably consumed public contracts across public interfaces, exported parameters, and module constants, preserving the target contracts authorized by the task. A requested behavior change may authorize a contract change when that consequence is clear from the task or authorized evolution; in all other cases, preserve exact declared types (for example, never substitute or wrap an exposed primitive `str` contract with `pathlib.Path` or custom wrapper objects merely for internal convenience). Internal intermediate representations may use appropriate helpers, provided exposed public contracts and types remain exact.
4. **Repository conformity:** Match surrounding naming, domain conventions, and architectural precedents.
5. **Economy and simplicity:** Minimal intervention. Delete dead weight; avoid premature abstractions.

This is a post-implementation audit and surgical cleanup skill. It is not permission to redesign the repository. A style preference or recognizable pattern is a candidate finding, not sufficient justification for mutation. Establish a concrete consequence such as inconsistent behavior, duplicated policy that must change together, unclear ownership, avoidable resource cost, or a demonstrated maintenance obstacle. Leave healthy code unchanged when the benefit is speculative.

---

## Minimal Intervention & Evidence Gate

- **Evidence-based intervention:** Refactor only when there is concrete evidence of divergence, defect, or operational risk. If greenfield code or an additive feature diff is already minimal, idiom-compliant, and passes tests, do not invent work or restructure working code. A recognizable pattern or style preference is a candidate finding, not justification for mutation.
- **Semantic DRY (Cost-benefit consolidation):** Consolidate shared validation or transformation logic into clean, reusable helpers or predicates only when implementations share ownership, invariants, semantic purpose, and reasons to change. Shared semantics make consolidation eligible, not mandatory. Consolidate only when reducing duplicated policy outweighs the added indirection, coupling, and navigation cost. Keep small local duplication when an abstraction would make ownership or behavior harder to understand. Do not prematurely consolidate incidental syntactic similarity across separate domain boundaries.
- **Contract boundary protection:** Preserve public interfaces, parameter names, and return types except where their change is clearly authorized by the task. During cleanup, preserve the authorized target contract rather than reverting to the previous contract.

---

## Operating Modes

- **Review vs. Refactor Authority:** Establish whether the requested outcome is findings, edits, or both. A review-only request authorizes inspection and verification, not source modification. An authorized cleanup permits bounded corrections within scope; do not require repeated approval for routine implementation choices.
- **Change-Set Cleanup:** Use for a working tree, branch, commit range, feature, or bounded implementation checkpoint. Work diff-first; inspect surrounding code only to understand ownership, contracts, and relevant precedent.
- **Repository Rehabilitation:** Use only when explicitly requested across multiple domains. Read [repository rehabilitation](references/repository-rehabilitation.md), build a concise profile, and work in independently verifiable batches.

---

## Evidence Hierarchy

Use the evidence hierarchy to guide investigation, not to resolve material contradictions automatically. Reconcile conflicting requirements, documentation, callers, and tests before changing the affected contract. When repository patterns conflict, resolve in order:
1. User requirements and explicitly authorized scope.
2. Documented architecture and repository guidelines.
3. Observable public contracts and persisted schemas.
4. Healthy sibling code within the same domain and runtime boundary.
5. Relevant tests, schemas, callers, and dependencies.
6. Dominant local conventions.
7. Language and runtime idioms.
8. Conservative, idiomatic defaults.

Never treat a temporary workaround, buggy sibling, or accidental pattern as precedent.

---

## Workflow

### 1. Establish Scope and Baseline
Before mutating code, identify:
- Comparison base and working-tree state.
- In-scope files vs. untouched user modifications.
- Existing verification commands and their current pass/fail status.

Differentiate pre-existing failures from regressions introduced by this pass. Never claim a check ran when it did not.

### 2. Establish Intent, Ownership, and Preservation
Refactoring is behavior-preserving by default. Protect:
- Public APIs, serializations, and database schemas.
- Concurrency guarantees, idempotency, timeouts, and retries.
- Resource lifecycles (file handles, sockets, database transactions).

If a bug requires an observable change, classify and report it as an intentional behavioral correction rather than routine cleanup.

### 3. Inventory Findings Before Rewriting
Inspect the authorized scope for:
- Validation or control flow whose structure obscures an invariant, creates inconsistent behavior, or duplicates the same owned policy.
- Misplaced domain ownership or leaky abstractions.
- Leaked unmanaged resources or missing atomic flush/sync calls.
- Unnecessary boilerplate, dead code, or commentary narrating syntax.

Read [finding taxonomy](references/finding-taxonomy.md) for complex cases. Establish the smallest adequate correction before editing.

### 4. Classify Risk and Refactor
Risk bands:
- **R0 — Mechanical:** Established formatter or locally provable cleanup.
- **R1 — Low Structural:** Local residue with straightforward test verification.
- **R2 — Contextual Structural:** Renames, control-flow changes, extraction of shared predicates.
- **R3 — Semantic:** Errors, fallbacks, retries, serialization, transactions, async, or lifecycles.
- **R4 — Critical Boundary:** Auth, permissions, crypto, data migrations, persistence durability.

Read [semantic risk](references/semantic-risk.md) for R2+ changes. Never mass-rewrite R3 or R4 behavior without explicit instructions and verified tests.

### 5. Audit Code Prose
- Treat comments, docstrings, CLI output, and error messages as distinct surfaces. Read [repository prose](references/repository-prose.md).
- Delete comments that merely narrate obvious syntax or execution order.
- Preserve and tighten comments that explain non-obvious invariants, protocol quirks, rounding, or hardware workarounds.
- Never invent fictitious tickets, PR references, or production incident IDs.

### 6. Verify and Review
- Run the smallest repository-native checks that meaningfully exercise the change. Read [error and reliability boundaries](references/error-reliability.md) and [testing integrity](references/testing-integrity.md).
- Prioritize diff reviewability and coherence over raw line minimization; do not compress code into unreadable one-liners.
- Distinguish intentional behavioral corrections from mechanical cleanup.
- Review the final diff as a skeptical maintainer:
  - Every modified line must have a concrete, defensible justification.
  - Zero unauthorized contract alterations.
  - Zero weakened test assertions.
  - Zero unneeded dependency churn or cosmetic formatting noise.

---

## Hard Stops

Do not force a refactor where intent, ownership, public-contract consequences, migration semantics, or concurrency behavior cannot be established. Do not guess between conflicting architectural patterns without evidence.

---

## Completion Report

Scale the completion report to the change. Omit empty sections. Format completion concisely:

### Result
Use one: **Verified**, **Verified with caveats**, **Needs review**, or **Failed verification**.

### Changed
Summarize material corrections by file and function.

### Preserved intentionally
Note specific patterns or contracts deliberately retained to avoid breaking downstream consumers.

### Verification
List exact verification commands executed and their outcomes.

### Residual uncertainty
Document unresolved limitations or high-risk boundaries intentionally deferred.


---

# TASK ASSIGNMENT

You are provided with a codebase repository.
Task requirement: Review the git diff between the current branch and main. This task is strictly READ-ONLY; you MUST NOT modify any files in the repository.
Inspect whether any public contract / interface changes broke dependent caller modules in the repository.

Review Report Specification:
Output results to the path specified via --evidence-file <REPO_ROOT>/runs_phase2/run_17_R2B_A2_rep2/evidence.json (JSON file outside repository).
The defect list must be a JSON array adhering to the structure:
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

Formatting conventions:
- source_file and broken_caller_file: Relative path from repository root (e.g. src/foo.py).
- source_symbol: Fully qualified identifier of the modified object (e.g. ClassName.method_name or function_name).
- broken_caller_symbol: Name of the caller function/method that broke.
- breakage_type: Choose one of the enum values listed above.
- If no contract drift defect is found, output an empty array [].
