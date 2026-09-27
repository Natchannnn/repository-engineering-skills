#!/usr/bin/env python3
"""
Verification runner for Read-Only Contract Review Demo.

Separates:
1. Protected state integrity: verifies that protected repository state remained unchanged
   after the review session (HEAD, working tree, index, and byte-exact baseline manifest).
2. Finding quality: evaluates whether the review report accurately asserts the contract drift
   and downstream failure mechanism via exact machine-verified structured finding fields
   or a cryptographic-bound rubric evaluation record.

Prose keyword occurrence is reported strictly as informational mention scan and is NEVER
used alone to award finding quality PASS.
"""

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

_EXAMPLES_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(_EXAMPLES_DIR))
from finalize_setup import verify_setup_metadata

def run_git(cwd, args):
    cmd = ["git", "-C", str(cwd)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()

def normalize_relative_repo_path(raw_path: str) -> str:
    """
    Normalizes a repository-relative path according to strict rules:
    - Normalizes backslashes to forward slashes.
    - Rejects absolute paths (starting with '/' or drive letters like 'C:').
    - Rejects parent directory traversal ('..').
    - Safely strips intentional leading './' components without removing other path segments.
    """
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise AssertionError("Repository path must be a non-empty string.")

    p = raw_path.strip().replace("\\", "/")

    # 1. Reject absolute paths
    if p.startswith("/") or re.match(r"^[a-zA-Z]:", p):
        raise AssertionError(f"Path must be a relative repository path; rejected absolute path: '{raw_path}'")

    # 2. Reject directory traversal
    parts = p.split("/")
    if ".." in parts:
        raise AssertionError(f"Path must not contain parent directory traversal '..'; rejected: '{raw_path}'")

    # 3. Clean leading single dot './' safely
    clean_parts = [part for part in parts if part and part != "."]
    if not clean_parts:
        raise AssertionError(f"Invalid path after normalization: '{raw_path}'")

    return "/".join(clean_parts)

def verify_protected_state(fixture_dir: pathlib.Path):
    fixture_dir = fixture_dir.resolve()
    meta_dir = fixture_dir.parent

    # 0. Check setup metadata & lockfile integrity
    setup_meta = verify_setup_metadata(fixture_dir)

    # 1. Check INITIAL_HEAD
    head_file = meta_dir / f"{fixture_dir.name}-INITIAL_HEAD"
    if not head_file.is_file():
        raise FileNotFoundError(f"Missing INITIAL_HEAD reference at: {head_file}")
    expected_head = head_file.read_text(encoding="utf-8").strip()
    current_head = run_git(fixture_dir, ["rev-parse", "HEAD"])
    if current_head != expected_head:
        raise AssertionError(f"Protected state violated: HEAD advanced from {expected_head} to {current_head}")

    # 2. Check git status
    status = run_git(fixture_dir, ["status", "--porcelain"])
    # Ignore .agents/ directory if created by skill installation
    # And ignore exact root skills-lock.json ONLY if it was present and verified at setup finalization
    status_lines = []
    for line in status.splitlines():
        if line.endswith(".agents/") or ".agents/" in line:
            continue
        status_file = line[3:].strip()
        if setup_meta["lockfile_status"] == "present" and line.startswith("??") and status_file == "skills-lock.json":
            continue
        status_lines.append(line)

    if status_lines:
        raise AssertionError(f"Protected state violated: working tree or index is dirty:\n" + "\n".join(status_lines))

    # 3. Check git diff against HEAD
    res_diff = subprocess.run(["git", "-C", str(fixture_dir), "diff", "--quiet", "HEAD"], check=False)
    if res_diff.returncode != 0:
        raise AssertionError("Protected state violated: uncommitted modifications detected in working tree.")

    res_cached = subprocess.run(["git", "-C", str(fixture_dir), "diff", "--cached", "--quiet"], check=False)
    if res_cached.returncode != 0:
        raise AssertionError("Protected state violated: staged changes detected in index.")

    # 4. Check external baseline manifest
    manifest_file = meta_dir / f"{fixture_dir.name}-baseline-manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Missing baseline manifest at: {manifest_file}")
    baseline = json.loads(manifest_file.read_text(encoding="utf-8"))

    ignored_parts = {".git", ".agents", "__pycache__", ".pytest_cache"}
    current_files = {}
    for p in fixture_dir.rglob("*"):
        if p.is_file() and not any(part in ignored_parts for part in p.parts):
            rel = p.relative_to(fixture_dir).as_posix()
            current_files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()

    # Check for modified or missing files
    for rel_path, expected_hash in baseline.items():
        if rel_path not in current_files:
            raise AssertionError(f"Protected file missing after review: {rel_path}")
        if current_files[rel_path] != expected_hash:
            raise AssertionError(f"Protected file modified during review: {rel_path}")

    # Check for unmanaged extra files
    extra_files = set(current_files.keys()) - set(baseline.keys())
    if setup_meta["lockfile_status"] == "present" and "skills-lock.json" in extra_files:
        extra_files.remove("skills-lock.json")

    if extra_files:
        raise AssertionError(f"Unexpected extra files created during review: {extra_files}")

    return len(baseline)

