# Bounded rating evaluation

The user authorized a usage-conscious evaluation of whether `repo-foundation`
and `repo-native-refactor` deserve a higher rating. The machine-readable
[protocol](protocol.json) declares the criteria, labels, run order and stopping
conditions before scored execution. The original plan allowed eleven sessions,
then [version 2](protocol.json) kept seven remaining review/routing sessions after
the migration treatment reached the fixed 180-second limit and the temporary run
directory subsequently disappeared for an undetermined reason. Both migration
attempts are excluded from audited scores because raw events and candidate files
are unavailable. [Version 1](protocol-v1.json) and the
[excluded summary](excluded-run-summary.json) preserve the original plan and
figures transcribed from evaluator tool outputs. Missing actual usage is recorded
as unavailable, with a separate conservative reserve used to decide whether
another session can start. No excluded attempt is repeated or replaced.
Seven remaining sessions are the maximum, not a
target to exceed if results already disqualify the rating gate.

Two identical matched task families use the same model and low
reasoning effort: an approved persisted-schema migration and a read-only review
containing a real retry regression plus two clean controls. Each matched pair
compares an empty skill catalog with both candidate skills available for implicit
selection. Review runs twice; migration has no audited result after the evidence
loss. The next run uses durable workspace storage, and each completed trial is
copied into the repository evidence immediately.
A Python explanation, a Vietnamese wording edit and a Vietnamese
implementation-then-review request probe exclusions and coordination.

Only project fixtures and installed runtime files are available within the
runner's permitted reading scope. The evaluator, labels and trusted checks stay
outside that scope. This is instruction-level isolation; the Windows runner uses
the host's unrestricted execution profile. Tools and network features unrelated
to the tasks are disabled. No source-repository commit or push is permitted.

`codex debug prompt-input` verifies the treatment catalog contains exactly the
two candidates and the control catalog contains neither. A temporary CLI profile
disables other host skills by their absolute `SKILL.md` paths. It does not edit
existing user settings and must be removed after execution. The initial runner
calibrations are excluded from scores but included in cost accounting.

Skill use requires the complete actual entrypoint text in captured command
output. A later failing subcommand in the same batch does not negate a completed
read; record the batch exit code separately. The initial observer incorrectly
discarded that read when a later Git check failed in a non-Git fixture. This
observer bug was corrected before any review or exclusion trial, with labels
unchanged and without rerunning the candidate. Agent statements alone do not
count. Runtime hashes, project inventories,
direct behavior checks, injected I/O failures and persistent candidate tests
verify results independently. Candidate tests are also run with the original
implementation restored in a disposable copy. Review findings and the timing of
the mixed companion read require artifact inspection in addition to automated
checks. A same-agent companion pass is not an independent reviewer.

The suite is a predeclared synthetic development probe, not held-out research or
a statistically powered benchmark. Two repetitions do not establish broad
reliability. Ties with control do not demonstrate incremental quality. A 10/10
claim must be restricted to supported tasks and conditions, and this small set
alone cannot establish universal quality. Account percentages and model token
counts are recorded separately; neither converts directly to the other.

From the repository root, using a new absolute scratch directory:

```text
python -B pilots/budget-rating-eval/run.py prepare <run-root>
python -B pilots/budget-rating-eval/run.py run <run-root> <run-id>
python -B pilots/budget-rating-eval/run.py verify <run-root> <run-id>
python -B pilots/budget-rating-eval/run.py cleanup <run-root>
```

Run IDs and their order are in `protocol.json`. Model runs refuse to overwrite
previous trials and check cumulative usage before starting another session.
Record any unavailable usage instead of treating it as zero. Preserve the
pre-execution protocol, raw CLI events, final submissions, runtime hashes,
verification records and any exclusions with the final evidence.
