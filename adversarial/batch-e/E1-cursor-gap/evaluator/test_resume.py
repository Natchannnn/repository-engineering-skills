# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E1. Point at a fixture with FIXTURE_DIR (default: ../fixture).

Run each variant in a SEPARATE process (module state is global):
  FIXTURE_DIR=../fixture  python -B -m pytest -q   # broken baseline: test 1 FAILs
  FIXTURE_DIR=../solution python -B -m pytest -q   # fixed: all PASS
"""
import os
import pathlib
import sys
import unittest

FIX = pathlib.Path(
    os.environ.get("FIXTURE_DIR", pathlib.Path(__file__).parent.parent / "fixture")
).resolve()
sys.path.insert(0, str(FIX))

from storage import events as store  # noqa: E402
from jobs import export as job  # noqa: E402


class ResumeTest(unittest.TestCase):
    def setUp(self):
        store.reset()
        self.calls = 0

        def hook():
            self.calls += 1
            if self.calls == 1:
                # Valid record arriving mid-export, outside the initial snapshot.
                store.insert({"id": 105, "ts": 1000})

        store.on_scan = hook

    def tearDown(self):
        store.reset()

    def test_filtered_gap(self):
        got = job.run_export()
        self.assertEqual(got, [101, 104], f"expected [101, 104], got {got}")

    def test_snapshot_excludes_later_inserts(self):
        got = job.run_export()
        self.assertNotIn(105, got, f"export leaked a post-snapshot record: {got}")

    def test_no_duplicates_in_order_and_bounded(self):
        got = job.run_export()
        self.assertEqual(got, sorted(set(got)), f"order/duplicates broken: {got}")
        self.assertLessEqual(self.calls, 10, f"scan loop not bounded: {self.calls}")


if __name__ == "__main__":
    unittest.main()
