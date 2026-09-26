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