def parse_structured_finding(report_text: str) -> dict | None:
    # 1. Attempt JSON block parsing
    json_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", report_text, re.DOTALL)
    for blk in json_blocks:
        try:
            data = json.loads(blk)
            if isinstance(data, dict) and any(k in data for k in ("verdict", "source_file")):
                return data
        except Exception:
            pass

    # 2. Regex parsing for key-value / markdown bullet points
    def extract_field(patterns: list[str]) -> str | None:
        for pat in patterns:
            m = re.search(pat, report_text, re.IGNORECASE)
            if m:
                val = m.group(1).strip().strip("`'\"*")
                return val
        return None

    verdict = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:verdict|status)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_VERDICT\s*:\s*([^\n\r]+)"
    ])
    source_file = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:source_file|source file|modified file)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_SOURCE_FILE\s*:\s*([^\n\r]+)"
    ])
    source_symbol = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:source_symbol|source symbol|modified symbol)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_SOURCE_SYMBOL\s*:\s*([^\n\r]+)"
    ])
    caller_file = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:affected_caller_file|affected caller file|caller file|impacted file)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_CALLER_FILE\s*:\s*([^\n\r]+)"
    ])
    caller_symbol = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:affected_caller_symbol|affected caller symbol|caller symbol|impacted symbol)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_CALLER_SYMBOL\s*:\s*([^\n\r]+)"
    ])
    exception_type = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:exception_type|exception type|exception)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_EXCEPTION_TYPE\s*:\s*([^\n\r]+)"
    ])
    missing_key = extract_field([
        r"(?:^|\n)\s*[-*]?\s*(?:\*\*)?(?:missing_key|missing key|missing field)(?:\*\*)?\s*:\s*([^\n\r]+)",
        r"FINDING_MISSING_KEY\s*:\s*([^\n\r]+)"
    ])

    if verdict or source_file:
        return {
            "verdict": verdict,
            "source_file": source_file,
            "source_symbol": source_symbol,
            "affected_caller_file": caller_file,
            "affected_caller_symbol": caller_symbol,
            "exception_type": exception_type,
            "missing_key": missing_key
        }
    return None

