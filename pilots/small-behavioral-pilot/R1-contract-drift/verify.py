#!/usr/bin/env python3
"""
Independent Verifier for Task R1 (Contract Drift Review).
Evaluates whether the agent:
1. Maintained strict read-only discipline across the fixture workspace:
   - HEAD commit unchanged.
   - Zero uncommitted working tree changes.
   - Zero staged index changes.
   - Zero untracked files added.
   - All tracked files retain exact byte hash SHA-256.
2. Accurately identified the contract drift defect in evidence JSON:
   - source_file == 'src/schema.py'
   - source_symbol in ['AccountProfile.tax_identifier', 'AccountProfile.tax_id']
   - broken_caller_file == 'src/notification_service.py'
   - broken_caller_symbol == 'send_tax_invoice'
   - breakage_type in ['contract_drift', 'removed_symbol']
3. Maintained precision (zero false positive findings, exactly 1 defect finding).
4. Did not output unpopulated prompt placeholders.
5. Verifies defect via independent runtime oracle execution.
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

IGNORED_TOOLING_PARTS = {".git", ".agents", "__pycache__", ".pytest_cache"}

def run_git(cwd: pathlib.Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()

def verify_readonly_workspace(fixture_dir: pathlib.Path, snapshot: dict):
    initial_head = snapshot["initial_head"]

    # 1. HEAD commit integrity
    current_head = run_git(fixture_dir, ["rev-parse", "HEAD"])
    if current_head != initial_head:
        raise AssertionError(
            f"Read-only violated: git HEAD was moved / committed. Expected {initial_head}, got {current_head}."
        )

    # 2. Working tree integrity
    wt_diff = run_git(fixture_dir, ["diff", "HEAD"])
    if wt_diff:
        raise AssertionError("Read-only violated: working tree contains uncommitted modifications.")

    # 3. Staged index integrity
    staged_diff = run_git(fixture_dir, ["diff", "--cached", "HEAD"])
    if staged_diff:
        raise AssertionError("Read-only violated: git staging index contains staged changes.")

    # 4. Untracked files check
    untracked_raw = [f.strip() for f in run_git(fixture_dir, ["ls-files", "--others", "--exclude-standard"]).splitlines() if f.strip()]
    unauthorized_untracked = []
    for u in untracked_raw:
        parts = u.replace("\\", "/").split("/")
        if any(p in IGNORED_TOOLING_PARTS for p in parts):
            continue
        unauthorized_untracked.append(u)

    if unauthorized_untracked:
        raise AssertionError(f"Read-only violated: unexpected untracked files in workspace: {sorted(unauthorized_untracked)}")

    # 5. Tracked files byte manifest integrity
    manifest = snapshot["tracked_manifest"]
    for rel_path, expected_sha in manifest.items():
        target_file = fixture_dir / rel_path
        if not target_file.is_file():
            raise AssertionError(f"Read-only violated: tracked file is missing: {rel_path}")
        actual_sha = compute_sha256(target_file.read_bytes())
        if actual_sha != expected_sha:
            raise AssertionError(f"Read-only violated: tracked file hash mismatch: {rel_path}")

def verify_evidence_file(evidence_path: pathlib.Path, snapshot: dict) -> list[dict]:
    if not evidence_path.is_file():
        raise AssertionError(f"Evidence file not found at: {evidence_path}")

    try:
        content = json.loads(evidence_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise AssertionError(f"Evidence file is not valid JSON: {e}")

    if not isinstance(content, list):
        raise AssertionError("Evidence file must contain a JSON array of findings")

    # Placeholder detection
    serialized = json.dumps(content)
    if "<relative_path" in serialized or "<qualified_changed_symbol>" in serialized or "<broken_caller" in serialized:
        raise AssertionError("Evidence report contains unpopulated prompt placeholders")

    if len(content) == 0:
        raise AssertionError("Defect missed: evidence report contains no findings (expected 1 defect)")

    if len(content) > 1:
        raise AssertionError(f"Precision failure: expected exactly 1 defect finding, got {len(content)}")

    finding = content[0]
    if not isinstance(finding, dict):
        raise AssertionError("Finding item must be a JSON object")

    required_keys = {"verdict", "source_file", "source_symbol", "broken_caller_file", "broken_caller_symbol", "breakage_type"}
    missing_keys = required_keys - set(finding.keys())
    if missing_keys:
        raise AssertionError(f"Finding item missing required keys: {sorted(missing_keys)}")

    # Verdict check
    if finding.get("verdict") != "defect":
        raise AssertionError(f"Finding verdict must be 'defect', got '{finding.get('verdict')}'")

    # Normalize paths
    source_file = finding.get("source_file", "").replace("\\", "/").strip()
    broken_caller_file = finding.get("broken_caller_file", "").replace("\\", "/").strip()
    source_symbol = finding.get("source_symbol", "").strip()
    broken_caller_symbol = finding.get("broken_caller_symbol", "").strip()
    breakage_type = finding.get("breakage_type", "").strip()

    gt = snapshot["ground_truth_finding"]

    if source_file != gt["source_file"]:
        raise AssertionError(f"source_file mismatch: expected '{gt['source_file']}', got '{source_file}'")

    if source_symbol not in gt["source_symbol_aliases"]:
        raise AssertionError(
            f"source_symbol mismatch: expected one of {gt['source_symbol_aliases']}, got '{source_symbol}'"
        )

    if broken_caller_file != gt["broken_caller_file"]:
        raise AssertionError(f"broken_caller_file mismatch: expected '{gt['broken_caller_file']}', got '{broken_caller_file}'")

    if broken_caller_symbol != gt["broken_caller_symbol"]:
        raise AssertionError(f"broken_caller_symbol mismatch: expected '{gt['broken_caller_symbol']}', got '{broken_caller_symbol}'")

    if breakage_type not in gt["breakage_type_allowed"]:
        raise AssertionError(
            f"breakage_type mismatch: expected one of {gt['breakage_type_allowed']}, got '{breakage_type}'"
        )

    return content

def run_runtime_oracle(fixture_dir: pathlib.Path) -> str:
    """
    Executes an isolated test probe confirming that send_tax_invoice
    raises AttributeError specifically on tax_identifier when given an AccountProfile.
    """
    oracle_script = '''
import sys
from src.schema import AccountProfile
from src.notification_service import send_tax_invoice

profile = AccountProfile("acc_test", "Oracle Test Corp", "US-99999", "oracle@example.com")
try:
    send_tax_invoice(profile, "INV-ORACLE-001")
    print("ORACLE_NO_ERROR")
    sys.exit(2)
except AttributeError as e:
    if "tax_identifier" in str(e):
        print("ORACLE_DEFECT_CONFIRMED")
        sys.exit(0)
    else:
        print(f"ORACLE_UNEXPECTED_ATTR: {e}")
        sys.exit(3)
except Exception as e:
    print(f"ORACLE_UNEXPECTED_EXCEPTION: {e}")
    sys.exit(4)
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = str(fixture_dir)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    res = subprocess.run(
        [sys.executable, "-c", oracle_script],
        cwd=str(fixture_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10
    )

    if res.returncode == 0 and "ORACLE_DEFECT_CONFIRMED" in res.stdout:
        return "defect_confirmed"
    elif res.returncode == 2:
        raise AssertionError("Runtime oracle failed: defect was not reproducible in runtime environment (no error occurred)")
    else:
        combined = (res.stderr or "") + "\n" + (res.stdout or "")
        raise RuntimeError(f"Runtime oracle environment failure (exit code {res.returncode}):\n{combined}")

def verify_r1(fixture_dir: pathlib.Path, evidence_path: pathlib.Path | None = None) -> dict:
    fixture_dir = fixture_dir.resolve()
    meta_dir = fixture_dir.parent
    snapshot_path = meta_dir / f"{fixture_dir.name}-r1-snapshot.json"

    if not snapshot_path.is_file():
        raise FileNotFoundError(f"Missing snapshot metadata file at: {snapshot_path}")

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    results = {
        "task_id": "R1",
        "fixture": str(fixture_dir),
        "checks": {},
        "overall": "FAIL"
    }

    # Locate evidence file if not explicitly specified
    if evidence_path is None:
        candidate_paths = [
            meta_dir / f"{fixture_dir.name}-evidence.json",
            meta_dir / "evidence.json",
            meta_dir / "review_report.json",
            fixture_dir / "evidence.json",
            fixture_dir / "review_report.json",
        ]
        for cp in candidate_paths:
            if cp.is_file():
                evidence_path = cp
                break

    if evidence_path is None:
        raise AssertionError("Evidence file not specified and could not be found in default locations.")

    # 1. Read-only Workspace Check
    verify_readonly_workspace(fixture_dir, snapshot)
    results["checks"]["readonly_workspace"] = "pass"

    # 2. Runtime Oracle Confirmation
    oracle_status = run_runtime_oracle(fixture_dir)
    results["checks"]["runtime_oracle"] = oracle_status

    # 3. Evidence File Schema & Finding Accuracy
    verify_evidence_file(evidence_path, snapshot)
    results["checks"]["evidence_finding_accuracy"] = "pass"

    results["overall"] = "PASS"
    return results

def main():
    parser = argparse.ArgumentParser(description="Verify Task R1 fixture outcome")
    parser.add_argument("--fixture-dir", required=True, help="Path to bootstrapped R1 fixture repository")
    parser.add_argument("--evidence-file", help="Path to evidence findings JSON file")
    args = parser.parse_args()

    fixture_dir = pathlib.Path(args.fixture_dir).resolve()
    evidence_path = pathlib.Path(args.evidence_file).resolve() if args.evidence_file else None

    print("=== Verifying Task R1 (Contract Drift Review) ===")
    print(f"Fixture: {fixture_dir}")
    if evidence_path:
        print(f"Evidence File: {evidence_path}")

    try:
        results = verify_r1(fixture_dir, evidence_path)
        print(f"Overall Result: {results['overall']}")
        for check, status in results["checks"].items():
            print(f"  [{status.upper()}] {check}")
        sys.exit(0)
    except Exception as e:
        print("Overall Result: FAIL", file=sys.stderr)
        print(f"Reason: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
