#!/usr/bin/env python3
"""
Self-audit test suite for Task R2A Verifier.
Validates that verify.py accurately passes valid clean review submissions ([]),
and strictly rejects hallucinated defect findings, workspace modifications, or schema violations.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
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


class TestR2AVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap_mod = load_module("r2a_bootstrap", BOOTSTRAP_SCRIPT)
        cls.verify_mod = load_module("r2a_verify", VERIFY_SCRIPT)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture_dir = pathlib.Path(self.temp_dir.name) / "review_task_r2a"
        self.bootstrap_mod.bootstrap_r2a(self.fixture_dir)
        self.evidence_file = pathlib.Path(self.temp_dir.name) / "evidence.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_canonical_clean_passes(self):
        # Clean diff: candidate reports empty array []
        self.evidence_file.write_text("[]", encoding="utf-8")
        res = self.verify_mod.verify_r2a(self.fixture_dir, self.evidence_file)
        self.assertEqual(res["overall"], "PASS")
        self.assertEqual(res["fp"], 0)
        self.assertEqual(res["precision"], 1.0)

    def test_negative_hallucinated_defect_fails(self):
        # Candidate hallucinates that sync_worker was broken
        fake_defect = [
            {
                "verdict": "defect",
                "source_file": "src/batch_sync.py",
                "source_symbol": "sync_batch",
                "broken_caller_file": "src/sync_worker.py",
                "broken_caller_symbol": "process_queue",
                "breakage_type": "contract_drift",
            }
        ]
        self.evidence_file.write_text(json.dumps(fake_defect), encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2a(self.fixture_dir, self.evidence_file)
        self.assertIn("false positive defect", str(ctx.exception).lower())

    def test_negative_modified_workspace_fails(self):
        self.evidence_file.write_text("[]", encoding="utf-8")
        # Candidate modified a source file
        (self.fixture_dir / "src" / "batch_sync.py").write_text("# edited", encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2a(self.fixture_dir, self.evidence_file)
        self.assertIn("read-only", str(ctx.exception).lower())

    def test_negative_schema_violation_fails(self):
        # Not a list
        self.evidence_file.write_text('{"status": "ok"}', encoding="utf-8")
        with self.assertRaises(AssertionError) as ctx:
            self.verify_mod.verify_r2a(self.fixture_dir, self.evidence_file)
        self.assertIn("must be a json array", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
