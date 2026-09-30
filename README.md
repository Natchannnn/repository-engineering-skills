# Repository Engineering Skills: Code Review and Refactoring for AI Agents

[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![version](https://img.shields.io/badge/version-0.3.0-green)](CHANGELOG.md) [![payload](https://img.shields.io/badge/payload-23%20files-lightgrey)](docs/installation.md)

Vibe coding feels great for the first few sessions. But 10 or 20 sessions in, you open the repo and it looks like it was written by random flatmates who never met, but each decided to completely remodel the house without asking, one is over-engineering, another is tearing it down to basics, and Jimmy is playing drums in the corner.

Everything an agent touches, it believes has turned into gold. Weirdly enough, nobody asked it to write 300 lines out of scope, and when every agent believes it's doing God's work, is that something you refactor from scratch, or is it time to get on your bike?

Anyway, here’s what Jimmy made while playing the drums to keep the band together:

- **`repo-foundation`**: gives every new session the same ground rules to start from: where the boundaries are, which conventions the repo follows, and which contracts can't be broken.
- **`repo-native-refactor`**: keeps each change in line with the ones before it. It trims bloated diffs, catches contract drift, and makes new code look like it was always there.

Use them together and you can pass a project from agent to agent across dozens of sessions, and it will still be comprehensible.

Much love,  
~~Jimmy~~ Natch

---

## 60-second try

```sh
mkdir skill-try && cd skill-try
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --list
npx skills@1.7.0 add Natchannnn/repository-engineering-skills --skill repo-foundation repo-native-refactor --agent codex --copy -y
```

Then in a new session:
- `Use $repo-foundation to create a small Python CSV CLI with a test and README notes. Do not commit.`
- `Use $repo-native-refactor to review the diff. Report only, do not edit.`

---

## What goes wrong without them

Contract drift is common: a return type changes and callers break (`str` to `Path` is a frequent offender).
Other common failure modes include scope creep (a narrow fix rewrites healthy unrelated modules), unchecked error paths (partial state left on disk when operations fail), and documentation drift (`README.md` still describes older behavior).

---

## Choosing a skill

No skill needed for typos, comments, or single-script tweaks.

| Situation | Skill |
|---|---|
| New repo or module from scratch | `repo-foundation` |
| New feature or bugfix on a working codebase | `repo-foundation` |
| Changing a public contract or migrating schemas | `repo-foundation` |
| Resuming work across sessions | `repo-foundation` |
| Reviewing a diff without touching code | `repo-native-refactor` |
| Cleaning up duplication or dead code in a diff | `repo-native-refactor` |

---

## Example prompts

```text
Use repo-foundation to add JSON export to this CLI tool.
Keep existing commands and error handling. Add tests and document the flag.
```

```text
Use repo-native-refactor to review the current diff against main.
Flag contract drift, unhandled error paths, or misplaced ownership.
Review only; do not edit files.
```

```text
Use repo-native-refactor to clean up this diff where a real maintenance or
correctness problem exists. Keep authorized behavior. Re-run affected checks.
```

---

## Installation options

Requires Git + Node.js 22.20.0 or newer. Verified for `codex`, `claude-code`, `cursor`, `opencode`, and `gemini-cli` (see [docs/installation.md](docs/installation.md)).

- **Skills CLI (recommended):** see the [60-second try](#60-second-try) above.
- **Claude Code Marketplace:** use this repository directly via `.claude-plugin/marketplace.json`.
- **Offline / No-Node setups:** use `scripts/install-skills.ps1` (or `install-skills.sh`), or download the pre-packaged runtime ZIP from releases.

---

## Demos with independent verifiers

No LLM judges are used for demo verifiers; deterministic scripts evaluate outcomes against ground truth:

- **Contract-drift review** ([`examples/read-only-contract-review/`](examples/read-only-contract-review/)): agent audits a breaking diff read-only and files a structured finding. Verifier rejects negations, wrong symbols, and any worktree mutation.
- **Scoped feature dev** ([`examples/foundation-development/`](examples/foundation-development/)): agent adds an `export-json` command with tests + docs. Verifier checks both suites, JSON schema, and that nothing outside scope changed.

![harness verification demo](docs/demo/demo-40s.gif)

*(Recorded directly from the test harness via `python scripts/render-demo-gif.py`. Full details in [docs/demo/](docs/demo/).)*

---

## Test results

| Test Suite | Result | Details |
|---|---|---|
| Pilot 1 (3 arms, deterministic verifiers) | **7/9 passed** (2 runs failed schema validation on test ID formatting) | [PROTOCOL.md](pilots/small-behavioral-pilot/PROTOCOL.md) |
| Phase 2 (27 runs, rotated triplets) | **27/27 passed** (tasks were too simple to differentiate arms statistically) | [PROTOCOL.md](pilots/phase2-contract-and-review/PROTOCOL.md) |
| Runtime polish smoke (6 fresh agent contexts) | **6/6 passed**, explicit invocation, one run per case; no baseline comparison | [PROTOCOL.md](pilots/runtime-polish-smoke/PROTOCOL.md) |
| Harness, example, runtime & demo suites | 110 tests (66 harness/example + 3 isolated-resource + 41 demo acceptance) | `repo-*/evals/tests`, `scripts/test_runtime_resources.py`, `scripts/test_demos.py` |
| Runtime package verification | 23 payload files verified byte-for-byte against Git commit tree | `scripts/test-package.ps1` |
| Real-world test runs | Colorama regression suite passes; 6 repositories correctly untouched; self-review verified | [docs/realworld.md](docs/realworld.md) |
| Adversarial probes | 8 held-out fixtures (Batch E) and cross-model boundary analysis | [ATTACK_REPORT.md](adversarial/ATTACK_REPORT.md) |

<details>
<summary><strong>Known limitations and design notes</strong></summary>

- **Task complexity:** Most experiments ran on bounded toy fixtures with single-operator evaluations; CP2/CP3 ablations were single-run case studies.
- **Gate 3 over-refactoring:** Initial refactor skill variants scored below baseline by modifying clean code unnecessarily; this led to introducing the evidence gate.
- **Platform focus:** Test suites run primarily on Windows (Linux verified via Docker; path ordering differences noted in `docs/reproduce.md`).
- **Durability boundaries:** Crash safety against unexpected power loss has not been tested against real hardware interruption.
- Full analysis: [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md) and [docs/evaluation.md](docs/evaluation.md).
</details>

---

## Verify it yourself

```sh
python -m pip install -r requirements-test.txt
python -B -m unittest discover -s repo-foundation/evals/tests      # 30 tests
python -B -m unittest discover -s repo-native-refactor/evals/tests  # 36 tests
python -B scripts/test_runtime_resources.py                       # 3 tests
python -B repo-foundation/evals/harness.py validate
python -B scripts/test_demos.py                                     # 41 tests
powershell -ExecutionPolicy Bypass -File scripts/test-package.ps1   # 8 acceptance tests
docker build -t reskills . && docker run --rm reskills              # linux reproduce
```

Pilot self-audits, archive checks, and installer/package tests: [docs/evaluation.md](docs/evaluation.md).

---

## Issues and license

Report issues with host, model, skill version, prompt, and what happened. See [CONTRIBUTING.md](CONTRIBUTING.md). [MIT License](LICENSE).
