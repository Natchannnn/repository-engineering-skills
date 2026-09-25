# Evaluation Harness

Harness 1.1.0 ships with skill 1.2.1. It requires Python 3.10+ and Git. This release was exercised on Windows; Linux/macOS execution is not yet validated. It does not launch an AI or implement a sandbox.

## Migration from harness 1.0.0

Prepare a new run directory; old runs cannot be resumed or rescored by this build. `prepare` now requires `--bars`. Suites/bars retain v1 schemas; judgments use v2 with required bar IDs. The `judge --replace` option is removed. Collection, judge preparation and scoring cannot overwrite existing outputs.

This harness tests whether the skill improves real repositories without teaching the runner how to pass. It is author tooling, not runtime guidance: `evals/` is deliberately removed from every runner-visible skill copy.

## What it proves

The protocol can support a bounded claim such as:

> Under the recorded model, tools, budget, repositories, and judge bar, this skill cleared all hard gates and achieved the reported pass rate across repeated blind runs.

It cannot prove that the skill is universally perfect. A `10.0` means full marks on the frozen suite only.

## Trust boundaries

- The **runner** receives one packet containing only a history-free repository snapshot, a neutral task, and optionally a sealed runtime copy of the skill. Use a fresh task for every packet.
- The **judge** receives candidate and baseline files, patch, task/scope, rubric, machine evidence and packet-local verification logs. Use a different fresh task. Variant identity is not intentionally supplied; known skill names and private paths are redacted from reports/logs. This is best-effort anonymization, not proof that arbitrary code or output reveals no identity.
- The **harness** checks only facts it can establish: baseline health, verification exits, protected and allowed paths, patch hygiene, source-checkout drift, and skill-package tampering.
- The **author** keeps `control/`, the suite, and private bars out of runner and judge contexts.

A sandbox is still required to prevent absolute-path reads or writes. Give each runner only its packet as the writable root. The post-run source-state check detects leakage into the source checkout, but cannot prove that no external path was read.

Keep `control/` author-only, including read access. Hashes detect drift relative to trusted records; they are not signatures and do not defend against someone who can rewrite both evidence and hashes. Stop runners before collection. Inspect judge packets before dispatch; an identifying packet must not be called blind. Fix the fixture and prepare a new run instead of editing sealed evidence.

Verification inherits the host environment. The harness does not sandbox commands, restrict network access or contain subprocess descendants. Run repository checks only in an appropriately isolated environment without secrets.

## Files

- `harness.py` — dependency-free Python 3.10+ runner.
- `examples/suite.example.json` — author-side task structure and variants; never send the full suite to a runner.
- `examples/bars.example.json` — private outcome bars and scoring dimensions.
- `schema/*.schema.json` — contracts for suites, bars, and judgments.
- `tests/test_harness.py` and `tests/test_integrity.py` — end-to-end and regression tests using temporary repos and synthetic judgments, not AI quality ratings.
- `evals.json` and `fixtures/` — the author-side case inventory; never runner input.

## 1. Design a suite

Copy both example JSON files outside the target repositories. Keep answers, smells, hidden checks, and known defects out of the suite's `task` field.

Each case must use a committed Git revision and at least one verification command. Commands are argument arrays, never shell strings. Set `expose_to_runner` to `false` for a harness-only check. Use:

- typical repositories from the real workload;
- edge cases with conflicting local conventions or sparse evidence;
- adversarial cases where attractive cleanup would break behavior;
- a final private holdout that was not used to edit the skill.

`protected_paths` are hard exclusions. When `allowed_paths` is non-empty, any changed file outside those patterns is a hard failure.

Patterns are case-sensitive Python `fnmatch`, not Git pathspecs: `*` crosses `/`, and `**/*.py` does not match root-level `app.py`. Use explicit root and subtree patterns. A matched directory prefix includes descendants. These scope constraints are disclosed to runners, not treated as hidden answers.

The task must identify the actual feature paths or rehabilitation scope. A history-free repository does not tell a runner which prior change set needs cleanup. Exposed verification commands include cwd and env settings; do not put secrets in them.

External checker files and tool installations are not bundled or content-hashed. Keep them immutable in an author-controlled environment and record their versions/hashes separately. Frozen argv alone does not freeze a program. Use trusted checks outside candidate control for critical contracts and inspect test diffs; exit code zero does not prove coverage was not weakened.

## 2. Validate and prepare

```text
python evals/harness.py validate --suite path/to/suite.json --bars path/to/private-bars.json
python evals/harness.py prepare --suite path/to/suite.json --bars path/to/private-bars.json --out path/to/new-run
```

Use `--skill candidate=path/to/skill` to override a variant path without changing the suite. `prepare`:

1. resolves every case to an exact commit;
2. exports raw Git tree files without branches or earlier commits by default, retaining tracked files even when ignore/export-ignore rules match them;
3. creates a new one-commit repository per run;
4. removes `evals/` from every skill copy and hashes the remaining runtime package;
5. runs baseline verification once per case;
6. freezes suite, private bars, rubric, baseline and runtime skills under `control/prepared/`, then emits opaque packet IDs in `run/dispatch.json`.

Later phases use frozen inputs, not live originals. Editing an original suite or skill does not change an already prepared run. Optional `--bars` on later commands checks consistency only. Runs are tied to the exact harness file hash.

Do not give runners `run/control/`. `--skip-baseline` exists for diagnosis, but makes certification impossible.

Set a case's `history` to `ancestors` only when repository history is part of the capability being tested. That mode constructs a temporary repository containing the selected commit and its ancestors only; other branches, tags, reflogs, and future commits are not copied. The default `none` mode remains the stricter choice for cases that do not require history.

