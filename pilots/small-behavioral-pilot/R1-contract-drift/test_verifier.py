#!/usr/bin/env python3
"""
Self-audit tests for Task R1 (Contract Drift Review) verifier.
Verifies that the verifier:
1. Passes canonical correct findings with intact read-only workspace.
2. Passes alternative findings with accepted aliases (tax_id / removed_symbol).
3. Fails negative controls: prompt placeholder copy, working tree mutation,
   git commit, git staging, precision failure (bogus finding added),
   wrong caller symbol, wrong source file, empty findings array, untracked files,
   and missing evidence file.
"""

import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

DIR = pathlib.Path(__file__).parent.resolve()
BOOTSTRAP_SCRIPT = DIR / "bootstrap.py"
VERIFY_SCRIPT = DIR / "verify.py"

def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

CANONICAL_FINDING = [
    {
        "verdict": "defect",
        "source_file": "src/schema.py",
        "source_symbol": "AccountProfile.tax_identifier",
        "broken_caller_file": "src/notification_service.py",
        "broken_caller_symbol": "send_tax_invoice",
        "breakage_type": "contract_drift"
    }
]

ALTERNATIVE_FINDING_ALIAS = [
    {
        "verdict": "defect",
        "source_file": "src/schema.py",
        "source_symbol": "AccountProfile.tax_id",
        "broken_caller_file": "src/notification_service.py",
        "broken_caller_symbol": "send_tax_invoice",
        "breakage_type": "removed_symbol"
    }
]

PROMPT_PLACEHOLDERS_FINDING = [
    {
        "verdict": "defect",
        "source_file": "<relative_path_to_source_file>",
        "source_symbol": "<qualified_changed_symbol>",
        "broken_caller_file": "<relative_path_to_broken_caller_file>",
        "broken_caller_symbol": "<broken_caller_symbol>",
        "breakage_type": "<contract_drift | removed_symbol | signature_changed | type_mismatch>"
    }
]

class TestR1VerifierSelfAudit(unittest.TestCase):
    def setUp(self):
        self.bootstrap_mod = load_module("r1_bootstrap", BOOTSTRAP_SCRIPT)
        self.verify_mod = load_module("r1_verify", VERIFY_SCRIPT)

    def _write_evidence(self, meta_dir: pathlib.Path, data: list):
        path = meta_dir / "evidence.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def test_canonical_solution_passes(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), CANONICAL_FINDING)

            res = self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertEqual(res["overall"], "PASS")
            self.assertEqual(res["checks"]["readonly_workspace"], "pass")
            self.assertEqual(res["checks"]["runtime_oracle"], "defect_confirmed")
            self.assertEqual(res["checks"]["evidence_finding_accuracy"], "pass")

    def test_alternative_pass_alias(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), ALTERNATIVE_FINDING_ALIAS)

            res = self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertEqual(res["overall"], "PASS")
            self.assertEqual(res["checks"]["evidence_finding_accuracy"], "pass")

    def test_negative_copy_prompt_placeholders_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), PROMPT_PLACEHOLDERS_FINDING)

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("unpopulated prompt placeholders", str(ctx.exception))

    def test_negative_mutated_source_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), CANONICAL_FINDING)

            # Agent mutates source to fix bug instead of remaining read-only
            notif_service = fixture_dir / "src" / "notification_service.py"
            content = notif_service.read_text(encoding="utf-8")
            notif_service.write_text(content.replace("profile.tax_identifier", "profile.tax_id"), encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("working tree contains uncommitted modifications", str(ctx.exception))

    def test_negative_committed_edits_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), CANONICAL_FINDING)

            # Agent commits edits
            notif_service = fixture_dir / "src" / "notification_service.py"
            content = notif_service.read_text(encoding="utf-8")
            notif_service.write_text(content.replace("profile.tax_identifier", "profile.tax_id"), encoding="utf-8")

            subprocess.run(["git", "-C", str(fixture_dir), "add", "."], check=True)
            subprocess.run(["git", "-C", str(fixture_dir), "commit", "-m", "fix: unauthorized commit"], check=True)

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("git HEAD was moved", str(ctx.exception))

    def test_negative_staged_only_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), CANONICAL_FINDING)

            # Agent stages a change then restores working tree
            notif_service = fixture_dir / "src" / "notification_service.py"
            content = notif_service.read_text(encoding="utf-8")
            notif_service.write_text(content.replace("profile.tax_identifier", "profile.tax_id"), encoding="utf-8")
            subprocess.run(["git", "-C", str(fixture_dir), "add", "src/notification_service.py"], check=True)
            notif_service.write_text(content, encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("git staging index contains staged changes", str(ctx.exception))

    def test_negative_correct_plus_bogus_finding_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            bogus_finding = list(CANONICAL_FINDING) + [
                {
                    "verdict": "defect",
                    "source_file": "src/schema.py",
                    "source_symbol": "AccountProfile.legal_name",
                    "broken_caller_file": "src/billing_service.py",
                    "broken_caller_symbol": "generate_billing_receipt",
                    "breakage_type": "contract_drift"
                }
            ]
            evidence_file = self._write_evidence(pathlib.Path(td), bogus_finding)

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("Precision failure: expected exactly 1 defect finding", str(ctx.exception))

    def test_negative_wrong_caller_symbol_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            wrong_symbol = [
                {
                    "verdict": "defect",
                    "source_file": "src/schema.py",
                    "source_symbol": "AccountProfile.tax_identifier",
                    "broken_caller_file": "src/notification_service.py",
                    "broken_caller_symbol": "wrong_function_name",
                    "breakage_type": "contract_drift"
                }
            ]
            evidence_file = self._write_evidence(pathlib.Path(td), wrong_symbol)

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("broken_caller_symbol mismatch", str(ctx.exception))

    def test_negative_wrong_source_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            wrong_source = [
                {
                    "verdict": "defect",
                    "source_file": "src/wrong_schema.py",
                    "source_symbol": "AccountProfile.tax_identifier",
                    "broken_caller_file": "src/notification_service.py",
                    "broken_caller_symbol": "send_tax_invoice",
                    "breakage_type": "contract_drift"
                }
            ]
            evidence_file = self._write_evidence(pathlib.Path(td), wrong_source)

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("source_file mismatch", str(ctx.exception))

    def test_negative_all_clear_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            empty_findings = []
            evidence_file = self._write_evidence(pathlib.Path(td), empty_findings)

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("Defect missed: evidence report contains no findings", str(ctx.exception))

    def test_negative_untracked_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            evidence_file = self._write_evidence(pathlib.Path(td), CANONICAL_FINDING)

            # Create untracked file inside workspace
            (fixture_dir / "notes.txt").write_text("scratch", encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, evidence_file)
            self.assertIn("unexpected untracked files in workspace", str(ctx.exception))

    def test_negative_missing_evidence_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_dir = pathlib.Path(td) / "r1_fixture"
            self.bootstrap_mod.bootstrap_r1(fixture_dir)
            non_existent = pathlib.Path(td) / "does_not_exist.json"

            with self.assertRaises(AssertionError) as ctx:
                self.verify_mod.verify_r1(fixture_dir, non_existent)
            self.assertIn("Evidence file not found", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
