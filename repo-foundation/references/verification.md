# Verification: Risk-Proportionate and Boundary Testing

Use this reference when designing checks for greenfield projects, verifying high-risk boundaries (auth, data loss, concurrency, migrations), or strengthening weak test suites.

---

## 1. Baseline Failures and Scope Distinction

Before or during initial execution, record baseline test failures and classify them clearly:

1. **Pre-existing failures:** Failures outside the current task's scope. Do not require all pre-existing checks to pass before starting work, and do not unilaterally fix unrelated out-of-scope failures just to make the baseline green.
2. **In-scope failures:** Failures directly within the task's assigned scope (for example, a bugfix task that begins with an existing failing test or a reproduction script). These are intended to be resolved by the current pass.
3. **Regressions:** Failures in previously passing checks caused by current changes. These must be caught and resolved before declaring completion.
4. **Environmental / tooling failures:** Checks that cannot run due to missing local tools, missing dependencies, or unconfigured environments. Distinguish these from code defects and report them as environment limitations.

---

## 2. Risk-Proportionate Verification Selection

Select checks based on the specific contract, domain boundary, and failure consequences of the change. Do not enforce a rigid matrix that mandates both unit and integration tests for every small helper, or forces unrelated checks (e.g., rollback tests for an auth change):

- **Mechanical / Local changes:** For typos, formatting, localized helper refactoring, or non-semantic edits within established boundaries, run stack linters, formatters, and localized unit tests.
- **Contract and boundary changes:** When modifying public APIs, data formats, state machines, or subsystem contracts, run tests that directly verify the updated contract and its callers.
- **Critical boundary vigilance:** Changes touching authorization, permission checks, data migrations, cryptographic routines, concurrency locks, transaction boundaries, or destructive persistence carry high risk even if they touch only a single line. Verify the specific critical behavior (e.g., testing both authorized and unauthorized paths for auth changes; testing schema validity and rollback for migration scripts).

---

## 3. Greenfield and Acceptance Verification

When building new features or starting a repository from scratch:

- **Separate environment checks from acceptance checks:**
  - *Environment / pre-existing checks:* Verify that the toolchain, package manager, and build environment function properly. These should pass before starting new feature development.
  - *Acceptance checks for new capabilities:* Define the expected observable behavior of the new feature.
- **Handling pre-build test states:**
  - An acceptance check for an unbuilt feature should detect the absence of the requested behavior when run in a valid environment.
  - Distinguish between a meaningful behavioral failure (e.g., endpoint returns 404, CLI returns unknown command, or feature returns null) and an unrunnable test (e.g., syntax error, broken import, missing binary).
  - Do not artificially inject bugs, syntax errors, or failing stubs into test code just to force a failure.
- **Post-implementation confirmation:** After completing implementation, the acceptance checks must pass cleanly on the final code state, providing verifiable evidence of completion.

---

## 4. Testing Integrity and Final State

- **Assert observable outcomes:** Check the external consequence of the action (HTTP status code and body, database row contents, exit code and stdout/stderr, or rendered DOM elements).
- **Independent expected outcomes:** Expected values must reflect business requirements, not mirror internal implementation logic.
- **No weakening of tests:** Never weaken assertion thresholds, delete valid assertions, or skip tests merely to achieve a passing run.
- **Always verify the final tree:** Execute verification commands on the actual code state intended for delivery. If a subsequent refactoring pass or companion skill modifies code, rerun all affected checks on the updated code.
- **Report actual results:** State exactly which commands were run, their outcomes, and any unverified areas.