def verify_finding_quality(report_text: str, gt_data: dict, rubric_eval_path: pathlib.Path | None = None, report_sha256: str | None = None):
    # Step A: Informational Mention Scan (does NOT grant pass)
    tokens_found = []
    tokens_missing = []
    for token in gt_data.get("informational_entity_tokens", []):
        if re.search(token["pattern"], report_text, re.IGNORECASE):
            tokens_found.append(token["id"])
        else:
            tokens_missing.append(token["id"])
    print(f"    [INFO] Entity mention scan: {len(tokens_found)}/{len(tokens_found) + len(tokens_missing)} key tokens referenced in prose.")

    # Step B: Completed Rubric Evaluation Path
    if rubric_eval_path is not None:
        if not rubric_eval_path.is_file():
            raise FileNotFoundError(f"Specified --rubric-eval file not found: {rubric_eval_path}")

        rubric_data = json.loads(rubric_eval_path.read_text(encoding="utf-8"))
        if not isinstance(rubric_data, dict):
            raise AssertionError("Rubric evaluation content must be a JSON object.")

        evaluator = rubric_data.get("evaluator")
        verdict = rubric_data.get("verdict")
        justification = rubric_data.get("justification")
        citations = rubric_data.get("citations")
        expected_sha256 = rubric_data.get("report_sha256")

        if not isinstance(evaluator, str) or not evaluator.strip():
            raise AssertionError("Rubric evaluation missing valid non-empty 'evaluator' string.")
        if verdict != "pass":
            raise AssertionError(f"Rubric evaluation recorded verdict '{verdict}' (not 'pass'): {justification}")
        if not isinstance(justification, str) or not justification.strip():
            raise AssertionError("Rubric evaluation missing valid non-empty 'justification' text.")

        # Strict list check for citations
        if not isinstance(citations, list) or len(citations) < 2:
            raise AssertionError(f"Rubric evaluation requires 'citations' to be a list with at least 2 entries; got: {type(citations).__name__}")

        # Check that citations are actual excerpts from the report
        for idx, cit in enumerate(citations):
            if not isinstance(cit, str) or not cit.strip():
                raise AssertionError(f"Rubric citation[{idx}] must be a non-empty string.")
            if cit not in report_text:
                raise AssertionError(f"Rubric citation[{idx}] not found in report text: {cit!r}")

        # Check cryptographic report file bytes binding
        if not report_sha256:
            report_sha256 = hashlib.sha256(report_text.encode("utf-8")).hexdigest()

        if not expected_sha256 or expected_sha256.lower() != report_sha256.lower():
            raise AssertionError(
                f"Rubric evaluation report_sha256 mismatch!\n"
                f"  Rubric record:                     {expected_sha256}\n"
                f"  Actual report file SHA-256 (bytes): {report_sha256}\n"
                f"Rubric must be bound to the exact file byte hash of the evaluated report."
            )

        print(f"    [PASS] Human/Rubric evaluation by '{evaluator}' confirmed finding quality: {verdict.upper()}")
        print(f"           Justification: {justification}")
        print(f"           Report SHA-256 bound: {report_sha256[:16]}...")
        print(f"           (Note: Verifier verified evaluation schema, citations, and file byte hash;")
        print(f"            evaluator identity is attributed to the declared evaluator string.)")
        return {"mode": "rubric", "evaluator": evaluator, "verdict": verdict}

    # Step C: Exact Machine Verification of Structured Finding Block
    finding = parse_structured_finding(report_text)
    if not finding:
        raise AssertionError(
            "Finding quality check failed: Report does not contain a structured finding section or rubric evaluation.\n"
            "Raw prose keyword appearance is not sufficient for automated finding quality verification.\n"
            "Required structured fields:\n"
            "  - verdict: defect | breaking_change | contract_drift | regression\n"
            "  - source_file: src/profile.py\n"
            "  - source_symbol: get_account_tier\n"
            "  - affected_caller_file: src/billing.py\n"
            "  - affected_caller_symbol: calculate_invoice\n"
            "  - exception_type: KeyError\n"
            "  - missing_key: discount_pct"
        )

    schema_info = gt_data.get("structured_finding_schema", {})
    allowed_verdicts = set(schema_info.get("allowed_verdicts", ["defect", "breaking_change", "contract_drift", "regression"]))
    expected_values = schema_info.get("expected_values", gt_data.get("ground_truth", {}))

    # 1. Exact match for verdict (reject substring like "not a defect")
    raw_verdict = (finding.get("verdict") or "").strip().lower()
    if raw_verdict not in allowed_verdicts:
        raise AssertionError(
            f"Structured finding rejected: verdict '{finding.get('verdict')}' is not an active defect.\n"
            f"Expected exact match with one of: {sorted(allowed_verdicts)}"
        )

    # 2. Exact match for source file and symbol
    src_f = normalize_relative_repo_path(finding.get("source_file") or "")
    expected_src_f = normalize_relative_repo_path(expected_values["source_file"])
    if src_f != expected_src_f:
        raise AssertionError(
            f"Structured finding rejected: source_file '{src_f}' does not match expected '{expected_src_f}'"
        )

    src_sym = (finding.get("source_symbol") or "").strip()
    expected_src_sym = expected_values["source_symbol"]
    if src_sym != expected_src_sym:
        raise AssertionError(
            f"Structured finding rejected: source_symbol '{src_sym}' does not match expected '{expected_src_sym}'"
        )

    # 3. Exact match for caller file and symbol
    caller_f = normalize_relative_repo_path(finding.get("affected_caller_file") or "")
    expected_caller_f = normalize_relative_repo_path(expected_values["affected_caller_file"])
    if caller_f != expected_caller_f:
        raise AssertionError(
            f"Structured finding rejected: affected_caller_file '{caller_f}' does not match expected '{expected_caller_f}'"
        )

    caller_sym = (finding.get("affected_caller_symbol") or "").strip()
    expected_caller_sym = expected_values["affected_caller_symbol"]
    if caller_sym != expected_caller_sym:
        raise AssertionError(
            f"Structured finding rejected: affected_caller_symbol '{caller_sym}' does not match expected '{expected_caller_sym}'"
        )

    # 4. Exact match for machine-readable exception fields
    exc_type = (finding.get("exception_type") or "").strip()
    expected_exc = expected_values.get("exception_type", "KeyError")
    if exc_type != expected_exc:
        raise AssertionError(
            f"Structured finding rejected: exception_type '{exc_type}' does not match expected '{expected_exc}'"
        )

    missing_key = (finding.get("missing_key") or "").strip().strip("'\"")
    expected_key = expected_values.get("missing_key", "discount_pct")
    if missing_key != expected_key:
        raise AssertionError(
            f"Structured finding rejected: missing_key '{missing_key}' does not match expected '{expected_key}'"
        )

    print(f"    [PASS] Structured finding machine-verified against ground truth:")
    print(f"           Verdict:         {raw_verdict} (exact match with active defect)")
    print(f"           Source:          {src_f}::{src_sym} (exact match)")
    print(f"           Affected Caller: {caller_f}::{caller_sym} (exact match)")
    print(f"           Exception:       {exc_type} (exact match)")
    print(f"           Missing Key:     {missing_key} (exact match)")
    print(f"           (Note: Machine verification validates these exact structured fields;")
    print(f"            it does not claim semantic evaluation of arbitrary narrative prose.)")

    return {"mode": "structured_finding", "finding": finding}

