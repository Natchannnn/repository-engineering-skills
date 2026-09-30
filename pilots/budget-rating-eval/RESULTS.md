# Bounded evaluation results

Executed on Windows on 2026-09-30. **10/10 is not established for either skill.**
The existing **9/10 subjective design ratings are retained**; this pilot does not
derive an overall score from its test pass rate.

Four audited fresh CLI sessions compared review with an empty skill catalog
against review with both skills available for implicit selection. The requested
model was `gpt-6.1-sol`, with low reasoning effort, identical prompts and fixture
bytes, and two repetitions per arm. The server model ID is not exposed in the
captured CLI events.

| Observable measure | No skills | Skills available |
|---|---:|---:|
| All prespecified review checks passed | 2/2 | 2/2 |
| Confirmed retry regression reported | 2/2 | 2/2 |
| False findings on the two clean controls | 0 | 0 |
| Project inventories preserved | 2/2 | 2/2 |
| `repo-native-refactor` entrypoint observed | 0 | 2/2 |
| Uncached input tokens, both repetitions | 32,075 | 49,466 |
| Mean wall time | 49.87 s | 55.17 s |

On this fixture, using the skill added **54.22% uncached input tokens** and
**5.30 seconds on average**, with equal graded outcomes. This does not demonstrate
incremental quality and does not establish that the skill lacks value on harder
tasks. Two synthetic repetitions are not a statistically powered or held-out
benchmark. Full entrypoint bytes in captured tool output establish actual reads;
agent self-reports do not count.

Four independent verifier controls were rejected: suppressing the real finding,
adding a false contract finding, editing review-only source, and replacing read
evidence with a self-report. Artifact inspection confirmed all four defect
reports describe the real producer, consumer and consequence. All 23 runtime
payload hashes match the previous six-case smoke evidence, so no skill
instructions changed during this evaluation.

Two earlier migration attempts are **excluded from audited results**. The skill
attempt reached the fixed 180-second limit, then the temporary evidence directory
disappeared for an undetermined reason before export. Raw events and candidate
files cannot be reconstructed; evaluator output summaries and their usage are
recorded separately. They were not repeated to replace the outcomes. The
remaining trials used durable storage and were exported after each completion.

Known CLI usage across the three calibrations, excluded control, and four audited
reviews was 131,646 uncached input tokens and 5,437 output tokens. One censored
turn's actual usage is unavailable. A separate 35,000-input/3,000-output reserve
was used only for the stop decision. Measured plus reserved input crossed the
150,000 ceiling during the final allowed turn; no further model turn started.
These numbers exclude the parent evaluator. Shared account snapshots changed
from 31% to 51% for the five-hour window and 70% to 73% for the weekly window;
those changes cannot be attributed solely to this pilot.

The neither-skill English/Vietnamese cases and mixed implementation/review case
were **not executed**, rather than counted as failures. Foundation's comparative
value, migration repeatability, exclusion routing and mixed-phase coordination
remain unmeasured here. Existing user configuration is unchanged, temporary CLI
profiles were removed, and no source-repository commit or push was made.

[Protocol and reproduction](PROTOCOL.md) ·
[Original plan](protocol-v1.json) ·
[Machine-readable report](../../evidence/budget-rating-eval/report.json) ·
[Negative controls](../../evidence/budget-rating-eval/negative-controls.json)
