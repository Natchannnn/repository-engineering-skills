# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E2. FIXTURE_DIR selects variant; separate process each run."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

FIX = pathlib.Path(
    os.environ.get("FIXTURE_DIR", pathlib.Path(__file__).parent.parent / "fixture")
).resolve()
sys.path.insert(0, str(FIX))

from catalog import persistence, state  # noqa: E402
from catalog import service  # noqa: E402
from reports import current_stock as reports  # noqa: E402


def bad_rows():
    yield {"sku": 2}
    raise ValueError("input feed broke mid-iteration")


class RefreshTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        persistence.DATA_PATH = str(pathlib.Path(self.tmp.name) / "data.json")
        with open(persistence.DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({"sku": 1}, f)
        state.reset()

    def tearDown(self):
        state.reset()
        self.tmp.cleanup()

    def test_replace_failure_preserves_state(self):
        v = reports.held_view()
        with mock.patch.object(persistence, "_replace", side_effect=OSError("disk gone")):
            with self.assertRaises(OSError):
                service.refresh([{"sku": 2}])
        self.assertEqual(
            persistence.load(), {"sku": 1}, "disk must keep pre-refresh state"
        )
        self.assertEqual(
            dict(v), {"sku": 1}, f"expected live view {{'sku': 1}}, got {dict(v)}"
        )

    def test_iterator_error_preserves_state(self):
        v = reports.held_view()
        with self.assertRaises(ValueError):
            service.refresh(bad_rows())
        self.assertEqual(
            persistence.load(), {"sku": 1}, "disk must keep pre-refresh state"
        )
        self.assertEqual(
            dict(v), {"sku": 1}, f"expected live view {{'sku': 1}}, got {dict(v)}"
        )

    def test_existing_view_observes_success(self):
        v = reports.held_view()
        service.refresh([{"sku": 2}])
        self.assertEqual(persistence.load(), {"sku": 2})
        self.assertEqual(dict(v), {"sku": 2}, f"held view went stale: {dict(v)}")

    def test_success_updates_everything(self):
        service.refresh([{"sku": 2}])
        self.assertEqual(
            reports.current(), {"sku": 2}, f"report wrong after success: {reports.current()}"
        )


if __name__ == "__main__":
    unittest.main()
