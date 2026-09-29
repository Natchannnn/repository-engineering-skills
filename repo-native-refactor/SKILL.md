---
name: repo-native-refactor
description: Review a diff or PR without editing it, or tidy a change set without changing behavior. Use for "review my changes", "check this diff for contract breaks", "clean this up before I open a PR", "is this safe", "merge the duplicates".
metadata:
  version: "0.2.0"
  license: "MIT"
---

# Repo-Native Refactor

Produce the smallest coherent change that belongs naturally in the target repository.

Prioritize in order:
1. **Correctness and security:** Prevent regressions, avoid new security vulnerabilities, and handle boundary conditions.
2. **Semantic integrity:** Preserve existing invariants, state transitions, validation, and error boundaries.
3. **Contracts stay as declared.** Rule lives in `references/shared-contracts.md` §1. Preserve the target contracts authorized by the task; otherwise preserve exact declared types. Internal helpers are allowed only when exposed contracts stay exact.
4. **Repository conformity:** Match surrounding naming, domain conventions, and architectural precedents.
5. **Economy and simplicity:** Minimal intervention. Delete dead weight; avoid premature abstractions.

This is a post-implementation audit and small cleanup skill. It is not permission to redesign the repository. Establish a concrete consequence such as inconsistent behavior, duplicated policy that must change together, unclear ownership, avoidable resource cost, or a demonstrated maintenance obstacle. Leave healthy code unchanged when the benefit is speculative.

---

## Minimal Intervention & Evidence Gate

- **Evidence-based intervention:** Refactor only when there is concrete evidence of divergence, defect, or operational risk. If greenfield code or an additive feature diff is already minimal, idiom-compliant, and passes tests, do not invent work or restructure working code. A recognizable pattern or style preference is a candidate finding, not justification for mutation.
- **Semantic DRY (Cost-benefit consolidation):** Merge duplicated logic only when the copies share an owner, an invariant, and a reason to change, and only if merging saves more than the extra indirection costs. Two similar-looking checks in different domains stay separate. Small local duplication stays when merging would obscure ownership.
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
- **R0 - Mechanical:** Established formatter or locally provable cleanup.
- **R1 - Low Structural:** Local residue with straightforward test verification.
- **R2 - Contextual Structural:** Renames, control-flow changes, extraction of shared predicates.
- **R3 - Semantic:** Errors, fallbacks, retries, serialization, transactions, async, or lifecycles.
- **R4 - Critical Boundary:** Auth, permissions, crypto, data migrations, persistence durability.

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
- Review the final diff like a skeptical maintainer. Every line needs a reason. No contract changed without permission, no test got weaker, no dependency moved for nothing.

---

## Reference Routing

Read supporting references only when the corresponding trigger occurs:

- **[references/shared-contracts.md](references/shared-contracts.md):** Canonical contract + evidence hierarchy. Read when touching any public interface or reconciling conflicts.
- **[references/refactor-examples.md](references/refactor-examples.md):** R0–R4 good/bad diffs. Read before rewriting a candidate finding.
- **[references/finding-taxonomy.md](references/finding-taxonomy.md):** Read for complex multi-smell diffs to name owner + consequence.
- **[references/semantic-risk.md](references/semantic-risk.md):** Read for R2+ changes, justification gate, and stop conditions.
- **[references/repository-prose.md](references/repository-prose.md):** Read when editing comments, docstrings, CLI output, or error messages.
- **[references/error-reliability.md](references/error-reliability.md) + [references/testing-integrity.md](references/testing-integrity.md):** Read for R3/R4 or weak test suites.
- **[references/deterministic-tooling.md](references/deterministic-tooling.md):** Read before introducing new scanners or bulk-codemod tools.
- **[references/repository-rehabilitation.md](references/repository-rehabilitation.md):** Read only for explicitly requested multi-domain rehabilitation, in verifiable batches.

---

## Hard Stops

Do not force a refactor where intent, ownership, public-contract consequences, migration semantics, or concurrency behavior cannot be established. Do not guess between conflicting architectural patterns without evidence.

---

## Completion Report

Scale the completion report to the change. Omit empty sections. Format completion concisely:

### Result
Use one: **Verified**, **Verified with caveats**, **Needs review**, or **Failed verification**.

For review-only requests, an empty findings list is a complete result, not an
embarrassing one. Never manufacture findings to fill a report: each reported
finding needs a producer, a consumer, and an observed consequence, or it is
not reported.

### Changed
Summarize material corrections by file and function.

### Preserved intentionally
Note specific patterns or contracts deliberately retained to avoid breaking downstream consumers.

### Verification
List exact verification commands executed and their outcomes.

### Residual uncertainty
Document unresolved limitations or high-risk boundaries intentionally deferred.

---

## When NOT to Use

- **Clean greenfield code:** Do not refactor newly written code that is already minimal, idiomatic, and passing all tests.
- **Speculative cleanup:** If you cannot state the domain owner and the concrete maintenance consequence in a single sentence, leave the code unmodified.
- **Risk classification:** When uncertain between risk bands (such as R2 structural vs. R3 semantic), default conservatively to the higher risk band and require explicit justification.
