# Changelog

All notable user-facing changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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
  - 58 deterministic unit tests (26 for foundation harness, 32 for refactor harness).
  - GitHub Actions CI workflow for automated Windows / Python 3.14 verification.
