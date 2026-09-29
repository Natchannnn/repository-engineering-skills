# Real-world runs (Batch C)

Skills tested outside their own toy fixtures. Every run below names its operator,
base commit, and verdict, PASS and no-action both recorded, nothing cherry-picked.

| Run | Target | Task | Verdict |
|---|---|---|---|
| [C1](../evidence/realworld-self/review-batchB.md) | this repo, diff `a905103..176301d` | refactor-review + fix accepted findings | 2 findings fixed, 1 deferred |
| [C2 positive](../evidence/realworld-colorama/run.md) | `tartley/colorama` @ `841634e` | regression test for init/deinit round-trip | PASS with caveat (no-tty env, logic verified directly + negative control) |
| [C2 control](../evidence/realworld-six/run.md) | `benjaminp/six` @ `c8e3940` | looked for the same gap class | NO-ACTION, tree left clean |

External clones live in temp dirs (no forks, no upstream PRs). The colorama test added
there is not contributed upstream, it is evidence of the workflow, kept in `run.md`.

## What this proves and what it does not

- The Continue-verify-review loop works on unfamiliar, real code with real suites
  (42 + 196 tests green around the changes).
- The evidence gate fires both ways: one real test added, one repo correctly untouched.
- It does not prove general efficacy: n=3, one operator (me, the repo author), no blind
  judge. Same honesty standard as the pilots.

## Reproduce

`docker build -t reskills . && docker run --rm reskills`, see `docs/reproduce.md`.
Found the hard way: `python:3.12-slim` ships without `git`, which the refactor harness
needs; the Dockerfile installs it. Windows-only PowerShell suites stay out of the image.
