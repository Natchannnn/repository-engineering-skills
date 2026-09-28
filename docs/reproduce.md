# Reproduce the green state in one command

```sh
docker build -t reskills . && docker run --rm reskills
```

What that runs, in order: shared-contracts sync check, foundation asset validation,
26 foundation harness tests, 33 refactor harness tests, and the demo acceptance
suite (`scripts/test_demos.py`). Tested on an image built from this commit; expect
exit 0 end to end.

Out of scope on purpose:

- Windows-only PowerShell suites (`test-installer.ps1`, `test-package.ps1`,
  `verify-archive.ps1`, `test-demos.ps1`) need Windows + PowerShell. Run those on
  a Windows box per `docs/evaluation.md`.
- Live pilot reruns (`pilots/...`) need agent hosts and model access; the container
  only runs deterministic checks, same as CI's `linux-harness` job.
