#!/usr/bin/env python3
"""
Self-audit test suite for Task R2B Verifier.
Validates that verify.py accurately passes valid defect findings (canonical and aliases),
permits harmless __pycache__ from running tests,
and strictly rejects degenerate submissions ([]), hallucinated findings, extra spurious findings,
workspace modifications, or committed edits.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

DIR = pathlib.Path(__file__).parent.resolve()
BOOTSTRAP_SCRIPT = DIR / "bootstrap.py"
VERIFY_SCRIPT = DIR / "verify.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestR2BVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap_mod = load_module("r2b_bootstrap", BOOTSTRAP_SCRIPT)
        cls.verify_mod = load_module("r2b_verify", VERIFY_SCRIPT)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture_dir = pathlib.Path(self.temp_dir.name) / "review_task_r2b"
        self.bootstrap_mod.bootstrap_r2b(self.fixture_dir)
        self.evidence_file = pathlib.Path(self.temp_dir.name) / "evidence.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_canonical_defect_passes(self):
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        res = self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertEqual(res["overall"], "PASS")
        self.assertEqual(res["tp"], 1)
        self.assertEqual(res["fp"], 0)
        self.assertEqual(res["fn"], 0)
        self.assertEqual(res["precision"], 1.0)
        self.assertEqual(res["recall"], 1.0)

    def test_unittest_execution_with_pycache_passes(self):
        # Running unittest discover generates __pycache__ in src and tests
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=self.fixture_dir,
            capture_output=True,
            check=False,
        )
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        res = self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertEqual(res["overall"], "PASS")

    def test_alternative_symbol_alias_passes(self):
        alias_finding = [
            {
                "verdict": "defect",
                "source_file": "auth_service.py",
                "source_symbol": "generate_session_token",
                "broken_caller_file": "api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "signature_changed",
            }
        ]
        self.evidence_file.write_text(json.dumps(alias_finding), encoding="utf-8")
        res = self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertEqual(res["overall"], "PASS")
        self.assertEqual(res["tp"], 1)
        self.assertEqual(res["fp"], 0)

    def test_negative_degenerate_empty_array_fails(self):
        # Degenerate agent returns []
        self.evidence_file.write_text("[]", encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("target defect missed", str(ctx.exception).lower())

    def test_negative_hallucinated_wrong_symbol_fails(self):
        # Candidate accuses web_controller which was actually properly migrated
        hallucinated = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/web_controller.py",
                "broken_caller_symbol": "login_web_user",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(hallucinated), encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("target defect missed", str(ctx.exception).lower())

    def test_negative_extra_spurious_finding_fails(self):
        # Reports real defect + a second bogus finding
        mixed = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            },
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/web_controller.py",
                "broken_caller_symbol": "login_web_user",
                "breakage_type": "contract_drift",
            },
        ]
        self.evidence_file.write_text(json.dumps(mixed), encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("spurious/hallucinated defect", str(ctx.exception).lower())

    def test_negative_modified_workspace_fails(self):
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        # Candidate modified a file without commit
        (self.fixture_dir / "src" / "api_gateway.py").write_text("# edited", encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("read-only", str(ctx.exception).lower())

    def test_negative_committed_changes_fails(self):
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        # Candidate modified a file and committed it!
        (self.fixture_dir / "src" / "__init__.py").write_text("# sneaky commit\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/__init__.py"], cwd=self.fixture_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "sneaky edit"], cwd=self.fixture_dir, check=True, capture_output=True)

        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("read-only violated", str(ctx.exception).lower())

    def test_negative_missing_snapshot_fails(self):
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        snapshot_path = self.fixture_dir.parent / f"{self.fixture_dir.name}-r2b-snapshot.json"
        snapshot_path.unlink()
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("mandatory snapshot file missing", str(ctx.exception).lower())

    def test_negative_committed_changes_without_snapshot_fails(self):
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        # Candidate committed a change AND omitted/deleted snapshot file
        (self.fixture_dir / "src" / "__init__.py").write_text("# stealth edit\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/__init__.py"], cwd=self.fixture_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "stealth commit"], cwd=self.fixture_dir, check=True, capture_output=True)
        snapshot_path = self.fixture_dir.parent / f"{self.fixture_dir.name}-r2b-snapshot.json"
        snapshot_path.unlink()

        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("mandatory snapshot file missing", str(ctx.exception).lower())

    def test_negative_incomplete_snapshot_fails(self):
        canonical_finding = [
            {
                "verdict": "defect",
                "source_file": "src/auth_service.py",
                "source_symbol": "AuthService.generate_session_token",
                "broken_caller_file": "src/api_gateway.py",
                "broken_caller_symbol": "handle_login",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(canonical_finding), encoding="utf-8")
        snapshot_path = self.fixture_dir.parent / f"{self.fixture_dir.name}-r2b-snapshot.json"
        snapshot_path.write_text("{}", encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2b(self.fixture_dir, self.evidence_file)
        self.assertIn("missing mandatory", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
