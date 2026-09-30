# Reproduce the green state in one command

```sh
docker build -t reskills . && docker run --rm reskills
```

What that runs, in order: shared-contracts sync check, 3 isolated skill-resource checks,
foundation asset validation, 30 foundation harness/example tests, 36 refactor
harness/example tests, and the demo acceptance
suite (`scripts/test_demos.py`). Tested on an image built from this commit; expect
exit 0 end to end.

Out of scope on purpose:

- Windows-only PowerShell suites (`test-installer.ps1`, `test-package.ps1`,
  `test-demos.ps1`, `verify-archive.ps1`) need Windows + PowerShell.
  `scripts/verify_archive.py` is a cross-platform twin of the archive runner for
  Windows use (same 31/31 result there).
- Archive packets do NOT verify on Linux, by design of their sealed hashes: the
  expected hashes encode Windows `Path` sort order (case-insensitive), while Linux
  sorts the same names byte-wise. Bytes are identical; order differs. Found while
  wiring this image; frozen verifiers stay untouched, so this stays Windows-only.
  See `docs/evaluation.md` for the full matrix.
- Live pilot reruns (`pilots/...`) need agent hosts and model access; the container
  only runs deterministic checks, same as CI's `linux-harness` job.
