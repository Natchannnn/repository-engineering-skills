#!/usr/bin/env python3
"""Triage helper: suggest R0-R4 risk band for a change description.

This is a triage hint only — it does not decide. The skill's
`semantic-risk.md` justification gate still governs any mutation.

Usage:
  python scripts/classify-risk.py --files "src/auth.py" --keywords "auth,retry"
  python scripts/classify-risk.py --diff-stat "3 files changed, 120 insertions"
"""
from __future__ import annotations
import argparse

R4 = {"auth", "permission", "crypto", "migration", "persist", "durability", "secret", "token"}
R3 = {"retry", "fallback", "transaction", "serial", "async", "concurr", "timeout", "idempot"}
R2 = {"rename", "extract", "predicate", "refactor", "move", "ownership"}


def classify(files: str, keywords: str) -> str:
    blob = f"{files} {keywords}".lower()
    if any(k in blob for k in R4):
        return "R4 — Critical Boundary: read semantic-risk.md stop conditions, maximum conservatism, preserve + report if evidence missing."
    if any(k in blob for k in R3):
        return "R3 — Semantic: never mass-rewrite without explicit instruction + verified tests. See error-reliability.md."
    if any(k in blob for k in R2):
        return "R2 — Contextual Structural: read semantic-risk.md justification gate + refactor-examples.md R2."
    if "dead" in blob or "unused" in blob or "format" in blob:
        return "R0–R1 — Mechanical/Low: smallest check, verify affected tests, see refactor-examples.md R0–R1."
    return "R1 default — treat as Low Structural until a higher-band keyword is established. See finding-taxonomy.md."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--diff-stat", default="")
    a = ap.parse_args()
    print(classify(f"{a.files} {a.diff_stat}", a.keywords))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
