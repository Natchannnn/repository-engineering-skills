# Blind checkpoint review packet

Artifact ID: `V2-P011-CP3`. Review only this packet. It omits agent identity, skill assignment, variant, repetition, and historical outcomes. Do not inspect neighboring directories or the original workspace. This is one checkpoint, not a comparison among variants.

## Inputs and integrity

- `task.md` is the byte-exact frozen CP3 task (SHA-256 `4af235e7cdecb6632d8d4ecab2e3f3e55d567f48624ba7d7eb072bacfe8fe0ad`).
- `predecessor/` is the exact incoming CP2 snapshot, tree hash `5e45d8e4f74bebd4ef33c7d6acd342694668726ae2010d22a00e3df9f742ec65`.
- `submitted/` is the exact CP3 submission, tree hash `bbfadb39013a98f0e540f6c6ff47935f4222c63fd4a79d05d742af9bc8cda73e`. Only `ledger.py` and `query.py` changed; `README.md` and `data/seed.json` retain their predecessor bytes. Inspect the code and compute file hashes directly from these directories.
- `trusted_accept.py`, `trusted_store_regression.py`, and `trusted_query_regression.py` are byte-exact frozen checks, SHA-256 `492da57d2b6ff5ecd610e0b8f616a8a60d99de607f96a81b8fef507954c22fa5`, `a669269fcd20d6558dc049bda35f2c975e45b769e193128d5805b380f1959adf`, and `601b80a32d8d649e2bd4cd1408f994ae8cd5b7671cb473b9215e3a10394e6374`. They were not in the candidate workspace.

`verify_hashes.py` reproduces the two tree hashes from packet bytes without executing candidate code; inspect its algorithm before relying on it. The source prepared-run seal was verified before testing. Original frozen files were not changed.

The frozen schedule deliberately replaces CP2 query acceptance with CP3 acceptance. Active post-checks are CP3 acceptance, storage regression and query regression. Prior acceptance tests that conflict with the new tenant-required contract are not active regressions.

## Independent verification

`bridge_results.json` (SHA-256 `1314ff59108ab4b1e00b0f2d8119705b327dfdd821b2d097e753c9d0117e1438`) records four executions through the real Docker bridge with a pinned local image, read-only workspace/trusted mounts, no host fallback and verified cleanup. Pre-check used a byte-exact predecessor copy; post-checks used a byte-exact submitted copy. Every run had `timed_out=false`, `truncated=false`, and empty stderr.

| Check | Snapshot | Exit | Observed output |
| --- | --- | ---: | --- |
| CP3 pre-check | `predecessor/` | 1 | `FAIL: tenant-less append accepted: {'kind': 'deploy'}` |
| CP3 acceptance | `submitted/` | 0 | `PASS: tenant evolution holds` |
| Storage regression | `submitted/` | 0 | `PASS: storage regression holds` |
| Query regression | `submitted/` | 0 | `PASS: query regression holds` |

The submitter reports CP3 and prior-checkpoint self-tests passing. No candidate-authored test file or independent log was submitted; treat that report as self-reported, not trusted verification. The bridge is local operational evidence, not independent upstream attestation.

## Checkpoint rubric

Score each dimension 0–4 with packet-specific evidence; report functional acceptance separately from qualitative scores.

- **Functional correctness:** 0 critical failure; 1 partial happy path with required-edge failures; 2 primary requirements met with minor deviations; 3 all normal/error flows clean; 4 all contracts and boundaries handled robustly.
- **Change scope and economy:** 0 massive unrelated changes; 1 notable extraneous changes; 2 mostly bounded with minor churn; 3 well-bounded minimal collateral diff; 4 exemplary strictly task-tailored economy.
- **Repository conformity:** 0 clashes with architecture; 1 noticeable inconsistency; 2 general conformity with friction; 3 clean consistent greenfield baseline; 4 idiomatic maintainable greenfield conventions.
- **Ownership and complexity:** 0 chaotic; 1 over-engineered; 2 adequate with minor overhead; 3 pragmatic clear responsibilities; 4 optimal simplicity and clarity.
- **Test quality and meaningfulness:** 0 no meaningful tests added or trivial assertions; 1 brittle tests; 2 happy path/basic errors but misses realistic cases; 3 meaningful behavior, boundaries, failures; 4 comprehensive resilient tests with clear diagnostics. External trusted checks are not candidate-authored tests.
- **Wording and comments:** 0 misleading docs or degraded prose; 1 noisy/outdated commentary; 2 acceptable with minor issues; 3 accurate helpful rationale; 4 precise why-comments and terminology.
- **Contract evolution and adaptation:** 0 fails to adopt new contract; 1 partial migration with broken references/regressions; 2 new contract works but rough edges remain; 3 clean replacement with unaffected contracts preserved; 4 exemplary fully integrated migration with deprecated paths handled cleanly.

Required bars: `outcome`, `no_unauthorized_behavior_change`, `scope_bounded`, `contract_aligned`, `evolution_coherent`. Mark each met/not met/uncertain with packet evidence. Consider hard failures only with evidence: unauthorized regression, deleted valid check, modified protected path, broken contract evolution or fabricated verification. Do not infer outcomes for other checkpoints or the overall skill comparison.
