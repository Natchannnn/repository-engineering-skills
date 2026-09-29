# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E4. BRANCH_DIR selects variant; separate process each run."""
import os
import pathlib
import sys
import unittest

BRANCH = pathlib.Path(
    os.environ.get("BRANCH_DIR", pathlib.Path(__file__).parent.parent / "branch-defect")
).resolve()
sys.path.insert(0, str(BRANCH))

from storage import jobs as storage  # noqa: E402
from api import errors, jobs as endpoint  # noqa: E402


def denied_request(job_id, user="alice"):
    try:
        endpoint.handle(job_id, user)
        return ("no-error", b"")
    except Exception as exc:  # noqa: BLE001 - mapping decides
        return errors.to_response(exc)


class DenialTest(unittest.TestCase):
    def setUp(self):
        storage.reset_count()
        endpoint.LOG.clear()

    def test_missing_job_does_not_change_denial(self):
        st1, body1 = denied_request("ghost")
        st2, body2 = denied_request("j1")
        self.assertEqual((st1, body1), (403, b"forbidden"), f"expected 403, got {st1}")
        self.assertEqual((st2, body2), (403, b"forbidden"), f"expected 403, got {st2}")
        self.assertEqual(body1, body2, "denial bodies must be identical")

    def test_denied_request_performs_no_read(self):
        denied_request("ghost")
        denied_request("j1")
        self.assertEqual(
            storage.read_count, 0, f"expected 0, got {storage.read_count}"
        )


if __name__ == "__main__":
    unittest.main()
