# Usage guide and workflows

This guide provides concrete usage patterns, prompt templates, and decision criteria for `repo-foundation` and `repo-native-refactor`.

---

## 1. When to Use Which Skill

Coding agents should not load every skill for every prompt. Use this decision chart:

```text
Are you creating a new project, adding a feature, or evolving a contract?
├── YES ──> Use repo-foundation
└── NO
    └── Are you reviewing or cleaning up code in a diff/pull request?
        ├── YES ──> Use repo-native-refactor
        └── NO  ──> Routine edit (fix typo, update comment). No skill needed.
```

---

## 2. Using `repo-foundation`

### Workflow A: Greenfield Setup (Bootstrap)
When creating a new repository or standalone service module:
```text
Use repo-foundation to initialize a new Python package for parsing CSV transactions.
Follow repository conventions: create pyproject.toml, author basic smoke tests, and document setup in README.md.
```

### Workflow B: Additive Feature Development (Slice)
When implementing a new feature in an existing codebase:
```text
Use repo-foundation to implement the `search_by_category` function in query.py.
Preserve existing function signatures, return types, and storage formats.
Author persistent unit tests asserting valid, empty, and invalid queries.
Update README.md to document the new query parameter.
```

### Workflow C: Contract Evolution (Evolve)
When an existing contract must change to support new requirements:
```text
Use repo-foundation to evolve the account model to include multi-tenant IDs.
Update all existing callers and migration scripts.
Ensure data migration is idempotent and maintains atomic flush semantics.
Update living documentation and existing test fixtures.
```

---

## 3. Using `repo-native-refactor`

### Workflow A: Read-Only Pull Request Review
When you want the agent to review a change set without editing files:
```text
Use repo-native-refactor to audit the working tree diff against main.
Classify findings into risk bands (R0 through R4).
Focus on contract preservation, unmanaged resources, and inverted validation logic.
Review only; do not edit any source code.
```

### Workflow B: Post-Implementation Cleanup
When you want the agent to clean up newly added code before committing:
```text
Use repo-native-refactor to clean up the diff in my-feature branch.
Consolidate duplicated validation into affirmative predicates only where shared ownership justifies it.
Preserve the authorized target contracts.
Run affected test suites after editing and provide a scaled completion report.
```

---

## 4. Key Behavioral Rules to Keep in Mind

1. **Contracts are sticky:** If a function specifies `def load(path: str) -> None`, do not allow the agent to change `str` to `Path` unless explicitly authorized.
2. **Review before mutating:** A code pattern or style preference is a *candidate finding*, not permission to mass-rewrite working code.
3. **Scale the report:** For small cleanups, completion reports should be concise and omit empty boilerplate sections.
