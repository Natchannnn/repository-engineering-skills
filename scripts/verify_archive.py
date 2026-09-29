#!/usr/bin/env python3
"""Cross-platform port of scripts/verify-archive.ps1.

Runs every verify_hashes.py under evals-suite/ in isolated subprocesses and
requires exactly 31 verifiers. Exit non-zero on any failure.

Usage: python scripts/verify_archive.py   (from the repo root)
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

EXPECTED = 31


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    archive_root = repo_root / "evals-suite"
    if not archive_root.is_dir():
        print(f"Archive root directory not found at: {archive_root}", file=sys.stderr)
        return 2
    verifiers = sorted(archive_root.rglob("verify_hashes.py"))
    if len(verifiers) != EXPECTED:
        print(
            f"Expected {EXPECTED} archive verifiers; found {len(verifiers)}. "
            "Review inventory.",
            file=sys.stderr,
        )
        return 2
    for verifier in verifiers:
        proc = subprocess.run(
            [sys.executable, "-B", str(verifier)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if proc.returncode != 0:
            print(f"Archive verification failed: {verifier}", file=sys.stderr)
            print(proc.stdout, file=sys.stderr)
            return 1
    print(f"Verified {len(verifiers)}/{EXPECTED} archive packets successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