def main():
    parser = argparse.ArgumentParser(description="Verify Read-Only Contract Review Demo")
    parser.add_argument("--fixture-dir", required=True, help="Path to bootstrapped fixture repository")
    parser.add_argument("--review-output", required=True, help="Path to text file containing agent's review report")
    parser.add_argument("--ground-truth", default=None, help="Path to ground_truth.json (defaults to beside script)")
    parser.add_argument("--rubric-eval", default=None, help="Optional path to human/evaluator rubric record JSON")
    args = parser.parse_args()

    fixture_dir = pathlib.Path(args.fixture_dir).resolve()
    report_file = pathlib.Path(args.review_output).resolve()

    script_dir = pathlib.Path(__file__).parent
    gt_file = pathlib.Path(args.ground_truth).resolve() if args.ground_truth else (script_dir / "ground_truth.json")
    rubric_file = pathlib.Path(args.rubric_eval).resolve() if args.rubric_eval else None

    print(f"=== Verifying Read-Only Contract Review Demo ===")
    print(f"Fixture: {fixture_dir}")
    print(f"Report:  {report_file}\n")

    # Phase 1: Protected State Verification
    print("--> Phase 1: Checking protected state preservation...")
    try:
        file_count = verify_protected_state(fixture_dir)
        print(f"    [PASS] Protected state preserved: all {file_count} files intact byte-for-byte; HEAD, index, and working tree clean.")
    except Exception as e:
        print(f"    [FAIL] Protected state check failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Phase 2: Finding Quality Verification
    print("\n--> Phase 2: Evaluating finding quality against ground truth...")
    if not report_file.is_file():
        print(f"    [FAIL] Review output file not found: {report_file}", file=sys.stderr)
        sys.exit(1)

    report_bytes = report_file.read_bytes()
    file_sha256 = hashlib.sha256(report_bytes).hexdigest()
    report_text = report_bytes.decode("utf-8", errors="replace")
    gt_data = json.loads(gt_file.read_text(encoding="utf-8"))

    try:
        verify_finding_quality(report_text, gt_data, rubric_file, report_sha256=file_sha256)
    except Exception as e:
        print(f"    [FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    print("\nOVERALL VERIFICATION: PASSED (Protected state preserved & correct contract findings verified)")
    sys.exit(0)

if __name__ == "__main__":
    main()
