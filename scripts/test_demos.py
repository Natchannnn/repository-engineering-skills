#!/usr/bin/env python3
"""
Acceptance test suite for examples/ (Demo 1, Demo 2, and evidence template).
Executes both happy paths and negative control probes against bootstraps and verifiers.
"""

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

try:
    import jsonschema
except ImportError:
    sys.stderr.write(
        "ERROR: Required Python test dependency 'jsonschema' is not installed.\n"
        "Please install it using: python -m pip install jsonschema\n"
    )
    sys.exit(1)


class DemoAcceptanceTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = REPO_ROOT / "examples" / "template" / "evidence-record.schema.json"
        cls.template_path = REPO_ROOT / "examples" / "template" / "run-template.json"
        cls.demo1_dir = REPO_ROOT / "examples" / "read-only-contract-review"
        cls.demo2_dir = REPO_ROOT / "examples" / "foundation-development"
        cls.finalize_script = REPO_ROOT / "examples" / "finalize_setup.py"

    def _finalize_setup(self, fixture_dir: pathlib.Path):
        cmd = [sys.executable, str(self.finalize_script), str(fixture_dir)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"finalize_setup.py failed:\n{res.stderr}\n{res.stdout}")

    # =========================================================================
    # Group 1: Template & Schema Tests
    # =========================================================================
    def test_schema_structural_validity(self):
        sys.path.insert(0, str(REPO_ROOT / "repo-foundation" / "evals"))
        try:
            import core
            schema_data = json.loads(self.schema_path.read_text(encoding="utf-8"))
            core.validate_json_schema_definition(schema_data, "evidence-record.schema.json")
            self.assertIn("$schema", schema_data.get("properties", {}))

            # Check tri-state enum on verification_results properties
            props = schema_data["properties"]["verification_results"]["properties"]
            for field in ("independent_checks_passed", "findings_or_behavior_verified", "protected_state_preserved"):
                self.assertEqual(props[field].get("enum"), ["not_run", "pass", "fail"])
        finally:
            if str(REPO_ROOT / "repo-foundation" / "evals") in sys.path:
                sys.path.remove(str(REPO_ROOT / "repo-foundation" / "evals"))

    def test_template_instance_validity_and_negative_control(self):
        schema_data = json.loads(self.schema_path.read_text(encoding="utf-8"))
        template_text = self.template_path.read_text(encoding="utf-8")

        # 1. Valid instance with real UTC timestamp
        instance_text = template_text.replace(
            "YYYY-MM-DDTHH:MM:SSZ", "2026-09-27T02:00:00Z"
        )
        data = json.loads(instance_text)
        jsonschema.validate(instance=data, schema=schema_data)

        # 2. Negative control: invented enum state must be rejected
        bad_enum = copy.deepcopy(data)
        bad_enum["verification_results"]["independent_checks_passed"] = "invented-state"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_enum, schema=schema_data)

        # 3. Negative control: empty fixture object must be rejected (missing required fields)
        bad_fixture = copy.deepcopy(data)
        bad_fixture["fixture"] = {}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_fixture, schema=schema_data)

        # 4. Negative control: string exit_code must be rejected
        bad_exit = copy.deepcopy(data)
        bad_exit["execution"]["commands_executed"] = [{"cmd": "test", "exit_code": "zero"}]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_exit, schema=schema_data)

        # 5. Negative control: empty limitations array must be rejected (minItems: 1)
        bad_limits = copy.deepcopy(data)
        bad_limits["limitations"] = []
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_limits, schema=schema_data)

    # =========================================================================
    # Group 2: Demo 1 (Read-Only Contract Review) Tests
    # =========================================================================
    def test_demo1_happy_path(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            cmd_boot = [sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)]
            res_boot = subprocess.run(cmd_boot, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res_boot.returncode, 0, f"Bootstrap failed:\n{res_boot.stderr}")
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "## Review Summary\n"
                "Audited feature branch against main.\n\n"
                "### Finding: Public Contract Drift\n"
                "- verdict: defect\n"
                "- source_file: src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n\n"
                "Details: get_account_tier removed discount_pct, breaking calculate_invoice.\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res_ver.returncode, 0, f"verify.py failed on happy path:\n{res_ver.stderr}\n{res_ver.stdout}")
            self.assertIn("OVERALL VERIFICATION: PASSED", res_ver.stdout)

    def test_demo1_readme_example_report_passes(self):
        """Validates that the exact report sample documented in README.md passes verify.py."""
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            readme_text = (self.demo1_dir / "README.md").read_text(encoding="utf-8")
            # Extract sample report from README code fence
            m = re.search(r"```text\s*(## Review Summary.*?```)", readme_text, re.DOTALL)
            self.assertIsNotNone(m, "README.md must contain the sample review report")
            sample_report = m.group(1).rstrip("`").strip()

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(sample_report, encoding="utf-8")

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res_ver.returncode, 0, f"README report sample failed verify.py:\n{res_ver.stderr}\n{res_ver.stdout}")
            self.assertIn("OVERALL VERIFICATION: PASSED", res_ver.stdout)

    def test_demo1_negative_control_prompt_copy_rejected(self):
        """Validates that copying the agent task prompt as a review report strictly fails verify.py."""
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            readme_text = (self.demo1_dir / "README.md").read_text(encoding="utf-8")
            m = re.search(r"```text\s*(Use repo-native-refactor to review.*?```)", readme_text, re.DOTALL)
            self.assertIsNotNone(m, "README.md must contain the agent task prompt specification")
            prompt_only = m.group(1).rstrip("`").strip()

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(prompt_only, encoding="utf-8")

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject a report consisting only of the copied task prompt")
            self.assertIn("Structured finding rejected", res_ver.stderr)

    def test_demo1_negative_control_denial_report_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "No issue: src/profile.py get_account_tier preserves discount_pct.\n"
                "No affected caller: src/billing.py calculate_invoice is safe; no KeyError occurs.\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject report that denies the defect")
            self.assertIn("Finding quality check failed", res_ver.stderr)

    def test_demo1_negative_control_keyword_salad_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "src/profile.py get_account_tier src/billing.py calculate_invoice discount_pct KeyError\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject unstructured keyword salad")

    def test_demo1_negative_control_substring_negated_verdict_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "### Finding\n"
                "- verdict: not a defect\n"
                "- source_file: src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject 'not a defect'")
            self.assertIn("not an active defect", res_ver.stderr)

    def test_demo1_negative_control_substring_wrong_file_symbol_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "### Finding\n"
                "- verdict: defect\n"
                "- source_file: unrelated/fake_profile.py.bak\n"
                "- source_symbol: not_get_account_tier\n"
                "- affected_caller_file: elsewhere/fake_billing.py\n"
                "- affected_caller_symbol: not_calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject wrong file and symbol")
            self.assertIn("does not match expected", res_ver.stderr)

    def test_demo1_negative_control_path_traversal_rejected(self):
        """Ensures that relative parent traversal (..) and absolute paths are strictly rejected."""
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            # Probe 1: parent traversal ..
            report_file1 = evidence_dir / "report1.txt"
            report_file1.write_text(
                "### Finding\n"
                "- verdict: defect\n"
                "- source_file: ../src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: ../../src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n",
                encoding="utf-8"
            )
            cmd1 = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file1)]
            res1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res1.returncode, 0, "Verifier must reject parent traversal '..'")

            # Probe 2: absolute path /
            report_file2 = evidence_dir / "report2.txt"
            report_file2.write_text(
                "### Finding\n"
                "- verdict: defect\n"
                "- source_file: /src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: /src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n",
                encoding="utf-8"
            )
            cmd2 = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file2)]
            res2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res2.returncode, 0, "Verifier must reject absolute paths")

    def test_demo1_negative_control_substring_negated_failure_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "### Finding\n"
                "- verdict: defect\n"
                "- source_file: src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- failure_mode: No KeyError on discount_pct occurs; billing works correctly.\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject missing structured exception fields")
            self.assertIn("exception_type", res_ver.stderr)

    def test_demo1_negative_control_protected_state_violation(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "### Finding: Public Contract Drift\n"
                "- verdict: defect\n"
                "- source_file: src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            # Mutate protected file inside fixture
            (fixture_dir / "src" / "profile.py").write_text("# mutated", encoding="utf-8")

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject modified protected files")
            self.assertIn("Protected state check failed", res_ver.stderr)

    def test_demo1_rubric_validation_strict(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            # Test LF and CRLF file byte hash binding
            for nl in ("\n", "\r\n"):
                report_file = evidence_dir / f"review_report_{'crlf' if nl == '\r\n' else 'lf'}.txt"
                report_text = f"Analysis shows removing discount_pct breaks downstream billing calculation.{nl}"
                raw_bytes = report_text.encode("utf-8")
                report_file.write_bytes(raw_bytes)
                correct_hash = hashlib.sha256(raw_bytes).hexdigest()

                rubric_file = evidence_dir / f"rubric_{'crlf' if nl == '\r\n' else 'lf'}.json"
                rubric_file.write_text(json.dumps({
                    "evaluator": "Lead Maintainer",
                    "verdict": "pass",
                    "justification": "Verified contract drift and failure mechanism.",
                    "citations": ["removing discount_pct", "breaks downstream billing"],
                    "report_sha256": correct_hash
                }), encoding="utf-8")

                cmd_ver = [
                    sys.executable, str(self.demo1_dir / "verify.py"),
                    "--fixture-dir", str(fixture_dir),
                    "--review-output", str(report_file),
                    "--rubric-eval", str(rubric_file)
                ]
                res = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.assertEqual(res.returncode, 0, f"Valid rubric failed for newline {repr(nl)}:\n{res.stderr}")
                self.assertIn("OVERALL VERIFICATION: PASSED", res.stdout)

            # 1. Non-existent rubric file must raise error
            missing_rubric = evidence_dir / "missing.json"
            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file),
                "--rubric-eval", str(missing_rubric)
            ]
            res = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("file not found", res.stderr.lower())

            # 2. String citations (not list) must be rejected
            rubric_file = evidence_dir / "rubric_bad_cit.json"
            rubric_file.write_text(json.dumps({
                "evaluator": "Reviewer",
                "verdict": "pass",
                "justification": "Good analysis",
                "citations": "xx",
                "report_sha256": correct_hash
            }), encoding="utf-8")
            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file),
                "--rubric-eval", str(rubric_file)
            ]
            res = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("citations", res.stderr)

            # 3. Phantom citations not in report must be rejected
            rubric_file.write_text(json.dumps({
                "evaluator": "Reviewer",
                "verdict": "pass",
                "justification": "Good analysis",
                "citations": ["phantom quote 1", "phantom quote 2"],
                "report_sha256": correct_hash
            }), encoding="utf-8")
            res = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("not found in report text", res.stderr)

            # 4. Hash mismatch (even by 1 byte) must be rejected
            rubric_file.write_text(json.dumps({
                "evaluator": "Reviewer",
                "verdict": "pass",
                "justification": "Good analysis",
                "citations": ["removing discount_pct", "breaks downstream billing"],
                "report_sha256": "0" * 64
            }), encoding="utf-8")
            res = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("report_sha256 mismatch", res.stderr)

    def test_demo1_negative_control_bootstrap_non_empty_dir_aborts(self):
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "existing_folder"
            target.mkdir(parents=True, exist_ok=True)
            (target / "README.md").write_text("USER ORIGINAL README", encoding="utf-8")
            (target / "unrelated.txt").write_text("important data", encoding="utf-8")

            cmd = [sys.executable, str(self.demo1_dir / "bootstrap.py"), str(target)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0, "Bootstrap must abort on non-empty target directory")
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "USER ORIGINAL README")
            self.assertEqual((target / "unrelated.txt").read_text(encoding="utf-8"), "important data")

    def test_demo1_negative_control_bootstrap_sidecar_collision(self):
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "fixture"
            sidecar = pathlib.Path(td) / f"{target.name}-INITIAL_HEAD"
            sidecar.write_text("existing_head", encoding="utf-8")

            cmd = [sys.executable, str(self.demo1_dir / "bootstrap.py"), str(target)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0, "Bootstrap must abort if INITIAL_HEAD sidecar already exists")
            self.assertEqual(sidecar.read_text(encoding="utf-8"), "existing_head")

    # =========================================================================
    # Group 3: Demo 2 (Foundation Development) Tests
    # =========================================================================
    def _apply_working_export_json_implementation(self, fixture_dir: pathlib.Path):
        cli_py = fixture_dir / "src" / "metric_hub" / "cli.py"
        cli_code = '''"""Command-line interface for metric_hub."""

import argparse
import json
import pathlib
import sys
from src.metric_hub.core import parse_csv_file, compute_category_totals

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metric_hub", description="Data aggregation utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Baseline command: summary
    summary_parser = subparsers.add_parser("summary", help="Display text summary of metrics")
    summary_parser.add_argument("csv_path", help="Path to input CSV file")

    # New command: export-json
    export_parser = subparsers.add_parser("export-json", help="Export category metrics as JSON")
    export_parser.add_argument("csv_path", help="Path to input CSV file")
    export_parser.add_argument("--out", required=True, help="Output JSON path")

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "summary":
        try:
            records = parse_csv_file(args.csv_path)
        except Exception as e:
            print(f"Error reading CSV: {e}", file=sys.stderr)
            sys.exit(1)

        totals = compute_category_totals(records)
        print("=== Metric Hub Summary Report ===")
        print(f"Total Records: {len(records)}")
        for cat, data in sorted(totals.items()):
            print(f"Category: {cat:<15} | Count: {data['count']:<4} | Total: ${data['total_amount']:.2f}")

    elif args.command == "export-json":
        csv_file = pathlib.Path(args.csv_path)
        if not csv_file.is_file():
            print(f"Error: CSV file not found: {args.csv_path}", file=sys.stderr)
            sys.exit(1)

        try:
            records = parse_csv_file(args.csv_path)
            totals = compute_category_totals(records)
            payload = {
                "status": "success",
                "record_count": int(len(records)),
                "categories": totals,
            }
            out_path = pathlib.Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Error exporting metrics: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
'''
        cli_py.write_text(cli_code, encoding="utf-8")

        readme = fixture_dir / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") +
            "\n### JSON Export\n```bash\npython -m src.metric_hub.cli export-json samples/transactions.csv --out out.json\n```\n",
            encoding="utf-8"
        )

        agent_test = fixture_dir / "tests" / "test_export_json.py"
        agent_test.write_text('''import unittest
import tempfile
import pathlib
import json
import subprocess
import sys

class ExportJsonCliTest(unittest.TestCase):
    def test_export_json_success(self):
        root = pathlib.Path(__file__).parent.parent
        sample = root / "samples" / "transactions.csv"
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "metrics.json"
            cmd = [sys.executable, "-m", "src.metric_hub.cli", "export-json", str(sample), "--out", str(out)]
            res = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(out.is_file())
            data = json.loads(out.read_text())
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["record_count"], 6)

if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

    def test_demo2_happy_path(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            self._apply_working_export_json_implementation(fixture_dir)

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res_ver.returncode, 0, f"verify.py failed on happy path:\n{res_ver.stderr}\n{res_ver.stdout}")
            self.assertIn("OVERALL VERIFICATION: PASSED", res_ver.stdout)

    def test_demo2_negative_control_broken_hardcoded_export_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            cli_py = fixture_dir / "src" / "metric_hub" / "cli.py"
            broken_cli = '''import argparse, pathlib, sys
from src.metric_hub.core import parse_csv_file, compute_category_totals

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    summary_p = sub.add_parser("summary")
    summary_p.add_argument("csv_path")
    exp = sub.add_parser("export-json")
    exp.add_argument("csv_path")
    exp.add_argument("--out")
    args = parser.parse_args()

    if args.command == "summary":
        records = parse_csv_file(args.csv_path)
        totals = compute_category_totals(records)
        print("=== Metric Hub Summary Report ===")
        for cat, d in sorted(totals.items()):
            print(f"Category: {cat} | Count: {d['count']} | Total: ${d['total_amount']}")
    elif args.command == "export-json":
        p = pathlib.Path(args.csv_path)
        if not p.is_file():
            sys.exit(1)
        pathlib.Path(args.out).write_text('{"status":"success","record_count":"NOT_A_COUNT","categories":{"electronics":{"count":3,"total_amount":450}}}')

if __name__ == "__main__":
    main()
'''
            cli_py.write_text(broken_cli, encoding="utf-8")
            (fixture_dir / "README.md").write_text("export-json docs", encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Verifier must reject hardcoded mock export")
            self.assertIn("test_feature.py", res_ver.stderr)

    def test_demo2_negative_control_scope_git_mv_rename_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            # Probe 3a: git mv pyproject.toml tests/pyproject.toml
            subprocess.run(["git", "-C", str(fixture_dir), "mv", "pyproject.toml", "tests/pyproject.toml"], check=True)

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Scope check must detect file moved from root with --no-renames")
            self.assertIn("pyproject.toml", res_ver.stderr)

    def test_demo2_negative_control_scope_leading_space_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            # Probe 3b: File with leading space ' README.md'
            (fixture_dir / " README.md").write_text("evil leading space", encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Scope check must reject ' README.md'")
            self.assertIn("README.md", res_ver.stderr)

    def test_demo2_negative_control_scope_readme_secret_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            (fixture_dir / "README.md.secret").write_text("secret leak", encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Scope check must reject README.md.secret")
            self.assertIn("README.md.secret", res_ver.stderr)

    def test_demo2_negative_control_scope_staged_index_leak_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            pyproject = fixture_dir / "pyproject.toml"
            orig = pyproject.read_text(encoding="utf-8")
            pyproject.write_text(orig + "\n# staged evil change", encoding="utf-8")
            subprocess.run(["git", "-C", str(fixture_dir), "add", "pyproject.toml"], check=True)
            pyproject.write_text(orig, encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0, "Scope check must detect staged modifications in index")
            self.assertIn("pyproject.toml", res_ver.stderr)

    def test_demo2_negative_control_bootstrap_non_empty_dir_aborts(self):
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "existing_folder"
            target.mkdir(parents=True, exist_ok=True)
            (target / "README.md").write_text("USER ORIGINAL README", encoding="utf-8")
            (target / "unrelated.txt").write_text("important data", encoding="utf-8")

            cmd = [sys.executable, str(self.demo2_dir / "bootstrap.py"), str(target)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0, "Bootstrap must abort on non-empty target directory")
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "USER ORIGINAL README")
            self.assertEqual((target / "unrelated.txt").read_text(encoding="utf-8"), "important data")

    def test_demo2_negative_control_bootstrap_sidecar_collision(self):
        with tempfile.TemporaryDirectory() as td:
            target = pathlib.Path(td) / "fixture"
            sidecar = pathlib.Path(td) / f"{target.name}-INITIAL_HEAD"
            sidecar.write_text("existing_head", encoding="utf-8")

            cmd = [sys.executable, str(self.demo2_dir / "bootstrap.py"), str(target)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0, "Bootstrap must abort if INITIAL_HEAD sidecar already exists")
            self.assertEqual(sidecar.read_text(encoding="utf-8"), "existing_head")

    # =========================================================================
    # Group 4: Step 1 (Setup Finalization & Lockfile Handling) Acceptance Tests
    # =========================================================================
    def _create_sample_lockfile(self, fixture_dir: pathlib.Path, skill_name: str = "repo-native-refactor"):
        lockfile_data = {
            "version": 1,
            "skills": {
                skill_name: {
                    "source": "Natchannnn/repository-engineering-skills",
                    "sourceType": "github",
                    "computedHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                }
            }
        }
        lockfile = fixture_dir / "skills-lock.json"
        lockfile.write_text(json.dumps(lockfile_data, indent=2) + "\n", encoding="utf-8")
        skill_dir = fixture_dir / ".agents" / "skills" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(f"# {skill_name}\nSkill instructions.\n", encoding="utf-8")
        return lockfile

    # Case 1: Fresh fixture -> simulated CLI setup via lockfile -> finalize setup -> state/scope checks pass
    def test_demo1_case1_fresh_fixture_simulated_cli_setup_finalize_passes_state_check(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._create_sample_lockfile(fixture_dir, "repo-native-refactor")
            self._finalize_setup(fixture_dir)

            spec = importlib.util.spec_from_file_location("demo1_verify_mod", str(self.demo1_dir / "verify.py"))
            d1_verify = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(d1_verify)
            count = d1_verify.verify_protected_state(fixture_dir)
            self.assertGreater(count, 0)

    def test_demo2_case1_fresh_fixture_simulated_cli_setup_finalize_passes_scope_check(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._create_sample_lockfile(fixture_dir, "repo-foundation")
            self._finalize_setup(fixture_dir)

            spec = importlib.util.spec_from_file_location("demo2_verify_mod", str(self.demo2_dir / "verify.py"))
            d2_verify = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(d2_verify)
            setup_meta = d2_verify.verify_setup_metadata(fixture_dir)
            modified = d2_verify.check_scope_boundaries(fixture_dir, setup_meta)
            self.assertEqual(modified, [])

    # Case 2: Demo 1 valid review report with lockfile present -> complete pass
    def test_demo1_case2_valid_review_report_with_lockfile_passes(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._create_sample_lockfile(fixture_dir, "repo-native-refactor")
            self._finalize_setup(fixture_dir)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "## Review Summary\n"
                "### Finding: Public Contract Drift\n"
                "- verdict: defect\n"
                "- source_file: src/profile.py\n"
                "- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n"
                "- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n"
                "- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [
                sys.executable, str(self.demo1_dir / "verify.py"),
                "--fixture-dir", str(fixture_dir),
                "--review-output", str(report_file)
            ]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res_ver.returncode, 0, f"verify.py failed:\n{res_ver.stderr}\n{res_ver.stdout}")
            self.assertIn("OVERALL VERIFICATION: PASSED", res_ver.stdout)

    # Case 3: Demo 2 valid implementation with lockfile present -> complete pass
    def test_demo2_case3_valid_implementation_with_lockfile_passes(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._create_sample_lockfile(fixture_dir, "repo-foundation")
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res_ver.returncode, 0, f"verify.py failed:\n{res_ver.stderr}\n{res_ver.stdout}")
            self.assertIn("OVERALL VERIFICATION: PASSED", res_ver.stdout)

    # Case 4: Modified or deleted skills-lock.json post-setup -> FAIL
    def test_demo1_case4_lockfile_modified_post_setup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            lockfile = self._create_sample_lockfile(fixture_dir, "repo-native-refactor")
            self._finalize_setup(fixture_dir)

            lockfile.write_text('{"version": 2, "tampered": true}', encoding="utf-8")

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "- verdict: defect\n- source_file: src/profile.py\n- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Lockfile integrity violation", res_ver.stderr)
            self.assertIn("modified post-setup", res_ver.stderr)

    def test_demo1_case4_lockfile_deleted_post_setup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            lockfile = self._create_sample_lockfile(fixture_dir, "repo-native-refactor")
            self._finalize_setup(fixture_dir)

            lockfile.unlink()

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "- verdict: defect\n- source_file: src/profile.py\n- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Lockfile integrity violation", res_ver.stderr)
            self.assertIn("missing", res_ver.stderr)

    def test_demo2_case4_lockfile_modified_post_setup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            lockfile = self._create_sample_lockfile(fixture_dir, "repo-foundation")
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            lockfile.write_text('{"modified": true}', encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Lockfile integrity violation", res_ver.stderr)

    def test_demo2_case4_lockfile_deleted_post_setup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            lockfile = self._create_sample_lockfile(fixture_dir, "repo-foundation")
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            lockfile.unlink()

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Lockfile integrity violation", res_ver.stderr)

    # Case 5: Lockfile absent at setup, but created during agent run -> FAIL
    def test_demo1_case5_lockfile_appeared_post_setup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            (fixture_dir / "skills-lock.json").write_text('{"unexpected": true}', encoding="utf-8")

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "- verdict: defect\n- source_file: src/profile.py\n- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Lockfile state violation", res_ver.stderr)
            self.assertIn("appeared during or after agent task", res_ver.stderr)

    def test_demo2_case5_lockfile_appeared_post_setup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            (fixture_dir / "skills-lock.json").write_text('{"unexpected": true}', encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Lockfile state violation", res_ver.stderr)

    # Case 7: Bypassing setup finalization (missing metadata) -> FAIL with clear diagnostic
    def test_demo1_case7_bypassing_setup_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text("- verdict: defect\n", encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Missing setup metadata file", res_ver.stderr)
            self.assertIn("finalize_setup.py", res_ver.stderr)

    def test_demo2_case7_bypassing_setup_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._apply_working_export_json_implementation(fixture_dir)

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Missing setup metadata file", res_ver.stderr)
            self.assertIn("finalize_setup.py", res_ver.stderr)

    # Case 8: Attempting to re-run setup on finalized metadata -> FAIL (no silent overwrite)
    def test_setup_case8_cannot_overwrite_finalized_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._finalize_setup(fixture_dir)

            cmd = [sys.executable, str(self.finalize_script), str(fixture_dir)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("Setup metadata already exists", res.stderr)
            self.assertIn("cannot be re-finalized", res.stderr)

    def test_setup_case8_concurrent_finalize_exclusive_creation_rejects_second_writer(self):
        import threading
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)

            spec = importlib.util.spec_from_file_location("finalize_setup_mod", str(self.finalize_script))
            setup_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(setup_mod)

            original_validate = setup_mod.validate_pristine_source
            barrier = threading.Barrier(2)

            def synchronized_validate(fixture):
                original_validate(fixture)
                barrier.wait(timeout=15)

            setup_mod.validate_pristine_source = synchronized_validate

            results = []
            exceptions = []

            def worker():
                try:
                    res = setup_mod.finalize_setup(fixture_dir)
                    results.append(res)
                except Exception as ex:
                    exceptions.append(ex)

            t1 = threading.Thread(target=worker)
            t2 = threading.Thread(target=worker)
            t1.start()
            t2.start()
            t1.join(timeout=15)
            t2.join(timeout=15)

            # Exactly one worker must succeed; the other must receive FileExistsError
            self.assertEqual(len(results), 1)
            self.assertEqual(len(exceptions), 1)
            self.assertIsInstance(exceptions[0], FileExistsError)
            self.assertIn("Setup metadata already exists", str(exceptions[0]))

            # The resulting metadata file is intact, valid JSON, and not truncated
            meta_path = results[0]
            self.assertTrue(meta_path.is_file())
            loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded.get("schema_version"), "1.0")

    def test_setup_case8_dirty_source_before_setup_aborts(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)

            (fixture_dir / "src" / "profile.py").write_text("# premature modification", encoding="utf-8")

            cmd = [sys.executable, str(self.finalize_script), str(fixture_dir)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("Pristine source check failed", res.stderr)

            meta_file = fixture_dir.parent / f"{fixture_dir.name}-setup-metadata.json"
            self.assertFalse(meta_file.exists())

    def test_setup_negative_control_unauthorized_root_json_aborts(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)

            (fixture_dir / "package.json").write_text('{"name": "unauthorized"}', encoding="utf-8")

            cmd = [sys.executable, str(self.finalize_script), str(fixture_dir)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("unauthorized untracked file detected", res.stderr)

    # Subfolder lockfile negative controls: only root skills-lock.json receives special exemption
    def test_demo2_negative_control_subfolder_lockfile_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "foundation_fixture"
            subprocess.run([sys.executable, str(self.demo2_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._create_sample_lockfile(fixture_dir, "repo-foundation")
            self._finalize_setup(fixture_dir)
            self._apply_working_export_json_implementation(fixture_dir)

            # Placing lockfile in samples/ (outside allowed prefixes) must violate scope
            (fixture_dir / "samples" / "skills-lock.json").write_text('{"sub": true}', encoding="utf-8")

            cmd_ver = [sys.executable, str(self.demo2_dir / "verify.py"), "--fixture-dir", str(fixture_dir)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Scope boundary violated", res_ver.stderr)

    def test_demo1_negative_control_subfolder_lockfile_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "contract_review_fixture"
            evidence_dir = pathlib.Path(td) / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)

            subprocess.run([sys.executable, str(self.demo1_dir / "bootstrap.py"), str(fixture_dir)], check=True)
            self._create_sample_lockfile(fixture_dir, "repo-native-refactor")
            self._finalize_setup(fixture_dir)

            (fixture_dir / "src" / "skills-lock.json").write_text('{"sub": true}', encoding="utf-8")

            report_file = evidence_dir / "review_report.txt"
            report_file.write_text(
                "- verdict: defect\n- source_file: src/profile.py\n- source_symbol: get_account_tier\n"
                "- affected_caller_file: src/billing.py\n- affected_caller_symbol: calculate_invoice\n"
                "- exception_type: KeyError\n- missing_key: discount_pct\n",
                encoding="utf-8"
            )

            cmd_ver = [sys.executable, str(self.demo1_dir / "verify.py"), "--fixture-dir", str(fixture_dir), "--review-output", str(report_file)]
            res_ver = subprocess.run(cmd_ver, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(res_ver.returncode, 0)
            self.assertIn("Protected state violated", res_ver.stderr)
            self.assertIn("src/skills-lock.json", res_ver.stderr)

if __name__ == "__main__":
    unittest.main()
