"""Deterministic unit tests for repo-foundation evaluation harness."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

# Paths
TEST_DIR = Path(__file__).resolve().parent
EVALS_DIR = TEST_DIR.parent
SYS_PATH_INJECT = str(EVALS_DIR)

if SYS_PATH_INJECT not in sys.path:
    sys.path.insert(0, SYS_PATH_INJECT)

import byte_snapshot
import core
import harness


class FoundationHarnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test_fnd_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_validate_assets(self):
        """Validate that all schemas, rubric, policy, and tasks load cleanly."""
        rubric_p = EVALS_DIR / "rubric.json"
        policy_p = EVALS_DIR / "scoring_policy.json"
        self.assertTrue(rubric_p.exists())
        self.assertTrue(policy_p.exists())

        rubric = json.loads(rubric_p.read_text(encoding="utf-8"))
        policy = json.loads(policy_p.read_text(encoding="utf-8"))

        core.validate_rubric_schema(rubric)
        core.validate_scoring_policy_schema(policy)

    def test_byte_snapshot_deterministic(self):
        """Verify that identical directory contents produce identical SHA-256 tree hashes."""
        d1 = self.tmp / "d1"
        d2 = self.tmp / "d2"
        d1.mkdir()
        d2.mkdir()

        (d1 / "a.py").write_text("print('hello')\n", encoding="utf-8")
        (d2 / "a.py").write_text("print('hello')\n", encoding="utf-8")

        h1, snap1 = byte_snapshot.create_snapshot(d1, self.tmp / "out1")
        h2, snap2 = byte_snapshot.create_snapshot(d2, self.tmp / "out2")

        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_verify_cp3_compliant_workspace(self):
        """Test that a compliant CP3 workspace passes CP3_EVOLUTION checks."""
        ws = self.tmp / "cp3_ws"
        ws.mkdir()

        # Compliant ledger.py
        (ws / "ledger.py").write_text(
            """import json, os, tempfile
from pathlib import Path

LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")

def _is_valid_tenant(v) -> bool:
    return isinstance(v, str) and bool(v.strip())

def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be dict")
    kind = event.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        raise ValueError("invalid kind")
    tenant = event.get("tenant")
    if not _is_valid_tenant(tenant):
        raise ValueError("invalid tenant")

    records = read_all()
    next_id = len(records) + 1
    record = {"id": next_id, **event}
    encoded = (json.dumps(record, separators=(",", ":")) + "\\n").encode("utf-8")

    existing = LEDGER_FILE.read_bytes() if LEDGER_FILE.exists() else b""
    fd, tmp_name = tempfile.mkstemp(dir=LEDGER_FILE.parent, prefix=".tmp.")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(existing + encoded)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, LEDGER_FILE)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return next_id

