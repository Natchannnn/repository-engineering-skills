# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E6. FIXTURE_DIR selects variant; separate process each run."""
import os
import pathlib
import sys
import unittest

FIX = pathlib.Path(
    os.environ.get("FIXTURE_DIR", pathlib.Path(__file__).parent.parent / "fixture")
).resolve()
sys.path.insert(0, str(FIX))

import flags  # noqa: E402
import query  # noqa: E402


class ExpiryTest(unittest.TestCase):
    def setUp(self):
        flags.reset()

    def tearDown(self):
        flags.reset()

    def test_ttl_respected(self):
        flags.add("x", True, expires_at=100)
        self.assertTrue(flags.is_active("x", 99))
        self.assertFalse(flags.is_active("x", 100), "expiry instant is exclusive")
        self.assertFalse(flags.is_active("x", 101))

    def test_purge_count_idempotent(self):
        flags.add("a", True, expires_at=10)
        flags.add("b", True, expires_at=20)
        flags.add("live", True, expires_at=999)
        self.assertEqual(flags.purge_expired(50), 2)
        self.assertEqual(flags.purge_expired(50), 0, "second purge must find nothing")
        self.assertEqual(query.active_flags(50), ["live"])

    def test_unknown_stays_false(self):
        self.assertFalse(flags.is_active("nope", 0))

    def test_boundary_type(self):
        flags.add("z", True, expires_at=100)
        resolved = flags.is_active("z", 100)
        self.assertIs(resolved, False, f"must be exactly False, got {resolved!r}")

    def test_docs_mention_ttl(self):
        text = pathlib.Path(FIX, "FLAGS.md").read_text(encoding="utf-8")
        self.assertIn("expires_at", text, "living docs must document TTL")
        self.assertIn("purge", text.lower(), "living docs must document purge")


if __name__ == "__main__":
    unittest.main()
