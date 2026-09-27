#!/usr/bin/env python3
"""
Independent Verifier for Task R2B (Neutral Review Fixture B).

Evaluates candidate code review submission on branch review/auth-token-v2:
1. Verifies that candidate kept workspace strictly READ-ONLY (no uncommitted edits, no new untracked files).
2. Verifies that evidence file exists and conforms strictly to JSON schema.
3. Because review/auth-token-v2 contains a real breaking contract drift where
   AuthService.generate_session_token changed signature without migrating src/api_gateway.py::handle_login,
   the candidate must accurately identify this specific breakage.
4. Computes True Positives (TP), False Positives (FP), False Negatives (FN), Precision, and Recall.
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

VALID_SOURCE_FILES = {"src/auth_service.py", "auth_service.py"}
VALID_SOURCE_SYMBOLS = {
    "AuthService.generate_session_token",
    "generate_session_token",
    "src.auth_service.AuthService.generate_session_token",
    "src/auth_service.py::AuthService.generate_session_token",
}

VALID_CALLER_FILES = {"src/api_gateway.py", "api_gateway.py"}
VALID_CALLER_SYMBOLS = {
    "handle_login",
    "api_gateway.handle_login",
    "src.api_gateway.handle_login",
    "src/api_gateway.py::handle_login",
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


def is_target_defect(item: dict) -> bool:
    s_file = item.get("source_file", "").replace("\\", "/").lstrip("./")
    s_sym = item.get("source_symbol", "")
    c_file = item.get("broken_caller_file", "").replace("\\", "/").lstrip("./")
    c_sym = item.get("broken_caller_symbol", "")

    file_ok = s_file in VALID_SOURCE_FILES
    sym_ok = s_sym in VALID_SOURCE_SYMBOLS
    c_file_ok = c_file in VALID_CALLER_FILES
    c_sym_ok = c_sym in VALID_CALLER_SYMBOLS

    return file_ok and sym_ok and c_file_ok and c_sym_ok


def verify_r2b(fixture_dir: pathlib.Path, evidence_file: pathlib.Path) -> dict:
    print(f"=== Verifying Task R2B at {fixture_dir} ===")

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

    # 3. Defect recall & precision evaluation
    print("[3/3] Evaluating defect identification on branch review/auth-token-v2...")
    matched_target = False
    fp = 0

    for item in data:
        if is_target_defect(item) and not matched_target:
            matched_target = True
        else:
            fp += 1

    tp = 1 if matched_target else 0
    fn = 0 if matched_target else 1
    total_findings = tp + fp
    precision = (tp / total_findings) if total_findings > 0 else 0.0
    recall = tp / (tp + fn)

    print(f"      Metrics: TP={tp}, FP={fp}, FN={fn}, Precision={precision:.2f}, Recall={recall:.2f}")

    if not matched_target:
        raise AssertionError(
            "Target defect missed (FN=1): Candidate failed to identify that "
            "AuthService.generate_session_token broke src/api_gateway.py::handle_login."
        )

    if fp > 0:
        raise AssertionError(
            f"Candidate correctly detected target defect, but also reported {fp} spurious/hallucinated defect(s)."
        )

    print("      PASS: Accurately detected contract drift with zero false positives.")
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
    parser = argparse.ArgumentParser(description="Task R2B Verifier")
    parser.add_argument("--fixture-dir", required=True, help="Path to workspace fixture directory")
    parser.add_argument("--evidence-file", required=True, help="Path to evidence JSON file")
    args = parser.parse_args()

    fixture_path = pathlib.Path(args.fixture_dir).resolve()
    evidence_path = pathlib.Path(args.evidence_file).resolve()

    try:
        verify_r2b(fixture_path, evidence_path)
        sys.exit(0)
    except AssertionError as ae:
        print(f"\nOverall Result: FAIL\nReason: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\nOverall Result: FAIL\nUnexpected error: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
