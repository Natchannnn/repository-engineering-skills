#!/usr/bin/env python3
"""Sync canonical shared contracts into both installable skills.

Canonical source: docs/contracts-canonical.md
Destinations:
- repo-foundation/references/shared-contracts.md
- repo-native-refactor/references/shared-contracts.md

Parity guard: repo-foundation/references/evolution.md §4 must keep the
tests/callers rank (drift-01 regression). It is checked, not overwritten.

Usage:
  python scripts/sync-shared.py         # copy + verify
  python scripts/sync-shared.py --check # fail if copies drift (for CI)
"""
from __future__ import annotations
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "docs" / "contracts-canonical.md"
DESTS = [
    ROOT / "repo-foundation" / "references" / "shared-contracts.md",
    ROOT / "repo-native-refactor" / "references" / "shared-contracts.md",
]

HEADER = "<!-- AUTO-GENERATED from docs/contracts-canonical.md — do not edit by hand. Run python scripts/sync-shared.py -->\n\n"

# Parity guard (drift-01): this exact rank must exist in evolution.md §4.
# Compared case-insensitively against the canonical §2 rank 5 wording.
PARITY_FILE = ROOT / "repo-foundation" / "references" / "evolution.md"
PARITY_NEEDLE = "relevant tests, schemas, callers"


def check_parity() -> int:
    text = PARITY_FILE.read_text(encoding="utf-8").lower()
    if PARITY_NEEDLE not in text:
        print(
            f"PARITY-FAIL: {PARITY_FILE.relative_to(ROOT)} lost the tests/callers "
            "rank (see adversarial/drift-01-tests-vs-local/case.md)",
            file=sys.stderr,
        )
        return 1
    print(f"OK: hierarchy parity holds in {PARITY_FILE.relative_to(ROOT)}")
    return 0


def build_payload() -> str:
    return HEADER + CANONICAL.read_text(encoding="utf-8").lstrip("\ufeff")


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if not CANONICAL.is_file():
        print(f"Missing canonical: {CANONICAL}", file=sys.stderr)
        return 2
    payload = build_payload()
    check_only = "--check" in sys.argv
    failed = check_parity()
    for d in DESTS:
        if check_only:
            if not d.is_file() or d.read_text(encoding="utf-8") != payload:
                print(f"DRIFT: {d.relative_to(ROOT)} != canonical", file=sys.stderr)
                failed += 1
            else:
                print(f"OK: {d.relative_to(ROOT)} in sync ({sha(d)[:12]})")
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_text(payload, encoding="utf-8", newline="\n")
            print(f"SYNCED: {d.relative_to(ROOT)} ({sha(d)[:12]})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
