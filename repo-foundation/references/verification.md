# Verification: testing in proportion to risk

Use this reference when designing checks for greenfield projects, high-risk boundaries (auth, data loss, concurrency, migrations), or weak test suites.

---

## 1. Baseline failures and scope

Before or during initial execution, record baseline test failures and sort them:

1. **Pre-existing failures:** outside the current task's scope. You don't need them green before starting, and don't fix unrelated ones just to green the baseline.
2. **In-scope failures:** inside the task's scope (a bugfix that starts with a failing test or repro script). These are yours to resolve.
3. **Regressions:** previously passing checks your changes broke. Catch and fix before declaring completion.
4. **Environment and tooling failures:** checks that can't run (missing tools, dependencies, setup). Report as environment limits, not code defects.

---

## 2. Picking checks by risk

Match checks to the contract, boundary, and failure consequences. Don't mandate unit plus integration tests for every small helper, or unrelated checks (rollback tests for an auth change):

- **Mechanical / Local changes:** For typos, formatting, localized helper refactoring, or non-semantic edits within established boundaries, run stack linters, formatters, and localized unit tests.
- **Contract and boundary changes:** When modifying public APIs, data formats, state machines, or subsystem contracts, run tests that directly verify the updated contract and its callers.
- **Critical boundary vigilance:** Changes touching authorization, permission checks, data migrations, cryptographic routines, concurrency locks, transaction boundaries, or destructive persistence carry high risk even if they touch only a single line. Verify the specific critical behavior (e.g., testing both authorized and unauthorized paths for auth changes; testing schema validity and rollback for migration scripts).

---

## 3. Greenfield and acceptance checks

When building new features or starting a repository from scratch:

- Keep environment checks separate from acceptance checks:
  - *Environment / pre-existing checks:* toolchain, package manager, and build environment must work. These pass before feature work starts.
  - *Acceptance checks for new capabilities:* the expected observable behavior of the new feature.
- For pre-build test states:
  - An acceptance check for an unbuilt feature should detect the missing behavior when run in a valid environment.
  - Tell apart a meaningful behavioral failure (endpoint 404s, CLI says unknown command, feature returns null) from an unrunnable test (syntax error, broken import, missing binary).
  - Do not inject bugs, syntax errors, or failing stubs into test code just to force a failure.
- After implementing, acceptance checks must pass cleanly on the final code state. That is the evidence of completion.

---

## 4. Testing integrity and final state

- **Reproduce before fixing:** For defect fixes, demonstrate the failure first with a minimal
  reproduction (failing test, repro script, or observed command output). A fix verified
  only after the fact is a guess with good lighting. For regression tests, prove red-green:
  revert the fix, watch it fail, restore, watch it pass.
- **Assert observable outcomes:** Check the external consequence of the action (HTTP status code and body, database row contents, exit code and stdout/stderr, or rendered DOM elements).
- **Independent expected outcomes:** Expected values must reflect business requirements, not mirror internal implementation logic.
- **No weakening of tests:** Never weaken assertion thresholds, delete valid assertions, or skip tests merely to achieve a passing run.
- **Always verify the final tree:** Execute verification commands on the actual code state intended for delivery. If a subsequent refactoring pass or companion skill modifies code, rerun all affected checks on the updated code.
- **Report actual results:** State exactly which commands were run, their outcomes, and any unverified areas.
