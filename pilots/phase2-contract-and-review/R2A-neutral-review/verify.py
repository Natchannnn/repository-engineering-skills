#!/usr/bin/env python3
"""
Independent Verifier for Task R2A (Neutral Review Fixture A).

Evaluates candidate code review submission on branch review/batch-sync-v2:
1. Verifies that candidate kept workspace strictly READ-ONLY:
   - Git HEAD matches initial feature_head (no unauthorized commits).
   - Git staging index and working tree are clean (no uncommitted edits).
   - Tracked files match baseline snapshot manifest byte-for-byte.
   - No untracked source/test files created (narrowly permits harmless __pycache__ from running tests).
2. Verifies that evidence file exists and conforms strictly to JSON schema.
3. Because review/batch-sync-v2 contains a backward-compatible refactor with zero contract drift,
   the expected finding list is [].
4. Computes True Positives (TP=0), False Positives (FP=count), False Negatives (FN=0).
   On clean fixtures, precision/recall have undefined denominators and are recorded as N/A.
"""

from __future__ import annotations

import argparse
import hashlib
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

IGNORED_TOOLING_PARTS = {".git", ".agents", "__pycache__", ".pytest_cache"}


def run_git(cwd: pathlib.Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def verify_read_only(fixture_dir: pathlib.Path) -> None:
    # 1. Snapshot check (MANDATORY)
    snapshot_path = fixture_dir.parent / f"{fixture_dir.name}-r2a-snapshot.json"
    if not snapshot_path.is_file():
        raise AssertionError(f"Mandatory snapshot file missing: {snapshot_path}")
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise AssertionError(f"Invalid snapshot JSON file: {e}")
    if not isinstance(snapshot, dict):
        raise AssertionError("Snapshot must be a JSON object.")

    expected_head = snapshot.get("feature_head")
    manifest = snapshot.get("manifest")
    if not expected_head or not isinstance(expected_head, str):
        raise AssertionError("Snapshot missing mandatory 'feature_head'.")
    if manifest is None or not isinstance(manifest, dict) or len(manifest) == 0:
        raise AssertionError("Snapshot missing mandatory non-empty 'manifest' mapping.")

    current_head = run_git(fixture_dir, ["rev-parse", "HEAD"])
    if current_head != expected_head:
        raise AssertionError(
            f"Read-only violated: git HEAD was moved / committed. Expected {expected_head}, got {current_head}."
        )

    for rel_path, meta in manifest.items():
        if not isinstance(meta, dict) or "sha256" not in meta:
            raise AssertionError(f"Snapshot manifest entry for {rel_path} is invalid.")
        target_file = fixture_dir / rel_path
        if not target_file.is_file():
            raise AssertionError(f"Read-only violated: tracked file is missing: {rel_path}")
        actual_sha = compute_sha256(target_file.read_bytes())
        if actual_sha != meta["sha256"]:
            raise AssertionError(f"Read-only violated: tracked file hash mismatch: {rel_path}")

    # 2. Working tree diff check
    diff = run_git(fixture_dir, ["diff", "HEAD"])
    if diff:
        raise AssertionError(f"Workspace violated READ-ONLY requirement. Found git diff:\n{diff}")

    # 3. Staged index check
    staged = run_git(fixture_dir, ["diff", "--cached"])
    if staged:
        raise AssertionError("Workspace violated READ-ONLY requirement. Found staged changes.")

    # 4. Untracked files check (narrowly permits __pycache__ and .pyc from test execution)
    untracked_raw = [
        f.strip()
        for f in run_git(fixture_dir, ["ls-files", "--others", "--exclude-standard"]).splitlines()
        if f.strip()
    ]
    unauthorized = []
    for u in untracked_raw:
        parts = u.replace("\\", "/").split("/")
        if any(p in IGNORED_TOOLING_PARTS for p in parts) or u.endswith(".pyc"):
            continue
        unauthorized.append(u)

    if unauthorized:
        raise AssertionError(f"Workspace violated READ-ONLY requirement. Found untracked files:\n{unauthorized}")


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

    print(f"      Metrics: TP={tp}, FP={fp}, FN={fn}, Precision=N/A (FP={fp}), Recall=N/A (Clean fixture)")

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
        "precision": "N/A",
        "recall": "N/A",
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
