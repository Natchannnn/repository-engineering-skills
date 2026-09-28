# Changelog

All notable user-facing changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed
- Corrected Pilot 1 outcome from 9/9 to 7/9 PASS (A0 3/3, A1 2/3, A2 2/3 — Runs 4-5 FAIL on strict Test ID schema) to match `PROTOCOL.md` §5-6 and evidence JSONs.
- Clarified Phase 2 27/27 as ceiling effect with no measurable skill advantage, and CP2/CP3 ablations as n=1 single-judge case studies.
- Fixed Phase 2 self-audit docstring from 17 to 35 tests (15 D2 + 9 R2A + 11 R2B) and clarified package test numbering.

### Added
- Unified skill packaging: `metadata.version 0.2.0` + MIT for both skills, added `repo-native-refactor/agents/openai.yaml`.
- Canonical shared contracts (`docs/contracts-canonical.md` + `scripts/sync-shared.py` with `--check`) to eliminate `str` vs `Path` duplication drift.
- Few-shot guidance: `refactor-examples.md` (R0–R4) and `migration-examples.md` (atomic vs transitional) plus `Reference Routing` table for refactor.
- Tooling: `scripts/classify-risk.py` triage helper, `scripts/install-skills.sh` POSIX mirror, `requirements-test.txt` pinned `jsonschema==4.23.0`, Linux harness CI job.
- Runtime payload expanded 17 → 22 files (shared contracts + examples + refactor adapter).

### Changed
- Replaced manual copy snippets with Skills CLI instructions and distinguished installation checks from host behavior and harness tests.
- Humanized skill wording: shorter router descriptions, field notes with real failure links, author-notes sections, slop sweep (`surgical`/`high-leverage`/`additionally`/`comprehensive`).

### Docs
- README hero with badges, 60-second try, honest 34/36 PASS count, and `What I got wrong`.
- New `docs/demo/` guide (GIF kept out of git to stay lean) and `ADOPTERS.md` + issue templates.
- CI Python 3.14 → 3.12 matrix (Windows full + Linux harness) with shared-contracts sync gate.

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