Supported snapshots contain regular files, UTF-8 path names, arbitrary file bytes and Git executable modes. On Windows, represent executable-mode changes in the index. Symlinks and submodules are explicitly rejected. LFS hydration, checkout filters, sparse checkout and nested repositories need separate adapters and are not validated here. Snapshot files contain Git blob bytes, not filter-transformed working-tree bytes. Additional platform path constraints may reject a fixture.

## 3. Run blind packets

For every entry in `dispatch.json`, start a fresh context-free agent and provide only that packet's `prompt.md` and packet directory. Do not mention evaluation criteria, suspected defects, other cases, or expected results.

Keep model, reasoning setting, tools, time budget, and retry policy equivalent across variants. Fill `run-metadata.json` when telemetry is available. One retry is a new run, not a continuation that replaces a failed sample.

Null metadata means unavailable, not zero. Record experimental conditions outside runner-editable metadata as well; the harness cannot attest that the skill was used or settings were equivalent.

## 4. Collect evidence

```text
python evals/harness.py collect --run path/to/run
```

Collection captures candidate files under `control/collections/<packet-id>/`, compares them against the frozen baseline and records deterministic gates. Committed, staged, unstaged and non-ignored untracked changes are included without altering the runner's index. Baseline paths remain in scope even if subsequently ignored. New ignored build products are excluded; do not use them as the product being evaluated.

Patch bytes bypass text conversion. Applying the patch to the baseline index must reconstruct the captured candidate tree. Verification runs in a separate temporary repository populated from the captured files, not the runner workspace. Checks must bootstrap required dependencies in that disposable workspace: ignored directories installed by the runner are not copied.

Verification that changes or adds non-ignored source makes the attempt invalid; ignored build outputs are permitted. Failed/skipped/mutating baselines are invalid. A failed or timed-out candidate check is a failure; use logs to investigate environmental causes. Missing executables or filesystem errors stop the phase without a complete index, preventing certification. Environment diagnosis is not automatic.

Judge and score consume the same frozen collection. Later workspace/report edits cannot change the judged artifact; changes to captured evidence are rejected. Partial or completed collections cannot be overwritten. If a phase is interrupted, retain it for diagnosis and prepare a new run; resume/force is not implemented. Never silently discard failed samples from a claim.

## 5. Prepare independent judgments

```text
python evals/harness.py judge --run path/to/run --bars path/to/private-bars.json
```

Dispatch every entry in `run/judge/dispatch.json` to a fresh judge. Give it only its anonymous judge packet. The judge must write the requested `judgment.json`, cite patch or report evidence, and distinguish a bad artifact from a broken case.

Grant read access only to that packet and write access only to `judgment.json`. The packet includes `baseline/`, `repository/`, `artifact.patch`, `task.json`, `scoring.md`, `runner-report.md`, `evidence.json` and referenced `verification-logs/`.

Every required bar ID must appear exactly once: `outcome`, each `principle-N`, and each `smell-N`, derived from the frozen bar order. For a smell, pass means absence. All dimensions require scores and evidence. An overall pass with a failed bar, hard failure or zero dimension is rejected, as are missing/duplicate bars and dimensions. The script validates evidence structure, not its truth: independent semantic review remains necessary.

Bars describe outcomes and failure smells at the level a competent maintainer can judge. Do not encode the expected patch, exact symbol list, or a checklist that tells the runner which edits to make. Exact assertions belong only to genuine conformance tasks.

## 6. Score and interpret

```text
python evals/harness.py score --run path/to/run --bars path/to/private-bars.json
```

The harness creates `scorecard.json` and `report.md`. A variant is certified only when:

- every expected artifact was judged;
- the suite used at least the required repetitions;
- no hard failure or invalid case occurred;
- every artifact passed the outcome bar;
- pass-rate and minimum-rating thresholds were met.

The exact case/variant/repetition set is checked against the manifest; repeated index entries cannot substitute for distinct samples. Collected and judge evidence hashes are checked; judgment hashes are recorded in the scorecard.

`certified` means configured thresholds were met, not universal quality, actual blinding or judge independence. A one-repetition configuration is permitted for self-tests, not adequate release evidence. Threshold comparisons use exact rational arithmetic; displayed ratings/averages use floating point and may round. Full-mark flags require every dimension score to be 4, not a display rounded to 10. Failed/invalid artifacts have no quality rating, so averages must be read alongside failure/invalid counts.

Prefer minimum, pass rate, and dispersion over a flattering mean. Compare candidate and baseline under equivalent settings. Treat token totals as cost telemetry only; lower cost never offsets a semantic failure.

Token totals include observed values only; `tokens_*_observed_artifacts` records coverage. A partial total is not the full cost of a run.

## Release discipline

Use calibration cases to find gaps, then rerun the entire suite after every skill edit. Keep the final holdout sealed until the release candidate is frozen. Promote failures from real use into new regression cases, but periodically audit the suite for stale bars, duplicated patterns, and cases the skill should not be forced to satisfy.

Run deterministic tests with `python -B -m unittest discover -s evals/tests -v`. They verify harness behavior, cryptographic hash integrity, and tamper-detection invariants.

Implementation references: Git's [index input format](https://git-scm.com/docs/git-update-index), [raw object hashing](https://git-scm.com/docs/git-hash-object) and [diff/text conversion](https://git-scm.com/docs/git-diff); Python's [binary versus text subprocess streams](https://docs.python.org/3/library/subprocess.html). These informed byte-preserving snapshots, not claims about skill quality.
