# Changelog

All notable user-facing changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-09-29

### Fixed
- Streamlined sentence structures in both `SKILL.md` files, replacing indirect phrasing with direct imperative guidance.
- Corrected Pilot 1 outcome from 9/9 to 7/9 PASS (A0 3/3, A1 2/3, A2 2/3; Runs 4-5 FAIL on schema validation due to test-ID formatting) to match `PROTOCOL.md` and evidence records.
- Clarified Phase 2 27/27 as a ceiling effect where tasks were too simple to differentiate arms statistically.
- Clarified archive verification status as sealed in Windows path order.
- Fixed Phase 2 self-audit docstring from 17 to 35 tests (15 D2 + 9 R2A + 11 R2B) and clarified package test numbering.

### Added
- Unified skill packaging: `metadata.version 0.3.0` and MIT license for both skills, including `repo-native-refactor/agents/openai.yaml`.
- Canonical shared contracts (`docs/contracts-canonical.md` + `scripts/sync-shared.py` with `--check`) to eliminate `str` vs `Path` duplication drift.
- Few-shot guidance: `refactor-examples.md` (R0–R4) and `migration-examples.md` (atomic vs transitional) plus `Reference Routing` table for refactor.
- Tooling: `scripts/classify-risk.py` triage helper, `scripts/install-skills.sh` POSIX mirror, `requirements-test.txt` pinned `jsonschema==4.23.0`, Linux harness CI job.
- Runtime payload expanded to 23 verified payload files (shared contracts, examples, companion guidance, and refactor adapter).
- Claude plugin marketplace manifests (`.claude-plugin/marketplace.json` + per-skill `plugin.json`), passing validation against plugin schemas.
- Documented cross-model validation findings, fixture boundaries, and Batch E held-out adversarial tests.

### Changed
- Streamlined README to focus on user workflow: unified installation instructions, direct guidance, and moved detailed evaluation telemetry to documentation links.
- Updated demo animation to demonstrate full evaluation harness verification across Demo 1, Demo 2, and the 41-test acceptance suite.
- Replaced manual copy snippets with Skills CLI instructions and distinguished installation checks from host behavior and harness tests.
- Trigger phrases extended after automated routing probes; residuals documented in `evals/trigger.md`.

### Docs
- Restructured README: concise quickstart, clear situation-to-skill table, and example prompts.
- New `docs/demo/` guide with standalone verification steps.
- Multi-agent install matrix (`claude-code`, `cursor`, `opencode`, `gemini-cli`) with byte spot-checks, plus `docs/launch-kit.md` paste-ready blurbs.
- Batch C evidence: `runs/realworld-self` review with 2 fixes, `runs/realworld-colorama` regression test run, `runs/realworld-six` negative control, plus `Dockerfile` + `docs/reproduce.md` one-command Linux reproduction.
- CI Python standardized on 3.12 with Linux harness job and shared-contracts sync gate.

## [0.1.0] - 2026-09-26

### Added
- **`repo-foundation` skill:**
  - Standardized repository lifecycle modes: Bootstrap, Continue, Evolve, and Continuity.
  - Public contract preservation rule preventing inadvertent type drift across exposed interfaces.
  - Proportionate, behavior-driven testing guidance.
  - Failure invariants and atomic state preservation principles for multi-session handoffs.
  - Living documentation synchronization guidance.
- **`repo-native-refactor` skill:**
  - Semantic risk bands from R0 (mechanical cleanup) through R4 (critical boundaries).
  - Minimal intervention and evidence gate: refactoring requires demonstrated operational consequences.
  - Cost-benefit semantic DRY consolidation rules.
  - Repository prose audit guidelines distinguishing comments from executable code.
  - Scalable completion reporting.
- **Foundation Evaluation Harness:**
  - Multi-checkpoint runner supporting `validate`, `snapshot`, `verify`, and `score` commands.
  - Deterministic byte-exact snapshot engine with SHA-256 tree hashing.
  - Atomic destination replacement with staging on destination filesystem and automatic rollback on I/O failure.
  - Exact rational scoring using `fractions.Fraction` to prevent false certifications.
  - Structural JSON Schema metaschema validator conforming to Draft 7 / Draft 2020-12.
- **Evaluation Suite & Archives:**
  - 31 sealed historical evidence packets in `evals-suite/` verified with bit-exact SHA-256 tree hashes.
  - 59 deterministic unit tests (26 for foundation harness, 33 for refactor harness including Windows 8.3 short-path resolution).
  - GitHub Actions CI workflow for automated Windows / Python 3.14 verification.
