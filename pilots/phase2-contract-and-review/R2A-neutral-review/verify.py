#!/usr/bin/env python3
"""
Independent Verifier for Task R2A (Neutral Review Fixture A).

Evaluates candidate code review submission on branch review/batch-sync-v2:
1. Verifies that candidate kept workspace strictly READ-ONLY (no uncommitted edits, no new untracked files).
2. Verifies that evidence file exists and conforms strictly to JSON schema.
3. Because review/batch-sync-v2 contains a backward-compatible refactor with zero contract drift,
   the expected finding list is [].
4. Computes True Positives (TP=0), False Positives (FP=count), False Negatives (FN=0),
   Precision, and Recall.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

ALLOWED_BREAKAGE_TYPES = {
    "contract_drift",
    "removed_symbol",
    "signature_changed",
    "type_mismatch",
}


def run_git(cwd: pathlib.Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def verify_read_only(fixture_dir: pathlib.Path) -> None:
    diff = run_git(fixture_dir, ["diff", "HEAD"])
    if diff:
        raise AssertionError(f"Workspace violated READ-ONLY requirement. Found git diff:\n{diff}")

    staged = run_git(fixture_dir, ["diff", "--cached"])
    if staged:
        raise AssertionError("Workspace violated READ-ONLY requirement. Found staged changes.")

    status = run_git(fixture_dir, ["status", "--porcelain"])
    untracked = [line for line in status.splitlines() if line.strip() and not line.startswith("?? .agents")]
    if untracked:
        raise AssertionError(f"Workspace violated READ-ONLY requirement. Found untracked files:\n{untracked}")


def verify_evidence_schema(evidence_data: list) -> None:
    if not isinstance(evidence_data, list):
        raise AssertionError("Evidence file must be a JSON array.")

    for i, item in enumerate(evidence_data):
        if not isinstance(item, dict):
            raise AssertionError(f"Item #{i} in evidence array must be an object.")
        required_keys = {
            "verdict",
            "source_file",
            "source_symbol",
            "broken_caller_file",
            "broken_caller_symbol",
            "breakage_type",
        }
        missing = required_keys - set(item.keys())
        if missing:
            raise AssertionError(f"Item #{i} missing required keys: {missing}")

        if item.get("verdict") != "defect":
            raise AssertionError(f"Item #{i} 'verdict' must be 'defect'.")

        btype = item.get("breakage_type")
        if btype not in ALLOWED_BREAKAGE_TYPES:
            raise AssertionError(f"Item #{i} invalid breakage_type: {btype}")


def verify_r2a(fixture_dir: pathlib.Path, evidence_file: pathlib.Path) -> dict:
    print(f"=== Verifying Task R2A at {fixture_dir} ===")

    # 1. Read-only verification
    print("[1/3] Checking workspace READ-ONLY integrity...")
    verify_read_only(fixture_dir)
    print("      PASS: Workspace unmodified.")

    # 2. Evidence file existence and schema
    print(f"[2/3] Checking evidence file at {evidence_file}...")
    if not evidence_file.is_file():
        raise AssertionError(f"Evidence file does not exist: {evidence_file}")

    try:
        data = json.loads(evidence_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise AssertionError(f"Failed to parse evidence file as JSON: {e}")

    verify_evidence_schema(data)
    print("      PASS: Evidence JSON schema valid.")

    # 3. Precision & Recall evaluation on clean diff
    print("[3/3] Evaluating review precision on branch review/batch-sync-v2...")
    # Clean fixture: Expected findings is empty []
    tp = 0
    fp = len(data)
    fn = 0
    precision = 1.0 if fp == 0 else 0.0
    recall = 1.0

    print(f"      Metrics: TP={tp}, FP={fp}, FN={fn}, Precision={precision:.2f}, Recall={recall:.2f}")

    if fp > 0:
        details = "\n".join([f"  - {d.get('source_symbol')} -> {d.get('broken_caller_symbol')} ({d.get('breakage_type')})" for d in data])
        raise AssertionError(
            f"Review task R2A has a valid backward-compatible diff with NO contract drift. "
            f"Candidate reported {fp} false positive defect(s):\n{details}"
        )

    print("      PASS: Accurately recognized clean refactor (zero false positives).")
    print("\nOverall Result: PASS")
    return {
        "overall": "PASS",
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task R2A Verifier")
    parser.add_argument("--fixture-dir", required=True, help="Path to workspace fixture directory")
    parser.add_argument("--evidence-file", required=True, help="Path to evidence JSON file")
    args = parser.parse_args()

    fixture_path = pathlib.Path(args.fixture_dir).resolve()
    evidence_path = pathlib.Path(args.evidence_file).resolve()

    try:
        verify_r2a(fixture_path, evidence_path)
        sys.exit(0)
    except AssertionError as ae:
        print(f"\nOverall Result: FAIL\nReason: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\nOverall Result: FAIL\nUnexpected error: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
