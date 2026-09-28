# Evolution: Adapting Architecture and Contracts

Use this reference when a task alters core contracts, architectural boundaries, or domain ownership, or when working in a repository with conflicting conventions.

---

## 1. Intentional Contract Changes vs. Regressions

When requirements evolve, contracts must adapt:

- **Distinguish intent:** An intentional contract change alters public API signatures, serialization schemas, data models, or error codes because the user explicitly requested new behavior. A regression is an unintended break in existing functionality.
- **Accept requested changes:** Do not fight explicit user requests by forcing compatibility with deprecated behavior. Refactoring and foundation work must accommodate authorized changes while preserving unaffected contracts.

---

## 2. Blast Radius Assessment

Before mutating shared contracts, determine the blast radius:

1. **Identify callers and consumers:** Locate all internal modules, external consumers, database schemas, message queues, or serialized data structures affected by the change.
2. **Boundary scope:** Confirm whether the change can be completed within the authorized scope or if it requires updating multiple subsystem boundaries.
3. **Migration strategy:**
   - *Atomic update:* When all callers reside within the codebase and are under the current task's scope, update the contract, callers, and tests together.
   - *Transitional migration:* When consumers are external, persisted data must be migrated, or callers span multiple independent services, maintain a compatibility bridge, migration script, or dual-read/write strategy as requested.

---

## 3. Controlled Migration Workflow

Execute architectural adjustments in logical order:

1. **Update contract definitions:** Modify the authoritative interfaces, schemas, or type definitions first.
2. **Migrate callers:** Update calling code, dependency injection bindings, and data transformations to use the new contract.
3. **Align tests:** Update existing tests that assert the old contract so they verify the new behavior. Add tests covering edge cases and error semantics of the new contract.
4. **Synchronize documentation:** Update repository instructions, schema definitions, and API documentation to prevent stale instructions from misleading future agents.

---

## 4. Reconciling Conflicting Repository Conventions

In mature repositories, different modules often reflect different architectural eras or styles:

- **Evidence hierarchy:** When patterns conflict, resolve in order:
  1. User's explicit instruction for the current task.
  2. Documented architecture and repository instructions.
  3. Preserved public contracts and persisted schemas.
  4. Healthy sibling code within the *same* owning domain and runtime boundary.
  5. Relevant tests, schemas, callers, and dependencies.
  6. Local module conventions.
- **No premature homogenization:** Do not rewrite healthy sibling code in another module merely to match your current change. Preserve legitimate domain-specific differences unless codebase-wide unification is explicitly requested.
- **Do not adopt defects as precedent:** If existing code contains obvious workarounds or defects, do not replicate them in new code; follow the healthiest precedent within the domain.

---

## 5. Multi-pressure checklist

When migration, risk, docs, and workspace pressures stack (the usual evolution mess),
work in this order and do not skip steps:

1. Baseline: record revision, failing checks, and uncommitted user work.
2. Protect user work: distinct-region edits only; stop on real collision.
3. Reconcile docs against code reality before mutating (code describes behavior, docs get fixed after).
4. Highest-risk caller first with maximum conservatism; atomic path for the rest.
5. Rerun affected checks on the final tree; report what remains red and why.