def read_all() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []
    with LEDGER_FILE.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def migrate() -> int:
    if not LEDGER_FILE.exists():
        return 0
    records = read_all()
    count = 0
    updated = []
    for r in records:
        if not _is_valid_tenant(r.get("tenant")):
            r["tenant"] = "default"
            count += 1
        updated.append(r)
    if count == 0:
        return 0
    fd, tmp_name = tempfile.mkstemp(dir=LEDGER_FILE.parent, prefix=".tmp.")
    try:
        with os.fdopen(fd, "wb") as f:
            for r in updated:
                f.write((json.dumps(r, separators=(",", ":")) + "\\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, LEDGER_FILE)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return count
""",
            encoding="utf-8",
        )

        # Compliant query.py
        (ws / "query.py").write_text(
            """import json
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_p = Path(__file__).resolve().with_name(LEDGER_FILE)

def _read_all():
    if not _p.exists():
        return []
    with _p.open("r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def get_by_id(n: int):
    for r in _read_all():
        if r.get("id") == n:
            return r
    return None

def find(kind=None, tenant=None):
    records = _read_all()
    if kind is not None:
        records = [r for r in records if r.get("kind") == kind]
    if tenant is not None:
        records = [r for r in records if r.get("tenant") == tenant]
    return records
""",
            encoding="utf-8",
        )

        # Run verify via harness CLI
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "verify", "CP3_EVOLUTION", str(ws)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Verify failed:\n{res.stdout}\n{res.stderr}")
        self.assertIn("ALL CHECKS PASSED", res.stdout)

    def test_snapshot_manifest_file(self):
        """Test that snapshot works and produces valid manifest json."""
        d = self.tmp / "snap_ws"
        d.mkdir()
        (d / "file.txt").write_text("content", encoding="utf-8")
        out_json = self.tmp / "manifest.json"
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(d), "--out", str(out_json)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Snapshot failed: {res.stdout}\n{res.stderr}")
        self.assertTrue(out_json.exists())
        data = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertIn("snapshot_hash", data)

    def test_score_valid_judgment(self):
        """Test scoring a complete, valid judgment conforming to CP2 rubric requirements."""
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [
                {"id": "outcome", "claim": "Outcome achieved", "verdict": "pass", "evidence": "Verified"},
                {"id": "no_unauthorized_behavior_change", "claim": "No regressions", "verdict": "pass", "evidence": "Verified"},
                {"id": "scope_bounded", "claim": "Scope clean", "verdict": "pass", "evidence": "Verified"},
                {"id": "contract_aligned", "claim": "Contracts preserved", "verdict": "pass", "evidence": "Verified"}
            ],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "change_scope", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "repository_conformity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "ownership_and_complexity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "test_quality", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "wording_and_comments", "score": 4, "reason": "Passed", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Complete valid judgment"
        }
        j_file = self.tmp / "valid_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "score", "--judgment", str(j_file), "--checkpoint", "CP2_SLICE"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Scoring failed: {res.stdout}\n{res.stderr}")
        self.assertIn("Final Certification: CERTIFIED", res.stdout)

    def test_score_incomplete_dimensions_rejected(self):
        """Test that judgment with missing required dimensions is strictly rejected."""
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [
                {"id": "outcome", "claim": "Outcome achieved", "verdict": "pass", "evidence": "Verified"},
                {"id": "no_unauthorized_behavior_change", "claim": "No regressions", "verdict": "pass", "evidence": "Verified"},
                {"id": "scope_bounded", "claim": "Scope clean", "verdict": "pass", "evidence": "Verified"},
                {"id": "contract_aligned", "claim": "Contracts preserved", "verdict": "pass", "evidence": "Verified"}
            ],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": 4, "reason": "Passed", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Missing 5 dimensions"
        }
        j_file = self.tmp / "incomplete_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "score", "--judgment", str(j_file), "--checkpoint", "CP2_SLICE"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Missing required dimensions", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_score_unknown_dimension_rejected(self):
        """Test that judgment with an unknown dimension ID is strictly rejected."""
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [],
            "hard_failures": [],
            "dimensions": [
                {"id": "invented_fake_dimension", "score": 4, "reason": "Fake", "evidence": ["fake"]}
            ],
            "confidence": "high",
            "notes": "Invented dimension"
        }
        j_file = self.tmp / "fake_dim_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "score", "--judgment", str(j_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unknown dimension ID", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_score_null_dimension_rejected(self):
        """Test that judgment with a null dimension score is strictly rejected."""
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [
                {"id": "outcome", "claim": "Outcome achieved", "verdict": "pass", "evidence": "Verified"},
                {"id": "no_unauthorized_behavior_change", "claim": "No regressions", "verdict": "pass", "evidence": "Verified"},
                {"id": "scope_bounded", "claim": "Scope clean", "verdict": "pass", "evidence": "Verified"},
                {"id": "contract_aligned", "claim": "Contracts preserved", "verdict": "pass", "evidence": "Verified"}
            ],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": None, "reason": "Unrated", "evidence": ["none"]},
                {"id": "change_scope", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "repository_conformity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "ownership_and_complexity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "test_quality", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "wording_and_comments", "score": 4, "reason": "Passed", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Null score"
        }
        j_file = self.tmp / "null_score_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "score", "--judgment", str(j_file), "--checkpoint", "CP2_SLICE"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("has null score", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_score_unknown_bar_rejected(self):
        """Test that judgment with an unknown bar ID is strictly rejected."""
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [
                {"id": "invented_fake_bar", "claim": "Fake", "verdict": "pass", "evidence": "Fake"}
            ],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "change_scope", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "repository_conformity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "ownership_and_complexity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "test_quality", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "wording_and_comments", "score": 4, "reason": "Passed", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Invented bar"
        }
        j_file = self.tmp / "fake_bar_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "score", "--judgment", str(j_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Unknown bar ID", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_score_missing_bars_rejected(self):
        """Test that judgment missing required bars is strictly rejected."""
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "change_scope", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "repository_conformity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "ownership_and_complexity", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "test_quality", "score": 4, "reason": "Passed", "evidence": ["ok"]},
                {"id": "wording_and_comments", "score": 4, "reason": "Passed", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Missing all bars"
        }
        j_file = self.tmp / "no_bars_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "score", "--judgment", str(j_file), "--checkpoint", "CP2_SLICE"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Missing required bars", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_snapshot_bundle_destination_reuse(self):
        """Test that exporting bundle to an existing directory overwrites cleanly without merging ghost files."""
        # Setup workspace 1 with old.txt
        ws1 = self.tmp / "ws1"
        ws1.mkdir()
        (ws1 / "old.txt").write_text("old content", encoding="utf-8")

        bundle_dir = self.tmp / "exported_bundle"
        res1 = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(ws1), "--out", str(bundle_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res1.returncode, 0, f"res1 failed: {res1.stdout}\n{res1.stderr}")
        self.assertTrue((bundle_dir / "files" / "old.txt").exists())

        # Setup workspace 2 with ONLY new.txt
        ws2 = self.tmp / "ws2"
        ws2.mkdir()
        (ws2 / "new.txt").write_text("new content", encoding="utf-8")

        # Overwrite bundle_dir with ws2
        res2 = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(ws2), "--out", str(bundle_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res2.returncode, 0, f"res2 failed: {res2.stdout}\n{res2.stderr}")
        self.assertTrue((bundle_dir / "files" / "new.txt").exists())
        self.assertFalse((bundle_dir / "files" / "old.txt").exists(), "Old ghost file must not leak into reused bundle destination!")

    def test_snapshot_ancestor_overlap_rejected_safely(self):
        """Test that snapshot rejects an output path that is an ancestor of the source and preserves all files."""
        overlap_dir = self.tmp / "overlap_case"
        src_dir = overlap_dir / "source"
        src_dir.mkdir(parents=True)
        (src_dir / "input.txt").write_text("critical input", encoding="utf-8")
        unrelated_file = overlap_dir / "unrelated.txt"
        unrelated_file.write_text("critical sibling", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(overlap_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("overlaps with or contains target directory", res.stdout)
        self.assertTrue((src_dir / "input.txt").exists(), "Source file must not be deleted on overlap error!")
        self.assertTrue(unrelated_file.exists(), "Unrelated sibling file must not be deleted on overlap error!")
        self.assertEqual(unrelated_file.read_text(encoding="utf-8"), "critical sibling")

    def test_snapshot_descendant_overlap_rejected_safely(self):
        """Test that snapshot rejects an output path inside the target directory."""
        src_dir = self.tmp / "src_self"
        src_dir.mkdir()
        (src_dir / "file.txt").write_text("content", encoding="utf-8")
        nested_out = src_dir / "nested_bundle"

        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(nested_out)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("overlaps with or contains target directory", res.stdout)
        self.assertTrue((src_dir / "file.txt").exists())

    def test_snapshot_unmanaged_directory_destination_rejected(self):
        """Test that snapshot refuses to overwrite an existing directory containing non-bundle files."""
        src_dir = self.tmp / "src_unmanaged"
        src_dir.mkdir()
        (src_dir / "payload.txt").write_text("payload", encoding="utf-8")

        unmanaged_dir = self.tmp / "unmanaged_dir"
        unmanaged_dir.mkdir()
        secret_file = unmanaged_dir / "secret.txt"
        secret_file.write_text("do not wipe me", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(unmanaged_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Destination directory cannot be overwritten", res.stdout)
        self.assertTrue(secret_file.exists(), "Existing unmanaged files must not be deleted!")
        self.assertEqual(secret_file.read_text(encoding="utf-8"), "do not wipe me")

    def test_metaschema_invalid_type_rejected(self):
        """Test that validate_json_schema_definition rejects schema definitions with invalid types."""
        invalid_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "InvalidSchema",
            "type": "not_a_json_schema_type"
        }
        with self.assertRaises(core.HarnessError) as ctx:
            core.validate_json_schema_definition(invalid_schema, "test.json")
        self.assertIn("Invalid JSON Schema type", str(ctx.exception))

    def test_scoring_policy_impossible_threshold_rejected(self):
        """Test that scoring policy schema rejects impossible probability thresholds like 2/1."""
        policy_data = {
            "schema_version": "repo-foundation-harness/scoring-policy-v1",
            "policy_id": "test-policy",
            "checkpoint_weights": {
                "CP1_BOOTSTRAP": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP2_SLICE": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP3_EVOLUTION": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP4_CONTINUITY": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"}
            },
            "optional_thresholds": {
                "min_checkpoint_pass_rate": {
                    "numerator": 2,
                    "denominator": 1,
                    "display": "2/1",
                    "decimal_string": "2.00"
                }
            }
        }
        with self.assertRaises(core.HarnessError) as ctx:
            core.validate_scoring_policy_schema(policy_data)
        self.assertIn("must be between 0 and 1", str(ctx.exception))

    def test_scoring_policy_threshold_enforced(self):
        """Test that scoring enforcement fails when candidate score does not meet policy threshold."""
        # Create custom policy requiring 4.00 utility
        strict_policy = {
            "schema_version": "repo-foundation-harness/scoring-policy-v1",
            "policy_id": "strict-policy",
            "checkpoint_weights": {
                "CP1_BOOTSTRAP": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP2_SLICE": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP3_EVOLUTION": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP4_CONTINUITY": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"}
            },
            "optional_thresholds": {
                "min_trajectory_utility": {
                    "numerator": 4,
                    "denominator": 1,
                    "display": "4/1",
                    "decimal_string": "4.00"
                }
            }
        }
        pol_file = self.tmp / "strict_policy.json"
        pol_file.write_text(json.dumps(strict_policy), encoding="utf-8")

        # Judgment with score 3.0 (< 4.0)
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [
                {"id": "outcome", "claim": "Outcome achieved", "verdict": "pass", "evidence": "Verified"},
                {"id": "no_unauthorized_behavior_change", "claim": "No regressions", "verdict": "pass", "evidence": "Verified"},
                {"id": "scope_bounded", "claim": "Scope clean", "verdict": "pass", "evidence": "Verified"},
                {"id": "contract_aligned", "claim": "Contracts preserved", "verdict": "pass", "evidence": "Verified"}
            ],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": 3, "reason": "Minor defect", "evidence": ["ok"]},
                {"id": "change_scope", "score": 3, "reason": "Slight churn", "evidence": ["ok"]},
                {"id": "repository_conformity", "score": 3, "reason": "Conformed", "evidence": ["ok"]},
                {"id": "ownership_and_complexity", "score": 3, "reason": "Acceptable", "evidence": ["ok"]},
                {"id": "test_quality", "score": 3, "reason": "Moderate", "evidence": ["ok"]},
                {"id": "wording_and_comments", "score": 3, "reason": "Good", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Score 3.0"
        }
        j_file = self.tmp / "subpar_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")

        res = subprocess.run(
            [
                sys.executable,
                str(EVALS_DIR / "harness.py"),
                "score",
                "--judgment",
                str(j_file),
                "--checkpoint",
                "CP2_SLICE",
                "--policy",
                str(pol_file),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Policy threshold unmet", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_snapshot_rejects_unmanaged_directory_with_fake_manifest(self):
        """Test that snapshot rejects a directory containing a fake snapshot.json and valuable files."""
        src_dir = self.tmp / "src_valid"
        src_dir.mkdir()
        (src_dir / "code.py").write_text("print('safe')", encoding="utf-8")

        unmanaged_dir = self.tmp / "unmanaged_with_fake_manifest"
        unmanaged_dir.mkdir()
        (unmanaged_dir / "snapshot.json").write_text("not a manifest", encoding="utf-8")
        valuable_file = unmanaged_dir / "valuable.txt"
        valuable_file.write_text("precious user data", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(unmanaged_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Destination directory cannot be overwritten", res.stdout)
        self.assertTrue(valuable_file.exists(), "valuable.txt must not be deleted!")
        self.assertEqual(valuable_file.read_text(encoding="utf-8"), "precious user data")

    def test_snapshot_default_persists_without_out_argument(self):
        """Test that running snapshot without --out persists the snapshot and manifest on disk."""
        src_dir = self.tmp / "src_for_default_snap"
        src_dir.mkdir()
        unique_content = f"print('persistent_{self.tmp.name}')"
        (src_dir / "app.py").write_text(unique_content, encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Snapshot command failed: {res.stdout}\n{res.stderr}")

        # Parse output for Snapshot Directory
        match = re.search(r"Snapshot Directory:\s+(.*)", res.stdout)
        self.assertIsNotNone(match, f"Snapshot Directory path missing in stdout: {res.stdout}")
        snap_dir_path = Path(match.group(1).strip())

        try:
            self.assertTrue(snap_dir_path.exists(), f"Snapshot directory {snap_dir_path} must exist after process exit!")
            self.assertTrue((snap_dir_path / "snapshot.json").exists())
            self.assertTrue((snap_dir_path / "files" / "app.py").exists())
        finally:
            shutil.rmtree(snap_dir_path, ignore_errors=True)

    def test_score_exact_rational_boundary_fails_properly(self):
        """Test that score 22/6 (3.6666...) does NOT round up to 3.667 and correctly fails a 3.6668 threshold."""
        strict_policy = {
            "schema_version": "repo-foundation-harness/scoring-policy-v1",
            "policy_id": "rational-boundary-policy",
            "checkpoint_weights": {
                "CP1_BOOTSTRAP": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP2_SLICE": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP3_EVOLUTION": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"},
                "CP4_CONTINUITY": {"numerator": 1, "denominator": 4, "display": "1/4", "decimal_string": "0.25"}
            },
            "optional_thresholds": {
                "min_trajectory_utility": {
                    "numerator": 9167,
                    "denominator": 2500,
                    "display": "9167/2500",
                    "decimal_string": "3.6668"
                }
            }
        }
        pol_file = self.tmp / "boundary_policy.json"
        pol_file.write_text(json.dumps(strict_policy), encoding="utf-8")

        # 6 dimensions with scores 2, 4, 4, 4, 4, 4 -> sum = 22, avg = 22/6 = 3.6666...
        j_data = {
            "schema_version": "repo-foundation-harness/judgment-v1",
            "artifact_id": "0123456789abcdef",
            "verdict": "pass",
            "bar_evidence": [
                {"id": "outcome", "claim": "Outcome achieved", "verdict": "pass", "evidence": "Verified"},
                {"id": "no_unauthorized_behavior_change", "claim": "No regressions", "verdict": "pass", "evidence": "Verified"},
                {"id": "scope_bounded", "claim": "Scope clean", "verdict": "pass", "evidence": "Verified"},
                {"id": "contract_aligned", "claim": "Contracts preserved", "verdict": "pass", "evidence": "Verified"}
            ],
            "hard_failures": [],
            "dimensions": [
                {"id": "functional_correctness", "score": 2, "reason": "Minor defect", "evidence": ["ok"]},
                {"id": "change_scope", "score": 4, "reason": "Slight churn", "evidence": ["ok"]},
                {"id": "repository_conformity", "score": 4, "reason": "Conformed", "evidence": ["ok"]},
                {"id": "ownership_and_complexity", "score": 4, "reason": "Acceptable", "evidence": ["ok"]},
                {"id": "test_quality", "score": 4, "reason": "Moderate", "evidence": ["ok"]},
                {"id": "wording_and_comments", "score": 4, "reason": "Good", "evidence": ["ok"]}
            ],
            "confidence": "high",
            "notes": "Score 22/6"
        }
        j_file = self.tmp / "boundary_judgment.json"
        j_file.write_text(json.dumps(j_data), encoding="utf-8")

        res = subprocess.run(
            [
                sys.executable,
                str(EVALS_DIR / "harness.py"),
                "score",
                "--judgment",
                str(j_file),
                "--checkpoint",
                "CP2_SLICE",
                "--policy",
                str(pol_file),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Policy threshold unmet", res.stdout)
        self.assertIn("Final Certification: FAILED", res.stdout)

    def test_metaschema_invalid_definitions_rejected(self):
        """Test that validate_json_schema_definition rejects probe cases: empty type, invalid properties, duplicate required, non-numeric min."""
        probes = [
            ({"type": []}, "cannot be empty array"),
            ({"properties": 7}, "must be an object"),
            ({"items": 7}, "must be a schema object, boolean, or list"),
            ({"required": ["a", "a"]}, "contains duplicate elements"),
            ({"minimum": "oops"}, "must be a number"),
        ]
        for probe_spec, expected_substr in probes:
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "ProbeTest",
                **probe_spec
            }
            with self.assertRaises(core.HarnessError) as ctx:
                core.validate_json_schema_definition(schema, "probe_schema")
            self.assertIn(expected_substr, str(ctx.exception), f"Failed for probe {probe_spec}")

    def test_snapshot_rejects_bundle_with_unmanaged_file_in_files_dir(self):
        """Test that snapshot rejects a bundle whose files/ directory contains unmanaged extra files."""
        src_dir = self.tmp / "src_valid"
        src_dir.mkdir()
        (src_dir / "valid.txt").write_text("legitimate content", encoding="utf-8")

        dest_bundle = self.tmp / "valid_bundle"
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(dest_bundle)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue((dest_bundle / "snapshot.json").exists())

        # Inject an unmanaged file into files/ without updating snapshot.json manifest
        unmanaged_file = dest_bundle / "files" / "unmanaged.txt"
        unmanaged_file.write_text("intruder file", encoding="utf-8")

        # Validator must catch this discrepancy
        is_valid, reason = core.is_valid_snapshot_bundle(dest_bundle)
        self.assertFalse(is_valid)
        self.assertIn("unmanaged file(s) in 'files/'", reason)

        # Attempting to export snapshot over this corrupted bundle must fail and preserve unmanaged.txt
        res2 = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(dest_bundle)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res2.returncode, 1)
        self.assertIn("Destination directory cannot be overwritten", res2.stdout)
        self.assertTrue(unmanaged_file.exists(), "unmanaged.txt must not be deleted!")
        self.assertEqual(unmanaged_file.read_text(encoding="utf-8"), "intruder file")

    def test_snapshot_replacement_io_error_preserves_old_bundle(self):
        """Test that if an I/O error occurs during snapshot replacement, the old bundle is fully restored."""
        old_src = self.tmp / "old_src"
        old_src.mkdir()
        (old_src / "old.txt").write_text("initial version", encoding="utf-8")

        dest_bundle = self.tmp / "dest_bundle"
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(old_src), "--out", str(dest_bundle)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue((dest_bundle / "files" / "old.txt").exists())
        self.assertEqual((dest_bundle / "files" / "old.txt").read_text(encoding="utf-8"), "initial version")

        new_src = self.tmp / "new_src"
        new_src.mkdir()
        (new_src / "new.txt").write_text("new version", encoding="utf-8")

        # Simulate OSError during replacement deploy
        real_copytree = shutil.copytree

        def failing_copytree(src, dst, *args, **kwargs):
            if ".deploy_" in str(dst):
                raise OSError("Simulated disk full or I/O failure during replacement copy")
            return real_copytree(src, dst, *args, **kwargs)

        with mock.patch("shutil.copytree", side_effect=failing_copytree):
            with self.assertRaises(OSError):
                tree_hash, snap_dir = byte_snapshot.create_snapshot(new_src, self.tmp / "stage_test")
                harness.deploy_snapshot_bundle(snap_dir, dest_bundle, tree_hash)

        # Assert old bundle is completely intact
        self.assertTrue(dest_bundle.exists(), "Original bundle directory must exist")
        self.assertTrue((dest_bundle / "files" / "old.txt").exists(), "Original file must be preserved")
        self.assertEqual(
            (dest_bundle / "files" / "old.txt").read_text(encoding="utf-8"),
            "initial version",
            "Original content must not be modified or wiped",
        )
        # Verify no orphan backup directories remain
        backups = list(self.tmp.glob(".backup_*"))
        self.assertEqual(len(backups), 0, f"No orphan backup directories should linger: {backups}")

    def test_snapshot_idempotent_reuse_identical_hash(self):
        """Test that deploying a snapshot bundle with identical hash reuses existing valid bundle."""
        src_dir = self.tmp / "src_reuse"
        src_dir.mkdir()
        (src_dir / "file.txt").write_text("same content", encoding="utf-8")

        dest_bundle = self.tmp / "reuse_bundle"
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(dest_bundle)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

        # Record initial mtime of snapshot.json
        meta_file = dest_bundle / "snapshot.json"
        initial_mtime = meta_file.stat().st_mtime_ns

        # Run snapshot again with identical contents
        res2 = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(dest_bundle)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res2.returncode, 0)
        self.assertEqual(meta_file.stat().st_mtime_ns, initial_mtime, "Snapshot bundle must be reused cleanly without rewriting")

    def test_snapshot_default_rejects_unmanaged_file_and_preserves_bundle(self):
        """Test that running snapshot without --out twice, with an unmanaged file injected between runs, fails and preserves all data."""
        src_dir = self.tmp / "src_default_guard"
        src_dir.mkdir()
        unique_content = f"print('default_guard_{self.tmp.name}')"
        (src_dir / "index.py").write_text(unique_content, encoding="utf-8")

        # 1. First snapshot without --out
        res1 = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res1.returncode, 0, f"res1 failed: {res1.stdout}\n{res1.stderr}")
        match = re.search(r"Snapshot Directory:\s+(.*)", res1.stdout)
        self.assertIsNotNone(match)
        snap_dir_path = Path(match.group(1).strip())
        self.assertTrue(snap_dir_path.exists())

        try:
            # 2. Inject unmanaged.txt into files/
            unmanaged_file = snap_dir_path / "files" / "unmanaged.txt"
            unmanaged_file.write_text("critical unmanaged state", encoding="utf-8")

            # 3. Second snapshot without --out (same source)
            res2 = subprocess.run(
                [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir)],
                capture_output=True,
                text=True,
            )
            # Must exit 1 and reject overwrite
            self.assertEqual(res2.returncode, 1)
            self.assertIn("Destination directory cannot be overwritten", res2.stdout)

            # 4. Verify unmanaged.txt and original files are 100% byte-preserved
            self.assertTrue(unmanaged_file.exists(), "unmanaged.txt must NOT be deleted!")
            self.assertEqual(unmanaged_file.read_text(encoding="utf-8"), "critical unmanaged state")
            self.assertTrue((snap_dir_path / "files" / "index.py").exists())
        finally:
            shutil.rmtree(snap_dir_path, ignore_errors=True)

    def test_snapshot_rejects_corrupted_metadata_consistently(self):
        """Test that modifying individual metadata fields (file_count, size_bytes, sha256, total_bytes) causes all validators to reject consistently."""
        src_dir = self.tmp / "src_meta_probes"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("hello world", encoding="utf-8")

        dest_bundle = self.tmp / "meta_test_bundle"
        res = subprocess.run(
            [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(dest_bundle)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

        meta_file = dest_bundle / "snapshot.json"
        original_meta = json.loads(meta_file.read_text(encoding="utf-8"))

        probes = [
            ({"file_count": 999}, "file_count mismatch"),
            ({"total_bytes": 999999}, "total_bytes mismatch"),
            ({"snapshot_hash": "0" * 64}, "tree hash"),
        ]

        for mod_dict, expected_err in probes:
            tampered = dict(original_meta)
            tampered.update(mod_dict)
            meta_file.write_text(json.dumps(tampered, indent=2), encoding="utf-8")

            # 1. core.is_valid_snapshot_bundle must reject
            is_valid, reason = core.is_valid_snapshot_bundle(dest_bundle)
            self.assertFalse(is_valid, f"is_valid_snapshot_bundle should reject for {mod_dict}")
            self.assertIn(expected_err, reason)

            # 2. core.verify_bundle_dir must raise
            with self.assertRaises(core.HarnessError) as ctx:
                core.verify_bundle_dir(dest_bundle)
            self.assertIn(expected_err, str(ctx.exception))

            # 3. Exporting snapshot to this destination must fail with exit code 1
            res_probe = subprocess.run(
                [sys.executable, str(EVALS_DIR / "harness.py"), "snapshot", str(src_dir), "--out", str(dest_bundle)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_probe.returncode, 1, f"Command should exit 1 for {mod_dict}")
            self.assertIn("Destination directory cannot be overwritten", res_probe.stdout)

        # Restore original valid metadata
        meta_file.write_text(json.dumps(original_meta, indent=2), encoding="utf-8")
        is_valid, reason = core.is_valid_snapshot_bundle(dest_bundle)
        self.assertTrue(is_valid, f"Restored metadata must be valid: {reason}")


if __name__ == "__main__":
    unittest.main()


