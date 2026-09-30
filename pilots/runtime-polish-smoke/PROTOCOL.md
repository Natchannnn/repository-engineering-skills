# Runtime polish smoke check

Executed 2026-09-30 against the uncommitted working-tree runtime. Six fresh agent
contexts received explicit skill invocations, synthetic project files, and installed
runtime copies. The evaluator, expected outcomes, snapshots, and other cases stayed
outside each runner's permitted reading scope. No project Git history was created.

This is a bounded development smoke check, not a held-out benchmark or an automatic
skill-routing measurement. Each case ran once with the same model. There is no
no-skill control arm or statistical comparison. `skills_read` is a runner report,
not an independently captured tool trace. The F2 companion pass was same-agent
self-review, not an independent reviewer.

## Cases and observed results

| Case | Request | Independently verified outcome |
|---|---|---|
| F1 | Fix integer-zero handling with both skills installed | Zero preserved; missing-value defaults retained; issue reference preserved; candidate regression tests reject the original code. Runner reported reading only foundation. |
| F2 | Approve a `str` to `Path` API change, then request one review | New type, caller, tests, and docs agree; filename result preserved; tests reject the original contract. Runner reported both skills. |
| F3 | Add an optional result shape with foundation installed alone | Feature, default integer behavior, tests, and docs verified; tests reject the unimplemented option; installed runtime unchanged. |
| R1 | Remove redundant comments with the issue tracker unavailable | Redundant comment removed; OPS-417 and gateway rationale retained; executable AST unchanged. |
| R2 | Review an unauthorized contract change without editing | Correctly reported the `Path`/`str` regression and failing `startswith` consumer; source inventory and hashes unchanged. |
| R3 | Review a clean implementation without editing | Empty defect findings; tests pass; source inventory and hashes unchanged. |

All six cases passed. Each installed skill tree retained its original hashes.
Independent checks ran candidate tests in disposable copies, and checked behavior
directly. For F1-F3, candidate tests also failed against the original `app.py`, so
their regression coverage detects the missing behavior.

Six verifier negative controls were rejected without failing unaffected cases:
restore original `app.py` for F1-F3/R1, suppress the real finding for R2, and inject
a false finding for R3. Additional artifact inspection confirmed that R1 changed
only prose and that all task edits stayed within the allowed project files.

The actual scratch package contained 23 payload files, all matching the current
workspace byte-for-byte. Resource checks passed with either skill copied alone;
missing reference and missing maintainer-script controls were rejected. Local
suites passed 30 foundation, 36 refactor, 3 resource, and 41 demo tests (110 total).
Skill validation, canonical synchronization, and CI YAML validation also passed.
Linux/Docker execution was not repeated during this Windows run.

## Evidence and reproduction

[Evidence](../../evidence/runtime-polish-smoke/report.json) records prompts,
before/after source, runner submissions, independent check output, negative controls,
and runtime hashes. `source_commit` identifies the baseline revision; tested skill
bytes were uncommitted and are identified by the payload hashes.

From the repository root, use a new absolute directory outside the repository:

```text
python -B pilots/runtime-polish-smoke/smoke.py prepare <new-run-directory>
```

The preparer builds the current runtime in scratch mode and writes one `prompt.txt`
per case. Give each prompt to a fresh agent with only its permitted workspace and
installed runtime context. Do not give runners this protocol, `smoke.py`, expected
outcomes, snapshots, or earlier results. Wait for all six `submission.json` files,
then run:

```text
python -B pilots/runtime-polish-smoke/smoke.py verify <run-directory>
python -B scripts/test_runtime_resources.py
```

Live repetitions require model access; the deterministic resource checks are part
of CI. Automatic selection, repeated-session reliability, other models and stacks,
and comparative cost remain unmeasured by this smoke check.
